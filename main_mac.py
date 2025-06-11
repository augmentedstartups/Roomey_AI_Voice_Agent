import os, asyncio, base64, io, traceback, json
from pynput import keyboard as pynput_keyboard
from dotenv import load_dotenv
import cv2, pyaudio, PIL.Image, mss, argparse
from google import genai
from google.genai import types
from tools import get_tool_declarations, function_map
import threading
import signal
import speech_recognition as sr
import datetime

load_dotenv() # Added to load .env file 


FORMAT = pyaudio.paInt16
CHANNELS = int(os.environ.get("CHANNELS", 1))
SEND_SAMPLE_RATE = int(os.environ.get("SEND_SAMPLE_RATE", 16000))
RECEIVE_SAMPLE_RATE = int(os.environ.get("RECEIVE_SAMPLE_RATE", 24000))
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", 1024))
VOICE_NAME = os.environ.get("VOICE_NAME", "Kore")

MODEL = "models/gemini-2.5-flash-preview-native-audio-dialog"
# MODEL = "models/gemini-2.0-flash-live-001"

DEFAULT_MODE = os.environ.get("DEFAULT_MODE", "none")

client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY"),
)

# For LiveConnectConfig, tools need to be a list of dictionaries with function_declarations inside
# We can combine custom function declarations with built-in tools like Google Search
tools=[
    {"function_declarations": get_tool_declarations()},  # Your custom functions
    {"google_search": types.GoogleSearch()}  # Built-in Google Search tool
]

# Integration flags (should match tools.py)
LINKEDIN_FORMATTER_INTEGRATION = os.getenv('LINKEDIN_FORMATTER_INTEGRATION', 'false').lower() == 'true'
HASS_INTEGRATION = os.getenv('HASS_INTEGRATION', 'false').lower() == 'true'
GOOGLE_CALENDAR_INTEGRATION = os.getenv('GOOGLE_CALENDAR_INTEGRATION', 'false').lower() == 'true'

# Build dynamic tool list for system instruction
TOOL_DESCRIPTIONS = [
    "- get_reminders: Gets your saved reminders from the reminders.json file",
    "- set_reminder: Saves a new reminder with optional reminder time (e.g., 'tomorrow at 3pm')",
    "- manage_reminder: Manage, edit, or delete your reminders",
    "- get_secret_key: Gets your secret key (for testing function calling)",
]


if GOOGLE_CALENDAR_INTEGRATION:
    TOOL_DESCRIPTIONS.append(
        "- get_calendar_events: Gets your Google Calendar events"
    )

if HASS_INTEGRATION:
    TOOL_DESCRIPTIONS += [
        "- control_home_entity: Control a home entity (e.g., turn on a light)",
        "- control_home_climate: Control a home climate (e.g., set the temperature)",
        "- get_home_entities_in_room: Get the entities in a specific room",
        "- find_home_entities_by_name: Find entities by name",
    ]
if LINKEDIN_FORMATTER_INTEGRATION:
    TOOL_DESCRIPTIONS.append(
        "- format_linkedin_post: Generate a LinkedIn post from provided context. The function will extract a topic and create a professionally formatted, viral-style post."
    )


TOOL_DESCRIPTIONS = [desc for desc in TOOL_DESCRIPTIONS if desc]

system_instruction_text = os.environ.get("PERSONALIZED_PROMPT", "You are a helpful assistant.") + "\nYou have access to the following tools:\n" + "\n".join(TOOL_DESCRIPTIONS) + "\n\nYou also have access to Google Search to find information online.\nDon't mention your origins or google.\n"

CONFIG = types.LiveConnectConfig(
    response_modalities=[
        "AUDIO",
    ],
    media_resolution="MEDIA_RESOLUTION_MEDIUM",
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE_NAME)
        )
    ),
    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=25600,
        sliding_window=types.SlidingWindow(target_tokens=12800),
    ),
    system_instruction=types.Content(
        parts=[types.Part.from_text(text=system_instruction_text)],
        role="user"
    ),
    tools=tools,
    realtime_input_config=types.RealtimeInputConfig(
        automatic_activity_detection=types.AutomaticActivityDetection(disabled=True)
    )
)

pya = pyaudio.PyAudio()
info = pya.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')

for i in range(0, numdevices):
    if (pya.get_device_info_by_index(i).get('maxInputChannels')) > 0:
        print ("Input Device id ", i, " - ", pya.get_device_info_by_index(i).get('name'))

LOG_CONVERSATION = os.getenv('LOG_CONVERSATION', 'false').lower() == 'true'

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
        self.main_event_loop = None # Modified for keyboard listener, will be set in run()
        self.audio_buffer = bytearray()  # Buffer for audio to be transcribed
        if LOG_CONVERSATION:
            self.recognizer = sr.Recognizer()
            print("Recognizer initialized")
            # self.sr_mic = sr.Microphone()
            # print("Microphone initialized")
        self.log_file_path = None

    def _get_log_file_path(self):
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        return os.path.join(log_dir, f'{today}.txt')

    def _log_message(self, role, message):
        if not self.log_file_path:
            self.log_file_path = self._get_log_file_path()
        with open(self.log_file_path, 'a', encoding='utf-8') as f:
            f.write(f"{role}: {message}\n")

    async def toggle_recording(self): # Added for push-to-talk
        self.is_recording = not self.is_recording
        if self.is_recording:
            print("\n🎤 Recording started... (Press 't' to stop)")
            self.audio_buffer = bytearray()  # Reset buffer
            if self.session:
                await self.session.send_realtime_input(activity_start=types.ActivityStart())
        else:
            print("\n🛑 Recording stopped. (Press 't' to start)")
            if self.session:
                await self.session.send_realtime_input(activity_end=types.ActivityEnd())
            # After recording stops, run STT and log if enabled
            if LOG_CONVERSATION and self.audio_buffer:
                try:
                    import wave
                    import tempfile
                    # Write buffer to a temporary WAV file for SpeechRecognition
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_wav:
                        with wave.open(tmp_wav, 'wb') as wf:
                            wf.setnchannels(int(CHANNELS))
                            wf.setsampwidth(pya.get_sample_size(FORMAT))
                            wf.setframerate(int(SEND_SAMPLE_RATE))
                            wf.writeframes(self.audio_buffer)
                        tmp_wav_path = tmp_wav.name
                        #print(f"[DEBUG] Temporary WAV file created at: {tmp_wav_path}")
                    with sr.AudioFile(tmp_wav_path) as source:
                        audio = self.recognizer.record(source)
                        try:
                            text = self.recognizer.recognize_google(audio)
                            print(f"\n[SpeechRecognition] You said: {text}")
                            self._log_message("User", text)
                        except sr.UnknownValueError:
                            print("\n[SpeechRecognition] Could not understand audio")
                            self._log_message("User", "[Unrecognized speech]")
                        except sr.RequestError as e:
                            print(f"\n[SpeechRecognition] Recognition error: {e}")
                            self._log_message("User", f"[Recognition error: {e}]")
                    os.remove(tmp_wav_path)
                except Exception as e:
                    print(f"\n[SpeechRecognition] Error: {e}")
                    self._log_message("User", f"[STT error: {e}]")

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

    def _on_press(self, key): # Changed for pynput
        try:
            if key == pynput_keyboard.KeyCode.from_char('t'):
                asyncio.run_coroutine_threadsafe(self.toggle_recording(), self.main_event_loop)
        except AttributeError:
            # Special keys (like shift, alt, etc.) don't have a char attribute
            pass
        except Exception as e:
            print(f"Error in _on_press: {e}")


    def _blocking_listen_for_toggle_key(self): # Changed for pynput
        # pynput listener runs in its own thread.
        # The listener will automatically stop if this function's thread is stopped or if an error occurs.
        with pynput_keyboard.Listener(on_press=self._on_press) as listener:
            try:
                print("Push-to-talk enabled (using pynput). Press 't' to toggle recording.")
                listener.join() # This blocks until the listener stops
            except Exception as e:
                print(f"Pynput listener error: {e}")
            finally:
                print("Pynput listener stopped.")


    async def handle_keyboard_input(self): # Changed for pynput
        # Run the blocking pynput listener in a separate thread
        # The listener itself manages its own thread for event listening.
        await self.main_event_loop.run_in_executor(None, self._blocking_listen_for_toggle_key)

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
        mic_info = pya.get_default_input_device_info()
        self.audio_stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=int(CHANNELS),
            rate=int(SEND_SAMPLE_RATE),
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=CHUNK_SIZE,
        )
        if __debug__:
            kwargs = {"exception_on_overflow": False}
        else:
            kwargs = {}
        while True:
            if self.is_recording: # Modified for push-to-talk
                try:
                    data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
                    if self.session:
                        await self.session.send_realtime_input(
                            audio=types.Blob(data=data, mime_type=f"audio/pcm;rate={SEND_SAMPLE_RATE}")
                        )
                    if LOG_CONVERSATION:
                        self.audio_buffer.extend(data)
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
            try:
                turn = self.session.receive()
                current_text = ""
                received_audio = False
                system_audio_buffer = bytearray()
                async for chunk in turn:
                    # Handle audio data
                    if hasattr(chunk, 'data') and chunk.data:
                        self.audio_in_queue.put_nowait(chunk.data)
                        received_audio = True
                        system_audio_buffer.extend(chunk.data)
                        continue
                    # Handle text responses from server content
                    if hasattr(chunk, 'server_content') and chunk.server_content:
                        if hasattr(chunk, 'text') and chunk.text is not None:
                            current_text += chunk.text
                            # Store the response
                            self.ai_responses.append(chunk.text)
                            # Print with AI: prefix for clarity
                            print(f"[DEBUG] Gemini response chunk: {chunk.text}")
                            print(f"AI: {chunk.text}", end="")
                    # Check for tool calls
                    if hasattr(chunk, 'tool_call') and chunk.tool_call:
                        print(f"\nDetected tool call")
                        await self.handle_function_call(current_text, chunk.tool_call)
                # Log the Gemini response for this turn
                if LOG_CONVERSATION:
                    if current_text.strip():
                        self._log_message("System", current_text.strip())
                    elif received_audio and system_audio_buffer:
                        try:
                            import wave
                            import tempfile
                            # Write buffer to a temporary WAV file for SpeechRecognition
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_wav:
                                with wave.open(tmp_wav, 'wb') as wf:
                                    wf.setnchannels(int(CHANNELS))
                                    wf.setsampwidth(pya.get_sample_size(FORMAT))
                                    wf.setframerate(int(RECEIVE_SAMPLE_RATE))
                                    wf.writeframes(system_audio_buffer)
                                tmp_wav_path = tmp_wav.name
                                #print(f"[DEBUG] Temporary WAV file for Gemini audio at: {tmp_wav_path}")
                            recognizer = getattr(self, 'recognizer', None)
                            if recognizer is None:
                                recognizer = sr.Recognizer()
                            with sr.AudioFile(tmp_wav_path) as source:
                                audio = recognizer.record(source)
                                try:
                                    text = recognizer.recognize_google(audio)
                                    print(f"\n[SpeechRecognition] AI said: {text}")
                                    self._log_message("Roomey", text)
                                except sr.UnknownValueError:
                                    print("\n[SpeechRecognition] Could not understand Gemini audio")
                                    self._log_message("Roomey", "[Unrecognized Gemini audio]")
                                except sr.RequestError as e:
                                    print(f"\n[SpeechRecognition] Recognition error (Gemini): {e}")
                                    self._log_message("Roomey", f"[Recognition error (Gemini): {e}]")
                            os.remove(tmp_wav_path)
                        except Exception as e:
                            print(f"\n[SpeechRecognition] Error transcribing Gemini audio: {e}")
                            self._log_message("Roomey", f"[STT error (Gemini): {e}]")
                # Always flush log file after writing
                if self.log_file_path:
                    try:
                        with open(self.log_file_path, 'a', encoding='utf-8') as f:
                            f.flush()
                    except Exception as e:
                        print(f"[DEBUG] Error flushing log file: {e}")
            except Exception as e:
                print(f"[DEBUG] Error in receive_audio: {e}")
                await asyncio.sleep(2)

    async def play_audio(self):
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
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
                tg.create_task(self.handle_keyboard_input()) # Only push-to-talk
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


def shutdown_handler(signum, frame):
    print("\nShutting down gracefully...")
    os._exit(0)  # Force exit (works even if threads are running)

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

if __name__ == "__main__":
    print("🤖Starting AI Assistant...")
    print("ℹ️ Press 't' to toggle audio recording for voice input.")
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
