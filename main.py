import asyncio
import sys
from openai.types.responses import ResponseTextDeltaEvent
from agents import Runner
from agents_collection import triage_agent
from voice import play_audio_from_text

async def chat_with_agent(agent):
    print(f"Starting chat with the AI Assistant. Type 'exit' or 'quit' to end the session.")
    print("This system will automatically route your questions to the appropriate specialist.")
    print("=" * 70)
    
    while True:
        try:
            # Get user input
            try:
                user_input = input("\nYou: ").strip()
            except EOFError:
                print("\nInput error detected. Ending chat session.")
                break
            
            # Check for exit conditions
            if user_input.lower() in ('exit', 'quit'):
                print("\nEnding chat session. Goodbye!")
                break
                
            if not user_input:
                continue
                
            # Get and stream the agent's response in blue
            print("\n\033[94mAgent: ", end="", flush=True)  # Blue color start
            
            result = Runner.run_streamed(agent, input=user_input)
            response_text = ""
            async for event in result.stream_events():
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    print(event.data.delta, end="", flush=True)
                    response_text += event.data.delta
            
            # Now await the async function properly
            await play_audio_from_text(response_text)
            print("\033[0m")  # Reset color and add newline
                    
        except KeyboardInterrupt:
            print("\n\nEnding chat session. Goodbye!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            break

async def main():
    # Start chat with the triage agent which will automatically route to appropriate specialists
    await chat_with_agent(triage_agent)

if __name__ == "__main__":
    asyncio.run(main())
