from local_attendance.config import DEFAULT_DUPLICATE_WINDOW_SECONDS, Settings


def test_duplicate_window_default_is_sixty_seconds():
    settings = Settings()
    assert settings.duplicate_window_seconds == DEFAULT_DUPLICATE_WINDOW_SECONDS
    assert settings.duplicate_window_seconds == 60


def test_required_local_settings_have_defaults():
    settings = Settings()
    assert settings.database_url
    assert settings.jwt_secret
    assert settings.jwt_algorithm == "HS256"
    assert settings.access_token_expire_minutes > 0
    assert isinstance(settings.camera_index, int)
    assert settings.face_match_threshold > 0
