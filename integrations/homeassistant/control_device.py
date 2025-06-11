#!/usr/bin/env python3
"""
Script to control Home Assistant entities
"""
import os
import sys
import requests
import json
import argparse
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

if not HASS_URL or not HASS_TOKEN or HASS_TOKEN == 'your_long_lived_token_here':
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
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling service: {e}")
        return None

def toggle_switch(entity_id):
    """Toggle a switch entity"""
    current_state = get_entity_state(entity_id)
    if not current_state:
        print(f"Could not get state for {entity_id}")
        return
    
    state = current_state.get("state")
    print(f"Current state of {entity_id}: {state}")
    
    # Determine which service to call based on current state
    service = "turn_off" if state == "on" else "turn_on"
    domain = entity_id.split('.')[0]
    
    result = call_service(domain, service, entity_id)
    if result is not None:
        print(f"Successfully {service.replace('_', ' ')}ed {entity_id}")
    else:
        print(f"Failed to {service.replace('_', ' ')} {entity_id}")

def set_light(entity_id, brightness=None, rgb_color=None, color_temp=None):
    """Control a light entity"""
    if not entity_id.startswith("light."):
        print(f"Error: {entity_id} is not a light entity")
        return
    
    # Prepare service data
    service_data = {}
    if brightness is not None:
        service_data["brightness"] = brightness
    if rgb_color is not None:
        service_data["rgb_color"] = rgb_color
    if color_temp is not None:
        service_data["color_temp"] = color_temp
    
    # If we have additional parameters, use turn_on with those parameters
    if service_data:
        result = call_service("light", "turn_on", entity_id, **service_data)
        if result is not None:
            print(f"Successfully set {entity_id} with parameters: {service_data}")
        else:
            print(f"Failed to set {entity_id}")
    else:
        # Otherwise just toggle the light
        toggle_switch(entity_id)

def set_climate(entity_id, temperature=None, hvac_mode=None):
    """Control a climate entity"""
    if not entity_id.startswith("climate."):
        print(f"Error: {entity_id} is not a climate entity")
        return
    
    # Prepare service data
    service_data = {}
    if temperature is not None:
        service_data["temperature"] = temperature
    if hvac_mode is not None:
        service_data["hvac_mode"] = hvac_mode
    
    # Set climate parameters
    if service_data:
        result = call_service("climate", "set_temperature", entity_id, **service_data)
        if result is not None:
            print(f"Successfully set {entity_id} with parameters: {service_data}")
        else:
            print(f"Failed to set {entity_id}")
    else:
        print(f"No parameters specified for {entity_id}")

def main():
    parser = argparse.ArgumentParser(description="Control Home Assistant entities")
    parser.add_argument("entity_id", help="The entity ID to control")
    parser.add_argument("--action", choices=["toggle", "turn_on", "turn_off", "set"], 
                        default="toggle", help="Action to perform")
    
    # Light parameters
    parser.add_argument("--brightness", type=int, help="Brightness value (0-255)")
    parser.add_argument("--rgb", nargs=3, type=int, help="RGB color (three values)")
    parser.add_argument("--color-temp", type=int, help="Color temperature")
    
    # Climate parameters
    parser.add_argument("--temperature", type=float, help="Temperature setting")
    parser.add_argument("--hvac-mode", help="HVAC mode (heat, cool, auto, off)")
    
    args = parser.parse_args()
    
    # Get current state to show before making changes
    current = get_entity_state(args.entity_id)
    if current:
        print(f"Current state of {args.entity_id}:")
        print(f"  State: {current.get('state')}")
        print(f"  Attributes: {json.dumps(current.get('attributes', {}), indent=2)}")
    
    # Determine the domain of the entity
    domain = args.entity_id.split('.')[0]
    
    # Handle different entity types
    if domain == "light":
        if args.action == "toggle":
            toggle_switch(args.entity_id)
        elif args.action in ["turn_on", "set"]:
            set_light(args.entity_id, args.brightness, args.rgb, args.color_temp)
        elif args.action == "turn_off":
            call_service("light", "turn_off", args.entity_id)
    elif domain == "climate":
        if args.temperature or args.hvac_mode:
            set_climate(args.entity_id, args.temperature, args.hvac_mode)
        else:
            print(f"Please specify temperature or hvac_mode for climate entity")
    elif domain in ["switch", "automation", "input_boolean"]:
        if args.action == "toggle":
            toggle_switch(args.entity_id)
        elif args.action == "turn_on":
            call_service(domain, "turn_on", args.entity_id)
        elif args.action == "turn_off":
            call_service(domain, "turn_off", args.entity_id)
    else:
        # Generic service call for other entity types
        if args.action == "toggle":
            toggle_switch(args.entity_id)
        elif args.action in ["turn_on", "turn_off"]:
            service = args.action
            call_service(domain, service, args.entity_id)
        else:
            print(f"Action {args.action} not supported for domain {domain}")
    
    # Get updated state after making changes
    updated = get_entity_state(args.entity_id)
    if updated:
        print(f"\nUpdated state of {args.entity_id}:")
        print(f"  State: {updated.get('state')}")
        print(f"  Attributes: {json.dumps(updated.get('attributes', {}), indent=2)}")

if __name__ == "__main__":
    main()
