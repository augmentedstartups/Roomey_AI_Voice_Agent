import os
import warnings
from google.genai import types
import asyncio # Import asyncio

# Suppress mcp-use warnings globally
warnings.filterwarnings("ignore", message=".*non-text parts.*")
warnings.filterwarnings("ignore", message=".*non-data parts.*")
warnings.filterwarnings("ignore", message=".*returning concatenated.*")
warnings.filterwarnings("ignore", message=".*executable_code.*")
warnings.filterwarnings("ignore", message=".*code_execution_result.*")

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

# MCP integration (dynamic, config-driven)
from integrations.mcp.mcp_client import MultiMCPClient, load_mcp_server_config

mcp_client = None # Initialize mcp_client as None
MCP_AVAILABLE = False

async def initialize_mcp_client():
    global mcp_client, MCP_AVAILABLE
    try:
        mcp_config = load_mcp_server_config()
        if mcp_config:
            mcp_client = MultiMCPClient()
            await mcp_client.initialize()
            MCP_AVAILABLE = True
        else:
            MCP_AVAILABLE = False
    except Exception as e:
        MCP_AVAILABLE = False

async def cleanup_mcp_client():
    global mcp_client, MCP_AVAILABLE
    if mcp_client and MCP_AVAILABLE:
        try:
            # Add timeout to prevent hanging during cleanup
            await asyncio.wait_for(mcp_client.cleanup(), timeout=5.0)
        except asyncio.TimeoutError:
            print(f"[MCP] Cleanup timed out after 5 seconds - forcing cleanup")
        except Exception as e:
            print(f"[MCP] Cleanup completed with warnings: {e}")
        finally:
            # Reset the global state
            mcp_client = None
            MCP_AVAILABLE = False
            print("[MCP] Global MCP client state reset")

# Removed call_mcp_tool and call_mcp_tool_declaration as they are replaced by dynamic MCP tools

#====Admin====================================================

async def get_tool_declarations():
    """Returns the list of tool declarations for the AI assistant."""
    # Note: MCP tools are added dynamically after initialization

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
    
    if MCP_AVAILABLE and mcp_client: # Check mcp_client is not None
        mcp_declarations = mcp_client.get_tool_declarations()
        if mcp_declarations:
            print("[MCP] Adding dynamically discovered MCP tools to declarations.")
            declarations.extend(mcp_declarations)
        else:
            print("[MCP] No dynamic MCP tools found to add to declarations.")

    print("\n--- Tools available to Roomey ---")
    for decl in declarations:
        print(f"Tool: {decl["name"]}\n  Description: {decl["description"]}")
    print("-------------------------------------------")

    return declarations

# Map function names to their actual implementations
def get_function_map():
    function_map = {
        "get_reminders": get_reminders,
        "set_reminder": set_reminder,
        "manage_reminder": manage_reminder,
        "get_secret_key": get_secret_key
    }
    if LINKEDIN_FORMATTER_INTEGRATION:
        function_map["format_linkedin_post"] = format_linkedin_post
    if GOOGLE_CALENDAR_INTEGRATION:
        function_map["get_calendar_events"] = get_calendar_events
    if HASS_INTEGRATION:
        function_map.update({
            "control_home_entity": control_home_entity,
            "control_home_climate": control_home_climate,
            "get_home_entities_in_room": get_home_entities_in_room,
            "find_home_entities_by_name": find_home_entities_by_name
        })
    
    if MCP_AVAILABLE and mcp_client: # Check mcp_client is not None
        # Dynamically add functions for each discovered MCP tool
        for tool_decl in mcp_client.get_tool_declarations():
            tool_name = tool_decl["name"]
            # Create a closure function to wrap the async execute_mcp_tool call
            # Use default parameter to capture the current value of tool_name
            def create_mcp_wrapper(tool_name=tool_name):
                return lambda **kwargs: asyncio.run(mcp_client.execute_mcp_tool(tool_name, kwargs))
            function_map[tool_name] = create_mcp_wrapper()
            print(f"[MCP] Mapped function '{tool_name}' to MCP client execution.")
    
    return function_map

# For backward compatibility
function_map = get_function_map()
