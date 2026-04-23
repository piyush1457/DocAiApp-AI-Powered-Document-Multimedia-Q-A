"""
Configuration module for the DocAiApp backend.
Uses Pydantic BaseSettings to load environment variables and provide type-safe access.
"""

from typing import List
from pydantic import Field, RedisDsn, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings for DocAiApp.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )

    PROJECT_NAME: str = Field("DocAiApp", description="The name of the project")
    VERSION: str = Field("0.1.0", description="The version of the application")
    DEBUG: bool = Field(False, description="Debug mode flag")
    API_V1_STR: str = "/docaiapp/v1"

    # Security
    SECRET_KEY: str = Field(..., description="Secret key for JWT signing")
    ALGORITHM: str = Field("HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        30, description="Access token expiration time"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        7, description="Refresh token expiration time"
    )

    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")

    # Redis
    REDIS_URL: RedisDsn = Field(..., description="Redis connection string")

    # AI Provider Keys
    GEMINI_API_KEY: str = Field(..., description="Gemini API key")
    GROQ_API_KEY: str = Field(..., description="Groq API key")

    # Storage
    FAISS_INDEX_PATH: str = Field(
        "/app/faiss_index", description="Path to store FAISS index"
    )
    UPLOAD_DIR: str = Field("/app/uploads", description="Directory for file uploads")

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        ["http://localhost:3000"],
        description="List of origins allowed to make CORS requests",
    )

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)


settings = Settings()
