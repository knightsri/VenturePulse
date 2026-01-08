"""
Routes module for VenturePulse v2.
Contains all API and page route definitions.
"""

from app.routes.auth import router as auth_router
from app.routes.public import router as public_router
from app.routes.projects import router as projects_router
from app.routes.analysis import router as analysis_router
from app.routes.admin import router as admin_router
from app.routes.settings import router as settings_router
from app.routes.share import router as share_router

__all__ = [
    "auth_router",
    "public_router",
    "projects_router",
    "analysis_router",
    "admin_router",
    "settings_router",
    "share_router",
]
