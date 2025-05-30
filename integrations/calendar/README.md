# Google Calendar Integration

This module provides integration with Google Calendar, allowing Roomey AI Voice Agent to access and provide information about your calendar events.

## Features

- OAuth 2.0 authentication for secure access to Google Calendar
- Fetch upcoming calendar events from your primary calendar
- Filter events by date range and maximum number of events
- Format event data for easy consumption by the AI assistant

## Working Solution

The integration is currently working with OAuth 2.0 authentication. This allows Roomey to access your Google Calendar events after you've authorized the application.

## Setup Instructions

### 1. Install Required Packages

The following packages are required for the Google Calendar integration:

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dotenv
```

### 2. Google Cloud Console Setup

To use the Google Calendar API, you need to create a project in the Google Cloud Console and enable the API:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Library"
4. Search for "Google Calendar API" and enable it
5. Go to "APIs & Services" > "Credentials"
6. Click "Create Credentials" and select "OAuth client ID"
7. Select "Desktop application" as the application type
8. Enter a name for your OAuth client (e.g., "Roomey AI Voice Agent")
9. Click "Create"
10. Download the credentials JSON file

### 3. Configure the Integration

1. Rename the downloaded credentials file to `credentials.json`
2. Place the file in the `integrations/calendar/credentials/` directory:
   ```
   /path/to/Roomey_AI_Voice_Agent/integrations/calendar/credentials/credentials.json
   ```

3. Make sure the credentials directory is added to your `.gitignore` file to prevent accidentally committing sensitive information:
   ```
   # .gitignore
   integrations/calendar/credentials/
   ```

### 4. First-time Authentication

The first time you run the application and try to access calendar events:

1. A browser window will open asking you to sign in to your Google account
2. Grant the requested permissions to access your calendar
3. After authorization, a token will be saved for future use in `token.pickle`
4. Subsequent requests will use this token without requiring re-authentication

## Usage

The calendar integration provides the following function:

### `get_calendar_events(days=7, max_events=5)`

Retrieves upcoming events from your Google Calendar.

**Parameters:**
- `days` (int, optional): Number of days to look ahead. Default is 7.
- `max_events` (int, optional): Maximum number of events to return. Default is 5.

**Returns:**
A dictionary containing:
- `status`: "success" or "error"
- `events`: A list of event objects with the following properties:
  - `id`: Unique event ID
  - `summary`: Event title
  - `start`: Start time in "YYYY-MM-DD HH:MM" format
  - `end`: End time in "YYYY-MM-DD HH:MM" format
  - `location`: Event location (if available)

## Example

```python
from integrations.calendar.calendar import get_calendar_events

# Get events for the next 3 days, maximum 10 events
events_data = get_calendar_events(days=3, max_events=10)

if events_data["status"] == "success":
    events = events_data.get("events", [])
    if events:
        print(f"Found {len(events)} upcoming events:")
        for event in events:
            print(f"- {event['summary']} on {event['start']} at {event['location']}")
    else:
        print("No upcoming events found.")
else:
    print(f"Error: {events_data.get('message')}")
```

## Troubleshooting

### Authentication Solution

The current working solution uses OAuth 2.0 authentication with a desktop application client type. This approach works well because:

1. Desktop application OAuth clients don't require Google verification for personal use
2. The authentication flow is handled locally with a browser redirect
3. Once authenticated, a token is saved for future use

### Authentication Issues

If you encounter authentication issues:

1. Delete the `token.pickle` file from the credentials directory
2. Try running the application again to trigger a new authentication flow
3. Check that your Google account has access to the calendar you're trying to access
4. Make sure your OAuth client is set to "Desktop application" type in Google Cloud Console

### Testing the Integration

You can test the Google Calendar integration by running:

```bash
python integrations/calendar/test_auth.py
```

This script will authenticate with Google Calendar and retrieve your upcoming events.

### API Quota Limits

The Google Calendar API has usage quotas. If you exceed these limits, you may receive errors. Check the [Google Calendar API documentation](https://developers.google.com/calendar/api/guides/quota) for more information.

### Permissions

Ensure that your Google account has the necessary permissions to access the calendar. The integration uses the `https://www.googleapis.com/auth/calendar.readonly` scope, which provides read-only access to your calendars.
