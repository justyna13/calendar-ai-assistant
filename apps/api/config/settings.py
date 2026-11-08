from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

API_DIR = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    google_client_id: str
    google_client_secret: SecretStr
    google_redirect_uri: str

    model_config = SettingsConfigDict(
        env_file=API_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()