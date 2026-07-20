from unittest.mock import patch

from local_attendance.api import auth as auth_module


def test_login_calls_verify_password_even_for_unknown_username(client):
    """Regression test: verify_password must run regardless of whether the
    username exists, so bcrypt's deliberately-slow hashing takes the same time
    either way. Otherwise the response-time difference lets an attacker
    enumerate valid usernames.
    """
    with patch.object(auth_module, "verify_password", wraps=auth_module.verify_password) as spy:
        response = client.post("/auth/login", json={"username": "no-such-user", "password": "irrelevant"})

    assert response.status_code == 401
    spy.assert_called_once()
