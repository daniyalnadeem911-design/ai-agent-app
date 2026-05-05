import base64
import email as email_lib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build
from auth.google_auth import dict_to_credentials, refresh_credentials_if_needed


def get_gmail_service(credentials_dict):
    """Build Gmail API service from stored credentials."""
    creds = dict_to_credentials(credentials_dict)
    creds = refresh_credentials_if_needed(creds)
    return build('gmail', 'v1', credentials=creds)


def fetch_inbox_emails(credentials_dict, max_results=20):
    """
    Fetch emails from inbox.
    Returns list of email dicts with id, sender, subject, snippet, body.
    """
    service = get_gmail_service(credentials_dict)

    # Get list of message IDs
    result = service.users().messages().list(
        userId='me',
        labelIds=['INBOX'],
        maxResults=max_results
    ).execute()

    messages = result.get('messages', [])
    emails = []

    for msg_ref in messages:
        try:
            msg = service.users().messages().get(
                userId='me',
                id=msg_ref['id'],
                format='full'
            ).execute()

            email_data = parse_email(msg)
            emails.append(email_data)
        except Exception as e:
            print(f"Error fetching email {msg_ref['id']}: {e}")
            continue

    return emails


def parse_email(msg):
    """Parse Gmail API message into clean dict."""
    headers = {h['name']: h['value'] for h in msg['payload'].get('headers', [])}

    body = extract_body(msg['payload'])

    return {
        'id': msg['id'],
        'thread_id': msg.get('threadId', ''),
        'sender': headers.get('From', 'Unknown'),
        'to': headers.get('To', ''),
        'subject': headers.get('Subject', '(No Subject)'),
        'date': headers.get('Date', ''),
        'snippet': msg.get('snippet', ''),
        'body': body[:3000],  # Limit body size for AI processing
        'label_ids': msg.get('labelIds', [])
    }


def extract_body(payload):
    """Recursively extract email body text."""
    body = ''

    if payload.get('body', {}).get('data'):
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
        return body

    for part in payload.get('parts', []):
        if part['mimeType'] == 'text/plain':
            if part.get('body', {}).get('data'):
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                return body
        elif part['mimeType'] == 'text/html' and not body:
            if part.get('body', {}).get('data'):
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
        elif part.get('parts'):
            body = extract_body(part)
            if body:
                return body

    return body


def send_email(credentials_dict, to, subject, body, thread_id=None):
    """Send an email via Gmail API."""
    service = get_gmail_service(credentials_dict)

    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    msg_body = {'raw': raw}
    if thread_id:
        msg_body['threadId'] = thread_id

    sent = service.users().messages().send(
        userId='me',
        body=msg_body
    ).execute()

    return sent


def get_email_thread(credentials_dict, thread_id):
    """Fetch full email thread for context."""
    service = get_gmail_service(credentials_dict)

    thread = service.users().threads().get(
        userId='me',
        id=thread_id,
        format='full'
    ).execute()

    messages = []
    for msg in thread.get('messages', []):
        messages.append(parse_email(msg))

    return messages


def fetch_emails_by_category(credentials_dict, category='INBOX', max_results=20):
    """
    Fetch emails by Gmail category label.
    category options: INBOX, CATEGORY_SOCIAL, CATEGORY_PROMOTIONS,
                      CATEGORY_UPDATES, CATEGORY_FORUMS, SPAM
    """
    service = get_gmail_service(credentials_dict)

    result = service.users().messages().list(
        userId='me',
        labelIds=[category],
        maxResults=max_results
    ).execute()

    messages = result.get('messages', [])
    emails = []

    for msg_ref in messages:
        try:
            msg = service.users().messages().get(
                userId='me',
                id=msg_ref['id'],
                format='full'
            ).execute()
            emails.append(parse_email(msg))
        except Exception as e:
            print(f"Error: {e}")
            continue

    return emails