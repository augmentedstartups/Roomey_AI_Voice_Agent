#!/usr/bin/env python3
"""
Simple script to control Home Assistant entities
"""
import os
import sys
import requests
import json
from dotenv import load_dotenv
from pathlib import Path

# Add the project root to the path to allow importing from the project
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Load environment variables from .env file
load_dotenv(project_root / '.env')

# Get Home Assistant URL and token from environment variables
HASS_URL = os.getenv('HASS_URL')
HASS_TOKEN = os.getenv('HASS_TOKEN')

if not HASS_URL or not HASS_TOKEN:
    print("Error: Home Assistant URL or token not set in .env file")
    print("Please update the .env file with your Home Assistant information")
    sys.exit(1)

# Set up headers for API requests
headers = {
    "Authorization": f"Bearer {HASS_TOKEN}",
    "Content-Type": "application/json",
}

def get_entity_state(entity_id):
    """Get the current state of an entity"""
    try:
        response = requests.get(f"{HASS_URL}/api/states/{entity_id}", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching entity state: {e}")
        return None

def call_service(domain, service, entity_id=None, **service_data):
    """Call a Home Assistant service"""
    data = service_data.copy()
    if entity_id:
        data["entity_id"] = entity_id
    
    try:
        response = requests.post(
            f"{HASS_URL}/api/services/{domain}/{service}",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error calling service: {e}")
        return False

def toggle_entity(entity_id):
    """Toggle an entity on/off"""
    # Get the domain from the entity_id
    domain = entity_id.split('.')[0]
    
    # Get current state
    current = get_entity_state(entity_id)
    if current:
        print(f"Current state of {entity_id}: {current.get('state')}")
    
    # Call the toggle service
    result = call_service(domain, "toggle", entity_id)
    
    if result:
        print(f"Successfully toggled {entity_id}")
        # Get the new state
        new_state = get_entity_state(entity_id)
        if new_state:
            print(f"New state: {new_state.get('state')}")
    else:
        print(f"Failed to toggle {entity_id}")

def turn_on_entity(entity_id):
    """Turn on an entity"""
    domain = entity_id.split('.')[0]
    result = call_service(domain, "turn_on", entity_id)
    if result:
        print(f"Successfully turned on {entity_id}")
    else:
        print(f"Failed to turn on {entity_id}")

def turn_off_entity(entity_id):
    """Turn off an entity"""
    domain = entity_id.split('.')[0]
    result = call_service(domain, "turn_off", entity_id)
    if result:
        print(f"Successfully turned off {entity_id}")
    else:
        print(f"Failed to turn off {entity_id}")

def set_climate(entity_id, temperature=None, hvac_mode=None):
    """Control a climate entity"""
    if not entity_id.startswith("climate."):
        print(f"Error: {entity_id} is not a climate entity")
        return
    
    # Get current state
    current = get_entity_state(entity_id)
    if current:
        print(f"Current state of {entity_id}:")
        print(f"  State: {current.get('state')}")
        print(f"  Temperature: {current.get('attributes', {}).get('temperature')}")
        print(f"  HVAC Mode: {current.get('attributes', {}).get('hvac_mode')}")
    
    # Prepare service data
    service_data = {}
    if temperature is not None:
        service_data["temperature"] = temperature
    if hvac_mode is not None:
        service_data["hvac_mode"] = hvac_mode
    
    # Set climate parameters
    if service_data:
        result = call_service("climate", "set_temperature", entity_id, **service_data)
        if result:
            print(f"Successfully set {entity_id} with parameters: {service_data}")
            # Get the new state
            new_state = get_entity_state(entity_id)
            if new_state:
                print(f"New state: {new_state.get('state')}")
                print(f"New temperature: {new_state.get('attributes', {}).get('temperature')}")
        else:
            print(f"Failed to set {entity_id}")
    else:
        print(f"No parameters specified for {entity_id}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python simple_control.py <action> <entity_id> [parameters]")
        print("Actions: toggle, on, off, climate")
        print("Examples:")
        print("  python simple_control.py toggle switch.bedroom_main_lights")
        print("  python simple_control.py on switch.bathroom_light")
        print("  python simple_control.py off switch.living_room_lights")
        print("  python simple_control.py climate climate.air_conditioner 24 cool")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    entity_id = sys.argv[2]
    
    if action == "toggle":
        toggle_entity(entity_id)
    elif action == "on":
        turn_on_entity(entity_id)
    elif action == "off":
        turn_off_entity(entity_id)
    elif action == "climate" and entity_id.startswith("climate."):
        temperature = float(sys.argv[3]) if len(sys.argv) > 3 else None
        hvac_mode = sys.argv[4] if len(sys.argv) > 4 else None
        set_climate(entity_id, temperature, hvac_mode)
    else:
        print(f"Unknown action: {action} or invalid entity type for this action")
        sys.exit(1)

if __name__ == "__main__":
    main()
