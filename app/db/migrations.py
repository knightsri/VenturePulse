"""
Database migrations for VenturePulse v2.
Handles schema setup and future migrations.

For now, using SQLAlchemy's create_all() for initial setup.
Future migrations can be added as functions here.
"""

import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_engine, get_session_factory

logger = logging.getLogger(__name__)


async def run_migrations() -> None:
    """
    Run all pending migrations.
    Called during database initialization.
    """
    logger.info("Checking for pending migrations...")

    # Check if this is a fresh database (no users yet = fresh install)
    async with get_session_factory()() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()

        if user_count == 0:
            logger.info("Fresh database detected - no migrations needed")
        else:
            logger.info(f"Existing database with {user_count} users")

    # Run migrations
    await migration_001_add_preferred_models()
    await migration_002_add_api_key_temp()

    logger.info("Migrations complete")


async def check_first_user(session: AsyncSession) -> bool:
    """
    Check if this is the first user being created.
    Used to automatically grant admin role to first user.
    """
    result = await session.execute(text("SELECT COUNT(*) FROM users"))
    count = result.scalar()
    return count == 0


async def migration_001_add_preferred_models() -> None:
    """Add preferred_models column to users table."""
    engine = get_engine()
    async with engine.begin() as conn:
        # Check if column exists first (SQLite)
        result = await conn.execute(text(
            "SELECT COUNT(*) FROM pragma_table_info('users') WHERE name='preferred_models'"
        ))
        if result.scalar() == 0:
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN preferred_models JSON"
            ))
            logger.info("Migration 001: Added preferred_models to users table")


async def migration_002_add_api_key_temp() -> None:
    """Add api_key_temp column to analyses table for recovery after restarts."""
    engine = get_engine()
    async with engine.begin() as conn:
        # Check if column exists first (SQLite)
        result = await conn.execute(text(
            "SELECT COUNT(*) FROM pragma_table_info('analyses') WHERE name='api_key_temp'"
        ))
        if result.scalar() == 0:
            await conn.execute(text(
                "ALTER TABLE analyses ADD COLUMN api_key_temp VARCHAR(500)"
            ))
            logger.info("Migration 002: Added api_key_temp to analyses table")
