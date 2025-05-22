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
            try:
                user_input = input("\nYou: ").strip()
            except EOFError:
                print("\nInput error detected. Ending chat session.")
                break
            
            if user_input.lower() in ('exit', 'quit'):
                print("\nEnding chat session. Goodbye!")
                break
                
            if not user_input:
                continue
                
            print("\n\033[94mAgent: ", end="", flush=True)  
            
            start_time = asyncio.get_event_loop().time()
            
            result = Runner.run_streamed(agent, input=user_input)
            response_text = ""
            async for event in result.stream_events():
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    print(event.data.delta, end="", flush=True)
                    response_text += event.data.delta
            
            streaming_time = asyncio.get_event_loop().time() - start_time
            print(f"\n\033[90m[Agent response streamed in {streaming_time:.2f} seconds]\033[0m")
            
            speech_start_time = asyncio.get_event_loop().time()
             
            await play_audio_from_text(response_text)
            

            speech_time = asyncio.get_event_loop().time() - speech_start_time
            print(f"\033[90m[Speech generated and played in {speech_time:.2f} seconds]\033[0m")
            
      
            total_time = streaming_time + speech_time
            print(f"\033[90m[Total response time: {total_time:.2f} seconds]\033[0m")
            
            print("\033[0m")  # Reset color
                    
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
