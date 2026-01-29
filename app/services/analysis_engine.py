"""
Analysis orchestration service for VenturePulse v2.
Handles running analyses, updating progress, and saving reports.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable

from app.config import get_settings
from app.services.openrouter import call_openrouter
from app.services.report import clean_html_output, format_cost, format_time, generate_provenance

logger = logging.getLogger(__name__)
settings = get_settings()

# Prompts directory
PROMPTS_DIR = settings.BASE_DIR / "prompts"


def load_prompt(section_num: str, section_slug: str) -> str:
    """Load section prompt from file."""
    prompt_file = PROMPTS_DIR / "sections" / f"section{section_num}-{section_slug}.md"
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")
    return ""


def load_common_instructions() -> str:
    """Load common instructions."""
    common_file = PROMPTS_DIR / "common-instructions.md"
    if common_file.exists():
        return common_file.read_text(encoding="utf-8")
    return ""


async def generate_section(
    api_key: str,
    model: str,
    section: Dict,
    common_instructions: str,
    project_data: str,
    output_dir: Path,
) -> Dict:
    """
    Generate a single section.

    Returns dict with: success, section_key, section_name, content/error, elapsed, cost, tokens, retries
    """
    section_key = f"section{section['num']}-{section['slug']}"
    section_name = f"{section['num']}. {section['name']}"

    # Load section prompt
    section_prompt = load_prompt(section["num"], section["slug"])
    if not section_prompt:
        return {
            "success": False,
            "section_key": section_key,
            "section_name": section_name,
            "error": f"Prompt file not found for {section['name']}",
            "elapsed": 0,
            "cost": 0,
            "tokens": 0,
            "retries": 0,
        }

    # Build full prompt
    full_prompt = f"""{common_instructions}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{section_prompt}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## PROJECT DATA

{project_data}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate the HTML for this section now."""

    # Get section-specific temperature and seed settings
    temperature = section.get("temperature")  # None uses default in openrouter.py
    seed = section.get("seed")  # None means no seed (non-deterministic)

    # Call API with retry logic
    success, content, elapsed, usage_info = await call_openrouter(
        api_key, model, full_prompt, temperature=temperature, seed=seed
    )

    result = {
        "section_key": section_key,
        "section_name": section_name,
        "elapsed": elapsed,
        "cost": usage_info.get("cost", 0.0),
        "tokens": usage_info.get("total_tokens", 0),
        "prompt_tokens": usage_info.get("prompt_tokens", 0),
        "completion_tokens": usage_info.get("completion_tokens", 0),
        "retries": usage_info.get("retries", 0),
    }

    if success:
        # Clean and save section HTML
        cleaned_content = clean_html_output(content)
        output_file = output_dir / f"{section_key}.html"
        output_file.write_text(cleaned_content, encoding="utf-8")
        result["success"] = True
        result["content"] = cleaned_content
        result["words"] = len(cleaned_content.split())
    else:
        result["success"] = False
        result["error"] = content

    return result


async def run_analysis(
    api_key: str,
    model: str,
    project_name: str,
    project_data: str,
    output_dir: Path,
    sections_to_run: List[Dict],
    progress_callback: Optional[Callable] = None,
    parallel: bool = False,
    max_workers: int = 5,
) -> Dict:
    """
    Run the full analysis and save results.

    Args:
        api_key: OpenRouter API key
        model: Model name to use
        project_name: Name of the project
        project_data: Project specification content
        output_dir: Directory to save output files
        sections_to_run: List of section dicts to generate
        progress_callback: Optional async callback(section_num, status, message)
        parallel: Whether to run sections in parallel
        max_workers: Maximum parallel workers if parallel=True

    Returns:
        Dict with results, timing, and cost information
    """
    analysis_start = time.time()

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save project spec
    (output_dir / "project-spec.md").write_text(project_data, encoding="utf-8")

    # Determine execution mode
    execution_mode = "parallel" if parallel else "sequential"
    parallel_workers = min(max_workers, len(sections_to_run)) if parallel else 1

    # Initialize metadata
    metadata = {
        "project_name": project_name,
        "model": model,
        "created_at": datetime.now().isoformat(),
        "sections": {},
        "sections_requested": [s["num"] for s in sections_to_run],
        "execution_mode": execution_mode,
        "parallel_workers": parallel_workers if parallel else None,
        "timing": {},
        "cost": {},
        "failures": [],
        "status": "running",
    }

    # Helper to save metadata incrementally
    def save_metadata():
        (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    # Write initial metadata
    save_metadata()

    # Load common instructions
    common_instructions = load_common_instructions()

    results = {}
    section_times = []

    # Cost tracking
    total_cost = 0.0
    total_tokens = 0
    section_costs = []
    total_retries = 0
    failed_sections = []

    total_sections = len(sections_to_run)

    if parallel:
        # Parallel execution using asyncio
        logger.info(f"Starting parallel generation ({parallel_workers} workers)...")

        semaphore = asyncio.Semaphore(parallel_workers)

        async def run_with_semaphore(section):
            async with semaphore:
                return await generate_section(
                    api_key, model, section, common_instructions, project_data, output_dir
                )

        # Create tasks for all sections
        tasks = [run_with_semaphore(section) for section in sections_to_run]

        # Process results as they complete
        completed_count = 0
        for coro in asyncio.as_completed(tasks):
            result = await coro
            completed_count += 1

            section_key = result["section_key"]
            section_times.append(result["elapsed"])

            # Track costs
            section_cost = result.get("cost", 0.0)
            section_tokens = result.get("tokens", 0)
            total_cost += section_cost
            total_tokens += section_tokens
            total_retries += result.get("retries", 0)

            section_costs.append({
                "name": result["section_name"],
                "cost": section_cost,
                "tokens": section_tokens,
                "retries": result.get("retries", 0),
            })

            if result["success"]:
                results[section_key] = {
                    "success": True,
                    "elapsed": result["elapsed"],
                    "cost": section_cost,
                    "tokens": section_tokens,
                    "retries": result.get("retries", 0),
                }
                metadata["sections"][section_key] = {
                    "status": "completed",
                    "words": result.get("words", 0),
                    "elapsed_seconds": result["elapsed"],
                    "cost": section_cost,
                    "tokens": section_tokens,
                    "prompt_tokens": result.get("prompt_tokens", 0),
                    "completion_tokens": result.get("completion_tokens", 0),
                    "retries": result.get("retries", 0),
                }
                if progress_callback:
                    await progress_callback(result["section_name"], "completed", f"Completed in {format_time(result['elapsed'])}")
            else:
                error_msg = result.get("error", "Unknown error")
                results[section_key] = {
                    "success": False,
                    "error": error_msg,
                    "elapsed": result["elapsed"],
                }
                metadata["sections"][section_key] = {
                    "status": "failed",
                    "error": error_msg,
                    "elapsed_seconds": result["elapsed"],
                    "retries": result.get("retries", 0),
                }
                failed_sections.append({
                    "section": result["section_name"],
                    "error": error_msg,
                    "retries": result.get("retries", 0),
                })
                if progress_callback:
                    await progress_callback(result["section_name"], "failed", error_msg[:50])

            # Save metadata incrementally
            save_metadata()

            logger.info(f"Completed {completed_count}/{total_sections} sections")

    else:
        # Sequential execution
        for i, section in enumerate(sections_to_run):
            section_key = f"section{section['num']}-{section['slug']}"

            logger.info(f"Generating section {section['num']}. {section['name']}...")

            if progress_callback:
                await progress_callback(section["name"], "running", f"Starting generation...")

            # Mark section as running in metadata
            metadata["sections"][section_key] = {"status": "running"}
            save_metadata()

            # Generate section
            result = await generate_section(
                api_key, model, section, common_instructions, project_data, output_dir
            )
            section_times.append(result["elapsed"])

            # Track costs
            section_cost = result.get("cost", 0.0)
            section_tokens = result.get("tokens", 0)
            total_cost += section_cost
            total_tokens += section_tokens
            total_retries += result.get("retries", 0)

            section_costs.append({
                "name": result["section_name"],
                "cost": section_cost,
                "tokens": section_tokens,
                "retries": result.get("retries", 0),
            })

            if result["success"]:
                results[section_key] = {
                    "success": True,
                    "elapsed": result["elapsed"],
                    "cost": section_cost,
                    "tokens": section_tokens,
                    "retries": result.get("retries", 0),
                }
                metadata["sections"][section_key] = {
                    "status": "completed",
                    "words": result.get("words", 0),
                    "elapsed_seconds": result["elapsed"],
                    "cost": section_cost,
                    "tokens": section_tokens,
                    "prompt_tokens": result.get("prompt_tokens", 0),
                    "completion_tokens": result.get("completion_tokens", 0),
                    "retries": result.get("retries", 0),
                }
                if progress_callback:
                    await progress_callback(section["name"], "completed", f"Completed in {format_time(result['elapsed'])}")
            else:
                error_msg = result.get("error", "Unknown error")
                results[section_key] = {
                    "success": False,
                    "error": error_msg,
                    "elapsed": result["elapsed"],
                }
                metadata["sections"][section_key] = {
                    "status": "failed",
                    "error": error_msg,
                    "elapsed_seconds": result["elapsed"],
                    "retries": result.get("retries", 0),
                }
                failed_sections.append({
                    "section": result["section_name"],
                    "error": error_msg,
                    "retries": result.get("retries", 0),
                })
                if progress_callback:
                    await progress_callback(section["name"], "failed", error_msg[:50])

            # Save metadata incrementally
            save_metadata()

            # Small delay to avoid rate limits
            await asyncio.sleep(0.5)

    # Record failures in metadata
    metadata["failures"] = failed_sections

    # Generate provenance section
    total_elapsed = time.time() - analysis_start
    logger.info(f"Generating provenance section...")

    # Build cost data for provenance
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

    provenance_html = generate_provenance(
        project_name,
        model,
        cost_data=cost_data,
        timing_data=timing_data,
        execution_mode=execution_mode,
        parallel_workers=parallel_workers if parallel else None,
        failed_sections=failed_sections,
    )
    (output_dir / "section20-provenance.html").write_text(provenance_html, encoding="utf-8")
    results["section20-provenance"] = {"success": True}
    metadata["sections"]["section20-provenance"] = {"status": "completed"}

    # Record total timing
    total_time = time.time() - analysis_start
    metadata["timing"] = {
        "total_seconds": total_time,
        "total_formatted": format_time(total_time),
        "avg_section_seconds": sum(section_times) / len(section_times) if section_times else 0,
    }

    # Record total cost
    metadata["cost"] = {
        "total_cost": total_cost,
        "total_cost_formatted": format_cost(total_cost),
        "total_tokens": total_tokens,
        "section_costs": section_costs,
        "total_retries": total_retries,
    }

    # Mark analysis complete
    metadata["status"] = "completed"
    save_metadata()

    logger.info(f"Analysis complete! Total time: {format_time(total_time)}, Total cost: {format_cost(total_cost)}")

    return {
        "results": results,
        "total_time": total_time,
        "total_cost": total_cost,
        "total_tokens": total_tokens,
        "failed_sections": failed_sections,
        "metadata": metadata,
    }


async def update_analysis_db(
    db_session,
    analysis_id: int,
    sections_completed: Dict,
    total_cost: float,
    total_tokens: int,
    status: str,
):
    """
    Update analysis record in database.

    This should be called periodically during analysis to update progress.
    """
    from sqlalchemy import update
    from app.db.models import Analysis

    stmt = (
        update(Analysis)
        .where(Analysis.id == analysis_id)
        .values(
            sections_completed=sections_completed,
            total_cost_usd=total_cost,
            total_tokens=total_tokens,
            status=status,
            completed_at=datetime.utcnow() if status in ["completed", "failed", "cancelled"] else None,
        )
    )
    await db_session.execute(stmt)
    await db_session.commit()
