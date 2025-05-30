"""Google Calendar integration module using OAuth authentication."""

import os
import datetime
import pickle
from pathlib import Path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dotenv import load_dotenv

# No mock calendar imports needed

# Load environment variables
load_dotenv()

# Define the scopes required for the Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Paths for credential files
CREDENTIALS_DIR = Path(__file__).parent / 'credentials'
TOKEN_PATH = CREDENTIALS_DIR / 'token.pickle'
CLIENT_SECRET_FILE = CREDENTIALS_DIR / 'client_secret_350408012690-vgj8akhfbaah1coljrs4dr9ppfcs49a9.apps.googleusercontent.com.json'

# Email of the calendar to access
CALENDAR_EMAIL = os.getenv("GOOGLE_CALENDAR_EMAIL", "rkanjee@augmentedstartups.com")

def get_calendar_service():
    """Get an authenticated Google Calendar service using OAuth.
    
    This function handles the OAuth2 authentication flow with Google.
    It will prompt the user to authenticate if necessary.
    
    Returns:
        An authenticated Google Calendar service object, or None if authentication fails
    """
    creds = None
    
    # Check if token file exists
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    
    # If credentials don't exist or are invalid, prompt for authentication
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Check if client secret file exists
            if not CLIENT_SECRET_FILE.exists():
                print(f"\nError: Client secret file not found at {CLIENT_SECRET_FILE}")
                return None
            
            print(f"Using OAuth client credentials: {CLIENT_SECRET_FILE.name}")
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                print(f"Error during authentication flow: {e}")
                return None
        
        # Save the credentials for the next run
        CREDENTIALS_DIR.mkdir(exist_ok=True)
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
    
    # Build and return the service
    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error building Google Calendar service: {e}")
        return None

def get_calendar_events(days=7, max_events=5):
    """Get upcoming events from the user's Google Calendar.
    
    Args:
        days: Number of days to look ahead (default: 7)
        max_events: Maximum number of events to return (default: 5)
        
    Returns:
        A dictionary containing the status and events
    """
    # Get the calendar service
    service = get_calendar_service()
    
    # If authentication fails, return error
    if not service:
        return {
            "status": "error",
            "message": "Failed to authenticate with Google Calendar API. Please check the console for instructions."
        }
    
    # Calculate time range
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    end_date = (datetime.datetime.utcnow() + datetime.timedelta(days=days)).isoformat() + 'Z'
    
    try:
        # Call the Calendar API to get events
        events_result = service.events().list(
            calendarId='primary',  # Use primary calendar
            timeMin=now,
            timeMax=end_date,
            maxResults=max_events,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return {
                "status": "success",
                "message": "No upcoming events found.",
                "events": []
            }
        
        # Format the events
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            # Format the start and end times
            if 'T' in start:  # This is a datetime, not just a date
                start_dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                start_formatted = start_dt.strftime("%Y-%m-%d %H:%M")
            else:  # This is just a date
                start_formatted = start
                
            if 'T' in end:  # This is a datetime, not just a date
                end_dt = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
                end_formatted = end_dt.strftime("%Y-%m-%d %H:%M")
            else:  # This is just a date
                end_formatted = end
            
            formatted_event = {
                "id": event['id'],
                "summary": event.get('summary', 'No title'),
                "start": start_formatted,
                "end": end_formatted,
                "location": event.get('location', 'No location specified')
            }
            
            formatted_events.append(formatted_event)
        
        return {
            "status": "success",
            "events": formatted_events
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error retrieving calendar events: {str(e)}"
        }

# Define the function declaration for the calendar integration
get_calendar_events_declaration = {
    "name": "get_calendar_events",
    "description": "Gets upcoming events from the user's Google Calendar",
    "parameters": {
        "type": "object",
        "properties": {
            "days": {
                "type": "integer",
                "description": "Number of days to look ahead (default: 7)"
            },
            "max_events": {
                "type": "integer",
                "description": "Maximum number of events to return (default: 5)"
            }
        },
        "required": []
    }
}
