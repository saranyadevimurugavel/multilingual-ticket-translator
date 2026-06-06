"""JWT helpers — sign and verify tokens."""

import os, jwt
from datetime import datetime, timedelta

SECRET = os.getenv('SECRET_KEY', 'dev-secret-change-me')
ALGO   = 'HS256'
EXPIRY = int(os.getenv('JWT_EXPIRY_HOURS', 24))


def create_token(user_id: int, role: str) -> str:
    payload = {
        'sub':  user_id,
        'role': role,
        'exp':  datetime.utcnow() + timedelta(hours=EXPIRY),
        'iat':  datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)


def decode_token(token: str) -> dict:
    """Returns payload dict or raises jwt.InvalidTokenError."""
    return jwt.decode(token, SECRET, algorithms=[ALGO])
