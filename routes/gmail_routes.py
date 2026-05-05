from flask import Blueprint, session, jsonify, request, render_template, redirect, url_for
from services.gmail_service import fetch_inbox_emails, send_email, get_email_thread, fetch_emails_by_category
from services.ai_service import analyze_email, generate_email_reply, generate_inbox_summary

gmail_bp = Blueprint('gmail', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@gmail_bp.route('/gmail')
@login_required
def gmail_page():
    return render_template('gmail.html', user=session['user'])

@gmail_bp.route('/api/emails')
@login_required
def get_emails():
    try:
        emails = fetch_inbox_emails(session['credentials'], max_results=20)
        return jsonify({'success': True, 'emails': emails})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@gmail_bp.route('/api/emails/category/<category>')
@login_required
def get_emails_by_category(category):
    allowed = ['INBOX', 'CATEGORY_SOCIAL', 'CATEGORY_PROMOTIONS',
               'CATEGORY_UPDATES', 'CATEGORY_FORUMS', 'SPAM']
    if category not in allowed:
        return jsonify({'success': False, 'error': 'Invalid category'}), 400
    try:
        emails = fetch_emails_by_category(session['credentials'], category)
        return jsonify({'success': True, 'emails': emails})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@gmail_bp.route('/api/emails/analyze', methods=['POST'])
@login_required
def analyze_single_email():
    email_data = request.json
    analysis = analyze_email(email_data)
    return jsonify({'success': True, 'analysis': analysis})

@gmail_bp.route('/api/emails/summary')
@login_required
def inbox_summary():
    try:
        emails = fetch_inbox_emails(session['credentials'], max_results=20)
        summary = generate_inbox_summary(emails)
        return jsonify({'success': True, 'summary': summary})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@gmail_bp.route('/api/emails/reply', methods=['POST'])
@login_required
def generate_reply():
    data = request.json
    email_data = data.get('email')
    tone = data.get('tone', 'Professional and concise')

    user_name = session.get('user', {}).get('name', '')
    first_name = user_name.split()[0] if user_name else None

    thread_context = None
    if email_data.get('thread_id'):
        try:
            thread = get_email_thread(session['credentials'], email_data['thread_id'])
            thread_context = '\n'.join([f"[{m['sender']}]: {m['snippet']}" for m in thread])
        except:
            pass

    reply = generate_email_reply(email_data, tone, thread_context, user_name=first_name)
    return jsonify({'success': True, 'reply': reply})

@gmail_bp.route('/api/emails/send', methods=['POST'])
@login_required
def send_reply():
    data = request.json
    try:
        result = send_email(
            session['credentials'],
            to=data['to'],
            subject=data['subject'],
            body=data['body'],
            thread_id=data.get('thread_id')
        )
        return jsonify({'success': True, 'message_id': result.get('id')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500