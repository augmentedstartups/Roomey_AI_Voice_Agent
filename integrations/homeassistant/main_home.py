#!/usr/bin/env python3
"""
Home Assistant Integration for Roomey AI Voice Agent
This script provides functions to control and get status of Home Assistant entities.
"""
import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the path to allow importing from the project
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Load environment variables from .env file
load_dotenv(project_root / '.env')

# Get Home Assistant URL and token from environment variables
HASS_URL = os.getenv('HASS_URL')
HASS_TOKEN = os.getenv('HASS_TOKEN')
HASS_INTEGRATION = os.getenv('HASS_INTEGRATION', 'false').lower() == 'true'

if not HASS_INTEGRATION:
    print("Home Assistant integration is disabled (HASS_INTEGRATION is not true). Home Assistant features will be unavailable.")
    class HomeAssistant:
        def __init__(self, *args, **kwargs):
            print("[HomeAssistant] Integration is disabled.")
        def get_entities(self, domain=None):
            print("[HomeAssistant] get_entities called, but integration is disabled.")
            return []
        def get_entity_state(self, entity_id):
            print("[HomeAssistant] get_entity_state called, but integration is disabled.")
            return None
        def call_service(self, domain, service, entity_id=None, **service_data):
            print("[HomeAssistant] call_service called, but integration is disabled.")
            return False
        def turn_on(self, entity_id):
            print("[HomeAssistant] turn_on called, but integration is disabled.")
            return False
        def turn_off(self, entity_id):
            print("[HomeAssistant] turn_off called, but integration is disabled.")
            return False
        def toggle(self, entity_id):
            print("[HomeAssistant] toggle called, but integration is disabled.")
            return False
        def set_climate(self, entity_id, temperature=None, hvac_mode=None):
            print("[HomeAssistant] set_climate called, but integration is disabled.")
            return False
        def get_entity_info(self, entity_id):
            print("[HomeAssistant] get_entity_info called, but integration is disabled.")
            return {"error": "Home Assistant integration is disabled."}
        def find_entities_by_name(self, name, exact=False):
            print("[HomeAssistant] find_entities_by_name called, but integration is disabled.")
            return []
        def find_entities_in_room(self, room):
            print("[HomeAssistant] find_entities_in_room called, but integration is disabled.")
            return []
else:
    if not HASS_URL or not HASS_TOKEN:
        print("Error: Home Assistant URL or token not set in .env file")
        print("Please update the .env file with your Home Assistant information")
        sys.exit(1)

# Set up headers for API requests
headers = {
    "Authorization": f"Bearer {HASS_TOKEN}",
    "Content-Type": "application/json",
}

class HomeAssistant:
    """Class to interact with Home Assistant"""
    
    def __init__(self, url=HASS_URL, token=HASS_TOKEN):
        """Initialize with Home Assistant URL and token"""
        self.url = url
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
    def get_entities(self, domain=None):
        """
        Get all entities or entities of a specific domain
        
        Args:
            domain (str, optional): Filter entities by domain (e.g., 'light', 'switch')
            
        Returns:
            list: List of entities
        """
        try:
            response = requests.get(f"{self.url}/api/states", headers=self.headers)
            response.raise_for_status()
            entities = response.json()
            
            if domain:
                return [e for e in entities if e['entity_id'].startswith(f"{domain}.")]
            return entities
        except requests.exceptions.RequestException as e:
            print(f"Error fetching entities: {e}")
            return []
    
    def get_entity_state(self, entity_id):
        """
        Get the state of a specific entity
        
        Args:
            entity_id (str): The entity ID to get state for
            
        Returns:
            dict: Entity state information or None if error
        """
        try:
            response = requests.get(f"{self.url}/api/states/{entity_id}", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching state for {entity_id}: {e}")
            return None
    
    def call_service(self, domain, service, entity_id=None, **service_data):
        """
        Call a Home Assistant service
        
        Args:
            domain (str): Service domain (e.g., 'light', 'switch')
            service (str): Service to call (e.g., 'turn_on', 'turn_off')
            entity_id (str, optional): Entity ID to target
            **service_data: Additional service data
            
        Returns:
            bool: True if successful, False otherwise
        """
        data = service_data.copy()
        if entity_id:
            data["entity_id"] = entity_id
        
        try:
            response = requests.post(
                f"{self.url}/api/services/{domain}/{service}",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error calling service {domain}.{service}: {e}")
            return False
    
    def turn_on(self, entity_id):
        """
        Turn on an entity
        
        Args:
            entity_id (str): Entity ID to turn on
            
        Returns:
            bool: True if successful, False otherwise
        """
        domain = entity_id.split('.')[0]
        return self.call_service(domain, "turn_on", entity_id)
    
    def turn_off(self, entity_id):
        """
        Turn off an entity
        
        Args:
            entity_id (str): Entity ID to turn off
            
        Returns:
            bool: True if successful, False otherwise
        """
        domain = entity_id.split('.')[0]
        return self.call_service(domain, "turn_off", entity_id)
    
    def toggle(self, entity_id):
        """
        Toggle an entity
        
        Args:
            entity_id (str): Entity ID to toggle
            
        Returns:
            bool: True if successful, False otherwise
        """
        domain = entity_id.split('.')[0]
        return self.call_service(domain, "toggle", entity_id)
    
    def set_climate(self, entity_id, temperature=None, hvac_mode=None):
        """
        Set climate entity parameters
        
        Args:
            entity_id (str): Climate entity ID
            temperature (float, optional): Temperature to set
            hvac_mode (str, optional): HVAC mode to set
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not entity_id.startswith("climate."):
            print(f"Error: {entity_id} is not a climate entity")
            return False
        
        service_data = {}
        if temperature is not None:
            service_data["temperature"] = temperature
        if hvac_mode is not None:
            service_data["hvac_mode"] = hvac_mode
        
        return self.call_service("climate", "set_temperature", entity_id, **service_data)
    
    def get_entity_info(self, entity_id):
        """
        Get detailed information about an entity
        
        Args:
            entity_id (str): Entity ID to get info for
            
        Returns:
            dict: Formatted entity information
        """
        state = self.get_entity_state(entity_id)
        if not state:
            return {"error": f"Could not get state for {entity_id}"}
        
        # Extract the most useful information
        domain = entity_id.split('.')[0]
        info = {
            "entity_id": entity_id,
            "state": state.get("state"),
            "friendly_name": state.get("attributes", {}).get("friendly_name", "Unknown"),
            "last_updated": state.get("last_updated"),
            "domain": domain,
        }
        
        # Add domain-specific attributes
        attributes = state.get("attributes", {})
        if domain == "light":
            if "brightness" in attributes:
                info["brightness"] = attributes["brightness"]
                # Convert to percentage for easier understanding
                info["brightness_pct"] = round((attributes["brightness"] / 255) * 100)
            if "rgb_color" in attributes:
                info["rgb_color"] = attributes["rgb_color"]
            if "color_temp" in attributes:
                info["color_temp"] = attributes["color_temp"]
        elif domain == "climate":
            if "temperature" in attributes:
                info["temperature"] = attributes["temperature"]
            if "current_temperature" in attributes:
                info["current_temperature"] = attributes["current_temperature"]
            if "hvac_mode" in attributes:
                info["hvac_mode"] = attributes["hvac_mode"]
            if "hvac_action" in attributes:
                info["hvac_action"] = attributes["hvac_action"]
        elif domain == "sensor":
            if "unit_of_measurement" in attributes:
                info["unit"] = attributes["unit_of_measurement"]
        elif domain == "switch":
            if "current_power_w" in attributes:
                info["power"] = attributes["current_power_w"]
            if "voltage" in attributes:
                info["voltage"] = attributes["voltage"]
        
        return info
    
    def find_entities_by_name(self, name, exact=False):
        """
        Find entities by name
        
        Args:
            name (str): Name to search for
            exact (bool, optional): If True, require exact match
            
        Returns:
            list: List of matching entities
        """
        entities = self.get_entities()
        matches = []
        
        name = name.lower()
        for entity in entities:
            friendly_name = entity.get("attributes", {}).get("friendly_name", "").lower()
            entity_id = entity.get("entity_id", "").lower()
            
            if exact:
                if name == friendly_name or name == entity_id:
                    matches.append(entity)
            else:
                if name in friendly_name or name in entity_id:
                    matches.append(entity)
        
        return matches
    
    def find_entities_in_room(self, room):
        """
        Find entities in a specific room
        
        Args:
            room (str): Room name to search for
            
        Returns:
            list: List of entities in the room
        """
        # This is a simple implementation that looks for room name in entity names
        # A more sophisticated implementation would use Home Assistant's areas
        room = room.lower()
        entities = self.get_entities()
        matches = []
        
        for entity in entities:
            friendly_name = entity.get("attributes", {}).get("friendly_name", "").lower()
            entity_id = entity.get("entity_id", "").lower()
            
            if room in friendly_name or room in entity_id:
                matches.append(entity)
        
        return matches

def print_entity_info(entity_info):
    """Print entity information in a readable format"""
    if "error" in entity_info:
        print(f"Error: {entity_info['error']}")
        return
    
    print(f"\n=== {entity_info['friendly_name']} ({entity_info['entity_id']}) ===")
    print(f"State: {entity_info['state']}")
    print(f"Last Updated: {entity_info['last_updated']}")
    
    # Print additional attributes based on domain
    if entity_info['domain'] == 'light':
        if 'brightness_pct' in entity_info:
            print(f"Brightness: {entity_info['brightness_pct']}%")
        if 'rgb_color' in entity_info:
            print(f"RGB Color: {entity_info['rgb_color']}")
    elif entity_info['domain'] == 'climate':
        if 'temperature' in entity_info:
            print(f"Set Temperature: {entity_info['temperature']}")
        if 'current_temperature' in entity_info:
            print(f"Current Temperature: {entity_info['current_temperature']}")
        if 'hvac_mode' in entity_info:
            print(f"HVAC Mode: {entity_info['hvac_mode']}")
    elif entity_info['domain'] == 'sensor':
        if 'unit' in entity_info:
            print(f"Value: {entity_info['state']} {entity_info['unit']}")
    elif entity_info['domain'] == 'switch':
        if 'power' in entity_info:
            print(f"Power: {entity_info['power']} W")
        if 'voltage' in entity_info:
            print(f"Voltage: {entity_info['voltage']} V")

def control_entity(ha, entity_id, action, **params):
    """
    Control an entity with the specified action
    
    Args:
        ha (HomeAssistant): HomeAssistant instance
        entity_id (str): Entity ID to control
        action (str): Action to perform (on, off, toggle, status)
        **params: Additional parameters for specific actions
        
    Returns:
        bool: True if successful, False otherwise
    """
    # First get the current state
    current_state = ha.get_entity_info(entity_id)
    print(f"\nCurrent state of {entity_id}:")
    print_entity_info(current_state)
    
    # Perform the requested action
    result = False
    if action == "on":
        print(f"Turning ON {entity_id}...")
        result = ha.turn_on(entity_id)
    elif action == "off":
        print(f"Turning OFF {entity_id}...")
        result = ha.turn_off(entity_id)
    elif action == "toggle":
        print(f"Toggling {entity_id}...")
        result = ha.toggle(entity_id)
    elif action == "status":
        # Already printed the status above
        return True
    elif action == "climate" and entity_id.startswith("climate."):
        temperature = params.get("temperature")
        hvac_mode = params.get("hvac_mode")
        print(f"Setting climate parameters for {entity_id}...")
        if temperature:
            print(f"  Temperature: {temperature}")
        if hvac_mode:
            print(f"  HVAC Mode: {hvac_mode}")
        result = ha.set_climate(entity_id, temperature, hvac_mode)
    else:
        print(f"Unknown action: {action}")
        return False
    
    # Check if the action was successful
    if result:
        print(f"Action '{action}' was successful")
        # Get the new state
        new_state = ha.get_entity_info(entity_id)
        print("\nNew state:")
        print_entity_info(new_state)
        return True
    else:
        print(f"Action '{action}' failed")
        return False

if __name__ == "__main__":
    # Initialize Home Assistant
    ha = HomeAssistant()
    
    # Test with office/study devices
    print("=== Home Assistant Control Test ===")
    
    # Test 1: Control the speaker
    speaker_entity = "switch.speaker"
    print("\nTest 1: Controlling the speaker")
    control_entity(ha, speaker_entity, "toggle")
    
    # Test 2: Check status of office light
    office_light = "switch.office_light_switch_1"
    print("\nTest 2: Checking status of office light")
    control_entity(ha, office_light, "status")
    
    print("\nTests completed. You can now integrate this with your voice assistant.")
