from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

API_DIR = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    google_client_id: str
    google_client_secret: SecretStr
    google_redirect_uri: str
    database_url: str = f"sqlite:///{API_DIR / 'calendar_assistant.db'}"
    token_encryption_key: SecretStr
    frontend_origin: str = "http://localhost:3000"
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "qwen3:latest"

    model_config = SettingsConfigDict(
        env_file=API_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()