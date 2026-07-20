from local_attendance.models.setting import LocalSetting
from local_attendance.services.settings_service import (
    DUPLICATE_WINDOW_SECONDS_KEY,
    ensure_default_settings,
    get_duplicate_window_seconds,
)


def test_get_duplicate_window_seconds_falls_back_to_config_default(db_session):
    assert get_duplicate_window_seconds(db_session) == 60


def test_get_duplicate_window_seconds_reads_custom_setting(db_session):
    db_session.add(LocalSetting(key=DUPLICATE_WINDOW_SECONDS_KEY, value="120"))
    db_session.commit()
    assert get_duplicate_window_seconds(db_session) == 120


def test_get_duplicate_window_seconds_falls_back_on_unparsable_value(db_session):
    db_session.add(LocalSetting(key=DUPLICATE_WINDOW_SECONDS_KEY, value="not-a-number"))
    db_session.commit()
    assert get_duplicate_window_seconds(db_session) == 60


def test_ensure_default_settings_seeds_row_when_missing(db_session):
    ensure_default_settings(db_session)
    setting = db_session.query(LocalSetting).filter_by(key=DUPLICATE_WINDOW_SECONDS_KEY).first()
    assert setting is not None
    assert setting.value == "60"


def test_ensure_default_settings_does_not_overwrite_existing(db_session):
    db_session.add(LocalSetting(key=DUPLICATE_WINDOW_SECONDS_KEY, value="30"))
    db_session.commit()
    ensure_default_settings(db_session)
    setting = db_session.query(LocalSetting).filter_by(key=DUPLICATE_WINDOW_SECONDS_KEY).first()
    assert setting.value == "30"
