"""
Analysis routes for VenturePulse v2.
Handles analysis configuration, execution, and viewing.
"""

import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Request, HTTPException, Depends, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.db.database import get_session_factory
from app.db.models import User, Project, Analysis
from app.auth.decorators import require_approved
from app.services.apikey import has_api_key, get_masked_api_key, get_api_key
from app.services.background import start_analysis_task, cancel_analysis_task, is_analysis_running
from app.services.report import format_cost, format_time
from app.services.preferences import get_user_preferred_models, save_user_preferred_models

logger = logging.getLogger(__name__)
settings = get_settings()
templates = Jinja2Templates(directory=settings.BASE_DIR / "app" / "templates")

router = APIRouter(tags=["analysis"])


# Section definitions - Full 19-section analysis framework
SECTIONS = [
    {"num": "01", "name": "Executive Summary", "slug": "executive-summary", "group": "Foundation"},
    {"num": "02", "name": "Market Landscape", "slug": "market-landscape", "group": "Foundation"},
    {"num": "03", "name": "User Stories", "slug": "user-stories", "group": "Foundation"},
    {"num": "04", "name": "Comparable Companies", "slug": "comparable-companies", "group": "Foundation"},
    {"num": "05", "name": "User Research", "slug": "user-research-validation", "group": "Foundation"},
    {"num": "06", "name": "Validation Experiments", "slug": "validation-experiments", "group": "Foundation"},
    {"num": "07", "name": "Technical Feasibility", "slug": "technical-feasibility", "group": "Strategy"},
    {"num": "08", "name": "Competitive Advantage", "slug": "competitive-advantage", "group": "Strategy"},
    {"num": "09", "name": "Business Model", "slug": "business-model", "group": "Strategy"},
    {"num": "10", "name": "Legal & Compliance", "slug": "legal-ip-compliance", "group": "Strategy"},
    {"num": "11", "name": "MVP Roadmap", "slug": "mvp-roadmap", "group": "Execution"},
    {"num": "12", "name": "Customer Journey", "slug": "customer-journey", "group": "Execution"},
    {"num": "13", "name": "Go-to-Market", "slug": "go-to-market", "group": "Execution"},
    {"num": "14", "name": "Partnerships", "slug": "partnerships-ecosystem", "group": "Execution"},
    {"num": "15", "name": "Expansion Plan", "slug": "expansion-plan", "group": "Execution"},
    {"num": "16", "name": "Success Metrics", "slug": "success-metrics", "group": "Future"},
    {"num": "17", "name": "Funding Strategy", "slug": "funding-investment", "group": "Future"},
    {"num": "18", "name": "Exit Strategy", "slug": "exit-strategy", "group": "Future"},
    {"num": "19", "name": "Pitch Narrative", "slug": "pitch-narrative", "group": "Future"},
]

# Section groups for organized navigation
SECTION_GROUPS = {
    "Foundation": "Understanding the problem & market (Sections 01-06)",
    "Strategy": "Building the solution (Sections 07-10)",
    "Execution": "Launching & growing (Sections 11-15)",
    "Future": "Scaling & exits (Sections 16-19)",
}

# Quick analysis preset - core sections for fast validation
QUICK_SECTIONS = ["01", "02", "07", "09", "11", "13", "16"]

# Top models for business analysis
POPULAR_MODELS = [
    "anthropic/claude-sonnet-4",
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "google/gemini-2.5-pro",
    "deepseek/deepseek-chat",
    "deepseek/deepseek-v3.2",
    "x-ai/grok-4.1-fast",
    "x-ai/grok-4-fast",
    "qwen/qwen3-max",
    "qwen/qwen-2.5-72b-instruct",
    "z-ai/glm-4.7",
    "z-ai/glm-4.5-air",
    "mistralai/mistral-large",
    "meta-llama/llama-3.3-70b-instruct",
]


@router.get("/project/{slug}/analyze", response_class=HTMLResponse)
async def analyze_form(
    request: Request,
    slug: str,
    user: User = Depends(require_approved),
):
    """
    Show analysis configuration form.
    Allows selecting model and sections.
    Requires API key to be set.
    """
    async with get_session_factory()() as db:
        result = await db.execute(
            select(Project).where(Project.slug == slug)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check access: owner or admin or public project
        is_owner = user.id == project.user_id
        is_admin = user.is_admin

        if not project.is_public and not is_owner and not is_admin:
            raise HTTPException(status_code=404, detail="Project not found")

        # Load user's preferred models
        user_preferred_models = await get_user_preferred_models(db, user.id)

    # Group sections by category
    grouped_sections = {}
    for section in SECTIONS:
        group = section["group"]
        if group not in grouped_sections:
            grouped_sections[group] = []
        grouped_sections[group].append(section)

    # Determine which models to show as selected
    # Priority: user preferences > default model
    if user_preferred_models:
        selected_models = user_preferred_models
    else:
        selected_models = [settings.DEFAULT_MODEL]

    return templates.TemplateResponse(
        "pages/analysis_run.html",
        {
            "request": request,
            "settings": settings,
            "user": user,
            "project": project,
            "models": POPULAR_MODELS,
            "default_model": settings.DEFAULT_MODEL,
            "selected_models": selected_models,
            "sections": SECTIONS,
            "grouped_sections": grouped_sections,
            "section_groups": SECTION_GROUPS,
            "quick_sections": QUICK_SECTIONS,
            "has_api_key": has_api_key(request),
            "masked_api_key": get_masked_api_key(request),
        }
    )


@router.post("/project/{slug}/analyze")
async def start_analysis(
    request: Request,
    slug: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_approved),
    models: List[str] = Form(...),
    sections: List[str] = Form(...),
):
    """
    Start one or more analyses (one per selected model).
    Creates analysis records and starts background tasks.
    Requires API key to be set.
    """
    # Check for API key
    if not has_api_key(request):
        return RedirectResponse(
            url=f"/project/{slug}/analyze?error=Please+set+your+OpenRouter+API+key+in+Settings+first",
            status_code=303
        )

    # Validate models list
    if not models:
        return RedirectResponse(
            url=f"/project/{slug}/analyze?error=Please+select+at+least+one+model",
            status_code=303
        )

    async with get_session_factory()() as db:
        result = await db.execute(
            select(Project).where(Project.slug == slug)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check access
        is_owner = user.id == project.user_id
        is_admin = user.is_admin

        if not project.is_public and not is_owner and not is_admin:
            raise HTTPException(status_code=404, detail="Project not found")

        # Validate sections
        valid_section_nums = {s["num"] for s in SECTIONS}
        selected_sections = [s for s in sections if s in valid_section_nums]

        if not selected_sections:
            return RedirectResponse(
                url=f"/project/{slug}/analyze?error=Please+select+at+least+one+section",
                status_code=303
            )

        # Get API key from session
        api_key = get_api_key(request)

        # Save user's model preferences for next time
        await save_user_preferred_models(db, user.id, models)

        # Create an analysis for each model
        created_analyses = []
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")

        for model in models:
            # Create report folder path (unique per model)
            model_slug = model.replace("/", "-").replace(".", "-")
            report_folder = f"data/reports/{project.user_id}/{project.slug}/{timestamp}-{model_slug}"

            # Create analysis record
            analysis = Analysis(
                project_id=project.id,
                model_name=model,
                status="pending",
                api_key_temp=api_key,  # Store for recovery after restarts
                report_folder_path=report_folder,
                sections_completed={},
                cost_breakdown={},
                total_cost_usd=0.0,
                total_tokens=0,
            )
            db.add(analysis)
            await db.commit()
            await db.refresh(analysis)

            # Store selected sections in analysis record
            analysis.sections_completed = {
                f"section{s}": {"status": "pending", "section_num": s}
                for s in selected_sections
            }
            await db.commit()

            logger.info(f"Created analysis {analysis.id} for project {slug} with model {model}")

            # Start background task
            start_analysis_task(
                analysis_id=analysis.id,
                api_key=api_key,
                sections_to_run=selected_sections,
            )

            logger.info(f"Started background analysis task for analysis {analysis.id}")
            created_analyses.append(analysis)

    # If only one model, redirect to that analysis
    if len(created_analyses) == 1:
        return RedirectResponse(url=f"/analysis/{created_analyses[0].id}", status_code=303)

    # Multiple models - redirect to project page with success message
    model_count = len(created_analyses)
    return RedirectResponse(
        url=f"/project/{slug}?success=Started+{model_count}+analyses.+You+can+monitor+progress+below.",
        status_code=303
    )


@router.get("/analysis/{analysis_id}/status")
async def analysis_status(request: Request, analysis_id: int):
    """
    Get current analysis status for polling.
    Returns JSON with status and progress.
    """
    async with get_session_factory()() as db:
        result = await db.execute(
            select(Analysis)
            .options(selectinload(Analysis.project))
            .where(Analysis.id == analysis_id)
        )
        analysis = result.scalar_one_or_none()

        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        # Calculate progress
        sections = analysis.sections_completed or {}
        total_sections = len(sections)
        completed_sections = sum(
            1 for s in sections.values()
            if isinstance(s, dict) and s.get("status") == "completed"
        )

        progress_percent = (
            int((completed_sections / total_sections) * 100)
            if total_sections > 0 else 0
        )

        return JSONResponse({
            "id": analysis.id,
            "status": analysis.status,
            "progress": progress_percent,
            "completed_sections": completed_sections,
            "total_sections": total_sections,
            "sections": sections,
            "total_cost_usd": analysis.total_cost_usd,
            "total_tokens": analysis.total_tokens,
        })


@router.post("/analysis/{analysis_id}/cancel")
async def cancel_analysis(
    request: Request,
    analysis_id: int,
    user: User = Depends(require_approved),
):
    """
    Cancel a running analysis.
    """
    async with get_session_factory()() as db:
        result = await db.execute(
            select(Analysis)
            .options(selectinload(Analysis.project))
            .where(Analysis.id == analysis_id)
        )
        analysis = result.scalar_one_or_none()

        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        # Check permissions
        is_owner = user.id == analysis.project.user_id
        is_admin = user.is_admin

        if not is_owner and not is_admin:
            raise HTTPException(status_code=403, detail="Access denied")

        if analysis.status in ("running", "pending"):
            # Cancel the background task if running
            cancel_analysis_task(analysis_id)

            analysis.status = "cancelled"
            analysis.completed_at = datetime.utcnow()
            analysis.api_key_temp = None  # Clear API key
            await db.commit()
            logger.info(f"Cancelled analysis {analysis_id}")

    return RedirectResponse(url=f"/analysis/{analysis_id}", status_code=303)


@router.post("/analysis/{analysis_id}/delete")
async def delete_analysis(
    request: Request,
    analysis_id: int,
    user: User = Depends(require_approved),
):
    """
    Delete an analysis and its report files.
    """
    import shutil

    async with get_session_factory()() as db:
        result = await db.execute(
            select(Analysis)
            .options(selectinload(Analysis.project))
            .where(Analysis.id == analysis_id)
        )
        analysis = result.scalar_one_or_none()

        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        project_slug = analysis.project.slug

        # Check permissions
        is_owner = user.id == analysis.project.user_id
        is_admin = user.is_admin

        if not is_owner and not is_admin:
            raise HTTPException(status_code=403, detail="Access denied")

        # Delete report folder
        if analysis.report_folder_path:
            report_path = settings.BASE_DIR / analysis.report_folder_path
            if report_path.exists():
                shutil.rmtree(report_path, ignore_errors=True)

        await db.delete(analysis)
        await db.commit()

        logger.info(f"Deleted analysis {analysis_id}")

    return RedirectResponse(url=f"/project/{project_slug}", status_code=303)


@router.get("/analysis/{analysis_id}", response_class=HTMLResponse)
async def view_analysis(
    request: Request,
    analysis_id: int,
    section: Optional[str] = None,
):
    """
    View an analysis report.
    Shows progress for running analyses, results for completed ones.
    """
    from app.auth.decorators import get_current_user

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

        # Check access: public project, owner, or admin
        is_owner = user and user.id == project.user_id
        is_admin = user and user.is_admin

        if not project.is_public and not is_owner and not is_admin:
            raise HTTPException(status_code=404, detail="Analysis not found")

        # Get sections info
        sections_completed = analysis.sections_completed or {}
        total_sections = len([s for s in sections_completed.keys() if s.startswith("section") and s != "section20"])
        completed_count = sum(
            1 for s in sections_completed.values()
            if isinstance(s, dict) and s.get("status") == "completed"
        )
        failed_count = sum(
            1 for s in sections_completed.values()
            if isinstance(s, dict) and s.get("status") == "failed"
        )

        # Calculate progress percentage
        progress_percent = int((completed_count / total_sections) * 100) if total_sections > 0 else 0

        # Get available section files
        available_sections = []
        report_path = settings.BASE_DIR / analysis.report_folder_path if analysis.report_folder_path else None

        if report_path and report_path.exists():
            for section_def in SECTIONS:
                section_file = report_path / f"section{section_def['num']}-{section_def['slug']}.html"
                if section_file.exists():
                    available_sections.append({
                        **section_def,
                        "file": str(section_file),
                        "status": "completed",
                    })
                else:
                    # Check if this section was requested
                    section_key = f"section{section_def['num']}"
                    if section_key in sections_completed:
                        section_status = sections_completed[section_key].get("status", "pending")
                        available_sections.append({
                            **section_def,
                            "file": None,
                            "status": section_status,
                        })

            # Check for provenance
            provenance_file = report_path / "section20-provenance.html"
            if provenance_file.exists():
                available_sections.append({
                    "num": "20",
                    "name": "Provenance",
                    "slug": "provenance",
                    "group": "Meta",
                    "file": str(provenance_file),
                    "status": "completed",
                })

        # Load selected section content
        section_content = None
        selected_section = None

        if section and report_path:
            # Find the section
            for sec in available_sections:
                if sec["num"] == section and sec.get("file"):
                    selected_section = sec
                    try:
                        section_content = open(sec["file"], "r", encoding="utf-8").read()
                    except Exception as e:
                        logger.error(f"Failed to read section file: {e}")
                    break
        elif available_sections:
            # Default to first available section
            for sec in available_sections:
                if sec.get("file"):
                    selected_section = sec
                    try:
                        section_content = open(sec["file"], "r", encoding="utf-8").read()
                    except Exception as e:
                        logger.error(f"Failed to read section file: {e}")
                    break

        # Group sections by category for navigation
        grouped_sections = {"Foundation": [], "Strategy": [], "Execution": [], "Future": [], "Meta": []}
        for sec in available_sections:
            group = sec.get("group", "Meta")
            if group in grouped_sections:
                grouped_sections[group].append(sec)

        # Check if task is still running
        is_running = is_analysis_running(analysis_id) or analysis.status == "running"

        return templates.TemplateResponse(
            "pages/analysis_view.html",
            {
                "request": request,
                "settings": settings,
                "user": user,
                "analysis": analysis,
                "project": project,
                "is_owner": is_owner,
                "is_admin": is_admin,
                "sections": available_sections,
                "grouped_sections": grouped_sections,
                "section_groups": SECTION_GROUPS,
                "selected_section": selected_section,
                "section_content": section_content,
                "progress_percent": progress_percent,
                "completed_count": completed_count,
                "failed_count": failed_count,
                "total_sections": total_sections,
                "is_running": is_running,
                "format_cost": format_cost,
                "format_time": format_time,
            }
        )


# Export section configuration for use by other modules
def get_sections():
    """Get all sections configuration."""
    return SECTIONS


def get_section_by_num(num: str):
    """Get section configuration by number."""
    for section in SECTIONS:
        if section["num"] == num:
            return section
    return None


def get_quick_sections():
    """Get quick section preset numbers."""
    return QUICK_SECTIONS


def get_models():
    """Get available models."""
    return POPULAR_MODELS
