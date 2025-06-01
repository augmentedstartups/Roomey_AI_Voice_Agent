#!/usr/bin/env python3
"""
Home Assistant integration for Roomey AI Voice Agent
Provides functionality to interact with Home Assistant
"""
import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

# Import the HomeAssistant class from main_home.py
from integrations.homeassistant.main_home import HomeAssistant, print_entity_info

# Path to cached entities file
ENTITIES_CACHE_FILE = Path(__file__).parent / "entities.json"
DEVICES_CACHE_FILE = Path(__file__).parent / "devices.json"

# Initialize Home Assistant client (will be lazy loaded)
_ha_client = None

# Centralized entity registry
_entity_registry: Dict[str, Dict[str, Any]] = {}
_entities_by_room: Dict[str, List[str]] = {}
_entities_by_type: Dict[str, List[str]] = {}
_entity_friendly_names: Dict[str, str] = {}

# Room mappings - standardize room names
_room_mappings = {
    'office': ['office', 'study', 'workspace'],
    'bedroom': ['bedroom', 'main bedroom', 'master bedroom'],
    'living_room': ['living room', 'lounge', 'family room'],
    'kitchen': ['kitchen', 'kitchenette'],
    'bathroom': ['bathroom', 'restroom', 'toilet'],
    'baby_room': ['baby room', 'nursery', 'kids room']
}

def get_ha_client():
    """Get or initialize the Home Assistant client"""
    global _ha_client
    if _ha_client is None:
        _ha_client = HomeAssistant()
    return _ha_client


def initialize_entity_registry():
    """
    Initialize the entity registry from the cache file
    This creates a fast lookup table for entities by ID, name, room, and type
    """
    global _entity_registry, _entities_by_room, _entities_by_type, _entity_friendly_names
    
    # If registry is already populated, return
    if _entity_registry:
        return True
        
    try:
        # Load entities from cache
        if not ENTITIES_CACHE_FILE.exists():
            print(f"Entities cache file not found: {ENTITIES_CACHE_FILE}")
            return False
            
        with open(ENTITIES_CACHE_FILE, 'r') as f:
            entities = json.load(f)
            
        # Build the registry
        for entity in entities:
            entity_id = entity.get('entity_id')
            if not entity_id:
                continue
                
            # Get basic info
            domain = entity_id.split('.')[0]
            friendly_name = entity.get('attributes', {}).get('friendly_name', entity_id)
            state = entity.get('state')
            
            # Store in registry
            _entity_registry[entity_id] = {
                'friendly_name': friendly_name,
                'domain': domain,
                'state': state,
                'attributes': entity.get('attributes', {})
            }
            
            # Store friendly name mapping
            _entity_friendly_names[friendly_name.lower()] = entity_id
            
            # Store by type/domain
            if domain not in _entities_by_type:
                _entities_by_type[domain] = []
            _entities_by_type[domain].append(entity_id)
            
            # Try to determine room
            room = determine_entity_room(entity_id, friendly_name)
            if room:
                if room not in _entities_by_room:
                    _entities_by_room[room] = []
                _entities_by_room[room].append(entity_id)
                
        return True
    except Exception as e:
        print(f"Error initializing entity registry: {e}")
        return False
        

def determine_entity_room(entity_id, friendly_name):
    """
    Try to determine which room an entity belongs to based on its ID and name
    
    Args:
        entity_id: The entity ID
        friendly_name: The friendly name of the entity
        
    Returns:
        str or None: The determined room or None if can't be determined
    """
    entity_text = f"{entity_id} {friendly_name}".lower()
    
    # Check each room name in our mappings
    for room, aliases in _room_mappings.items():
        for alias in aliases:
            if alias.lower() in entity_text:
                return room
                
    return None

def get_cached_entities():
    """
    Get entities from the cache file
    
    Returns:
        list: List of entities from cache or empty list if file not found
    """
    try:
        if ENTITIES_CACHE_FILE.exists():
            with open(ENTITIES_CACHE_FILE, 'r') as f:
                return json.load(f)
        else:
            print(f"Entities cache file not found: {ENTITIES_CACHE_FILE}")
            return []
    except Exception as e:
        print(f"Error reading entities cache: {e}")
        return []

def get_entity_names():
    """
    Get a dictionary mapping entity_ids to friendly names
    
    Returns:
        dict: Dictionary of entity_id -> friendly_name
    """
    # Initialize registry if needed
    if not _entity_registry:
        initialize_entity_registry()
        
    # If registry initialized, use it
    if _entity_registry:
        return {
            entity_id: info.get('friendly_name', entity_id)
            for entity_id, info in _entity_registry.items()
        }
    
    # Fallback to loading from cache
    entities = get_cached_entities()
    return {
        entity.get('entity_id'): entity.get('attributes', {}).get('friendly_name', entity.get('entity_id'))
        for entity in entities
        if 'entity_id' in entity
    }

def get_entities_by_domain(domain):
    """
    Get entities filtered by domain (e.g., 'light', 'switch')
    
    Args:
        domain (str): Domain to filter by
        
    Returns:
        list: List of entities in that domain
    """
    # Initialize registry if needed
    if not _entity_registry:
        initialize_entity_registry()
    
    # If we have the registry and this domain
    if _entity_registry and domain in _entities_by_type:
        # Convert to full entity objects
        return [
            {
                'entity_id': entity_id,
                'state': _entity_registry[entity_id].get('state'),
                'attributes': _entity_registry[entity_id].get('attributes', {}),
                'friendly_name': _entity_registry[entity_id].get('friendly_name')
            }
            for entity_id in _entities_by_type[domain]
        ]
    
    # Fallback to loading from cache
    entities = get_cached_entities()
    return [
        entity for entity in entities
        if entity.get('entity_id', '').startswith(f"{domain}.")
    ]

def get_entity_status(entity_id):
    """
    Get the current status of an entity
    
    Args:
        entity_id (str): The entity ID to get status for
        
    Returns:
        dict: Entity information
    """
    ha = get_ha_client()
    entity_info = ha.get_entity_info(entity_id)
    return entity_info

def control_entity(entity_id, action, **params):
    """
    Control an entity (turn on/off, toggle)
    
    Args:
        entity_id (str): The entity ID to control
        action (str): Action to perform (on, off, toggle)
        **params: Additional parameters for specific actions
        
    Returns:
        dict: Result of the operation
    """
    # Initialize registry if needed
    if not _entity_registry:
        initialize_entity_registry()
    
    ha = get_ha_client()
    
    # Validate entity_id
    if not entity_id:
        return {"success": False, "message": "No entity_id provided"}
    
    # If entity looks like a friendly name, try to resolve it
    if not entity_id.count('.') and _entity_friendly_names:
        friendly_name_lower = entity_id.lower()
        if friendly_name_lower in _entity_friendly_names:
            entity_id = _entity_friendly_names[friendly_name_lower]
    
    # Check if entity exists in registry
    entity_exists = False
    if _entity_registry and entity_id in _entity_registry:
        entity_exists = True
    
    # Validate action
    valid_actions = ["on", "off", "toggle", "status", "climate"]
    if action not in valid_actions:
        return {"success": False, "message": f"Invalid action: {action}. Valid actions are: {valid_actions}"}
    
    # If entity doesn't exist in registry, find similar entities
    if not entity_exists and _entity_registry:
        # Try to find similar entities
        similar_entities = []
        domain = entity_id.split('.')[0] if '.' in entity_id else None
        
        # If we have a domain, suggest entities from that domain
        if domain and domain in _entities_by_type:
            similar_entities = [
                (eid, _entity_registry[eid]['friendly_name'])
                for eid in _entities_by_type[domain][:5]  # Limit to 5 suggestions
            ]
        else:
            # Otherwise find entities with similar names
            query = entity_id.lower()
            for eid, info in _entity_registry.items():
                if query in eid.lower() or query in info.get('friendly_name', '').lower():
                    similar_entities.append((eid, info.get('friendly_name', eid)))
                    if len(similar_entities) >= 5:  # Limit to 5 suggestions
                        break
        
        if similar_entities:
            suggestions = [f"{name} ({eid})" for eid, name in similar_entities]
            return {
                "success": False,
                "entity_id": entity_id,
                "message": f"Entity '{entity_id}' not found. Did you mean one of these? {', '.join(suggestions)}"
            }
    
    # Get current state before action
    current_state = ha.get_entity_info(entity_id)
    
    # If action is just status, return current state
    if action == "status":
        return {
            "success": True, 
            "entity_id": entity_id,
            "action": "status",
            "state": current_state
        }
    
    # Perform the action
    result = False
    if action == "on":
        result = ha.turn_on(entity_id)
    elif action == "off":
        result = ha.turn_off(entity_id)
    elif action == "toggle":
        result = ha.toggle(entity_id)
    elif action == "climate" and entity_id.startswith("climate."):
        temperature = params.get("temperature")
        hvac_mode = params.get("hvac_mode")
        result = ha.set_climate(entity_id, temperature, hvac_mode)
    
    # Get new state after action
    if result:
        new_state = ha.get_entity_info(entity_id)
        return {
            "success": True,
            "entity_id": entity_id,
            "action": action,
            "previous_state": current_state.get("state"),
            "new_state": new_state.get("state"),
            "friendly_name": current_state.get("friendly_name", entity_id)
        }
    else:
        return {
            "success": False,
            "entity_id": entity_id,
            "action": action,
            "message": f"Failed to {action} {entity_id}"
        }

def find_entities_by_name(name, exact=False):
    """
    Find entities by name
    
    Args:
        name (str): Name to search for
        exact (bool, optional): If True, require exact match
        
    Returns:
        list: List of matching entities
    """
    # Initialize registry if needed
    if not _entity_registry:
        initialize_entity_registry()
    
    matches = []
    name = name.lower()
    
    # If registry is available, use it for fast lookups
    if _entity_registry:
        # First check if there's an exact match in friendly names
        if name in _entity_friendly_names:
            entity_id = _entity_friendly_names[name]
            entity_info = _entity_registry[entity_id]
            return [{
                'entity_id': entity_id,
                'state': entity_info.get('state'),
                'attributes': entity_info.get('attributes', {}),
                'friendly_name': entity_info.get('friendly_name')
            }]
        
        # Otherwise search through all entities
        for entity_id, info in _entity_registry.items():
            friendly_name = info.get('friendly_name', '').lower()
            entity_id_lower = entity_id.lower()
            
            if exact:
                if name == friendly_name or name == entity_id_lower:
                    matches.append({
                        'entity_id': entity_id,
                        'state': info.get('state'),
                        'attributes': info.get('attributes', {}),
                        'friendly_name': info.get('friendly_name')
                    })
            else:
                if name in friendly_name or name in entity_id_lower:
                    matches.append({
                        'entity_id': entity_id,
                        'state': info.get('state'),
                        'attributes': info.get('attributes', {}),
                        'friendly_name': info.get('friendly_name')
                    })
    else:
        # Fallback to cache lookup
        entities = get_cached_entities()
        for entity in entities:
            friendly_name = entity.get("attributes", {}).get("friendly_name", "").lower()
            entity_id = entity.get("entity_id", "").lower()
            
            if exact:
                if name == friendly_name or name == entity_id:
                    matches.append(entity)
            else:
                if name in friendly_name or name in entity_id:
                    matches.append(entity)
    
    # If no matches found in cache or registry, try direct API call
    if not matches and not _entity_registry and not get_cached_entities():
        ha = get_ha_client()
        matches = ha.find_entities_by_name(name, exact)
    
    return matches

def find_entities_in_room(room):
    """
    Find entities in a specific room
    
    Args:
        room (str): Room name to search for
        
    Returns:
        list: List of entities in the room
    """
    # Initialize registry if needed
    if not _entity_registry:
        initialize_entity_registry()
    
    matches = []
    room_lower = room.lower()
    
    # Check if this room is in our standard room mappings
    standard_room = None
    for std_room, aliases in _room_mappings.items():
        if room_lower == std_room or room_lower in [alias.lower() for alias in aliases]:
            standard_room = std_room
            break
    
    # If registry is available and we found a standard room
    if _entity_registry and standard_room and standard_room in _entities_by_room:
        # Return all entities in this room
        return [
            {
                'entity_id': entity_id,
                'state': _entity_registry[entity_id].get('state'),
                'attributes': _entity_registry[entity_id].get('attributes', {}),
                'friendly_name': _entity_registry[entity_id].get('friendly_name')
            }
            for entity_id in _entities_by_room[standard_room]
        ]
    
    # If we don't have a standard room or it's not in our registry,
    # do a text search through all entities
    if _entity_registry:
        for entity_id, info in _entity_registry.items():
            friendly_name = info.get('friendly_name', '').lower()
            entity_id_lower = entity_id.lower()
            
            if room_lower in friendly_name or room_lower in entity_id_lower:
                matches.append({
                    'entity_id': entity_id,
                    'state': info.get('state'),
                    'attributes': info.get('attributes', {}),
                    'friendly_name': info.get('friendly_name')
                })
    else:
        # Fallback to cache lookup
        entities = get_cached_entities()
        for entity in entities:
            friendly_name = entity.get("attributes", {}).get("friendly_name", "").lower()
            entity_id = entity.get("entity_id", "").lower()
            
            if room_lower in friendly_name or room_lower in entity_id:
                matches.append(entity)
    
    # If no matches found in cache or registry, try direct API call
    if not matches and not _entity_registry and not get_cached_entities():
        ha = get_ha_client()
        matches = ha.find_entities_in_room(room)
    
    return matches

#====Declarations==================================================

# Control entity declaration
control_entity_declaration = {
    "name": "control_home_entity",
    "description": "Control a Home Assistant entity (turn on/off, toggle, get status)",
    "parameters": {
        "type": "object",
        "properties": {
            "entity_id": {
                "type": "string",
                "description": "The entity ID to control (e.g., 'switch.speaker', 'switch.office_light_switch_1', 'light.office_light')"
            },
            "action": {
                "type": "string",
                "enum": ["on", "off", "toggle", "status"],
                "description": "Action to perform on the entity"
            }
        },
        "required": ["entity_id", "action"]
    }
}

# Control climate entity declaration
control_climate_declaration = {
    "name": "control_home_climate",
    "description": "Control a Home Assistant climate entity (set temperature, HVAC mode)",
    "parameters": {
        "type": "object",
        "properties": {
            "entity_id": {
                "type": "string",
                "description": "The climate entity ID (e.g., 'climate.air_conditioner')"
            },
            "temperature": {
                "type": "number",
                "description": "Temperature to set (in degrees)"
            },
            "hvac_mode": {
                "type": "string",
                "enum": ["heat", "cool", "auto", "off", "fan_only", "dry"],
                "description": "HVAC mode to set"
            }
        },
        "required": ["entity_id"]
    }
}

# Get entities in room declaration
get_entities_in_room_declaration = {
    "name": "get_home_entities_in_room",
    "description": "Find Home Assistant entities in a specific room",
    "parameters": {
        "type": "object",
        "properties": {
            "room": {
                "type": "string",
                "description": "Room name to search for (e.g., 'office', 'bedroom', 'study')"
            }
        },
        "required": ["room"]
    }
}

# Find entities by name declaration
find_entities_by_name_declaration = {
    "name": "find_home_entities_by_name",
    "description": "Find Home Assistant entities by name",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name to search for (e.g., 'speaker', 'office light', 'switch')"
            },
            "exact": {
                "type": "boolean",
                "description": "If true, require exact name match"
            }
        },
        "required": ["name"]
    }
}

# Functions that will be exposed to the AI assistant
def control_home_entity(entity_id, action):
    """
    Function exposed to the AI assistant to control a Home Assistant entity
    
    Args:
        entity_id (str): Entity ID to control
        action (str): Action to perform
        
    Returns:
        dict: Result information
    """
    result = control_entity(entity_id, action)
    
    # Format the response to be more readable for the AI
    if result["success"]:
        if action == "status":
            entity_info = result["state"]
            response = f"Status of {entity_info.get('friendly_name', entity_id)}: {entity_info.get('state')}"
            if entity_info["domain"] == "light" and "brightness_pct" in entity_info:
                response += f", brightness: {entity_info['brightness_pct']}%"
            elif entity_info["domain"] == "climate":
                if "current_temperature" in entity_info:
                    response += f", current temperature: {entity_info['current_temperature']}"
                if "temperature" in entity_info:
                    response += f", set to: {entity_info['temperature']}"
            return {"message": response, "details": entity_info}
        else:
            return {
                "message": f"Successfully {action}ed {result['friendly_name']} ({entity_id}). " +
                           f"Previous state: {result['previous_state']}, new state: {result['new_state']}",
                "success": True
            }
    else:
        return {"message": result["message"], "success": False}

def control_home_climate(entity_id, temperature=None, hvac_mode=None):
    """
    Function exposed to the AI assistant to control a Home Assistant climate entity
    
    Args:
        entity_id (str): Climate entity ID
        temperature (float, optional): Temperature to set
        hvac_mode (str, optional): HVAC mode to set
        
    Returns:
        dict: Result information
    """
    if not entity_id.startswith("climate."):
        return {"message": f"Error: {entity_id} is not a climate entity", "success": False}
    
    params = {}
    if temperature is not None:
        params["temperature"] = temperature
    if hvac_mode is not None:
        params["hvac_mode"] = hvac_mode
    
    result = control_entity(entity_id, "climate", **params)
    
    if result["success"]:
        message = f"Successfully set {result['friendly_name']} ({entity_id}). "
        if temperature is not None:
            message += f"Temperature: {temperature}. "
        if hvac_mode is not None:
            message += f"Mode: {hvac_mode}. "
        message += f"Previous state: {result['previous_state']}, new state: {result['new_state']}"
        return {"message": message, "success": True}
    else:
        return {"message": result["message"], "success": False}

def get_home_entities_in_room(room):
    """
    Function exposed to the AI assistant to find entities in a room
    
    Args:
        room (str): Room name
        
    Returns:
        dict: Result with entities in the room
    """
    entities = find_entities_in_room(room)
    
    if entities:
        # Format the entities for better readability
        simplified_entities = []
        for entity in entities:
            entity_id = entity.get("entity_id")
            friendly_name = entity.get("attributes", {}).get("friendly_name", entity_id)
            state = entity.get("state")
            
            simplified_entities.append({
                "entity_id": entity_id,
                "friendly_name": friendly_name,
                "state": state
            })
        
        return {
            "message": f"Found {len(entities)} entities in {room}",
            "entities": simplified_entities
        }
    else:
        return {"message": f"No entities found in {room}", "entities": []}

def find_home_entities_by_name(name, exact=False):
    """
    Function exposed to the AI assistant to find entities by name
    
    Args:
        name (str): Name to search for
        exact (bool, optional): If True, require exact match
        
    Returns:
        dict: Result with matching entities
    """
    entities = find_entities_by_name(name, exact)
    
    if entities:
        # Format the entities for better readability
        simplified_entities = []
        for entity in entities:
            entity_id = entity.get("entity_id")
            friendly_name = entity.get("attributes", {}).get("friendly_name", entity_id)
            state = entity.get("state")
            
            simplified_entities.append({
                "entity_id": entity_id,
                "friendly_name": friendly_name,
                "state": state
            })
        
        return {
            "message": f"Found {len(entities)} entities matching '{name}'",
            "entities": simplified_entities
        }
    else:
        return {"message": f"No entities found matching '{name}'", "entities": []}


# Initialize the entity registry when the module is imported
# This ensures the AI has access to entity data immediately
try:
    initialize_entity_registry()
    print(f"Home Assistant entity registry initialized with {len(_entity_registry)} entities")
    if _entities_by_room:
        print(f"Entities organized by {len(_entities_by_room)} rooms")
    if _entities_by_type:
        print(f"Entity types: {', '.join(_entities_by_type.keys())}")
except Exception as e:
    print(f"Note: Could not initialize Home Assistant entity registry: {e}")
    print("The registry will be initialized on first use.")

