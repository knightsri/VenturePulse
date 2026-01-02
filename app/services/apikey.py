"""
API Key management for VenturePulse v2.
Handles session-based storage of OpenRouter API keys.
API keys are stored in encrypted session cookies only - never in the database.
"""

from typing import Optional
from fastapi import Request


def mask_api_key(key: str) -> str:
    """
    Mask an API key showing only first 6 and last 4 characters.
    Example: sk-or-v1-abc...xyz1
    """
    if not key:
        return ""

    if len(key) <= 10:
        return "*" * len(key)

    return f"{key[:6]}...{key[-4:]}"


def get_api_key(request: Request) -> Optional[str]:
    """
    Get the OpenRouter API key from the session.
    Returns None if no key is set.
    """
    return request.session.get("openrouter_api_key")


def set_api_key(request: Request, api_key: str) -> None:
    """
    Store the OpenRouter API key in the session.
    The key is stored in the encrypted session cookie.
    """
    request.session["openrouter_api_key"] = api_key


def clear_api_key(request: Request) -> None:
    """
    Remove the API key from the session.
    """
    if "openrouter_api_key" in request.session:
        del request.session["openrouter_api_key"]


def has_api_key(request: Request) -> bool:
    """
    Check if an API key is set in the session.
    """
    key = request.session.get("openrouter_api_key")
    return bool(key and len(key) > 10)


def get_masked_api_key(request: Request) -> Optional[str]:
    """
    Get a masked version of the API key for display.
    Returns None if no key is set.
    """
    key = get_api_key(request)
    if not key:
        return None
    return mask_api_key(key)
