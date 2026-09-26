import json
from pathlib import Path
from typing import List, Union
from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory of the backend
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Explicitly load .env file via python-dotenv if present
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """Application configuration settings."""

    PROJECT_NAME: str = "Learning Debugger API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_SECRET_KEY: str = ""

    # CORS configuration - localhost development origins
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v_stripped = v.strip()
            if v_stripped.startswith("[") and v_stripped.endswith("]"):
                return json.loads(v_stripped)
            return [i.strip() for i in v_stripped.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=str(env_path),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
