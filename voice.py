import asyncio
from openai import AsyncOpenAI
from openai.helpers import LocalAudioPlayer
import utils

# Initialize the OpenAI client (can be done globally or within the function)
openai_client = AsyncOpenAI()

async def play_audio_from_text(input_text: str) -> None:
    instructions = utils.instructions

    print("\nGenerating speech... 🔊")
    try:
        async with openai_client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",  # Using a generally available model, adjust if needed
            voice="coral",           # Example voice, can be changed
            input=input_text,
            instructions=instructions,
            response_format="pcm",   # Pulse Code Modulation, common raw audio format
        ) as response:
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