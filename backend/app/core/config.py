"""
Configuration module for the DocAiApp backend.
Uses Pydantic BaseSettings to load environment variables and provide type-safe access.
"""

import json
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings for DocAiApp.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    PROJECT_NAME: str = Field("DocAiApp", description="The name of the project")
    VERSION: str = Field("0.1.0", description="The version of the application")
    DEBUG: bool = Field(False, description="Debug mode flag")
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = Field(
        "dev_secret_key_change_me", description="Secret key for JWT signing"
    )
    ALGORITHM: str = Field("HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        30, description="Access token expiration time"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        7, description="Refresh token expiration time"
    )

    # Database
    DATABASE_URL: str = Field(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/docai",
        description="PostgreSQL connection string",
    )

    # Redis
    REDIS_URL: str = Field(
        "redis://localhost:6379/0", description="Redis connection string"
    )

    # AI Provider Keys
    GEMINI_API_KEY: str = Field("dummy_gemini_key", description="Gemini API key")
    GROQ_API_KEY: str = Field("dummy_groq_key", description="Groq API key")

    # Storage
    # On Vercel serverless filesystem only /tmp is writable - override via env
    FAISS_INDEX_PATH: str = Field(
        "/tmp/faiss_index", description="Path to store FAISS index"
    )
    UPLOAD_DIR: str = Field("/tmp/uploads", description="Directory for file uploads")
    # Vercel Blob (persistent storage) - set BLOB_READ_WRITE_TOKEN in Vercel dashboard
    BLOB_READ_WRITE_TOKEN: str = Field(
        "", description="Vercel Blob RW token (auto-injected when Blob store is added)"
    )

    # CORS
    # Use str to avoid Pydantic JSON decoding error on Vercel when env is plain comma-separated string
    BACKEND_CORS_ORIGINS: str = Field(
        "http://localhost:3000",
        description="Comma-separated list of origins allowed to make CORS requests",
    )

    @property
    def cors_origins(self) -> List[str]:
        v = self.BACKEND_CORS_ORIGINS
        if isinstance(v, list):
            return v
        v = v.strip()
        if not v:
            return []
        # Handle JSON array string e.g. '["https://a","https://b"]'
        if v.startswith("["):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(i).strip() for i in parsed]
            except Exception:
                pass
        return [i.strip() for i in v.split(",") if i.strip()]

    @property
    def is_blob_enabled(self) -> bool:
        return bool(self.BLOB_READ_WRITE_TOKEN and self.BLOB_READ_WRITE_TOKEN.strip())

    @property
    def is_vercel(self) -> bool:
        import os

        return bool(os.getenv("VERCEL"))


settings = Settings()
