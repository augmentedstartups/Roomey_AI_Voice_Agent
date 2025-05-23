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

Add in a tool for getting stocks\
    stock_price_agent = Agent(
    name='stock_agent',
    instructions= 'You are an agent who retrieves stock prices. If a ticker symbol is provided, fetch the current price. If only a company name is given, first perform a Google search to find the correct ticker symbol before retrieving the stock price. If the provided ticker symbol is invalid or data cannot be retrieved, inform the user that the stock price could not be found.',
    handoff_description='This agent specializes in retrieving real-time stock prices within 2 decimal places. Given a stock ticker symbol (e.g., AAPL, GOOG, MSFT) or the stock name, use the tools and reliable data sources to provide the most up-to-date price.',
    tools=[get_stock_price,WebSearchTool(search_context_size="low")],


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
        {"function_declarations": [set_light_values_declaration]},
    ]

