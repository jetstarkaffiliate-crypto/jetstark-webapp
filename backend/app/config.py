from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import List
import os


class Settings(BaseSettings):
    app_name: str = "Jetstark Affiliate Hub"
    debug: bool = False

    # Database
    # Render provides postgres:// URLs; auto-convert to asyncpg scheme
    database_url: str = "postgresql+asyncpg://jetstark:changeme@localhost:5432/jetstark"
    database_url_sync: str = "postgresql://jetstark:changeme@localhost:5432/jetstark"

    @model_validator(mode="after")
    def normalize_db_urls(self):
        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if self.database_url_sync.startswith("postgres://"):
            self.database_url_sync = self.database_url_sync.replace("postgres://", "postgresql://", 1)
        return self

    # Security
    secret_key: str = "change-me-to-a-random-64-char-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    bcrypt_rounds: int = 12

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Payment
    paystack_secret_key: str = ""
    paystack_public_key: str = ""

    # Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "noreply@jetstark.com"

    # CORS
    cors_origins: str = "http://localhost:8000,http://localhost:5500,http://127.0.0.1:5500,https://jetstark-api.onrender.com,https://jetstark.com"

    # Sentry
    sentry_dsn: str = ""

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
