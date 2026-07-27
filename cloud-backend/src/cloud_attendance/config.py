from functools import lru_cache
from typing import Dict

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "cloud-dev-secret-change-me-in-production-min32"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CLOUD_ATTENDANCE_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./cloud_attendance.db"
    jwt_secret: str = DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    
    # Map of site_key_id -> shared_secret for authenticating incoming sync batches
    sync_api_keys: Dict[str, str] = {"default-site": "dev-sync-secret-change-me"}

@lru_cache
def get_settings() -> Settings:
    return Settings()
