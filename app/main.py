"""
VenturePulse v2 - FastAPI Application Entry Point
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.db.database import init_db, close_db
from app.db.models import User
from app.auth.session import get_current_user
from app.auth.decorators import require_auth
from app.routes.auth import router as auth_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    logger.info("Starting VenturePulse v2...")

    # Ensure directories exist
    settings.ensure_directories()

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Validate settings
    errors = settings.validate()
    if errors:
        for error in errors:
            logger.warning(f"Configuration warning: {error}")

    logger.info(f"VenturePulse v2 started on port {settings.PORT}")
    logger.info(f"DEV_MODE: {settings.DEV_MODE}")

    yield

    # Shutdown
    logger.info("Shutting down VenturePulse v2...")
    await close_db()


# Create FastAPI application
app = FastAPI(
    title="VenturePulse",
    description="AI-Powered Product Viability Analysis",
    version="2.0.0",
    lifespan=lifespan,
)

# Add session middleware for OAuth state management
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="venturepulse_oauth_state",
    max_age=3600,  # 1 hour for OAuth state
)

# Mount static files
app.mount(
    "/static",
    StaticFiles(directory=settings.BASE_DIR / "app" / "static"),
    name="static"
)

# Setup Jinja2 templates
templates = Jinja2Templates(directory=settings.BASE_DIR / "app" / "templates")

# Include auth router
app.include_router(auth_router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Docker and load balancers."""
    return {"status": "healthy", "version": "2.0.0"}


# =============================================================================
# Public Routes
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page."""
    user = await get_current_user(request)
    return templates.TemplateResponse(
        "pages/home.html",
        {
            "request": request,
            "settings": settings,
            "user": user,
        }
    )


@app.get("/browse", response_class=HTMLResponse)
async def browse(request: Request):
    """Browse public projects."""
    user = await get_current_user(request)
    return templates.TemplateResponse(
        "pages/browse.html",
        {
            "request": request,
            "settings": settings,
            "user": user,
            "projects": [],  # Will be populated in Phase 3
        }
    )


# =============================================================================
# Protected Routes
# =============================================================================

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: User = Depends(require_auth)):
    """User dashboard showing their projects."""
    return templates.TemplateResponse(
        "pages/dashboard.html",
        {
            "request": request,
            "settings": settings,
            "user": user,
            "projects": [],  # Will be populated in Phase 3
        }
    )


@app.get("/pending-approval", response_class=HTMLResponse)
async def pending_approval(request: Request):
    """Page shown to users awaiting approval."""
    user = await get_current_user(request)
    return templates.TemplateResponse(
        "pages/pending-approval.html",
        {
            "request": request,
            "settings": settings,
            "user": user,
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEV_MODE,
    )
