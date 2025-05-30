#!/usr/bin/env python
"""
Google Calendar Authentication Script

This script handles the OAuth2 authentication flow with Google Calendar API.
Run this script once to authenticate and generate the token.pickle file.
"""

import os
import pickle
import datetime
from pathlib import Path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Define the scopes required for the Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Paths for credential files
SCRIPT_DIR = Path(__file__).parent
CREDENTIALS_DIR = SCRIPT_DIR / 'credentials'
TOKEN_PATH = CREDENTIALS_DIR / 'token.pickle'

# Check if credentials.json exists in the credentials directory
credentials_files = list(CREDENTIALS_DIR.glob('*.json'))
if credentials_files:
    CREDENTIALS_PATH = credentials_files[0]
    print(f"Found credentials file: {CREDENTIALS_PATH.name}")
else:
    CREDENTIALS_PATH = CREDENTIALS_DIR / 'credentials.json'
    print(f"No credentials file found. Please place your credentials.json file in: {CREDENTIALS_DIR}")
    print("If your file has a different name, rename it to 'credentials.json' or update this script.")

def authenticate():
    """Authenticate with Google Calendar API and save the token."""
    creds = None
    
    # Check if token file exists
    if TOKEN_PATH.exists():
        print(f"Token file found at: {TOKEN_PATH}")
        try:
            with open(TOKEN_PATH, 'rb') as token:
                creds = pickle.load(token)
            print("Token loaded successfully.")
        except Exception as e:
            print(f"Error loading token: {e}")
            creds = None
    
    # If credentials don't exist or are invalid, prompt for authentication
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Token expired. Refreshing...")
            try:
                creds.refresh(Request())
                print("Token refreshed successfully.")
            except Exception as e:
                print(f"Error refreshing token: {e}")
                creds = None
        
        if not creds:
            # Check if credentials.json exists
            if not CREDENTIALS_PATH.exists():
                print("\nError: credentials file not found.")
                print("Please follow these steps to set up Google Calendar API access:")
                print("1. Go to https://console.developers.google.com/")
                print("2. Create a new project or select an existing one")
                print("3. Enable the Google Calendar API")
                print("4. Create OAuth 2.0 credentials (Desktop application)")
                print("5. Download the credentials JSON file")
                print(f"6. Save it to: {CREDENTIALS_DIR}")
                return False
            
            print("\nInitiating OAuth2 authentication flow...")
            print("A browser window will open. Please sign in and grant the requested permissions.")
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
                print("Authentication successful!")
            except Exception as e:
                print(f"Error during authentication: {e}")
                return False
        
        # Save the credentials for the next run
        CREDENTIALS_DIR.mkdir(exist_ok=True)
        try:
            with open(TOKEN_PATH, 'wb') as token:
                pickle.dump(creds, token)
            print(f"Token saved to: {TOKEN_PATH}")
        except Exception as e:
            print(f"Error saving token: {e}")
            return False
    
    # Test the credentials by building the service
    try:
        service = build('calendar', 'v3', credentials=creds)
        print("\nTesting connection to Google Calendar API...")
        
        # Get the next 3 events to test the connection
        now = "2025-01-01T00:00:00Z"  # Use a fixed date to avoid issues with time zones
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=3,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            print("No upcoming events found, but connection was successful.")
        else:
            print(f"Connection successful! Found {len(events)} upcoming events.")
            for event in events:
                summary = event.get('summary', 'No title')
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(f"- {summary} ({start})")
        
        print("\nAuthentication and connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error testing connection: {e}")
        return False

if __name__ == "__main__":
    print("Google Calendar Authentication Script")
    print("====================================")
    print(f"Credentials directory: {CREDENTIALS_DIR}")
    print(f"Token path: {TOKEN_PATH}")
    print("------------------------------------")
    
    success = authenticate()
    
    if success:
        print("\nYou have successfully authenticated with Google Calendar API.")
        print("You can now use the calendar integration in your voice agent.")
    else:
        print("\nAuthentication failed. Please check the error messages above and try again.")
