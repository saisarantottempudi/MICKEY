"""
Token-based authentication for MICKEY API.
Generates a random token on first run, stores it in data/auth_token.
All API requests must include this token in the Authorization header.
Local requests (127.0.0.1, ::1) bypass auth for convenience.
"""

import os
import secrets
from functools import wraps
from flask import request, jsonify
from config import DATA_DIR

TOKEN_FILE = os.path.join(DATA_DIR, "auth_token")


def get_or_create_token() -> str:
    """Get existing token or generate a new one."""
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            token = f.read().strip()
            if token:
                return token

    # Generate new token
    token = secrets.token_urlsafe(32)
    with open(TOKEN_FILE, "w") as f:
        f.write(token)
    os.chmod(TOKEN_FILE, 0o600)  # Owner read/write only
    return token


def is_local_request() -> bool:
    """Check if request comes from localhost."""
    remote = request.remote_addr
    return remote in ("127.0.0.1", "::1", "localhost")


def require_auth(f):
    """Decorator: require valid token for non-local requests."""

    @wraps(f)
    def decorated(*args, **kwargs):
        # Local requests bypass auth
        if is_local_request():
            return f(*args, **kwargs)

        # Check Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            provided_token = auth_header[7:]
        else:
            provided_token = auth_header

        if not provided_token or provided_token != get_or_create_token():
            return jsonify({"error": "Unauthorized. Provide valid token in Authorization header."}), 401

        return f(*args, **kwargs)

    return decorated
