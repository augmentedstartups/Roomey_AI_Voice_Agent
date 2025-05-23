"""Tools module containing function declarations and implementations for the AI assistant."""

from google.genai import types

# ===== DECLARATIONS =====

set_light_values_declaration = {
    "name": "set_light_values",
    "behavior": "NON_BLOCKING",
    "description": "Sets the brightness and color temperature of a light.",
    "parameters": {
        "type": "object",
        "properties": {
            "brightness": {
                "type": "integer",
                "description": "Light level from 0 to 100. Zero is off and 100 is full brightness",
            },
            "color_temp": {
                "type": "string",
                "enum": ["daylight", "cool", "warm"],
                "description": "Color temperature of the light fixture, which can be `daylight`, `cool` or `warm`.",
            },
        },
        "required": ["brightness", "color_temp"],
    },
}

set_sound_values_declaration = {
    "name": "set_sound_values",
    "behavior": "NON_BLOCKING",
    "description": "Sets the volumne and profile of a sound.",
    "parameters": {
        "type": "object",
        "properties": {
            "volume": {
                "type": "integer",
                "description": "Volume level from 0 to 100. Zero is off and 100 is full volume",
            },
            "profile": {
                "type": "string",
                "enum": ["base", "dynamic", "vocal"],
                "description": "Profile of the sound, which can be `base`, `dynamic` or `vocal`.",
            },
        },
        "required": ["volume", "profile"],
    },
}

set_reminder_declaration = {
    "name": "set_reminder",
    "behavior": "NON_BLOCKING",
    "description": "Sets a reminder.",
    "parameters": {
        "type": "object",
        "properties": {
            "item": {
                "type": "string",
                "description": "Item to be reminded of",
            },
            "time": {
                "type": "string",
                "description": "Time to be reminded of",
            },
        },
        "required": ["item"],
    },
}


# ===== FUNCTIONS =====
def set_reminder(item: str, time: str) -> dict[str, str]:
    """Set a reminder. (mock API).

    Args:
        item: Item to be reminded of
        time: Time to be reminded of

    Returns:
        A dictionary containing the set item and time.
    """
    return {"item": item, "time": time}

def set_sound_values(volume: int, profile: str) -> dict[str, int | str]:
    """Set the volume and profile of a sound. (mock API).

    Args:
        volume: Volume level from 0 to 100. Zero is off and 100 is full volume
        profile: Profile of the sound, which can be `base`, `dynamic` or `vocal`.

    Returns:
        A dictionary containing the set volume and profile.
    """
    return {"volume": volume, "profile": profile}



# ===== FUNCTIONS =====

def set_light_values(brightness: int, color_temp: str) -> dict[str, int | str]:
    """Set the brightness and color temperature of a room light. (mock API).

    Args:
        brightness: Light level from 0 to 100. Zero is off and 100 is full brightness
        color_temp: Color temperature of the light fixture, which can be `daylight`, `cool` or `warm`.

    Returns:
        A dictionary containing the set brightness and color temperature.
    """
    return {"brightness": brightness, "colorTemperature": color_temp}


# ===== TOOLS LIST =====

def get_tools():
    """Returns the list of tools configured for the AI assistant."""
    return [
        {"google_search": {}},
        {"function_declarations": [set_light_values_declaration, set_sound_values_declaration, set_reminder_declaration]},
    ]

