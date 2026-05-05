from flask import Blueprint, session, redirect, url_for, request, render_template
from auth.google_auth import get_authorization_url, exchange_code_for_tokens, credentials_to_dict, get_user_info
from database.db import get_session, User
import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login')
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@auth_bp.route('/authorize')
def authorize():
    auth_url, state = get_authorization_url()
    session['oauth_state'] = state
    return redirect(auth_url)


@auth_bp.route('/callback')
def callback():
    if 'error' in request.args:
        return f"OAuth error: {request.args.get('error')}", 400

    code = request.args.get('code')
    if not code:
        return "Missing authorization code", 400

    state = request.args.get('state')
    credentials = exchange_code_for_tokens(request.url, state)
    creds_dict = credentials_to_dict(credentials)

    # Get user info
    user_info = get_user_info(credentials)

    # Save to database
    db = get_session()
    user = db.query(User).filter_by(google_id=user_info['id']).first()

    if not user:
        user = User(
            google_id=user_info['id'],
            email=user_info['email'],
            name=user_info.get('name', ''),
            picture=user_info.get('picture', '')
        )
        db.add(user)

    user.access_token = creds_dict['token']
    user.refresh_token = creds_dict.get('refresh_token', '')
    db.commit()
    db.close()

    # Store in session
    session['user'] = {
        'id': user_info['id'],
        'email': user_info['email'],
        'name': user_info.get('name', ''),
        'picture': user_info.get('picture', '')
    }
    session['credentials'] = creds_dict

    return redirect(url_for('dashboard'))


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))