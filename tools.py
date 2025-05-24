import os
import json
from google.genai import types
from datetime import datetime

# Path to the reminders file
REMINDERS_FILE = "reminders.json"

#====Functions====================================================
def get_reminders() -> dict:
    """Get user reminders from the reminders.json file.
    
    Returns:
        A dictionary containing all saved reminders.
    """
    # Check if reminders file exists
    if not os.path.exists(REMINDERS_FILE):
        # Create an empty reminders file
        with open(REMINDERS_FILE, 'w') as f:
            json.dump({"reminders": []}, f)
        return {"reminders": []}
    
    # Read reminders from file
    try:
        with open(REMINDERS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading reminders: {e}")
        return {"reminders": [], "error": str(e)}

def set_reminder(reminder_text: str, reminder_time: str = None) -> dict:
    """Save a new reminder to the reminders.json file.
    
    Args:
        reminder_text: The text of the reminder to save
        reminder_time: Optional time for when to be reminded (e.g. "tomorrow at 3pm")
        
    Returns:
        A dictionary containing the status of the operation.
    """
    # Check if reminders file exists
    if not os.path.exists(REMINDERS_FILE):
        reminders = {"reminders": []}
    else:
        # Read existing reminders
        try:
            with open(REMINDERS_FILE, 'r') as f:
                reminders = json.load(f)
        except Exception as e:
            print(f"Error reading reminders: {e}")
            reminders = {"reminders": []}
    
    # Add the new reminder with timestamp and optional reminder time
    new_reminder = {
        "id": len(reminders["reminders"]) + 1,  # Simple ID for reference
        "text": reminder_text,
        "created_at": datetime.now().isoformat()
    }
    
    # Add reminder time if provided
    if reminder_time:
        new_reminder["reminder_time"] = reminder_time
    
    reminders["reminders"].append(new_reminder)
    
    # Save updated reminders
    try:
        with open(REMINDERS_FILE, 'w') as f:
            json.dump(reminders, f, indent=2)
        return {"status": "success", "message": f"Reminder saved: {reminder_text}", "reminder": new_reminder}
    except Exception as e:
        print(f"Error saving reminder: {e}")
        return {"status": "error", "message": str(e)}


def manage_reminder(action: str, reminder_id: int = None, new_text: str = None, new_time: str = None) -> dict:
    """Manage reminders - edit or delete specific reminders or delete all.
    
    Args:
        action: The action to perform ("edit", "delete", "delete_all")
        reminder_id: ID of the reminder to edit or delete (not needed for delete_all)
        new_text: New text for the reminder when editing
        new_time: New reminder time when editing
        
    Returns:
        A dictionary containing the status of the operation.
    """
    # Check if reminders file exists
    if not os.path.exists(REMINDERS_FILE):
        return {"status": "error", "message": "No reminders found"}
    
    # Read existing reminders
    try:
        with open(REMINDERS_FILE, 'r') as f:
            reminders = json.load(f)
    except Exception as e:
        print(f"Error reading reminders: {e}")
        return {"status": "error", "message": str(e)}
    
    # Handle different actions
    if action == "delete_all":
        # Delete all reminders
        reminders["reminders"] = []
        result = {"status": "success", "message": "All reminders deleted"}
    
    elif action == "delete":
        # Delete a specific reminder
        if reminder_id is None:
            return {"status": "error", "message": "Reminder ID is required for deletion"}
        
        # Find the reminder with the given ID
        found = False
        for i, reminder in enumerate(reminders["reminders"]):
            if reminder.get("id") == reminder_id:
                del reminders["reminders"][i]
                found = True
                break
        
        if found:
            result = {"status": "success", "message": f"Reminder {reminder_id} deleted"}
        else:
            return {"status": "error", "message": f"Reminder with ID {reminder_id} not found"}
    
    elif action == "edit":
        # Edit a specific reminder
        if reminder_id is None:
            return {"status": "error", "message": "Reminder ID is required for editing"}
        if new_text is None and new_time is None:
            return {"status": "error", "message": "New text or time is required for editing"}
        
        # Find the reminder with the given ID
        found = False
        for reminder in reminders["reminders"]:
            if reminder.get("id") == reminder_id:
                if new_text is not None:
                    reminder["text"] = new_text
                if new_time is not None:
                    reminder["reminder_time"] = new_time
                reminder["updated_at"] = datetime.now().isoformat()
                found = True
                break
        
        if found:
            result = {"status": "success", "message": f"Reminder {reminder_id} updated"}
        else:
            return {"status": "error", "message": f"Reminder with ID {reminder_id} not found"}
    
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}
    
    # Save updated reminders
    try:
        with open(REMINDERS_FILE, 'w') as f:
            json.dump(reminders, f, indent=2)
        return result
    except Exception as e:
        print(f"Error saving reminders: {e}")
        return {"status": "error", "message": str(e)}


def get_secret_key() -> dict:
    """Get user secret key.
    
    Returns:
        A dictionary containing the secret key.
    """
    return {"secret_key": "ITE819"}



#====Declarations==================================================

# Define the function declaration that describes the function to Gemini
get_reminders_declaration = {
    "name": "get_reminders",
    "description": "Gets the user's saved reminders from the reminders.json file",
    "parameters": {
        "type": "object",
        "properties": {},  # No parameters needed for this function
        "required": []
    }
}

set_reminder_declaration = {
    "name": "set_reminder",
    "description": "Saves a new reminder to the reminders.json file",
    "parameters": {
        "type": "object",
        "properties": {
            "reminder_text": {
                "type": "string",
                "description": "The text of the reminder to save"
            },
            "reminder_time": {
                "type": "string",
                "description": "Optional time for when to be reminded (e.g. 'tomorrow at 3pm')"
            }
        },
        "required": ["reminder_text"]
    }
}

manage_reminder_declaration = {
    "name": "manage_reminder",
    "description": "Manage reminders - edit or delete specific reminders or delete all",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["edit", "delete", "delete_all"],
                "description": "Action to perform: edit a reminder, delete a specific reminder, or delete all reminders"
            },
            "reminder_id": {
                "type": "integer",
                "description": "ID of the reminder to edit or delete (not needed for delete_all)"
            },
            "new_text": {
                "type": "string",
                "description": "New text for the reminder when editing"
            },
            "new_time": {
                "type": "string",
                "description": "New reminder time when editing (e.g. 'tomorrow at 3pm')"
            }
        },
        "required": ["action"]
    }
}

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

