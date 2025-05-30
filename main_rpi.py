"""
## Documentation
Quickstart: https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_started_LiveAPI.py

## Setup

To install the dependencies for this script, run:

```
pip install google-genai opencv-python pyaudio pillow mss
```

Note: This version uses terminal input instead of pynput for headless operation.
"""

import os
import asyncio
import base64
import io
import traceback
import threading # For non-blocking input handling
from dotenv import load_dotenv # Added to load .env file
import time

import cv2
import pyaudio
import PIL.Image
import mss
import RPi.GPIO as GPIO

import argparse

from google import genai
from google.genai import types
from tools import get_tool_declarations, function_map
from integrations.respeaker_leds.voice_assistant_leds import voice_leds
load_dotenv() # Added to load .env file


# Audio configuration
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000  # Keep mic input at 16kHz as required by Gemini
RECEIVE_SAMPLE_RATE = 24000  # Restored to 24kHz for correct voice pitch
CHUNK_SIZE = 4096  # Further increased buffer size for smoother playback

# Audio buffer configuration
AUDIO_BUFFER_SIZE = 5  # Reduced buffer size for lower latency while maintaining smoothness

# Audio thread priority (higher number = higher priority, range 0-99)
AUDIO_THREAD_PRIORITY = 80  # Set audio threads to high priority

# Audio device configuration
INPUT_DEVICE_INDEX = 2  # Index 2: Logitech Webcam C930e
OUTPUT_DEVICE_INDEX = None  # Use None to use system default (headphone jack via ~/.asoundrc)

# GPIO Button configuration
BUTTON_PIN = 17  # GPIO pin for the ReSpeaker button
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN)

MODEL = "models/gemini-2.5-flash-preview-native-audio-dialog"
# MODEL = "models/gemini-2.0-flash-live-001"


DEFAULT_MODE = "text"

HEADLESS = True  # Set to True when running without a display

client = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=os.environ.get("GEMINI_API_KEY"),
)

# For LiveConnectConfig, tools need to be a list of dictionaries with function_declarations inside
# We can combine custom function declarations with built-in tools like Google Search
tools = [
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
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Zephyr")
        )
    ),
    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=25600,
        sliding_window=types.SlidingWindow(target_tokens=12800),
    ),
    system_instruction=types.Content(
        parts=[types.Part.from_text(text="""You are a helpful assistant. My name is Ritesh Kanjee, founder of Augmented AI. I am a tech entrepreneur and AI enthusiast. I live in South Africa.
        You have access to the following tools:
        1. get_reminders: Gets the user's saved reminders from the reminders.json file
        2. set_reminder: Saves a new reminder with optional reminder time (e.g., 'tomorrow at 3pm')
        3. manage_reminder: Manages existing reminders - can edit or delete specific reminders or delete all reminders
        4. get_secret_key: Gets the user's secret key (it's not actually a secret key, it's just a test for function calling)
        5. get_calendar_events: Gets upcoming events from the user's Google Calendar
        
        You also have access to Google Search to find information online.
        Don't mention your origins or google.

        """)],
        role="user"
    ),
    tools=tools,
    realtime_input_config=types.RealtimeInputConfig( # Added to disable VAD
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
        self.main_event_loop = None # Modified for keyboard listener, will be set in run()

    async def toggle_recording(self, state=None): # Modified for GPIO button
        # If state is provided, set recording state to that value
        # Otherwise toggle the current state
        if state is not None:
            self.is_recording = state
        else:
            self.is_recording = not self.is_recording
            
        if self.is_recording:
            print("\n🎤 Recording started...")
            # Activate recording LEDs
            voice_leds.recording_on()
            if self.session:
                await self.session.send_realtime_input(activity_start=types.ActivityStart())
        else:
            print("\n🛑 Recording stopped.")
            # Turn off recording LEDs and show thinking pattern
            voice_leds.recording_off()
            voice_leds.thinking()
            if self.session:
                await self.session.send_realtime_input(activity_end=types.ActivityEnd())
                
    async def handle_function_call(self, response_text, tool_call):
        if tool_call and hasattr(tool_call, 'function_calls') and tool_call.function_calls:
            function_responses = []
            
            # Show thinking pattern while executing functions
            voice_leds.thinking()
            
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
                        voice_leds.error()  # Show error pattern
                else:
                    print(f"Unknown function: {fc.name}")
                    voice_leds.error()  # Show error pattern
            
            # Send all function responses back to the model
            if function_responses:
                try:
                    # Continue showing thinking pattern while waiting for response
                    voice_leds.thinking()
                    await self.session.send_tool_response(function_responses=function_responses)
                    return True
                except Exception as e:
                    print(f"Error sending function responses: {e}")
                    voice_leds.error()  # Show error pattern
                    
        return False

    def _gpio_button_listener(self):
        """GPIO button-based listener for ReSpeaker button"""
        print("Push-to-talk enabled. Press the ReSpeaker button to talk.")
        last_state = GPIO.input(BUTTON_PIN)
        try:
            while True:
                current_state = GPIO.input(BUTTON_PIN)
                
                # Button state changed
                if current_state != last_state:
                    if current_state == GPIO.LOW:  # Button pressed (active low)
                        print("Button pressed - Starting recording")
                        asyncio.run_coroutine_threadsafe(self.toggle_recording(True), self.main_event_loop)
                    else:  # Button released
                        print("Button released - Stopping recording")
                        asyncio.run_coroutine_threadsafe(self.toggle_recording(False), self.main_event_loop)
                    
                    last_state = current_state
                    
                # Small delay to prevent CPU hogging
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Error in GPIO button listener: {e}")
        finally:
            print("GPIO button listener stopped.")
            GPIO.cleanup()


    def _blocking_listen_for_toggle_key(self):
        """Blocking function that listens for GPIO button input"""
        try:
            self._gpio_button_listener()
        except Exception as e:
            print(f"GPIO button listener error: {e}")
        finally:
            print("GPIO button listener stopped.")


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
        # Skip camera capture in headless mode
        if HEADLESS:
            print("Camera capture disabled in headless mode.")
            return
            
        # This takes about a second, and will block the whole program
        # causing the audio pipeline to overflow if you don't to_thread it.
        try:
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
        except Exception as e:
            print(f"Error in camera capture: {e}")
            print("Continuing without camera...")

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
        # Skip screen capture in headless mode
        if HEADLESS:
            print("Screen capture disabled in headless mode.")
            return
            
        try:
            while True:
                frame = await asyncio.to_thread(self._get_screen)
                if frame is None:
                    break

                await asyncio.sleep(1.0)

                await self.out_queue.put(frame)

        except Exception as e:
            print(f"Error in screen capture: {e}")
            print("Continuing without screen capture...")

    async def send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            await self.session.send(input=msg)

    async def listen_audio(self):
        try:
            # Use the Logitech C930e webcam microphone for input
            self.audio_stream = pya.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=SEND_SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE,
                input_device_index=INPUT_DEVICE_INDEX,
            )
            
            if __debug__:
                kwargs = {"exception_on_overflow": False}
            else:
                kwargs = {}
                
        except Exception as e:
            print(f"Error initializing audio input: {e}")
            raise
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
            response_started = False
            
            # Clear the audio queue before starting a new response
            while not self.audio_in_queue.empty():
                try:
                    self.audio_in_queue.get_nowait()
                except:
                    pass
                    
            async for chunk in turn:
                # Handle audio data
                if hasattr(chunk, 'data') and chunk.data:
                    # If this is the first audio data chunk, switch to speaking LED pattern
                    if not response_started:
                        voice_leds.speaking()
                        response_started = True
                        print("Receiving audio response...")
                    
                    try:
                        # Add audio chunk to queue with error handling
                        await self.audio_in_queue.put(chunk.data)
                    except Exception as e:
                        print(f"Error queuing audio data: {e}")
                    continue
                    
                # Handle text responses from server content
                if hasattr(chunk, 'server_content') and chunk.server_content:
                    if hasattr(chunk, 'text') and chunk.text is not None:
                        # If this is the first text chunk, switch to speaking LED pattern
                        if not response_started:
                            voice_leds.speaking()
                            response_started = True
                            
                        current_text += chunk.text
                        # Store the response
                        self.ai_responses.append(chunk.text)
                        # Print with AI: prefix for clarity
                        print(f"AI: {chunk.text}", end="")
                
                # Check for tool calls
                if hasattr(chunk, 'tool_call') and chunk.tool_call:
                    print(f"\nDetected tool call")
                    await self.handle_function_call(current_text, chunk.tool_call)
            
            # Turn off speaking LEDs when response is complete
            voice_leds.recording_off()
            
            # If you interrupt the model, it sends a turn_complete.
            # For interruptions to work, we need to stop playback.
            # So empty out the audio queue because it may have loaded
            # much more audio than has played yet.
            while not self.audio_in_queue.empty():
                self.audio_in_queue.get_nowait()

    async def play_audio(self):
        # Try to set real-time priority for this thread
        try:
            import ctypes
            import ctypes.util
            
            # Load the POSIX threads library
            librt = ctypes.CDLL(ctypes.util.find_library('pthread'))
            
            # Define the necessary structures and constants
            class sched_param(ctypes.Structure):
                _fields_ = [('sched_priority', ctypes.c_int)]
                
            SCHED_FIFO = 1  # Real-time scheduling policy
            
            # Set the priority for the current thread
            param = sched_param(AUDIO_THREAD_PRIORITY)
            result = librt.pthread_setschedparam(
                0,  # 0 means current thread
                SCHED_FIFO,
                ctypes.byref(param)
            )
            
            if result == 0:
                print(f"Audio thread priority set to {AUDIO_THREAD_PRIORITY} (real-time)")
            else:
                print(f"Could not set thread priority: error code {result}")
        except Exception as e:
            print(f"Could not set thread priority: {e}")
        
        # Disable CPU throttling if possible
        try:
            # Run a command to set CPU governor to performance mode
            import subprocess
            subprocess.run(["echo", "performance", ">", "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"], 
                          shell=True, 
                          stderr=subprocess.DEVNULL)
            print("CPU set to performance mode")
        except Exception as e:
            print(f"Could not set CPU governor: {e}")
        
        try:
            # Use the system default output device with optimized settings
            stream = pya.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RECEIVE_SAMPLE_RATE,
                output=True,
                frames_per_buffer=CHUNK_SIZE,
                output_device_index=OUTPUT_DEVICE_INDEX,
            )
            print(f"Audio output initialized with sample rate: {RECEIVE_SAMPLE_RATE}, buffer size: {CHUNK_SIZE}")
        except Exception as e:
            print(f"Error initializing audio output: {e}")
            raise
            
        # Buffer to collect audio chunks for smoother playback
        audio_buffer = []
        is_buffering = True
        buffer_count = 0
        
        while True:
            try:
                bytestream = await self.audio_in_queue.get()
                
                # Initial buffering phase
                if is_buffering:
                    audio_buffer.append(bytestream)
                    buffer_count += 1
                    
                    # Start playback once we have enough buffered chunks
                    if buffer_count >= AUDIO_BUFFER_SIZE:
                        is_buffering = False
                        print(f"Starting audio playback with {buffer_count} buffered chunks")
                        
                        # Play the buffered audio
                        for chunk in audio_buffer:
                            # Use direct write without asyncio to reduce overhead
                            stream.write(chunk)
                        audio_buffer = []
                else:
                    # Normal playback after initial buffering - direct write for less overhead
                    stream.write(bytestream)
                    
            except Exception as e:
                print(f"Error during audio playback: {e}")
                await asyncio.sleep(0.1)  # Avoid tight loop on error

    async def run(self):
        try:
            # Initialize LEDs - show wakeup pattern
            voice_leds.recording_off()
            
            # Set higher priority for this process to improve audio processing
            try:
                import os
                os.nice(-10)  # Lower nice value = higher priority (range: -20 to 19)
                print("Process priority increased for better audio performance")
            except Exception as e:
                print(f"Could not set process priority: {e}")
                
            # Reduce background processes if possible
            try:
                import subprocess
                # Stop unnecessary services that might be using CPU
                services_to_stop = ["bluetooth", "cups", "avahi-daemon"]
                for service in services_to_stop:
                    try:
                        subprocess.run(["systemctl", "stop", service], 
                                      stderr=subprocess.DEVNULL,
                                      stdout=subprocess.DEVNULL)
                        print(f"Stopped {service} service for better performance")
                    except:
                        pass
            except Exception as e:
                print(f"Could not optimize system services: {e}")
            
            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                self.main_event_loop = asyncio.get_running_loop() # Set event loop here

                # Increase the audio queue size for better buffering
                self.audio_in_queue = asyncio.Queue(maxsize=100)
                self.out_queue = asyncio.Queue(maxsize=5) # For video/screen frames

                send_text_task = tg.create_task(self.send_text())
                tg.create_task(self.send_realtime()) # For video/screen frames
                tg.create_task(self.listen_audio()) # Now handles its own sending for audio
                tg.create_task(self.handle_keyboard_input()) # Added for push-to-talk

                if self.video_mode == "camera":
                    tg.create_task(self.get_frames())
                elif self.video_mode == "screen":
                    tg.create_task(self.get_screen())

                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())

                await send_text_task
                raise asyncio.CancelledError("User requested exit")

        except asyncio.CancelledError:
            # Clean up LEDs
            voice_leds.cleanup()
            pass
        except ExceptionGroup as EG:
            # Show error pattern and clean up
            voice_leds.error()
            voice_leds.cleanup()
            self.audio_stream.close()
            traceback.print_exception(EG)


if __name__ == "__main__":
    print("🤖Starting AI Assistant...")
    print("ℹ️ Press the ReSpeaker button to talk.")
    print("ℹ️ Type 'q' and press Enter in the 'message >' prompt to quit.")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        type=str,
        default=DEFAULT_MODE,
        help="Mode to use for input. Default: %(default)s",
        choices=["camera", "screen", "text"],
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=HEADLESS,
        help="Run in headless mode without display. Forces text mode.",
    )
    args = parser.parse_args()

    # Force text mode if headless is enabled
    if args.headless:
        print("Running in headless mode. Using text mode only.")
        args.mode = "text"

    try:
        main = AudioLoop(video_mode=args.mode)
        asyncio.run(main.run())
    except KeyboardInterrupt:
        print("\nExiting application...")
    except Exception as e:
        print(f"\nError in main application: {e}")
        # Show error pattern on LEDs
        voice_leds.error()
    finally:
        # Clean up resources on exit
        voice_leds.cleanup()
        GPIO.cleanup()

