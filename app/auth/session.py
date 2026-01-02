"""
Session management for VenturePulse v2.
Handles session creation, validation, and cleanup.
"""

import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Request, Response
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import Session, User
from app.db.database import get_session_factory

logger = logging.getLogger(__name__)
settings = get_settings()


async def create_session(user_id: int, response: Response) -> str:
    """
    Create a new session for a user and set the session cookie.

    Args:
        user_id: The ID of the user to create a session for
        response: FastAPI response object to set the cookie on

    Returns:
        The session token
    """
    token = secrets.token_hex(32)
    expires_at = datetime.utcnow() + timedelta(hours=settings.SESSION_EXPIRE_HOURS)

    async with get_session_factory()() as db:
        # Create session record
        session = Session(
            token=token,
            user_id=user_id,
            expires_at=expires_at,
        )
        db.add(session)
        await db.commit()

        # Update user's last login
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.last_login = datetime.utcnow()
            await db.commit()

    # Set session cookie
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_EXPIRE_HOURS * 3600,
        httponly=True,
        samesite="lax",
        secure=not settings.DEV_MODE,  # Secure in production
    )

    logger.info(f"Created session for user {user_id}")
    return token


async def get_session(request: Request) -> Optional[Session]:
    """
    Get the current session from the request cookie.

    Args:
        request: FastAPI request object

    Returns:
        Session object if valid, None otherwise
    """
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        return None

    async with get_session_factory()() as db:
        result = await db.execute(
            select(Session).where(Session.token == token)
        )
        session = result.scalar_one_or_none()

        if session is None:
            return None

        # Check if session is expired
        if session.is_expired:
            await db.delete(session)
            await db.commit()
            return None

        return session


async def get_current_user(request: Request) -> Optional[User]:
    """
    Get the current authenticated user from the session.

    Args:
        request: FastAPI request object

    Returns:
        User object if authenticated, None otherwise
    """
    session = await get_session(request)
    if session is None:
        return None

    async with get_session_factory()() as db:
        result = await db.execute(
            select(User).where(User.id == session.user_id)
        )
        return result.scalar_one_or_none()


async def delete_session(request: Request, response: Response) -> bool:
    """
    Delete the current session and clear the cookie.

    Args:
        request: FastAPI request object
        response: FastAPI response object

    Returns:
        True if session was deleted, False if no session existed
    """
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)

    # Clear the cookie regardless
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        httponly=True,
        samesite="lax",
    )

    if not token:
        return False

    async with get_session_factory()() as db:
        result = await db.execute(
            delete(Session).where(Session.token == token)
        )
        await db.commit()
        deleted = result.rowcount > 0

    if deleted:
        logger.info(f"Deleted session {token[:8]}...")

    return deleted


async def cleanup_expired_sessions() -> int:
    """
    Remove all expired sessions from the database.

    Returns:
        Number of sessions deleted
    """
    async with get_session_factory()() as db:
        result = await db.execute(
            delete(Session).where(Session.expires_at < datetime.utcnow())
        )
        await db.commit()

    count = result.rowcount
    if count > 0:
        logger.info(f"Cleaned up {count} expired sessions")

    return count
