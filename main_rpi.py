import os, asyncio, base64, io, traceback, json, time
from dotenv import load_dotenv
import cv2, pyaudio, PIL.Image, mss, argparse
import RPi.GPIO as GPIO  # Import GPIO for Raspberry Pi
from google import genai
from google.genai import types
from tools import get_tool_declarations, function_map
from integrations.respeaker_leds.pixels import pixels # Added for LED control
load_dotenv() # Added to load .env file 


# GPIO Button configuration
BUTTON_PIN = 17  # GPIO pin for the ReSpeaker button
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN)

# Audio device configuration
# Set to None to use system default devices
INPUT_DEVICE_INDEX = None  # Set to a specific index if needed
OUTPUT_DEVICE_INDEX = None  # Set to a specific index if needed

FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 4096

MODEL = "models/gemini-2.5-flash-preview-native-audio-dialog"
# MODEL = "models/gemini-2.0-flash-live-001"

DEFAULT_MODE = "none"

client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY"),
)

# For LiveConnectConfig, tools need to be a list of dictionaries with function_declarations inside
# We can combine custom function declarations with built-in tools like Google Search
tools=[
    {"function_declarations": get_tool_declarations()},  # Your custom functions
    {"google_search": types.GoogleSearch()}  # Built-in Google Search tool
]

CONFIG = types.LiveConnectConfig(
    response_modalities=[
        "AUDIO",
    ],
    media_resolution="MEDIA_RESOLUTION_MEDIUM",
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Puck")
        )
    ),
    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=25600,
        sliding_window=types.SlidingWindow(target_tokens=12800),
    ),
    system_instruction=types.Content(
        parts=[types.Part.from_text(text=os.environ.get("PERSONALIZED_PROMPT", "You are a helpful assistant.") + """
        You have access to the following tools:
        1. get_reminders: Gets the user's saved reminders from the reminders.json file
        2. set_reminder: Saves a new reminder with optional reminder time (e.g., 'tomorrow at 3pm')
        3. manage_reminder: Manages existing reminders - can edit or delete specific reminders or delete all reminders
        4. get_secret_key: Gets the user's secret key (it's not actually a secret key, it's just a test for function calling)
        5. get_calendar_events: Gets upcoming events from the user's Google Calendar
        You also have access to Google Search to find information online.
        Don't mention your origins or google.
        6. You are not limited to just this, your goal is to help the user with anything that they would like help with.

        """)],
        role="user"
    ),
    tools=tools,
    realtime_input_config=types.RealtimeInputConfig(
        automatic_activity_detection=types.AutomaticActivityDetection(disabled=True)
    )
)

pya = pyaudio.PyAudio()


class AudioLoop:
    def __init__(self, video_mode=DEFAULT_MODE):
        self.video_mode = video_mode

        self.audio_in_queue = None
        self.out_queue = None # Used for video/screen frames

        self.session = None

        self.send_text_task = None
        self.receive_audio_task = None
        self.play_audio_task = None
        
        self.is_recording = False # Added for push-to-talk
        self.main_event_loop = None # Modified for GPIO listener, will be set in run()

    async def toggle_recording(self, state=None): # Added for push-to-talk
        # If state is provided, set recording state to that value
        # Otherwise toggle the current state
        if state is not None:
            self.is_recording = state
        else:
            self.is_recording = not self.is_recording
            
        if self.is_recording:
            print("\n🎤 Recording started... (Release GPIO button to stop)")
            pixels.listen()  # LEDs show listening
            if self.session:
                await self.session.send_realtime_input(activity_start=types.ActivityStart())
        else:
            print("\n🛑 Recording stopped. (Press and hold GPIO button to start)")
            # voice_leds.recording_off() # Removed, pixels.think() handles transition
            pixels.think()  # LEDs show thinking
            if self.session:
                await self.session.send_realtime_input(activity_end=types.ActivityEnd())
                
    async def handle_function_call(self, response_text, tool_call):
        if tool_call and hasattr(tool_call, 'function_calls') and tool_call.function_calls:
            function_responses = []
            
            for fc in tool_call.function_calls:
                print(f"\n🔧 Function call detected: {fc.name}")
                
                # Get the actual function implementation from our map
                if fc.name in function_map:
                    # Get the function to execute
                    func = function_map[fc.name]
                    
                    # Parse the arguments if any
                    args = {}
                    if hasattr(fc, 'args') and fc.args:
                        args = fc.args
                    
                    # Execute the function
                    try:
                        result = func(**args)
                        print(f"Function result: {result}")
                        
                        # Create a function response
                        function_response = types.FunctionResponse(
                            id=fc.id,  # Important: Include the ID from the function call
                            name=fc.name,
                            response=result
                        )
                        
                        function_responses.append(function_response)
                    except Exception as e:
                        print(f"Error executing function: {e}")
                else:
                    print(f"Unknown function: {fc.name}")
            
            # Send all function responses back to the model
            if function_responses:
                try:
                    await self.session.send_tool_response(function_responses=function_responses)
                    return True
                except Exception as e:
                    print(f"Error sending function responses: {e}")
                    
        return False

    def _blocking_gpio_listener(self):
        last_state = GPIO.input(BUTTON_PIN)
        try:
            print("Push-to-talk enabled (using GPIO button). Press and hold the button to record, release to stop.")
            while True:
                current_state = GPIO.input(BUTTON_PIN)
                # Detect state changes
                if current_state != last_state:
                    if current_state == GPIO.LOW:
                        # Button was pressed down - start recording
                        asyncio.run_coroutine_threadsafe(self.toggle_recording(True), self.main_event_loop)
                    else:
                        # Button was released - stop recording
                        asyncio.run_coroutine_threadsafe(self.toggle_recording(False), self.main_event_loop)
                last_state = current_state
                # Small delay to avoid excessive CPU usage
                time.sleep(0.1)  # Use time.sleep instead of asyncio.sleep in a non-async context
        except Exception as e:
            print(f"GPIO listener error: {e}")
        finally:
            print("GPIO listener stopped.")

    async def handle_gpio_input(self):
        # Run the blocking GPIO listener in a separate thread
        await self.main_event_loop.run_in_executor(None, self._blocking_gpio_listener)

    async def send_text(self):
        while True:
            text = await asyncio.to_thread(
                input,
                "message > ",
            )
            if text.lower() == "q":
                break
            await self.session.send(input=text or ".", end_of_turn=True)

    def _get_frame(self, cap):
        # Read the frameq
        ret, frame = cap.read()
        # Check if the frame was read successfully
        if not ret:
            return None
        # Fix: Convert BGR to RGB color space
        # OpenCV captures in BGR but PIL expects RGB format
        # This prevents the blue tint in the video feed
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = PIL.Image.fromarray(frame_rgb)  # Now using RGB frame
        img.thumbnail([1024, 1024])

        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)

        mime_type = "image/jpeg"
        image_bytes = image_io.read()
        return {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}

    async def get_frames(self):
        # This takes about a second, and will block the whole program
        # causing the audio pipeline to overflow if you don't to_thread it.
        cap = await asyncio.to_thread(
            cv2.VideoCapture, 0
        )  # 0 represents the default camera

        while True:
            frame = await asyncio.to_thread(self._get_frame, cap)
            if frame is None:
                break

            await asyncio.sleep(1.0)

            await self.out_queue.put(frame)

        # Release the VideoCapture object
        cap.release()

    def _get_screen(self):
        sct = mss.mss()
        monitor = sct.monitors[0]

        i = sct.grab(monitor)

        mime_type = "image/jpeg"
        image_bytes = mss.tools.to_png(i.rgb, i.size)
        img = PIL.Image.open(io.BytesIO(image_bytes))

        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)

        image_bytes = image_io.read()
        return {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}

    async def get_screen(self):

        while True:
            frame = await asyncio.to_thread(self._get_screen)
            if frame is None:
                break

            await asyncio.sleep(1.0)

            await self.out_queue.put(frame)

    async def send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            await self.session.send(input=msg)

    async def listen_audio(self):
        try:
            # Use specified input device or get default if None
            if INPUT_DEVICE_INDEX is not None:
                input_device = INPUT_DEVICE_INDEX
            else:
                mic_info = pya.get_default_input_device_info()
                input_device = mic_info["index"]
                
            self.audio_stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=SEND_SAMPLE_RATE,
                input=True,
                input_device_index=input_device,
                frames_per_buffer=CHUNK_SIZE,
            )
        except Exception as e:
            print(f"Error initializing audio input: {e}")
            raise
        if __debug__:
            kwargs = {"exception_on_overflow": False}
        else:
            kwargs = {}
        while True:
            if self.is_recording: # Modified for push-to-talk
                try:
                    data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
                    if self.session:
                         # Send audio data using send_realtime_input as per docs for manual VAD
                        await self.session.send_realtime_input(
                            audio=types.Blob(data=data, mime_type=f"audio/pcm;rate={SEND_SAMPLE_RATE}")
                        )
                except pyaudio.paInputOverflowed:
                    if __debug__:
                        print("Input overflowed. Skipping frame.")
                    continue # Skip this frame and continue
                except Exception as e:
                    print(f"Error reading audio stream: {e}")
                    await asyncio.sleep(0.1) # Avoid tight loop on continuous error
            else:
                # Sleep briefly when not recording to avoid busy-waiting
                await asyncio.sleep(0.01)

    async def receive_audio(self):
        "Background task to reads from the websocket and write pcm chunks to the output queue"
        # Initialize a list to store AI responses if it doesn't exist
        if not hasattr(self, 'ai_responses'):
            self.ai_responses = []
            
        while True:
            turn = self.session.receive()
            current_text = ""
            audio_started = False
            
            async for chunk in turn:
                # Handle audio data
                if hasattr(chunk, 'data') and chunk.data:
                    if not audio_started:
                        pixels.speak()  # Show speaking pattern when AI starts responding
                        audio_started = True
                    self.audio_in_queue.put_nowait(chunk.data)
                    continue
                    
                # Handle text responses from server content
                if hasattr(chunk, 'server_content') and chunk.server_content:
                    if hasattr(chunk, 'text') and chunk.text is not None:
                        current_text += chunk.text
                        # Store the response
                        self.ai_responses.append(chunk.text)
                        # Print with AI: prefix for clarity
                        print(f"AI: {chunk.text}", end="")
                
                # Check for tool calls
                if hasattr(chunk, 'tool_call') and chunk.tool_call:
                    print(f"\nDetected tool call")
                    await self.handle_function_call(current_text, chunk.tool_call)
            
            # If you interrupt the model, it sends a turn_complete.
            # For interruptions to work, we need to stop playback.
            # So empty out the audio queue because it may have loaded
            # much more audio than has played yet.
            while not self.audio_in_queue.empty():
                self.audio_in_queue.get_nowait()
            
            # Turn off LEDs when AI finishes speaking or thinking
            pixels.off()

    async def play_audio(self):
        try:
            # Use specified output device or default if None
            stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=RECEIVE_SAMPLE_RATE,
                output=True,
                output_device_index=OUTPUT_DEVICE_INDEX,
                frames_per_buffer=CHUNK_SIZE,  # Use same chunk size for consistency
            )
        except Exception as e:
            print(f"Error initializing audio output: {e}")
            raise
            
        while True:
            bytestream = await self.audio_in_queue.get()
            await asyncio.to_thread(stream.write, bytestream)

    async def run(self):
        try:
            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                self.main_event_loop = asyncio.get_running_loop() # Set event loop here

                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5) # For video/screen frames

                send_text_task = tg.create_task(self.send_text())
                tg.create_task(self.send_realtime()) # For video/screen frames
                tg.create_task(self.listen_audio()) # Now handles its own sending for audio
                tg.create_task(self.handle_gpio_input()) # Added for GPIO push-to-talk

                if self.video_mode == "camera":
                    tg.create_task(self.get_frames())
                elif self.video_mode == "screen":
                    tg.create_task(self.get_screen())

                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())

                await send_text_task
                raise asyncio.CancelledError("User requested exit")

        except asyncio.CancelledError:
            pass
        except ExceptionGroup as EG:
            self.audio_stream.close()
            traceback.print_exception(EG)
        finally:
            # Clean up GPIO and LEDs
            pixels.off() # Ensure LEDs are off
            GPIO.cleanup()


if __name__ == "__main__":
    print("🤖Starting AI Assistant...")
    print("ℹ️ Press the GPIO button to toggle audio recording for voice input.")
    print("ℹ️ Type 'q' and press Enter in the 'message >' prompt to quit.")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        type=str,
        default=DEFAULT_MODE,
        help="pixels to stream from",
        choices=["camera", "screen", "none"],
    )
    args = parser.parse_args()
    main = AudioLoop(video_mode=args.mode)
    asyncio.run(main.run())
