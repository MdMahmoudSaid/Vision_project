from sqlalchemy import select
from sqlalchemy.orm import Session

from local_attendance.config import get_settings
from local_attendance.models.setting import LocalSetting

DUPLICATE_WINDOW_SECONDS_KEY = "duplicate_window_seconds"


def get_duplicate_window_seconds(db: Session) -> int:
    setting = db.scalar(select(LocalSetting).where(LocalSetting.key == DUPLICATE_WINDOW_SECONDS_KEY))
    if setting is None:
        return get_settings().duplicate_window_seconds
    try:
        return int(setting.value)
    except ValueError:
        return get_settings().duplicate_window_seconds


def ensure_default_settings(db: Session) -> None:
    existing = db.scalar(select(LocalSetting).where(LocalSetting.key == DUPLICATE_WINDOW_SECONDS_KEY))
    if existing is None:
        db.add(LocalSetting(key=DUPLICATE_WINDOW_SECONDS_KEY, value=str(get_settings().duplicate_window_seconds)))
        db.commit()
