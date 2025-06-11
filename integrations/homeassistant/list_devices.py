#!/usr/bin/env python3
"""
Script to list all devices and entities from Home Assistant
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
HASS_INTEGRATION = os.getenv('HASS_INTEGRATION', 'false').lower() == 'true'

if not HASS_INTEGRATION:
    print("Home Assistant integration is disabled (HASS_INTEGRATION is not true). Skipping Home Assistant actions.")
    def main():
        print("No Home Assistant actions to perform.")
        return
else:
    def main():
        print("Fetching data from Home Assistant...")
        entities = get_states()
        print(f"\nSuccessfully retrieved {len(entities)} entities")
        devices = get_devices()
        print(f"Extracted information for {len(devices)} devices from entities")
        print_devices(devices)
        print_entities(entities)
        with open(Path(__file__).parent / 'entities.json', 'w') as f:
            json.dump(entities, f, indent=2)
        with open(Path(__file__).parent / 'devices.json', 'w') as f:
            json.dump(devices, f, indent=2)
        home_data = {
            'url': HASS_URL,
            'token': HASS_TOKEN,
            'entities': [e['entity_id'] for e in entities],
            'devices': devices
        }
        with open(Path(__file__).parent / '.home', 'w') as f:
            json.dump(home_data, f, indent=2)
        print("\nData has been saved to entities.json, devices.json, and .home for reference")
        print("Note: The .home file contains sensitive information and should not be committed to version control.")

if not HASS_URL or not HASS_TOKEN or HASS_TOKEN == 'your_long_lived_token_here':
    print("Error: Home Assistant URL or token not set in .env file")
    print("Please update the .env file with your Home Assistant information")
    sys.exit(1)

# Set up headers for API requests
headers = {
    "Authorization": f"Bearer {HASS_TOKEN}",
    "Content-Type": "application/json",
}

# Print debug information
print(f"Connecting to Home Assistant at: {HASS_URL}")
print(f"Using token: {HASS_TOKEN[:5]}...{HASS_TOKEN[-5:]}")

def get_states():
    """Get all entity states from Home Assistant"""
    try:
        url = f"{HASS_URL}/api/states"
        print(f"Making request to: {url}")
        response = requests.get(url, headers=headers)
        print(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            print(f"Response content: {response.text}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching states: {e}")
        sys.exit(1)

def get_devices():
    """Get all devices from Home Assistant by extracting from entities"""
    try:
        # Home Assistant API might not expose device registry directly
        # We'll extract device info from entities instead
        entities = get_states()
        
        # Extract unique device_ids from entities
        devices = {}
        for entity in entities:
            if 'attributes' in entity and 'device_id' in entity['attributes']:
                device_id = entity['attributes']['device_id']
                if device_id not in devices:
                    devices[device_id] = {
                        'id': device_id,
                        'name': entity['attributes'].get('friendly_name', 'Unknown'),
                        'entities': []
                    }
                devices[device_id]['entities'].append(entity['entity_id'])
        
        return list(devices.values())
    except Exception as e:
        print(f"Error extracting devices: {e}")
        return []

def print_entities(entities):
    """Print all entities in a formatted way"""
    print("\n=== ENTITIES ===")
    # Group entities by domain
    domains = {}
    for entity in entities:
        entity_id = entity['entity_id']
        domain = entity_id.split('.')[0]
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(entity)
    
    # Print entities by domain
    for domain, domain_entities in sorted(domains.items()):
        print(f"\n--- {domain.upper()} ---")
        for entity in sorted(domain_entities, key=lambda x: x['entity_id']):
            entity_id = entity['entity_id']
            friendly_name = entity.get('attributes', {}).get('friendly_name', 'No name')
            state = entity.get('state', 'unknown')
            print(f"{entity_id}: {friendly_name} (State: {state})")

def print_devices(devices):
    """Print all devices in a formatted way"""
    print("\n=== DEVICES ===")
    if not devices:
        print("No devices found with device_id information")
        return
        
    for device in sorted(devices, key=lambda x: x.get('name', 'unknown')):
        name = device.get('name', 'No name')
        device_id = device.get('id', 'No ID')
        entity_count = len(device.get('entities', []))
        print(f"{name} (ID: {device_id}) - {entity_count} entities")
        
        # Print the first few entities for this device
        entities = device.get('entities', [])
        if entities:
            print("  Entities:")
            for entity in entities[:5]:  # Show only first 5 to avoid cluttering output
                print(f"    - {entity}")
            if len(entities) > 5:
                print(f"    ... and {len(entities) - 5} more")
        print()

if __name__ == "__main__":
    main()
