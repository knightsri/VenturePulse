"""
Authentication module for VenturePulse v2.
Provides OAuth, session management, and auth decorators.
"""

from app.auth.session import (
    create_session,
    get_session,
    delete_session,
    get_current_user,
)
from app.auth.decorators import (
    require_auth,
    require_approved,
    require_admin,
)

__all__ = [
    "create_session",
    "get_session",
    "delete_session",
    "get_current_user",
    "require_auth",
    "require_approved",
    "require_admin",
]
