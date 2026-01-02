"""
Routes module for VenturePulse v2.
Contains all API and page route definitions.
"""

from app.routes.auth import router as auth_router

__all__ = [
    "auth_router",
]
