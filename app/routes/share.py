"""
Share link management routes for VenturePulse v2.
Handles creation, extension, and deletion of shareable project links.
"""

import hashlib
import logging
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.db.database import get_session_factory
from sqlalchemy import func as sql_func
from app.db.models import User, Project, ShareableLink, ShareLinkVisitor
from app.auth.decorators import require_approved

logger = logging.getLogger(__name__)
settings = get_settings()
templates = Jinja2Templates(directory=settings.BASE_DIR / "app" / "templates")

router = APIRouter(tags=["share"])


def generate_share_key() -> str:
    """Generate 42-character alphanumeric key (mixed-case, no symbols)."""
    alphabet = string.ascii_letters + string.digits  # A-Za-z0-9
    return ''.join(secrets.choice(alphabet) for _ in range(42))


def compute_visitor_hash(request: Request) -> str:
    """Compute SHA-256 hash of IP + User-Agent for unique visitor tracking."""
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    combined = f"{ip}:{user_agent}"
    return hashlib.sha256(combined.encode()).hexdigest()


async def validate_allowkey(
    db: AsyncSession,
    project_id: int,
    allowkey: str
) -> Optional[ShareableLink]:
    """
    Validate an allowkey against the database.
    Returns the ShareableLink if valid and not expired, None otherwise.
    """
    result = await db.execute(
        select(ShareableLink)
        .where(
            ShareableLink.project_id == project_id,
            ShareableLink.key == allowkey,
            ShareableLink.expires_at > datetime.utcnow()
        )
    )
    return result.scalar_one_or_none()


async def record_visitor(
    db: AsyncSession,
    link: ShareableLink,
    visitor_hash: str
) -> None:
    """Record or update visitor for a shareable link."""
    # Check if visitor already exists
    result = await db.execute(
        select(ShareLinkVisitor).where(
            ShareLinkVisitor.shareable_link_id == link.id,
            ShareLinkVisitor.visitor_hash == visitor_hash
        )
    )
    visitor = result.scalar_one_or_none()

    if visitor:
        # Update existing visitor
        visitor.last_visit_at = datetime.utcnow()
        visitor.visit_count += 1
    else:
        # Create new visitor
        visitor = ShareLinkVisitor(
            shareable_link_id=link.id,
            visitor_hash=visitor_hash,
        )
        db.add(visitor)

    # Increment total visit_count on link
    link.visit_count += 1
    await db.commit()


@router.get("/project/{slug}/share", response_class=HTMLResponse)
async def share_management_page(
    request: Request,
    slug: str,
    user: User = Depends(require_approved),
):
    """
    Share management page - owner only.
    Shows active and expired links with management options.
    """
    async with get_session_factory()() as db:
        result = await db.execute(
            select(Project).where(Project.slug == slug)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Owner-only access
        if project.user_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get all links for this project
        result = await db.execute(
            select(ShareableLink)
            .options(selectinload(ShareableLink.visitors))
            .where(ShareableLink.project_id == project.id)
            .order_by(desc(ShareableLink.created_at))
        )
        all_links = result.scalars().all()

        now = datetime.utcnow()
        active_links = [link for link in all_links if link.expires_at > now]
        expired_links = [link for link in all_links if link.expires_at <= now]

        # Get pending user count for admin badge
        pending_count = 0
        if user.is_admin:
            result = await db.execute(
                select(sql_func.count(User.id)).where(User.role == "pending")
            )
            pending_count = result.scalar() or 0

    return templates.TemplateResponse(
        "pages/project_share.html",
        {
            "request": request,
            "settings": settings,
            "user": user,
            "project": project,
            "active_links": active_links,
            "expired_links": expired_links,
            "pending_count": pending_count,
            "now": now,
        }
    )


@router.post("/project/{slug}/share/create")
async def create_share_link(
    request: Request,
    slug: str,
    user: User = Depends(require_approved),
    days: int = Form(default=7),
):
    """Create a new shareable link for the project."""
    # Validate days (1-90)
    days = max(1, min(90, days))

    async with get_session_factory()() as db:
        result = await db.execute(
            select(Project).where(Project.slug == slug)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.user_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Generate unique key
        key = generate_share_key()

        # Create link
        link = ShareableLink(
            project_id=project.id,
            key=key,
            created_by_user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(days=days),
        )
        db.add(link)
        await db.commit()

        logger.info(f"Created share link {key[:8]}... for project {slug} ({days} days)")

    return RedirectResponse(
        url=f"/project/{slug}/share?success=Share+link+created+for+{days}+days",
        status_code=303
    )


@router.post("/project/{slug}/share/{link_id}/extend")
async def extend_share_link(
    request: Request,
    slug: str,
    link_id: int,
    user: User = Depends(require_approved),
    days: int = Form(default=7),
):
    """Extend expiration of an existing shareable link (from today, not from current expiry)."""
    days = max(1, min(90, days))

    async with get_session_factory()() as db:
        result = await db.execute(
            select(ShareableLink)
            .options(selectinload(ShareableLink.project))
            .where(ShareableLink.id == link_id)
        )
        link = result.scalar_one_or_none()

        if not link or link.project.slug != slug:
            raise HTTPException(status_code=404, detail="Link not found")

        if link.project.user_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Check if link is already expired - cannot extend expired links
        if link.expires_at <= datetime.utcnow():
            return RedirectResponse(
                url=f"/project/{slug}/share?error=Cannot+extend+expired+links",
                status_code=303
            )

        # Extend from today (always from now, up to max 90 days)
        link.expires_at = datetime.utcnow() + timedelta(days=days)
        await db.commit()

        logger.info(f"Extended share link {link.key[:8]}... to {days} days from now")

    return RedirectResponse(
        url=f"/project/{slug}/share?success=Link+extended+to+{days}+days+from+today",
        status_code=303
    )


@router.post("/project/{slug}/share/{link_id}/delete")
async def delete_share_link(
    request: Request,
    slug: str,
    link_id: int,
    user: User = Depends(require_approved),
):
    """Soft-delete a shareable link by setting expires_at to now."""
    async with get_session_factory()() as db:
        result = await db.execute(
            select(ShareableLink)
            .options(selectinload(ShareableLink.project))
            .where(ShareableLink.id == link_id)
        )
        link = result.scalar_one_or_none()

        if not link or link.project.slug != slug:
            raise HTTPException(status_code=404, detail="Link not found")

        if link.project.user_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Soft-delete: set expiration to now
        link.expires_at = datetime.utcnow()
        await db.commit()

        logger.info(f"Soft-deleted share link {link.key[:8]}...")

    return RedirectResponse(
        url=f"/project/{slug}/share?success=Link+deactivated",
        status_code=303
    )
