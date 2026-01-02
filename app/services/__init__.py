"""
Services module for VenturePulse v2.
Contains business logic and external service integrations.
"""

from app.services.apikey import (
    get_api_key,
    set_api_key,
    clear_api_key,
    has_api_key,
    get_masked_api_key,
    mask_api_key,
)

from app.services.openrouter import call_openrouter
from app.services.report import (
    clean_html_output,
    format_cost,
    format_time,
    generate_provenance,
)
from app.services.analysis_engine import (
    run_analysis,
    generate_section,
    load_prompt,
    load_common_instructions,
    update_analysis_db,
)

__all__ = [
    # API key management
    "get_api_key",
    "set_api_key",
    "clear_api_key",
    "has_api_key",
    "get_masked_api_key",
    "mask_api_key",
    # OpenRouter
    "call_openrouter",
    # Report generation
    "clean_html_output",
    "format_cost",
    "format_time",
    "generate_provenance",
    # Analysis engine
    "run_analysis",
    "generate_section",
    "load_prompt",
    "load_common_instructions",
    "update_analysis_db",
]
