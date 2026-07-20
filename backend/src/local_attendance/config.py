from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DUPLICATE_WINDOW_SECONDS = 60


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LOCAL_ATTENDANCE_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./local_attendance.db"
    jwt_secret: str = "local-dev-secret-change-me-in-production-min32"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    camera_index: int = 0
    duplicate_window_seconds: int = DEFAULT_DUPLICATE_WINDOW_SECONDS
    # DeepFaceEngine compares ArcFace embeddings with plain (unnormalized) Euclidean
    # distance; 4.15 is DeepFace's own pre-tuned same-person threshold for that exact
    # model/metric pair (deepface.modules.verification.find_threshold("ArcFace",
    # "euclidean")). Lower distance = more similar; matches are distance <= threshold.
    face_match_threshold: float = 4.15


@lru_cache
def get_settings() -> Settings:
    return Settings()
