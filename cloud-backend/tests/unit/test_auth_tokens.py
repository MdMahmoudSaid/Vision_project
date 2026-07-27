import pytest
from datetime import timedelta
import time
import jwt

from cloud_attendance.auth.password import hash_password, verify_password
from cloud_attendance.auth.tokens import create_access_token, decode_access_token, TokenError
from cloud_attendance.config import get_settings


def test_password_hashing():
    password = "secretpassword"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)


def test_create_and_decode_token():
    token = create_access_token("user-123", "owner")
    
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"
    assert payload["role"] == "owner"


def test_decode_invalid_token():
    with pytest.raises(TokenError):
        decode_access_token("invalid.token.here")


def test_decode_expired_token(monkeypatch):
    settings = get_settings()
    
    # We can mock jwt.encode to create an expired token or simply create one manually
    payload = {
        "sub": "user-123",
        "role": "owner",
        "exp": time.time() - 3600  # expired an hour ago
    }
    expired_token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    
    with pytest.raises(TokenError):
        decode_access_token(expired_token)
