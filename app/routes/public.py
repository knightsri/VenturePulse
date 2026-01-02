"""
Public routes for VenturePulse v2.
Handles home, browse, public project viewing, and analysis viewing.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.db.database import get_session_factory
from app.db.models import User, Project, Analysis
from app.auth.session import get_current_user

logger = logging.getLogger(__name__)
settings = get_settings()
templates = Jinja2Templates(directory=settings.BASE_DIR / "app" / "templates")

router = APIRouter(tags=["public"])


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Home page.
    Shows featured public projects and login/register CTA if not authenticated.
    """
    user = await get_current_user(request)

    async with get_session_factory()() as db:
        # Get featured public projects (most recent with completed analyses)
        result = await db.execute(
            select(Project)
            .options(selectinload(Project.analyses))
            .where(Project.is_public == True)
            .order_by(desc(Project.created_at))
            .limit(4)
        )
        featured_projects = result.scalars().all()

        # Get quick stats
        project_count_result = await db.execute(
            select(func.count(Project.id)).where(Project.is_public == True)
        )
        total_projects = project_count_result.scalar() or 0

        analysis_count_result = await db.execute(
            select(func.count(Analysis.id)).where(Analysis.status == "completed")
        )
        total_analyses = analysis_count_result.scalar() or 0

    return templates.TemplateResponse(
        "pages/home.html",
        {
            "request": request,
            "settings": settings,
            "user": user,
            "featured_projects": featured_projects,
            "stats": {
                "total_projects": total_projects,
                "total_analyses": total_analyses,
            },
        }
    )


@router.get("/browse", response_class=HTMLResponse)
async def browse(
    request: Request,
    search: Optional[str] = None,
    sort: str = "recent",
):
    """
    Browse public projects gallery.
    Supports filtering by search and sorting.
    """
    user = await get_current_user(request)

    async with get_session_factory()() as db:
        # Build query
        query = (
            select(Project)
            .options(selectinload(Project.user))
            .options(selectinload(Project.analyses))
            .where(Project.is_public == True)
        )

        # Apply search filter
        if search:
            search_filter = f"%{search}%"
            query = query.where(
                (Project.name.ilike(search_filter)) |
                (Project.description.ilike(search_filter))
            )

        # Apply sorting
        if sort == "recent":
            query = query.order_by(desc(Project.created_at))
        elif sort == "name":
            query = query.order_by(Project.name)
        elif sort == "analyses":
            # Sort by number of completed analyses (requires subquery)
            query = query.order_by(desc(Project.updated_at))
        else:
            query = query.order_by(desc(Project.created_at))

        result = await db.execute(query)
        projects = result.scalars().all()

    return templates.TemplateResponse(
        "pages/browse.html",
        {
            "request": request,
            "settings": settings,
            "user": user,
            "projects": projects,
            "search": search or "",
            "sort": sort,
        }
    )


@router.get("/project/{slug}", response_class=HTMLResponse)
async def view_project(request: Request, slug: str):
    """
    View public project details.
    Shows project info and list of analyses.
    """
    user = await get_current_user(request)

    async with get_session_factory()() as db:
        result = await db.execute(
            select(Project)
            .options(selectinload(Project.user))
            .options(selectinload(Project.analyses))
            .where(Project.slug == slug)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check access: public or owner or admin
        is_owner = user and user.id == project.user_id
        is_admin = user and user.is_admin

        if not project.is_public and not is_owner and not is_admin:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get analyses for this project, sorted by most recent
        analyses = sorted(
            project.analyses,
            key=lambda a: a.started_at,
            reverse=True
        )

    return templates.TemplateResponse(
        "pages/project_view.html",
        {
            "request": request,
            "settings": settings,
            "user": user,
            "project": project,
            "analyses": analyses,
            "is_owner": is_owner,
            "is_admin": is_admin,
            "can_edit": is_owner or is_admin,
            "can_analyze": user and user.is_approved,
        }
    )


@router.get("/analysis/{analysis_id}", response_class=HTMLResponse)
async def view_analysis(request: Request, analysis_id: int):
    """
    View analysis report.
    Shows section navigation and report content.
    """
    user = await get_current_user(request)

    async with get_session_factory()() as db:
        result = await db.execute(
            select(Analysis)
            .options(selectinload(Analysis.project).selectinload(Project.user))
            .where(Analysis.id == analysis_id)
        )
        analysis = result.scalar_one_or_none()

        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        project = analysis.project

        # Check access: public project or owner or admin
        is_owner = user and user.id == project.user_id
        is_admin = user and user.is_admin

        if not project.is_public and not is_owner and not is_admin:
            raise HTTPException(status_code=404, detail="Analysis not found")

        # Get completed sections for navigation
        sections_completed = analysis.sections_completed or {}

        # Read first section content if analysis is completed
        first_section_content = None
        if analysis.status == "completed" and sections_completed:
            # Get first available section
            first_section_key = sorted(sections_completed.keys())[0] if sections_completed else None
            if first_section_key and analysis.report_folder_path:
                section_file = settings.BASE_DIR / analysis.report_folder_path / f"{first_section_key}.html"
                if section_file.exists():
                    first_section_content = section_file.read_text(encoding="utf-8")

    return templates.TemplateResponse(
        "pages/analysis_view.html",
        {
            "request": request,
            "settings": settings,
            "user": user,
            "analysis": analysis,
            "project": project,
            "sections_completed": sections_completed,
            "first_section_content": first_section_content,
            "is_owner": is_owner,
            "can_edit": is_owner or is_admin,
        }
    )


@router.get("/analysis/{analysis_id}/section/{section_key}", response_class=HTMLResponse)
async def view_analysis_section(
    request: Request,
    analysis_id: int,
    section_key: str,
):
    """
    View a specific section of an analysis report.
    Returns the section HTML content.
    """
    user = await get_current_user(request)

    async with get_session_factory()() as db:
        result = await db.execute(
            select(Analysis)
            .options(selectinload(Analysis.project))
            .where(Analysis.id == analysis_id)
        )
        analysis = result.scalar_one_or_none()

        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        project = analysis.project

        # Check access
        is_owner = user and user.id == project.user_id
        is_admin = user and user.is_admin

        if not project.is_public and not is_owner and not is_admin:
            raise HTTPException(status_code=404, detail="Analysis not found")

        # Read section content
        if not analysis.report_folder_path:
            raise HTTPException(status_code=404, detail="Report not found")

        section_file = settings.BASE_DIR / analysis.report_folder_path / f"{section_key}.html"

        if not section_file.exists():
            raise HTTPException(status_code=404, detail="Section not found")

        section_content = section_file.read_text(encoding="utf-8")

    # Return just the section content for AJAX loading
    return HTMLResponse(content=section_content)


@router.get("/pending-approval", response_class=HTMLResponse)
async def pending_approval(request: Request):
    """Page shown to users awaiting approval."""
    user = await get_current_user(request)

    if not user:
        return templates.TemplateResponse(
            "pages/login.html",
            {"request": request, "settings": settings}
        )

    # If already approved, redirect to dashboard
    if user.is_approved:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        "pages/pending-approval.html",
        {
            "request": request,
            "settings": settings,
            "user": user,
        }
    )
