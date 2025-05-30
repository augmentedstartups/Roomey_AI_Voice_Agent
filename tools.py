from google.genai import types

# Import reminders functionality from the new module
from integrations.reminders.reminders import (
    get_reminders,
    set_reminder,
    manage_reminder,
    get_reminders_declaration,
    set_reminder_declaration,
    manage_reminder_declaration
)


def get_secret_key() -> dict:
    """Get user secret key.
    
    Returns:
        A dictionary containing the secret key.
    """
    return {"secret_key": "ITE819"}


#====Declarations==================================================

# Define the function declaration that describes the function to Gemini
get_secret_key_declaration = {
    "name": "get_secret_key",
    "description": "Gets the user's secret key",
    "parameters": {
        "type": "object",
        "properties": {},  # No parameters needed for this function
        "required": []
    }
}

#====Admin====================================================

# Function to get all tool declarations for the assistant
def get_tool_declarations():
    """Returns the list of tool declarations for the AI assistant."""
    return [get_reminders_declaration, set_reminder_declaration, manage_reminder_declaration, get_secret_key_declaration]

# Map function names to their actual implementations
function_map = {
    "get_reminders": get_reminders,
    "set_reminder": set_reminder,
    "manage_reminder": manage_reminder,
    "get_secret_key": get_secret_key
}

