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

    # Future migrations would go here
    # Example:
    # await migration_001_add_new_column()
    # await migration_002_create_new_table()

    logger.info("Migrations complete")


async def check_first_user(session: AsyncSession) -> bool:
    """
    Check if this is the first user being created.
    Used to automatically grant admin role to first user.
    """
    result = await session.execute(text("SELECT COUNT(*) FROM users"))
    count = result.scalar()
    return count == 0


# Future migration functions would be defined here
# Each migration should be idempotent (safe to run multiple times)

# async def migration_001_example() -> None:
#     """Example migration - add a new column."""
#     engine = get_engine()
#     async with engine.begin() as conn:
#         # Check if column exists first
#         result = await conn.execute(text(
#             "SELECT COUNT(*) FROM pragma_table_info('users') WHERE name='new_column'"
#         ))
#         if result.scalar() == 0:
#             await conn.execute(text(
#                 "ALTER TABLE users ADD COLUMN new_column TEXT"
#             ))
#             logger.info("Migration 001: Added new_column to users table")
