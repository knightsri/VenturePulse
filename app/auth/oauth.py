"""
OAuth configuration for Google and GitHub providers.
Uses Authlib for OAuth 2.0 flow handling.
"""

from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

from app.config import get_settings

settings = get_settings()

# Create OAuth instance
oauth = OAuth()

# Google OAuth configuration
if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid email profile",
        },
    )

# GitHub OAuth configuration
if settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET:
    oauth.register(
        name="github",
        client_id=settings.GITHUB_CLIENT_ID,
        client_secret=settings.GITHUB_CLIENT_SECRET,
        authorize_url="https://github.com/login/oauth/authorize",
        access_token_url="https://github.com/login/oauth/access_token",
        api_base_url="https://api.github.com/",
        client_kwargs={
            "scope": "read:user user:email",
        },
    )


def get_oauth() -> OAuth:
    """Get the configured OAuth instance."""
    return oauth


def is_google_configured() -> bool:
    """Check if Google OAuth is configured."""
    return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)


def is_github_configured() -> bool:
    """Check if GitHub OAuth is configured."""
    return bool(settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET)
