import os
print("Step 1: os imported")
from flask import Flask, session, redirect, url_for, render_template
print("Step 2: flask imported")
from config import Config
print("Step 3: config imported")
from routes.auth_routes import auth_bp
print("Step 4: auth_routes imported")
from routes.gmail_routes import gmail_bp
print("Step 5: gmail_routes imported")
from routes.calendar_routes import calendar_bp
print("Step 6: calendar_routes imported")
from routes.ai_routes import ai_bp
print("Step 7: ai_routes imported")
from database.db import get_engine
print("Step 8: database imported")
print("Starting app import...")


def create_app():
    print("Creating Flask app...")
    app = Flask(__name__)
    print("Flask app created")
    app.config.from_object(Config)
    print("Config loaded")

    get_engine()
    print("Database initialized")

    app.register_blueprint(auth_bp)
    print("auth_bp registered")
    app.register_blueprint(gmail_bp)
    print("gmail_bp registered")
    app.register_blueprint(calendar_bp)
    print("calendar_bp registered")
    app.register_blueprint(ai_bp)
    print("ai_bp registered")

    @app.route('/')
    def index():
        if 'user' in session:
            return redirect(url_for('dashboard'))
        return redirect(url_for('auth.login'))

    @app.route('/dashboard')
    def dashboard():
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return render_template('dashboard.html', user=session['user'])

    @app.errorhandler(404)
    def not_found(e):
        return render_template('login.html'), 404

    print("App fully created")
    return app


try:
    app = create_app()
except Exception as e:
    import traceback
    print("APP STARTUP ERROR:")
    traceback.print_exc()
    raise

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)