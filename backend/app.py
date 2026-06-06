"""
Multilingual Ticket Translator — Flask Application Entry Point
"""

import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from database import db, init_db
from routes.auth_routes      import auth_bp
from routes.ticket_routes    import ticket_bp
from routes.dashboard_routes import dashboard_bp
from routes.glossary_routes  import glossary_bp
from routes.batch_routes     import batch_bp

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)

    # ── Database URL ──────────────────────────────────────────────────────────
    # Render provides DATABASE_URL — use it if available, else fallback to SQLite
    db_url = os.getenv('DATABASE_URL', 'sqlite:///mtt.db')
    # Render Postgres URLs start with postgres:// — SQLAlchemy needs postgresql://
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)

    app.config['SECRET_KEY']                  = os.getenv('SECRET_KEY', 'dev-secret-change-me')
    app.config['SQLALCHEMY_DATABASE_URI']     = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Allow all origins in dev; in production allow your Vercel domain
    allowed_origins = os.getenv('ALLOWED_ORIGINS', '*')
    origins = [o.strip() for o in allowed_origins.split(',')] if ',' in allowed_origins else allowed_origins
    CORS(app, resources={r"/api/*": {"origins": origins}})

    # ── Extensions ────────────────────────────────────────────────────────────
    db.init_app(app)

    with app.app_context():
        init_db()

    # ── Blueprints ────────────────────────────────────────────────────────────
    app.register_blueprint(auth_bp,      url_prefix='/api/auth')
    app.register_blueprint(ticket_bp,    url_prefix='/api/tickets')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(glossary_bp,  url_prefix='/api/glossary')
    app.register_blueprint(batch_bp,     url_prefix='/api/batch')

    # ── Health & root ─────────────────────────────────────────────────────────
    @app.route('/')
    def index():
        return {'status': 'ok', 'message': 'MTT API running'}, 200

    @app.route('/api/health')
    def health():
        return {'status': 'ok'}, 200

    # ── Error handlers ────────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return {'success': False, 'error': 'Not found'}, 404

    @app.errorhandler(500)
    def server_error(e):
        return {'success': False, 'error': 'Internal server error'}, 500

    return app


if __name__ == '__main__':
    application = create_app()
    application.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', '1') == '1'
    )
