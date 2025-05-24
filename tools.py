from google.genai import types

# Define the function that will be executed
def get_reminders() -> dict:
    """Get user reminders.
    
    Returns:
        A dictionary containing reminder information.
    """
    # This is where you'd actually retrieve reminders from a database or service
    # For this example, we'll just return a static reminder
    return {"reminder": "Remember to take out the trash", "secret_key": "ITE819"}

def get_secret_key() -> dict:
    """Get user reminders.
    
    Returns:
        A dictionary containing reminder information.
    """
    # This is where you'd actually retrieve reminders from a database or service
    # For this example, we'll just return a static reminder
    return {"secret_key": "ITE819"}

# Define the function declaration that describes the function to Gemini
get_reminders_declaration = {
    "name": "get_reminders",
    "description": "Gets the user's reminders",
    "parameters": {
        "type": "object",
        "properties": {},  # No parameters needed for this simple function
        "required": []
    }
}

get_secret_key_declaration = {
    "name": "get_secret_key",
    "description": "Gets the user's secret key",
    "parameters": {
        "type": "object",
        "properties": {},  # No parameters needed for this simple function
        "required": []
    }
}

# Function to get all tool declarations for the assistant
def get_tool_declarations():
    """Returns the list of tool declarations for the AI assistant."""
    return [get_reminders_declaration, get_secret_key_declaration]

# Map function names to their actual implementations
function_map = {
    "get_reminders": get_reminders,
    "get_secret_key": get_secret_key
}

