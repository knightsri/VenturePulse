"""
Settings routes for VenturePulse v2.
Handles user settings including API key management.
"""

import logging
from urllib.parse import quote

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.db.models import User
from app.auth.decorators import require_auth
from app.services.apikey import (
    get_api_key,
    set_api_key,
    clear_api_key,
    has_api_key,
    get_masked_api_key,
)

logger = logging.getLogger(__name__)
settings = get_settings()
templates = Jinja2Templates(directory=settings.BASE_DIR / "app" / "templates")

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_class=HTMLResponse)
async def settings_page(request: Request, user: User = Depends(require_auth)):
    """
    User settings page.
    Shows API key management and other user preferences.
    """
    return templates.TemplateResponse(
        "pages/settings.html",
        {
            "request": request,
            "settings": settings,
            "user": user,
            "has_api_key": has_api_key(request),
            "masked_api_key": get_masked_api_key(request),
        }
    )


@router.post("/api-key")
async def update_api_key(
    request: Request,
    user: User = Depends(require_auth),
    api_key: str = Form(...),
    return_url: str = Form(None),
):
    """
    Set or update the OpenRouter API key.
    The key is stored in the session only, never in the database.
    """
    # Validate the key format (basic validation)
    api_key = api_key.strip()

    if not api_key:
        redirect_url = "/settings?error=API+key+cannot+be+empty"
        if return_url:
            redirect_url += f"&return_url={quote(return_url, safe='')}"
        return RedirectResponse(url=redirect_url, status_code=303)

    if len(api_key) < 20:
        redirect_url = "/settings?error=Invalid+API+key+format"
        if return_url:
            redirect_url += f"&return_url={quote(return_url, safe='')}"
        return RedirectResponse(url=redirect_url, status_code=303)

    # Store the key in the session
    set_api_key(request, api_key)

    logger.info(f"API key updated for user {user.email}")

    # Redirect to return_url if provided, otherwise to settings
    if return_url:
        return RedirectResponse(url=return_url, status_code=303)
    
    return RedirectResponse(
        url="/settings?success=API+key+saved+successfully",
        status_code=303
    )


@router.post("/api-key/clear")
async def clear_api_key_route(
    request: Request,
    user: User = Depends(require_auth),
):
    """
    Remove the API key from the session.
    """
    clear_api_key(request)

    logger.info(f"API key cleared for user {user.email}")

    return RedirectResponse(
        url="/settings?success=API+key+removed",
        status_code=303
    )


@router.get("/api-key/status")
async def api_key_status(request: Request, user: User = Depends(require_auth)):
    """
    Check if an API key is set (JSON response for AJAX).
    """
    from fastapi.responses import JSONResponse

    return JSONResponse({
        "has_key": has_api_key(request),
        "masked_key": get_masked_api_key(request),
    })
