import asyncio
import time
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from openai.helpers import LocalAudioPlayer
from utils.instructions import instructions

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client with API key from .env
openai_client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

async def play_audio_from_text(input_text: str) -> None:
    # instructions is now directly imported from utils.instructions

    print("\nGenerating speech... 🔊")
    try:
        start_time = time.time()
        async with openai_client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",  # Using a generally available model, adjust if needed
            voice="onyx",           # Example voice, can be changed
            input=input_text,
            instructions=instructions,
            response_format="pcm",   # Pulse Code Modulation, common raw audio format
        ) as response:
            generation_time = time.time() - start_time
            print(f"Speech generated in {generation_time:.2f} seconds")
            print("Playing audio... 🎶\n")
            await LocalAudioPlayer().play(response)
        print("Playback finished. ✨")
    except Exception as e:
        print(f"An error occurred: {e}")

def get_user_input_and_play():
    print("🧘 Welcome to your moment of mindfulness audio generator.")
    print("-------------------------------------------------------")
    user_text = input("Please enter the text:\n> ")

    if not user_text.strip():
        user_text = "Hello"
        print("\nUsing default mindfulness message.")

    asyncio.run(play_audio_from_text(user_text))

if __name__ == "__main__":
    get_user_input_and_play()