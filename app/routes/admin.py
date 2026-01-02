"""
Admin routes for VenturePulse v2.
Handles user management and system administration.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func, desc

from app.config import get_settings
from app.db.database import get_session_factory
from app.db.models import User, Project, Analysis
from app.auth.decorators import require_admin

logger = logging.getLogger(__name__)
settings = get_settings()
templates = Jinja2Templates(directory=settings.BASE_DIR / "app" / "templates")

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("", response_class=HTMLResponse)
async def admin_dashboard(request: Request, user: User = Depends(require_admin)):
    """
    Admin dashboard.
    Shows pending approvals, all users, and system stats.
    """
    async with get_session_factory()() as db:
        # Get pending users
        result = await db.execute(
            select(User)
            .where(User.role == "pending")
            .order_by(desc(User.created_at))
        )
        pending_users = result.scalars().all()

        # Get all users
        result = await db.execute(
            select(User).order_by(desc(User.created_at))
        )
        all_users = result.scalars().all()

        # Get system stats
        user_count_result = await db.execute(select(func.count(User.id)))
        total_users = user_count_result.scalar() or 0

        project_count_result = await db.execute(select(func.count(Project.id)))
        total_projects = project_count_result.scalar() or 0

        public_project_count_result = await db.execute(
            select(func.count(Project.id)).where(Project.is_public == True)
        )
        public_projects = public_project_count_result.scalar() or 0

        analysis_count_result = await db.execute(select(func.count(Analysis.id)))
        total_analyses = analysis_count_result.scalar() or 0

        completed_analysis_count_result = await db.execute(
            select(func.count(Analysis.id)).where(Analysis.status == "completed")
        )
        completed_analyses = completed_analysis_count_result.scalar() or 0

    return templates.TemplateResponse(
        "pages/admin.html",
        {
            "request": request,
            "settings": settings,
            "user": user,
            "pending_users": pending_users,
            "all_users": all_users,
            "stats": {
                "total_users": total_users,
                "total_projects": total_projects,
                "public_projects": public_projects,
                "total_analyses": total_analyses,
                "completed_analyses": completed_analyses,
            },
        }
    )


@router.post("/user/{user_id}/approve")
async def approve_user(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin),
):
    """
    Approve a pending user.
    Sets user role from 'pending' to 'approved'.
    """
    async with get_session_factory()() as db:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        target_user = result.scalar_one_or_none()

        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")

        if target_user.role == "admin":
            raise HTTPException(status_code=400, detail="Cannot modify admin role")

        target_user.role = "approved"
        await db.commit()

        logger.info(f"Admin {admin.email} approved user {target_user.email}")

    return RedirectResponse(url="/admin", status_code=303)


@router.post("/user/{user_id}/reject")
async def reject_user(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin),
):
    """
    Reject and delete a pending user.
    Removes the user from the system.
    """
    async with get_session_factory()() as db:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        target_user = result.scalar_one_or_none()

        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")

        if target_user.role == "admin":
            raise HTTPException(status_code=400, detail="Cannot delete admin user")

        if target_user.id == admin.id:
            raise HTTPException(status_code=400, detail="Cannot delete yourself")

        email = target_user.email
        await db.delete(target_user)
        await db.commit()

        logger.info(f"Admin {admin.email} rejected/deleted user {email}")

    return RedirectResponse(url="/admin", status_code=303)


@router.post("/user/{user_id}/revoke")
async def revoke_user(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin),
):
    """
    Revoke an approved user's access.
    Sets user role from 'approved' back to 'pending'.
    """
    async with get_session_factory()() as db:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        target_user = result.scalar_one_or_none()

        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")

        if target_user.role == "admin":
            raise HTTPException(status_code=400, detail="Cannot revoke admin access")

        if target_user.id == admin.id:
            raise HTTPException(status_code=400, detail="Cannot revoke your own access")

        target_user.role = "pending"
        await db.commit()

        logger.info(f"Admin {admin.email} revoked access for user {target_user.email}")

    return RedirectResponse(url="/admin", status_code=303)


@router.post("/user/{user_id}/promote")
async def promote_user(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin),
):
    """
    Promote a user to admin role.
    """
    async with get_session_factory()() as db:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        target_user = result.scalar_one_or_none()

        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")

        if target_user.role == "admin":
            raise HTTPException(status_code=400, detail="User is already admin")

        target_user.role = "admin"
        await db.commit()

        logger.info(f"Admin {admin.email} promoted user {target_user.email} to admin")

    return RedirectResponse(url="/admin", status_code=303)


@router.post("/user/{user_id}/demote")
async def demote_user(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin),
):
    """
    Demote an admin to approved role.
    """
    async with get_session_factory()() as db:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        target_user = result.scalar_one_or_none()

        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")

        if target_user.id == admin.id:
            raise HTTPException(status_code=400, detail="Cannot demote yourself")

        if target_user.role != "admin":
            raise HTTPException(status_code=400, detail="User is not an admin")

        # Check there's at least one admin left
        admin_count_result = await db.execute(
            select(func.count(User.id)).where(User.role == "admin")
        )
        admin_count = admin_count_result.scalar() or 0

        if admin_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot demote the last admin"
            )

        target_user.role = "approved"
        await db.commit()

        logger.info(f"Admin {admin.email} demoted user {target_user.email} from admin")

    return RedirectResponse(url="/admin", status_code=303)
