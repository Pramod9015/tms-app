"""
Application configuration using Pydantic BaseSettings.
Reads values from .env file automatically.
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
import secrets


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Secure Transaction Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./tms_dev.db"

    @field_validator("DATABASE_URL")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        return v

    # Encryption (Fernet / AES-256)
    AES_ENCRYPTION_KEY: str = ""  # Must be set in production

    # JWT
    SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Admin Bootstrap
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "Admin@123!"
    ADMIN_EMAIL: str = "admin@tms.local"

    # Gemini Vision API (for slip OCR)
    GEMINI_API_KEY: str = ""  # Set in .env — get from https://aistudio.google.com/

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
