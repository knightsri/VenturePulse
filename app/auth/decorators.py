"""
Authentication decorators for route protection.
Provides require_auth, require_approved, and require_admin dependencies.
"""

from functools import wraps
from typing import Optional, Callable

from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse

from app.auth.session import get_current_user
from app.db.models import User


async def get_user_or_none(request: Request) -> Optional[User]:
    """
    Dependency that returns the current user or None.
    Use this for routes that work with or without authentication.
    """
    return await get_current_user(request)


async def require_auth(request: Request) -> User:
    """
    Dependency that requires authentication.
    Redirects to login page if not authenticated.

    Usage:
        @app.get("/protected")
        async def protected_route(user: User = Depends(require_auth)):
            return {"message": f"Hello {user.name}"}
    """
    user = await get_current_user(request)

    if user is None:
        # For API requests, return 401
        if request.headers.get("accept", "").startswith("application/json"):
            raise HTTPException(status_code=401, detail="Not authenticated")
        # For browser requests, redirect to login
        raise HTTPException(
            status_code=303,
            headers={"Location": "/login"}
        )

    # Store user in request state for templates
    request.state.user = user
    return user


async def require_approved(request: Request) -> User:
    """
    Dependency that requires an approved user (admin or approved role).
    Redirects to pending-approval page if user is pending.

    Usage:
        @app.get("/create-project")
        async def create_project(user: User = Depends(require_approved)):
            return {"message": "You can create projects"}
    """
    user = await require_auth(request)

    if not user.is_approved:
        # For API requests, return 403
        if request.headers.get("accept", "").startswith("application/json"):
            raise HTTPException(
                status_code=403,
                detail="Account pending approval"
            )
        # For browser requests, redirect to pending page
        raise HTTPException(
            status_code=303,
            headers={"Location": "/pending-approval"}
        )

    return user


async def require_admin(request: Request) -> User:
    """
    Dependency that requires admin role.
    Returns 403 if user is not an admin.

    Usage:
        @app.get("/admin/users")
        async def admin_users(user: User = Depends(require_admin)):
            return {"message": "Admin access granted"}
    """
    user = await require_auth(request)

    if not user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return user


def inject_user(func: Callable) -> Callable:
    """
    Decorator to inject current user into template context.
    For use with template routes that optionally show user info.

    Usage:
        @app.get("/")
        @inject_user
        async def home(request: Request, user: Optional[User] = None):
            return templates.TemplateResponse("home.html", {"user": user})
    """
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        user = await get_current_user(request)
        request.state.user = user
        return await func(request, *args, user=user, **kwargs)
    return wrapper
