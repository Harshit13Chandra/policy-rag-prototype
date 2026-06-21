import os
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Build the absolute path to the .env file located at backend/.env
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    embedding_service_url: str
    gemini_api_key: str
    gemini_model: str
    upload_dir: str

    model_config = SettingsConfigDict(env_file=str(ENV_FILE_PATH), case_sensitive=False)

@lru_cache()
def get_settings() -> Settings:
    return Settings()
