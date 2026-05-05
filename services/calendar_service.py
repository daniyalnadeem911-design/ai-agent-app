from googleapiclient.discovery import build
from auth.google_auth import dict_to_credentials, refresh_credentials_if_needed
import datetime


def get_calendar_service(credentials_dict):
    """Build Calendar API service."""
    creds = dict_to_credentials(credentials_dict)
    creds = refresh_credentials_if_needed(creds)
    return build('calendar', 'v3', credentials=creds)


def fetch_upcoming_events(credentials_dict, max_results=100, days_ahead=30):
    service = get_calendar_service(credentials_dict)

    now = datetime.datetime.utcnow().isoformat() + 'Z'
    future = (datetime.datetime.utcnow() + datetime.timedelta(days=days_ahead)).isoformat() + 'Z'

    result = service.events().list(
        calendarId='primary',
        timeMin=now,
        timeMax=future,
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = result.get('items', [])

    # Deduplicate by title — removes repeated holiday entries
    seen_titles = set()
    unique_events = []
    for e in events:
        title = e.get('summary', '')
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_events.append(parse_event(e))

    return unique_events


def parse_event(event):
    """Parse Calendar API event into clean dict."""
    start = event.get('start', {})
    end = event.get('end', {})

    # Handle all-day events vs timed events
    start_time = start.get('dateTime', start.get('date', ''))
    end_time = end.get('dateTime', end.get('date', ''))

    # Extract attendee emails
    attendees = []
    for att in event.get('attendees', []):
        attendees.append({
            'email': att.get('email', ''),
            'name': att.get('displayName', att.get('email', '')),
            'response': att.get('responseStatus', 'needsAction')
        })

    # Extract meeting link if present
    meeting_link = ''
    conf_data = event.get('conferenceData', {})
    for entry in conf_data.get('entryPoints', []):
        if entry.get('entryPointType') == 'video':
            meeting_link = entry.get('uri', '')
            break

    return {
        'id': event.get('id', ''),
        'title': event.get('summary', 'Untitled Event'),
        'description': event.get('description', ''),
        'start': start_time,
        'end': end_time,
        'location': event.get('location', ''),
        'attendees': attendees,
        'meeting_link': meeting_link,
        'organizer': event.get('organizer', {}).get('email', ''),
        'status': event.get('status', 'confirmed'),
        'html_link': event.get('htmlLink', '')
    }


def get_todays_events(credentials_dict):
    """Get only today's events."""
    service = get_calendar_service(credentials_dict)

    today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0).isoformat() + 'Z'
    today_end = datetime.datetime.utcnow().replace(hour=23, minute=59, second=59).isoformat() + 'Z'

    result = service.events().list(
        calendarId='primary',
        timeMin=today_start,
        timeMax=today_end,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    return [parse_event(e) for e in result.get('items', [])]