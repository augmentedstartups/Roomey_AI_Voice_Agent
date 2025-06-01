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

# Import calendar functionality from the new module
from integrations.calendar.google_calendar import (
    get_calendar_events,
    get_calendar_events_declaration
)

# Import Home Assistant functionality from the new module
from integrations.homeassistant.ha_tools import (
    control_home_entity,
    control_home_climate,
    get_home_entities_in_room,
    find_home_entities_by_name,
    control_entity_declaration,
    control_climate_declaration,
    get_entities_in_room_declaration,
    find_entities_by_name_declaration
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

# Function to get all tool declarations for the AI assistant
def get_tool_declarations():
    """Returns the list of tool declarations for the AI assistant."""
    return [get_reminders_declaration, set_reminder_declaration, manage_reminder_declaration, get_secret_key_declaration, get_calendar_events_declaration, control_entity_declaration, control_climate_declaration, get_entities_in_room_declaration, find_entities_by_name_declaration]

# Map function names to their actual implementations
function_map = {
    "get_reminders": get_reminders,
    "set_reminder": set_reminder,
    "manage_reminder": manage_reminder,
    "get_secret_key": get_secret_key,
    "get_calendar_events": get_calendar_events,
    "control_home_entity": control_home_entity,
    "control_home_climate": control_home_climate,
    "get_home_entities_in_room": get_home_entities_in_room,
    "find_home_entities_by_name": find_home_entities_by_name
}

