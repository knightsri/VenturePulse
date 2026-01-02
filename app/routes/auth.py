"""
Authentication routes for VenturePulse v2.
Handles OAuth login/callback, dev login, and logout.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.database import get_session_factory
from app.db.models import User
from app.auth.oauth import oauth, is_google_configured, is_github_configured
from app.auth.session import create_session, delete_session, get_current_user

logger = logging.getLogger(__name__)
settings = get_settings()
templates = Jinja2Templates(directory=settings.BASE_DIR / "app" / "templates")

router = APIRouter(tags=["auth"])


# Helper function to get or create user
async def get_or_create_user(
    email: str,
    name: str,
    provider: str,
    provider_id: str,
    avatar_url: Optional[str] = None,
) -> User:
    """
    Get existing user or create a new one.
    First user to register becomes admin.
    """
    async with get_session_factory()() as db:
        # Check if user exists
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if user:
            # Update provider info if needed
            user.provider = provider
            user.provider_id = provider_id
            if avatar_url:
                user.avatar_url = avatar_url
            await db.commit()
            await db.refresh(user)
            logger.info(f"Existing user logged in: {email}")
            return user

        # Check if this is the first user
        result = await db.execute(select(func.count(User.id)))
        user_count = result.scalar()
        role = "admin" if user_count == 0 else "pending"

        # Create new user
        user = User(
            email=email,
            name=name,
            provider=provider,
            provider_id=provider_id,
            avatar_url=avatar_url,
            role=role,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(f"New user created: {email} (role: {role})")
        return user


# =============================================================================
# Login Page
# =============================================================================

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Display login page with OAuth buttons."""
    # If already logged in, redirect to dashboard
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        "pages/login.html",
        {
            "request": request,
            "settings": settings,
        }
    )


# =============================================================================
# Google OAuth
# =============================================================================

@router.get("/auth/google")
async def google_login(request: Request):
    """Initiate Google OAuth flow."""
    if not is_google_configured():
        raise HTTPException(status_code=400, detail="Google OAuth not configured")

    redirect_uri = f"{settings.BASE_URL}/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/google/callback")
async def google_callback(request: Request):
    """Handle Google OAuth callback."""
    if not is_google_configured():
        raise HTTPException(status_code=400, detail="Google OAuth not configured")

    try:
        token = await oauth.google.authorize_access_token(request)

        # For OpenID Connect, userinfo is included in the token
        user_info = token.get("userinfo")

        if not user_info:
            # Fallback: parse the ID token
            user_info = dict(token.get("id_token", {}))

        if not user_info or "email" not in user_info:
            logger.error("No user info in Google OAuth response")
            raise HTTPException(status_code=400, detail="Could not get user info from Google")

        user = await get_or_create_user(
            email=user_info["email"],
            name=user_info.get("name", user_info["email"]),
            provider="google",
            provider_id=user_info.get("sub", user_info["email"]),
            avatar_url=user_info.get("picture"),
        )

        response = RedirectResponse(url="/dashboard", status_code=303)
        await create_session(user.id, response)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        raise HTTPException(status_code=400, detail="OAuth authentication failed")


# =============================================================================
# GitHub OAuth
# =============================================================================

@router.get("/auth/github")
async def github_login(request: Request):
    """Initiate GitHub OAuth flow."""
    if not is_github_configured():
        raise HTTPException(status_code=400, detail="GitHub OAuth not configured")

    redirect_uri = f"{settings.BASE_URL}/auth/github/callback"
    return await oauth.github.authorize_redirect(request, redirect_uri)


@router.get("/auth/github/callback")
async def github_callback(request: Request):
    """Handle GitHub OAuth callback."""
    if not is_github_configured():
        raise HTTPException(status_code=400, detail="GitHub OAuth not configured")

    try:
        token = await oauth.github.authorize_access_token(request)
        access_token = token.get("access_token")

        # Fetch user info from GitHub API using httpx
        import httpx
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient() as client:
            # Get user profile
            resp = await client.get("https://api.github.com/user", headers=headers)
            user_info = resp.json()

            # Get email (might need separate API call if private)
            email = user_info.get("email")
            if not email:
                # Fetch emails separately
                resp = await client.get("https://api.github.com/user/emails", headers=headers)
                emails = resp.json()
                primary_email = next(
                    (e for e in emails if e.get("primary") and e.get("verified")),
                    None
                )
                if primary_email:
                    email = primary_email["email"]
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="No verified email found on GitHub account"
                    )

        user = await get_or_create_user(
            email=email,
            name=user_info.get("name") or user_info.get("login"),
            provider="github",
            provider_id=str(user_info["id"]),
            avatar_url=user_info.get("avatar_url"),
        )

        response = RedirectResponse(url="/dashboard", status_code=303)
        await create_session(user.id, response)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub OAuth error: {e}")
        raise HTTPException(status_code=400, detail="OAuth authentication failed")


# =============================================================================
# Dev Login (Development Mode Only)
# =============================================================================

@router.get("/auth/dev-login")
async def dev_login(request: Request):
    """
    Development-only login that creates a test user.
    Only available when DEV_MODE=true.
    """
    if not settings.DEV_MODE:
        raise HTTPException(status_code=404, detail="Not found")

    user = await get_or_create_user(
        email="dev@venturepulse.local",
        name="Dev User",
        provider="dev",
        provider_id="dev-001",
        avatar_url=None,
    )

    response = RedirectResponse(url="/dashboard", status_code=303)
    await create_session(user.id, response)

    logger.info("Dev login used")
    return response


# =============================================================================
# Logout
# =============================================================================

@router.post("/logout")
async def logout(request: Request):
    """Log out the current user."""
    response = RedirectResponse(url="/", status_code=303)
    await delete_session(request, response)
    return response


@router.get("/logout")
async def logout_get(request: Request):
    """Log out via GET (for simple links)."""
    response = RedirectResponse(url="/", status_code=303)
    await delete_session(request, response)
    return response
