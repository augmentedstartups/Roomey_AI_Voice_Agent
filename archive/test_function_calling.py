import os
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types
from tools import get_tool_declarations, function_map

# Load environment variables from .env file
load_dotenv()

# Initialize the Gemini client
client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY"),
)

# Model to use for Live API testing
MODEL = "models/gemini-2.0-flash-live-001"

async def main():
    print("🚀 Testing Gemini Live API Function Calling")
    
    # Create tools configuration with our function declarations using Live API format
    tools = [{"function_declarations": get_tool_declarations()}]
    
    # Configure the Live API connection
    config = types.LiveConnectConfig(
        response_modalities=["TEXT"],  # Just use text for simplicity
        tools=tools
    )
    
    # Connect to the Live API session
    async with client.aio.live.connect(model=MODEL, config=config) as session:
        # Initial message to prime the model to use our function
        print("\n🔍 Sending prompt to ask for reminders or secret key...")
        
        # Send the prompt
        await session.send(input="Please tell me my reminders and any secret key you have for me", end_of_turn=True)
        
        # Process the response
        await process_responses(session)
        
        # Another test to specifically ask for the secret key
        print("\n🔍 Asking specifically for the secret key...")
        await session.send(input="What's my secret key?", end_of_turn=True)
        
        # Process the response
        await process_responses(session)

async def process_responses(session):
    turn = session.receive()
    current_text = ""
    
    async for chunk in turn:
        # Handle text responses
        if hasattr(chunk, 'text') and chunk.text is not None:
            current_text += chunk.text
            print(f"AI: {chunk.text}", end="")
        
        # Check for tool calls
        if hasattr(chunk, 'tool_call') and chunk.tool_call:
            function_responses = []
            
            # Process each function call
            for fc in chunk.tool_call.function_calls:
                print(f"\n🔧 Function call detected: {fc.name}")
                
                # Get the actual function implementation
                if fc.name in function_map:
                    func = function_map[fc.name]
                    
                    # Parse arguments if any
                    args = {}
                    if hasattr(fc, 'args') and fc.args:
                        args = fc.args
                    
                    # Execute the function
                    try:
                        result = func(**args)
                        print(f"✅ Function result: {result}")
                        
                        # Create a function response
                        function_response = types.FunctionResponse(
                            id=fc.id,
                            name=fc.name,
                            response=result
                        )
                        
                        function_responses.append(function_response)
                    except Exception as e:
                        print(f"❌ Error executing function: {e}")
                else:
                    print(f"❓ Unknown function: {fc.name}")
            
            # Send all function responses back to the model
            if function_responses:
                await session.send_tool_response(function_responses=function_responses)
    
    print("\nTurn complete")

if __name__ == "__main__":
    asyncio.run(main())
