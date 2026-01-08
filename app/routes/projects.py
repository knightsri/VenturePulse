"""
Project management routes for VenturePulse v2.
Handles project CRUD operations for authenticated users.
"""

import logging
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Depends, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.db.database import get_session_factory
from app.db.models import User, Project, Analysis
from app.auth.session import get_current_user
from app.auth.decorators import require_auth, require_approved

logger = logging.getLogger(__name__)
settings = get_settings()
templates = Jinja2Templates(directory=settings.BASE_DIR / "app" / "templates")

router = APIRouter(tags=["projects"])


def generate_slug(name: str) -> str:
    """Generate a URL-safe slug from a project name."""
    # Convert to lowercase and replace spaces with hyphens
    slug = name.lower().strip()
    # Remove special characters except hyphens
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    # Replace spaces with hyphens
    slug = re.sub(r'[\s]+', '-', slug)
    # Remove consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug[:100]  # Limit length


async def ensure_unique_slug(db, slug: str, exclude_id: Optional[int] = None) -> str:
    """Ensure slug is unique, appending number if needed."""
    base_slug = slug
    counter = 1

    while True:
        query = select(Project).where(Project.slug == slug)
        if exclude_id:
            query = query.where(Project.id != exclude_id)

        result = await db.execute(query)
        if result.scalar_one_or_none() is None:
            return slug

        counter += 1
        slug = f"{base_slug}-{counter}"


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    User dashboard showing their projects.
    For pending users or users with no projects, also show public projects.
    Unauthenticated users are redirected to /browse.
    """
    from app.auth.session import get_current_user

    user = await get_current_user(request)
    if user is None:
        # Redirect unauthenticated users to browse page
        return RedirectResponse(url="/browse", status_code=302)
    async with get_session_factory()() as db:
        # Get user's own projects
        result = await db.execute(
            select(Project)
            .options(selectinload(Project.analyses))
            .where(Project.user_id == user.id)
            .order_by(desc(Project.updated_at))
        )
        projects = result.scalars().all()

        # Get user's project counts (public/private)
        user_public_count = sum(1 for p in projects if p.is_public)
        user_private_count = sum(1 for p in projects if not p.is_public)
        user_total_count = len(projects)

        # For pending users or users with no projects, fetch public projects
        public_projects = []
        if not user.is_approved or not projects:
            result = await db.execute(
                select(Project)
                .options(selectinload(Project.user))
                .options(selectinload(Project.analyses))
                .where(Project.is_public == True)
                .where(Project.user_id != user.id)  # Exclude user's own projects
                .order_by(desc(Project.created_at))
                .limit(6)
            )
            public_projects = result.scalars().all()

        # Get pending user count for admin badge
        pending_count = 0
        if user.is_admin:
            result = await db.execute(
                select(func.count(User.id)).where(User.role == "pending")
            )
            pending_count = result.scalar() or 0

    return templates.TemplateResponse(
        "pages/dashboard.html",
        {
            "request": request,
            "settings": settings,
            "user": user,
            "projects": projects,
            "public_projects": public_projects,
            "total_count": user_total_count,
            "public_count": user_public_count,
            "private_count": user_private_count,
            "pending_count": pending_count,
        }
    )


@router.get("/project/new", response_class=HTMLResponse)
async def new_project_form(request: Request, user: User = Depends(require_approved)):
    """
    Display form for creating a new project.
    """
    return templates.TemplateResponse(
        "pages/project_new.html",
        {
            "request": request,
            "settings": settings,
            "user": user,
        }
    )


@router.post("/project/new", response_class=HTMLResponse)
async def create_project(
    request: Request,
    user: User = Depends(require_approved),
    name: str = Form(...),
    description: str = Form(""),
    spec_content: str = Form(""),
    is_public: bool = Form(False),
    spec_file: Optional[UploadFile] = File(None),
):
    """
    Create a new project.
    Spec can be provided via text input or file upload.
    """
    errors = []

    # Validate name
    name = name.strip()
    if not name:
        errors.append("Project name is required")
    elif len(name) > 255:
        errors.append("Project name must be less than 255 characters")

    # Get spec content from file or form
    final_spec_content = ""
    if spec_file and spec_file.filename:
        try:
            content = await spec_file.read()
            final_spec_content = content.decode("utf-8")
        except Exception as e:
            errors.append(f"Error reading uploaded file: {e}")
    else:
        final_spec_content = spec_content.strip()

    if not final_spec_content:
        errors.append("Project spec is required (paste or upload)")

    if errors:
        return templates.TemplateResponse(
            "pages/project_new.html",
            {
                "request": request,
                "settings": settings,
                "user": user,
                "errors": errors,
                "form_data": {
                    "name": name,
                    "description": description,
                    "spec_content": spec_content,
                    "is_public": is_public,
                },
            }
        )

    async with get_session_factory()() as db:
        # Generate unique slug
        base_slug = generate_slug(name)
        slug = await ensure_unique_slug(db, base_slug)

        # Create spec file path
        user_specs_dir = settings.specs_dir / str(user.id)
        user_specs_dir.mkdir(parents=True, exist_ok=True)
        spec_file_path = user_specs_dir / f"{slug}.md"

        # Save spec file
        spec_file_path.write_text(final_spec_content, encoding="utf-8")

        # Create project record
        project = Project(
            user_id=user.id,
            name=name,
            slug=slug,
            description=description.strip() if description else None,
            spec_content=final_spec_content,
            spec_file_path=str(spec_file_path.relative_to(settings.BASE_DIR)),
            is_public=is_public,
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)

        logger.info(f"Created project: {project.slug} (user: {user.email})")

    return RedirectResponse(url=f"/project/{slug}", status_code=303)


@router.get("/project/{slug}/edit", response_class=HTMLResponse)
async def edit_project_form(
    request: Request,
    slug: str,
    user: User = Depends(require_approved),
):
    """
    Display form for editing a project.
    Only owner or admin can edit.
    """
    async with get_session_factory()() as db:
        result = await db.execute(
            select(Project).where(Project.slug == slug)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check permissions
        if project.user_id != user.id and not user.is_admin:
            raise HTTPException(status_code=403, detail="Access denied")

    return templates.TemplateResponse(
        "pages/project_edit.html",
        {
            "request": request,
            "settings": settings,
            "user": user,
            "project": project,
        }
    )


@router.post("/project/{slug}/edit", response_class=HTMLResponse)
async def update_project(
    request: Request,
    slug: str,
    user: User = Depends(require_approved),
    name: str = Form(...),
    description: str = Form(""),
    spec_content: str = Form(...),
    is_public: bool = Form(False),
):
    """
    Update an existing project.
    """
    errors = []

    # Validate name
    name = name.strip()
    if not name:
        errors.append("Project name is required")
    elif len(name) > 255:
        errors.append("Project name must be less than 255 characters")

    spec_content = spec_content.strip()
    if not spec_content:
        errors.append("Project spec is required")

    async with get_session_factory()() as db:
        result = await db.execute(
            select(Project).where(Project.slug == slug)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check permissions
        if project.user_id != user.id and not user.is_admin:
            raise HTTPException(status_code=403, detail="Access denied")

        if errors:
            return templates.TemplateResponse(
                "pages/project_edit.html",
                {
                    "request": request,
                    "settings": settings,
                    "user": user,
                    "project": project,
                    "errors": errors,
                }
            )

        # Update slug if name changed
        new_slug = slug
        if name != project.name:
            base_slug = generate_slug(name)
            new_slug = await ensure_unique_slug(db, base_slug, exclude_id=project.id)

            # Rename spec file if slug changed
            if new_slug != slug:
                old_spec_path = settings.BASE_DIR / project.spec_file_path
                new_spec_path = settings.specs_dir / str(project.user_id) / f"{new_slug}.md"

                if old_spec_path.exists():
                    old_spec_path.rename(new_spec_path)
                else:
                    new_spec_path.parent.mkdir(parents=True, exist_ok=True)
                    new_spec_path.write_text(spec_content, encoding="utf-8")

                project.spec_file_path = str(new_spec_path.relative_to(settings.BASE_DIR))

        # Update project
        project.name = name
        project.slug = new_slug
        project.description = description.strip() if description else None
        project.spec_content = spec_content
        project.is_public = is_public
        project.updated_at = datetime.utcnow()

        # Update spec file content
        spec_path = settings.BASE_DIR / project.spec_file_path
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(spec_content, encoding="utf-8")

        await db.commit()

        logger.info(f"Updated project: {project.slug} (user: {user.email})")

    return RedirectResponse(url=f"/project/{new_slug}", status_code=303)


@router.post("/project/{slug}/delete")
async def delete_project(
    request: Request,
    slug: str,
    user: User = Depends(require_approved),
):
    """
    Delete a project and all associated data.
    """
    async with get_session_factory()() as db:
        result = await db.execute(
            select(Project)
            .options(selectinload(Project.analyses))
            .where(Project.slug == slug)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check permissions
        if project.user_id != user.id and not user.is_admin:
            raise HTTPException(status_code=403, detail="Access denied")

        # Delete spec file
        spec_path = settings.BASE_DIR / project.spec_file_path
        if spec_path.exists():
            spec_path.unlink()

        # Delete report folders for all analyses
        for analysis in project.analyses:
            if analysis.report_folder_path:
                report_path = settings.BASE_DIR / analysis.report_folder_path
                if report_path.exists():
                    shutil.rmtree(report_path, ignore_errors=True)

        # Delete project (cascades to analyses)
        await db.delete(project)
        await db.commit()

        logger.info(f"Deleted project: {slug} (user: {user.email})")

    return RedirectResponse(url="/dashboard", status_code=303)


@router.post("/project/{slug}/toggle-visibility")
async def toggle_visibility(
    request: Request,
    slug: str,
    user: User = Depends(require_approved),
):
    """
    Toggle project visibility between public and private.
    """
    async with get_session_factory()() as db:
        result = await db.execute(
            select(Project).where(Project.slug == slug)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check permissions
        if project.user_id != user.id and not user.is_admin:
            raise HTTPException(status_code=403, detail="Access denied")

        project.is_public = not project.is_public
        project.updated_at = datetime.utcnow()
        await db.commit()

        visibility = "public" if project.is_public else "private"
        logger.info(f"Toggled project visibility: {slug} -> {visibility}")

    return RedirectResponse(url=f"/project/{slug}", status_code=303)
