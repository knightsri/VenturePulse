"""
Background task runner for VenturePulse v2.
Handles running analysis tasks in the background without blocking requests.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.db.database import get_session_factory
from app.db.models import Analysis, Project
from app.services.analysis_engine import run_analysis
from app.services.report import format_cost, format_time, generate_provenance

logger = logging.getLogger(__name__)
settings = get_settings()

# Store running tasks
_running_tasks: Dict[int, asyncio.Task] = {}


def get_sections_config():
    """Get section configuration (imported from routes to avoid circular imports)."""
    from app.routes.analysis import SECTIONS, get_section_by_num
    return SECTIONS, get_section_by_num


async def execute_analysis(
    analysis_id: int,
    api_key: str,
    sections_to_run: List[str],
):
    """
    Execute an analysis in the background.

    Args:
        analysis_id: ID of the analysis record
        api_key: OpenRouter API key from user session
        sections_to_run: List of section numbers to run (e.g., ["01", "02", "07"])
    """
    logger.info(f"Starting background analysis {analysis_id}")

    SECTIONS, get_section_by_num = get_sections_config()

    try:
        async with get_session_factory()() as db:
            # Load analysis and project
            result = await db.execute(
                select(Analysis)
                .options(selectinload(Analysis.project).selectinload(Project.user))
                .where(Analysis.id == analysis_id)
            )
            analysis = result.scalar_one_or_none()

            if not analysis:
                logger.error(f"Analysis {analysis_id} not found")
                return

            project = analysis.project

            # Update status to running
            analysis.status = "running"
            analysis.started_at = datetime.utcnow()
            await db.commit()

            # Get section configs for requested sections
            section_configs = []
            for num in sections_to_run:
                section = get_section_by_num(num)
                if section:
                    section_configs.append(section)

            if not section_configs:
                logger.error(f"No valid sections found for analysis {analysis_id}")
                analysis.status = "failed"
                analysis.completed_at = datetime.utcnow()
                await db.commit()
                return

            # Create output directory
            output_dir = Path(settings.BASE_DIR) / analysis.report_folder_path
            output_dir.mkdir(parents=True, exist_ok=True)

            # Define progress callback to update database
            async def progress_callback(section_name: str, status: str, message: str):
                try:
                    async with get_session_factory()() as progress_db:
                        result = await progress_db.execute(
                            select(Analysis).where(Analysis.id == analysis_id)
                        )
                        analysis_record = result.scalar_one_or_none()
                        if analysis_record:
                            # Update sections_completed
                            sections = analysis_record.sections_completed or {}

                            # Find section key from name
                            section_key = None
                            for s in section_configs:
                                if s["name"] == section_name:
                                    section_key = f"section{s['num']}"
                                    break

                            if section_key:
                                sections[section_key] = {
                                    "status": status,
                                    "message": message,
                                    "updated_at": datetime.utcnow().isoformat(),
                                }
                                analysis_record.sections_completed = sections
                                await progress_db.commit()
                except Exception as e:
                    logger.warning(f"Failed to update progress: {e}")

            # Run the analysis
            analysis_result = await run_analysis(
                api_key=api_key,
                model=analysis.model_name,
                project_name=project.name,
                project_data=project.spec_content,
                output_dir=output_dir,
                sections_to_run=section_configs,
                progress_callback=progress_callback,
                parallel=False,  # Sequential for now - safer for rate limits
            )

            # Update analysis record with results
            async with get_session_factory()() as db:
                result = await db.execute(
                    select(Analysis).where(Analysis.id == analysis_id)
                )
                analysis = result.scalar_one_or_none()

                if analysis:
                    # Build sections_completed from results
                    sections_completed = {}
                    for key, result_data in analysis_result["results"].items():
                        section_num = key.replace("section", "").split("-")[0]
                        sections_completed[f"section{section_num}"] = {
                            "status": "completed" if result_data.get("success") else "failed",
                            "section_num": section_num,
                            "elapsed": result_data.get("elapsed", 0),
                            "cost": result_data.get("cost", 0),
                            "tokens": result_data.get("tokens", 0),
                            "error": result_data.get("error") if not result_data.get("success") else None,
                        }

                    # Build cost breakdown
                    cost_breakdown = {
                        "section_costs": analysis_result["metadata"].get("cost", {}).get("section_costs", []),
                        "total_retries": analysis_result["metadata"].get("cost", {}).get("total_retries", 0),
                    }

                    # Determine final status
                    failed_count = len(analysis_result.get("failed_sections", []))
                    if failed_count == len(section_configs):
                        final_status = "failed"
                    elif failed_count > 0:
                        final_status = "completed"  # Partial success
                    else:
                        final_status = "completed"

                    analysis.status = final_status
                    analysis.sections_completed = sections_completed
                    analysis.cost_breakdown = cost_breakdown
                    analysis.total_cost_usd = analysis_result["total_cost"]
                    analysis.total_tokens = analysis_result["total_tokens"]
                    analysis.completed_at = datetime.utcnow()
                    analysis.api_key_temp = None  # Clear API key after completion

                    await db.commit()

                    logger.info(
                        f"Analysis {analysis_id} completed: "
                        f"status={final_status}, "
                        f"time={format_time(analysis_result['total_time'])}, "
                        f"cost={format_cost(analysis_result['total_cost'])}"
                    )

    except asyncio.CancelledError:
        logger.info(f"Analysis {analysis_id} was cancelled")
        async with get_session_factory()() as db:
            result = await db.execute(
                select(Analysis).where(Analysis.id == analysis_id)
            )
            analysis = result.scalar_one_or_none()
            if analysis:
                analysis.status = "cancelled"
                analysis.completed_at = datetime.utcnow()
                analysis.api_key_temp = None  # Clear API key
                await db.commit()

    except Exception as e:
        logger.exception(f"Analysis {analysis_id} failed with error: {e}")
        async with get_session_factory()() as db:
            result = await db.execute(
                select(Analysis).where(Analysis.id == analysis_id)
            )
            analysis = result.scalar_one_or_none()
            if analysis:
                analysis.status = "failed"
                analysis.completed_at = datetime.utcnow()
                analysis.api_key_temp = None  # Clear API key
                # Store error in sections_completed
                analysis.sections_completed = {
                    "error": {"status": "failed", "message": str(e)}
                }
                await db.commit()

    finally:
        # Remove from running tasks
        if analysis_id in _running_tasks:
            del _running_tasks[analysis_id]


def start_analysis_task(
    analysis_id: int,
    api_key: str,
    sections_to_run: List[str],
) -> asyncio.Task:
    """
    Start an analysis task in the background.

    Returns the asyncio Task object.
    """
    task = asyncio.create_task(
        execute_analysis(analysis_id, api_key, sections_to_run)
    )
    _running_tasks[analysis_id] = task
    return task


def cancel_analysis_task(analysis_id: int) -> bool:
    """
    Cancel a running analysis task.

    Returns True if task was found and cancelled.
    """
    if analysis_id in _running_tasks:
        task = _running_tasks[analysis_id]
        task.cancel()
        return True
    return False


def is_analysis_running(analysis_id: int) -> bool:
    """Check if an analysis task is currently running."""
    return analysis_id in _running_tasks and not _running_tasks[analysis_id].done()


def get_running_analysis_ids() -> List[int]:
    """Get list of currently running analysis IDs."""
    return [
        aid for aid, task in _running_tasks.items()
        if not task.done()
    ]


async def finalize_analysis(analysis_id: int) -> bool:
    """
    Finalize an analysis by generating provenance if missing.

    This handles the case where all sections completed but provenance
    wasn't generated (e.g., due to a container restart).

    Returns True if finalization was successful.
    """
    logger.info(f"Finalizing analysis {analysis_id}...")

    try:
        async with get_session_factory()() as db:
            result = await db.execute(
                select(Analysis)
                .options(selectinload(Analysis.project))
                .where(Analysis.id == analysis_id)
            )
            analysis = result.scalar_one_or_none()

            if not analysis:
                logger.error(f"Analysis {analysis_id} not found")
                return False

            # Check if provenance already exists
            output_dir = Path(settings.BASE_DIR) / analysis.report_folder_path
            provenance_path = output_dir / "section20-provenance.html"

            if provenance_path.exists():
                logger.info(f"Provenance already exists for analysis {analysis_id}")
                # Just mark as complete if stuck in running
                if analysis.status == "running":
                    analysis.status = "completed"
                    analysis.completed_at = analysis.completed_at or datetime.utcnow()
                    analysis.api_key_temp = None
                    await db.commit()
                return True

            # Build cost data from analysis record
            total_cost = analysis.total_cost_usd or 0
            total_tokens = analysis.total_tokens or 0
            section_costs = []

            if analysis.cost_breakdown and "section_costs" in analysis.cost_breakdown:
                section_costs = analysis.cost_breakdown["section_costs"]
            elif analysis.sections_completed:
                # Build section_costs from sections_completed
                for key, data in analysis.sections_completed.items():
                    if isinstance(data, dict) and data.get("status") == "completed":
                        section_num = key.replace("section", "")
                        section_costs.append({
                            "section": section_num,
                            "cost": data.get("cost", 0),
                            "tokens": data.get("tokens", 0),
                            "elapsed": data.get("elapsed", 0),
                        })

            total_retries = 0
            if analysis.cost_breakdown and "total_retries" in analysis.cost_breakdown:
                total_retries = analysis.cost_breakdown["total_retries"]

            # Calculate total elapsed time
            total_elapsed = 0
            if analysis.started_at and analysis.completed_at:
                total_elapsed = (analysis.completed_at - analysis.started_at).total_seconds()
            elif analysis.started_at:
                total_elapsed = (datetime.utcnow() - analysis.started_at).total_seconds()

            cost_data = {
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "section_costs": section_costs,
                "total_retries": total_retries,
            }

            timing_data = {
                "total_seconds": total_elapsed,
                "total_formatted": format_time(total_elapsed),
            }

            # Generate provenance
            provenance_html = generate_provenance(
                analysis.project.name,
                analysis.model_name,
                cost_data=cost_data,
                timing_data=timing_data,
                execution_mode="Sequential",
                parallel_workers=None,
                failed_sections=[],
            )

            # Write provenance file
            output_dir.mkdir(parents=True, exist_ok=True)
            provenance_path.write_text(provenance_html, encoding="utf-8")

            # Update analysis record
            analysis.status = "completed"
            analysis.completed_at = analysis.completed_at or datetime.utcnow()
            analysis.api_key_temp = None

            # Add provenance to sections_completed
            sections = analysis.sections_completed or {}
            sections["section20"] = {"status": "completed"}
            analysis.sections_completed = sections

            await db.commit()

            logger.info(f"Successfully finalized analysis {analysis_id}")
            return True

    except Exception as e:
        logger.exception(f"Failed to finalize analysis {analysis_id}: {e}")
        return False


async def recover_interrupted_analyses():
    """
    Resume analyses that were interrupted by a restart.
    Called during application startup.

    Finds analyses with status 'running' or 'pending' that have an api_key_temp,
    and restarts them.
    """
    logger.info("Checking for interrupted analyses to recover...")

    try:
        async with get_session_factory()() as db:
            # Find interrupted analyses
            result = await db.execute(
                select(Analysis)
                .where(
                    Analysis.status.in_(["pending", "running"]),
                    Analysis.api_key_temp.isnot(None)
                )
            )
            interrupted = result.scalars().all()

            if not interrupted:
                logger.info("No interrupted analyses to recover")
                return

            logger.info(f"Found {len(interrupted)} interrupted analyses to recover")

            SECTIONS, get_section_by_num = get_sections_config()

            for analysis in interrupted:
                try:
                    # Get sections to run from sections_completed
                    sections_to_run = []
                    if analysis.sections_completed:
                        for key, value in analysis.sections_completed.items():
                            if key.startswith("section") and key != "section20":
                                # Extract section number
                                section_num = key.replace("section", "")
                                # Only re-run if not completed
                                if isinstance(value, dict) and value.get("status") != "completed":
                                    sections_to_run.append(section_num)
                                elif isinstance(value, dict) and "section_num" in value:
                                    # Pending section
                                    sections_to_run.append(value["section_num"])

                    if not sections_to_run:
                        # All sections were completed, finalize (generate provenance)
                        logger.info(f"Analysis {analysis.id} has no pending sections, finalizing...")
                        await finalize_analysis(analysis.id)
                        continue

                    logger.info(
                        f"Recovering analysis {analysis.id} with {len(sections_to_run)} sections: {sections_to_run}"
                    )

                    # Start the background task
                    start_analysis_task(
                        analysis_id=analysis.id,
                        api_key=analysis.api_key_temp,
                        sections_to_run=sections_to_run,
                    )

                except Exception as e:
                    logger.error(f"Failed to recover analysis {analysis.id}: {e}")
                    # Mark as failed
                    analysis.status = "failed"
                    analysis.completed_at = datetime.utcnow()
                    analysis.api_key_temp = None
                    analysis.sections_completed = {
                        "error": {"status": "failed", "message": f"Recovery failed: {str(e)}"}
                    }
                    await db.commit()

    except Exception as e:
        logger.exception(f"Error during analysis recovery: {e}")
