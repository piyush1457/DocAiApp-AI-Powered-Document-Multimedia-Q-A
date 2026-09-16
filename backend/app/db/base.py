"""
Database connection and session management.
Initializes the async SQLAlchemy engine and session factory.
"""

from datetime import datetime
from typing import Annotated

from sqlalchemy import DateTime, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, mapped_column

from app.core.config import settings

# Engine setup
# Normalize DATABASE_URL to async driver — Vercel env often provides postgresql:// (psycopg2 default) but we use asyncpg
# Also strip Neon/Supabase channel_binding param which asyncpg 0.28 doesn't support
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

_db_url = settings.DATABASE_URL
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif _db_url.startswith("postgresql+psycopg2://"):
    _db_url = _db_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)

# Remove params asyncpg 0.28 doesn't support — channel_binding and sslmode
# asyncpg expects `ssl` not `sslmode`; Neon injects both
try:
    _parsed = urlparse(_db_url)
    if _parsed.query:
        _qs = parse_qsl(_parsed.query, keep_blank_values=True)
        _filtered = []
        _has_ssl = any(k == "ssl" for k, _ in _qs)
        for k, v in _qs:
            if k == "channel_binding":
                continue
            if k == "sslmode":
                # Convert sslmode=require/verify-full -> ssl=true
                if not _has_ssl:
                    _filtered.append(("ssl", "require" if v in ("require", "verify-full", "verify-ca") else v))
                continue
            _filtered.append((k, v))
        if len(_filtered) != len(_qs):
            _db_url = urlunparse(_parsed._replace(query=urlencode(_filtered)))
except Exception:
    pass

engine = create_async_engine(_db_url, echo=settings.DEBUG, future=True)

# Session factory
async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    Includes common fields like created_at and updated_at.
    """

    pass


# Mixins and common types
timestamp = Annotated[
    datetime, mapped_column(DateTime(timezone=True), server_default=func.now())
]
updated_timestamp = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    ),
]

# Import models to register them with Base.metadata AFTER common types are defined


async def get_db():
    async with async_session() as session:
        yield session
