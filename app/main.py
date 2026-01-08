"""
VenturePulse v2 - FastAPI Application Entry Point
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__, __version_date__, __version_name__
from app.config import get_settings
from app.auth.session import get_current_user
from app.db.database import init_db, close_db
from app.services.background import recover_interrupted_analyses
from app.routes import (
    auth_router,
    public_router,
    projects_router,
    analysis_router,
    admin_router,
    settings_router,
    share_router,
)

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
    logger.info(f"Starting VenturePulse v{__version__}...")

    # Ensure directories exist
    settings.ensure_directories()

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Recover any interrupted analyses from previous runs
    await recover_interrupted_analyses()

    # Validate settings
    errors = settings.validate()
    if errors:
        for error in errors:
            logger.warning(f"Configuration warning: {error}")

    logger.info(f"VenturePulse v{__version__} started on port {settings.PORT}")
    logger.info(f"DEV_MODE: {settings.DEV_MODE}")

    yield

    # Shutdown
    logger.info(f"Shutting down VenturePulse v{__version__}...")
    await close_db()


# Create FastAPI application
app = FastAPI(
    title="VenturePulse",
    description="AI-Powered Product Viability Analysis",
    version=__version__,
    lifespan=lifespan,
)

# Add session middleware for OAuth state management
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="venturepulse_oauth_state",
    max_age=3600,  # 1 hour for OAuth state
    same_site="lax",
    https_only=not settings.DEV_MODE,  # Secure cookie in production
)

# Mount static files
app.mount(
    "/static",
    StaticFiles(directory=settings.BASE_DIR / "app" / "static"),
    name="static"
)

# Setup Jinja2 templates
templates = Jinja2Templates(directory=settings.BASE_DIR / "app" / "templates")

# Include routers
# Note: Order matters! Specific routes must come before parameterized routes
# e.g., /project/new (in projects_router) must come before /project/{slug} (in public_router)
app.include_router(auth_router)
app.include_router(projects_router)  # Has /project/new - must be before public_router
app.include_router(analysis_router)  # Has /analysis/{id} specific routes
app.include_router(share_router)     # Has /project/{slug}/share - must be before public_router
app.include_router(public_router)    # Has /project/{slug} catch-all
app.include_router(admin_router)
app.include_router(settings_router)


# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Only add HSTS in production
        if not settings.DEV_MODE:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)


# Custom exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with custom error pages or JSON for API routes."""
    # API routes should return JSON responses
    if request.url.path.startswith("/api/"):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    user = await get_current_user(request)

    if exc.status_code == 404:
        return templates.TemplateResponse(
            "pages/404.html",
            {"request": request, "user": user, "settings": settings},
            status_code=404
        )
    elif exc.status_code >= 500:
        return templates.TemplateResponse(
            "pages/500.html",
            {"request": request, "user": user, "settings": settings},
            status_code=exc.status_code
        )
    else:
        # For other HTTP errors, return a simple HTML response
        return HTMLResponse(
            content=f"<h1>Error {exc.status_code}</h1><p>{exc.detail}</p>",
            status_code=exc.status_code
        )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with 500 error page or JSON for API routes."""
    logger.exception(f"Unhandled exception: {exc}")

    # API routes should return JSON responses
    if request.url.path.startswith("/api/"):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

    user = None
    try:
        user = await get_current_user(request)
    except Exception:
        pass

    return templates.TemplateResponse(
        "pages/500.html",
        {"request": request, "user": user, "settings": settings},
        status_code=500
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Docker and load balancers."""
    return {"status": "healthy", "version": __version__}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEV_MODE,
    )
