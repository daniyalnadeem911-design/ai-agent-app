import os
from flask import Flask, session, redirect, url_for, render_template
from config import Config
from routes.auth_routes import auth_bp
from routes.gmail_routes import gmail_bp
from routes.calendar_routes import calendar_bp
from routes.ai_routes import ai_bp
from database.db import get_engine


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database
    get_engine()

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(gmail_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(ai_bp)

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

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)