"""Calendar module for accessing and managing Google Calendar information."""

from .google_calendar import (
    get_calendar_events,
    get_calendar_events_declaration
)

__all__ = [
    'get_calendar_events',
    'get_calendar_events_declaration'
]
