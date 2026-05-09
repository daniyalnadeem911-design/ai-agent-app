import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-fallback-key')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    AI_MODEL = os.getenv('AI_MODEL', 'gpt-4o-mini')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database/app.db')
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False

    # Google OAuth scopes
    GOOGLE_SCOPES = [
        'openid',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/calendar.readonly',
    ]

    CLIENT_SECRETS_FILE = 'client_secret.json'
    REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:5000/callback')