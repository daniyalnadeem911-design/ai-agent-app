from flask import Blueprint, session, jsonify, request, render_template, redirect, url_for
from services.ai_service import chat_with_assistant
from services.gmail_service import fetch_inbox_emails
from services.calendar_service import fetch_upcoming_events

ai_bp = Blueprint('ai', __name__)


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)

    return decorated


@ai_bp.route('/assistant')
@login_required
def assistant_page():
    return render_template('assistant.html', user=session['user'])


@ai_bp.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data = request.json
    user_message = data.get('message', '')
    chat_history = data.get('history', [])

    # Fetch fresh context
    try:
        emails = fetch_inbox_emails(session['credentials'], max_results=10)
    except:
        emails = []

    try:
        events = fetch_upcoming_events(session['credentials'], days_ahead=3)
    except:
        events = []

    response = chat_with_assistant(
        user_message,
        calendar_events=events,
        recent_emails=emails,
        chat_history=chat_history
    )

    return jsonify({'success': True, 'response': response})