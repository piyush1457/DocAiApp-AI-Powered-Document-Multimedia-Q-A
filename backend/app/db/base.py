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
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, future=True)

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
