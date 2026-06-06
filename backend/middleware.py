"""
Auth middleware — decorators for protected routes.
"""

from functools import wraps
from flask import request, jsonify
from services.auth_service import decode_token
from database import User
import jwt as pyjwt


def _get_token():
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return auth.split(' ', 1)[1]
    # Also accept token in JSON body (for simple frontend fetch calls)
    data = request.get_json(silent=True) or {}
    return data.get('token') or request.args.get('token')


def login_required(f):
    """Requires a valid JWT. Attaches current_user to request.g."""
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import g
        token = _get_token()
        if not token:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        try:
            payload = decode_token(token)
            user = User.query.get(payload['sub'])
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 401
            g.current_user = user
        except pyjwt.ExpiredSignatureError:
            return jsonify({'success': False, 'error': 'Token expired'}), 401
        except pyjwt.InvalidTokenError:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Requires a valid JWT with admin role."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        from flask import g
        if g.current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated
