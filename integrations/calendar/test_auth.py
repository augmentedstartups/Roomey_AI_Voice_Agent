#!/usr/bin/env python
"""Google Calendar Integration Test Script

This script tests the Google Calendar integration with either OAuth or mock data.
Run this script to verify that your calendar integration is working correctly.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to the path to allow importing the modules
sys.path.append(str(Path(__file__).parent))

# Import the calendar modules
from google_calendar import get_calendar_service, get_calendar_events

# Load environment variables
load_dotenv()

def test_calendar_integration():
    """Test the Google Calendar integration."""
    print("Google Calendar Integration Test")
    print("="*30)
    
    # Test authentication
    print("\nTesting calendar service authentication...")
    service = get_calendar_service()
    
    if not service:
        print("\nAuthentication failed. Please check the error messages above.")
        return False
    
    print("Authentication successful!")
    
    # Test getting calendar events
    print("\nTesting calendar events retrieval...")
    calendar_email = os.getenv("GOOGLE_CALENDAR_EMAIL")
    print(f"Calendar email: {calendar_email}")
    
    events_data = get_calendar_events(days=30, max_events=10)
    
    if events_data.get("status") == "error":
        print(f"Error: {events_data.get('message')}")
        return False
    
    events = events_data.get("events", [])
    if events:
        print(f"\nFound {len(events)} upcoming events:")
        for event in events:
            print(f"- {event['summary']} on {event['start']} at {event['location']}")
    else:
        print("\nNo upcoming events found in the next 30 days.")
    
    print("\nTest completed successfully!")
    return True

if __name__ == "__main__":
    # Test the calendar integration
    test_calendar_integration()
