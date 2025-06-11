import os
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

# Home Assistant integration (conditional)
HASS_INTEGRATION = os.getenv('HASS_INTEGRATION', 'false').lower() == 'true'
if HASS_INTEGRATION:
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

GOOGLE_CALENDAR_INTEGRATION = os.getenv('GOOGLE_CALENDAR_INTEGRATION', 'true').lower() == 'true'

if GOOGLE_CALENDAR_INTEGRATION:
    # Import calendar functionality from the new module
    from integrations.calendar.google_calendar import (
        get_calendar_events,
        get_calendar_events_declaration
    )


# LinkedIn formatter integration (conditional)
LINKEDIN_FORMATTER_INTEGRATION = os.getenv('LINKEDIN_FORMATTER_INTEGRATION', 'true').lower() == 'true'

if LINKEDIN_FORMATTER_INTEGRATION:
    from integrations.linkedinformater.linkedin_formatter import format_linkedin_post

# LinkedIn formatter function declaration
format_linkedin_post_declaration = {
    "name": "format_linkedin_post",
    "description": "Creates or formats a LinkedIn post from provided context. The function will automatically extract a topic from the context.",
    "parameters": {
        "type": "object",
        "properties": {
            "context": {
                "type": "string",
                "description": "The context information to use for generating the LinkedIn post. This should be detailed enough to create a meaningful post."
            }
        },
        "required": ["context"]
    }
}

#====Admin====================================================

def get_tool_declarations():
    """Returns the list of tool declarations for the AI assistant."""
    declarations = [
        get_reminders_declaration,
        set_reminder_declaration,
        manage_reminder_declaration,
        get_secret_key_declaration
    ]
    if LINKEDIN_FORMATTER_INTEGRATION:
        declarations.append(format_linkedin_post_declaration)
    if GOOGLE_CALENDAR_INTEGRATION:
        declarations.append(get_calendar_events_declaration)
    if HASS_INTEGRATION:
        declarations += [
            control_entity_declaration,
            control_climate_declaration,
            get_entities_in_room_declaration,
            find_entities_by_name_declaration
        ]
    return declarations

# Map function names to their actual implementations
def get_function_map():
    function_map = {
        "get_reminders": get_reminders,
        "set_reminder": set_reminder,
        "manage_reminder": manage_reminder,
        "get_secret_key": get_secret_key,
        "get_calendar_events": get_calendar_events
    }
    if LINKEDIN_FORMATTER_INTEGRATION:
        function_map["format_linkedin_post"] = format_linkedin_post
    if HASS_INTEGRATION:
        function_map.update({
            "control_home_entity": control_home_entity,
            "control_home_climate": control_home_climate,
            "get_home_entities_in_room": get_home_entities_in_room,
            "find_home_entities_by_name": find_home_entities_by_name
        })
    return function_map

# For backward compatibility
function_map = get_function_map()

