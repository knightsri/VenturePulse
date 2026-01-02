"""
Database connection and session management for VenturePulse v2.
Uses SQLAlchemy async with aiosqlite for SQLite support.
"""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import StaticPool

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Global engine reference
_engine: AsyncEngine | None = None
AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Get or create the database engine."""
    global _engine

    if _engine is None:
        # Ensure data directory exists
        settings.ensure_directories()

        # Use StaticPool for SQLite to handle async properly
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEV_MODE,  # Log SQL in dev mode
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    return _engine


async def init_db() -> None:
    """Initialize database: create engine, session factory, and tables."""
    global AsyncSessionLocal

    engine = get_engine()

    # Create session factory
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Import models and create tables
    from app.db.models import Base
    from app.db.migrations import run_migrations

    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    # Run any pending migrations
    await run_migrations()

    logger.info(f"Database initialized at {settings.database_path}")


async def close_db() -> None:
    """Close database connections."""
    global _engine, AsyncSessionLocal

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        AsyncSessionLocal = None
        logger.info("Database connections closed")


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get the session factory, raising an error if not initialized."""
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    Use with FastAPI's Depends().
    """
    session_factory = get_session_factory()

    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
