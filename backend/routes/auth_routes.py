"""
Auth Routes
===========
Serves both login pages:
  pages/client/login.html  →  POST /api/auth/login  (role=client)
  pages/admin/login.html   →  POST /api/auth/login  (role=admin)

Single endpoint — the frontend redirects based on the 'role' in the response.
"""

from flask import Blueprint, request, jsonify
from database import db, User
from services.auth_service import create_token

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Request JSON:
        { "email": "admin@mtt.com", "password": "admin123" }

    Response 200:
        {
          "success": true,
          "token": "<jwt>",
          "user": { "id": 1, "email": "...", "role": "admin", "name": "..." }
        }

    Response 401:
        { "success": false, "error": "Invalid email or password" }
    """
    data = request.get_json(silent=True) or {}

    email    = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({'success': False, 'error': 'Invalid email or password'}), 401

    token = create_token(user.id, user.role)

    return jsonify({
        'success': True,
        'token':   token,
        'user':    user.to_dict(),
    }), 200


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Request JSON:
        { "email": "...", "password": "...", "name": "...", "role": "client" }
    """
    data = request.get_json(silent=True) or {}

    email    = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    name     = (data.get('name')  or '').strip()
    role     = data.get('role', 'client')

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'error': 'Email already registered. Please log in instead.'}), 409

    user = User(email=email, name=name, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_token(user.id, user.role)

    return jsonify({
        'success': True,
        'token':   token,
        'user':    user.to_dict(),
    }), 201


@auth_bp.route('/me', methods=['GET'])
def me():
    """Return current user from token — used to restore session on page load."""
    from middleware import login_required
    from flask import g

    @login_required
    def _inner():
        return jsonify({'success': True, 'user': g.current_user.to_dict()}), 200

    return _inner()
