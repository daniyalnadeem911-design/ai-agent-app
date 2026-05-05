from flask import Blueprint, session, jsonify, render_template, redirect, url_for
from services.calendar_service import fetch_upcoming_events, get_todays_events
from services.ai_service import generate_event_preparation, generate_meeting_briefing

calendar_bp = Blueprint('calendar', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@calendar_bp.route('/calendar')
@login_required
def calendar_page():
    return render_template('calendar.html', user=session['user'])

@calendar_bp.route('/api/events')
@login_required
def get_events():
    try:
        events = fetch_upcoming_events(session['credentials'], max_results=100, days_ahead=30)
        return jsonify({'success': True, 'events': events})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@calendar_bp.route('/api/events/today')
@login_required
def todays_events():
    try:
        events = get_todays_events(session['credentials'])
        return jsonify({'success': True, 'events': events})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@calendar_bp.route('/api/events/prepare', methods=['POST'])
@login_required
def prepare_for_event():
    from flask import request
    event = request.json
    preparation = generate_event_preparation(event)
    return jsonify({'success': True, 'preparation': preparation})

@calendar_bp.route('/api/events/briefing', methods=['POST'])
@login_required
def event_briefing():
    from flask import request
    event = request.json
    briefing = generate_meeting_briefing(event)
    return jsonify({'success': True, 'briefing': briefing})