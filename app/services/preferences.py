"""
User preferences service for VenturePulse v2.
Handles saving and loading user preferences like model selections.
"""

import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User

logger = logging.getLogger(__name__)


async def get_user_preferred_models(db: AsyncSession, user_id: int) -> Optional[List[str]]:
    """
    Get user's preferred models from the database.
    Returns None if no preferences saved.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user and user.preferred_models:
        return user.preferred_models
    return None


async def save_user_preferred_models(db: AsyncSession, user_id: int, models: List[str]) -> bool:
    """
    Save user's preferred models to the database.
    Returns True on success, False on failure.
    """
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user:
            user.preferred_models = models
            await db.commit()
            logger.info(f"Saved {len(models)} preferred models for user {user_id}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to save preferred models for user {user_id}: {e}")
        await db.rollback()
        return False
