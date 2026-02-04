"""
Configuration management for closetGPT backend.
Loads environment-specific settings from .env files.
"""

import os
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    env: Literal["dev", "prod"] = "dev"
    debug: bool = False

    # Database
    database_url: str

    # Redis
    redis_url: str

    # Storage Provider (MinIO for dev, R2 for prod)
    storage_provider: Literal["minio", "r2"] = "minio"

    # MinIO (local development)
    minio_endpoint: str | None = None  # Internal endpoint for backend
    minio_public_endpoint: str | None = None  # Public endpoint for browser access
    minio_access_key: str | None = None
    minio_secret_key: str | None = None
    minio_bucket: str | None = None
    minio_use_ssl: bool = False
    minio_region: str = "us-east-1"

    # Cloudflare R2 (production)
    r2_account_id: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_bucket: str | None = None
    r2_public_url: str | None = None

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Logging
    log_level: str = "INFO"

    # Authentication (Phase 6)
    jwt_secret: str | None = None
    supabase_url: str | None = None
    supabase_anon_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env.dev",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def __init__(self, **kwargs):
        """Initialize settings with environment-specific .env file."""
        # Determine which .env file to load based on ENV variable
        env = os.getenv("ENV", "dev")
        env_file = f".env.{env}"

        # Check if env-specific file exists, otherwise fall back to .env.dev
        if not Path(env_file).exists():
            env_file = ".env.dev"

        # Update model config with correct env file
        self.model_config["env_file"] = env_file

        super().__init__(**kwargs)

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.env == "dev"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.env == "prod"

    def validate_storage_config(self) -> None:
        """Validate that required storage credentials are present."""
        if self.storage_provider == "minio":
            required = ["minio_endpoint", "minio_access_key", "minio_secret_key", "minio_bucket"]
            missing = [field for field in required if getattr(self, field) is None]
            if missing:
                raise ValueError(f"MinIO storage requires: {', '.join(missing)}")

        elif self.storage_provider == "r2":
            required = ["r2_account_id", "r2_access_key_id", "r2_secret_access_key", "r2_bucket"]
            missing = [field for field in required if getattr(self, field) is None]
            if missing:
                raise ValueError(f"R2 storage requires: {', '.join(missing)}")


# Global settings instance
settings = Settings()

# Validate storage configuration on startup
settings.validate_storage_config()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


if __name__ == "__main__":
    # Test configuration loading
    print(f"Environment: {settings.env}")
    print(f"Debug: {settings.debug}")
    print(f"Database URL: {settings.database_url[:30]}...")
    print(f"Redis URL: {settings.redis_url[:30]}...")
    print(f"Storage Provider: {settings.storage_provider}")
    print(f"CORS Origins: {settings.cors_origins_list}")
    print(f"Is Development: {settings.is_development}")
