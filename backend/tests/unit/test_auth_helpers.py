import pytest

from local_attendance.auth.password import hash_password, verify_password
from local_attendance.auth.tokens import TokenError, create_access_token, decode_access_token


def test_hash_password_and_verify_roundtrip():
    hashed = hash_password("correct-horse-battery")
    assert hashed != "correct-horse-battery"
    assert verify_password("correct-horse-battery", hashed)


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("correct-horse-battery")
    assert not verify_password("wrong-password", hashed)


def test_create_and_decode_access_token_roundtrip():
    token = create_access_token(subject="user-1", role="admin")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-1"
    assert payload["role"] == "admin"
    assert "exp" in payload


def test_decode_access_token_rejects_garbage_token():
    with pytest.raises(TokenError):
        decode_access_token("not-a-real-token")


def test_decode_access_token_rejects_tampered_token():
    token = create_access_token(subject="user-1", role="guard")
    # Flip a character in the middle of the signature segment, not the last
    # character: trailing base64url padding bits don't affect the decoded
    # signature bytes, so tampering there is not guaranteed to invalidate it.
    mid = len(token) // 2
    tampered = token[:mid] + ("A" if token[mid] != "A" else "B") + token[mid + 1 :]
    with pytest.raises(TokenError):
        decode_access_token(tampered)
