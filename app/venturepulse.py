"""
VenturePulse - AI-Powered Product Viability Analysis
Streamlit Web Application
"""

import streamlit as st
import os
import json
import requests
import time
import random
from datetime import datetime
from pathlib import Path
import re
import html
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Load .env file from current directory and parent directory
# This ensures the env file is loaded whether running from app/ or project root
load_dotenv()  # Try current directory
load_dotenv(Path(__file__).parent.parent / ".env")  # Try project root

# Configuration
# Use an absolute path for analyses so it works both locally and in Docker
BASE_DIR = Path(__file__).parent.parent
ANALYSES_DIR = BASE_DIR / "analyses"
ANALYSES_DIR.mkdir(parents=True, exist_ok=True)
# Verify we can write to the analyses folder
test_path = ANALYSES_DIR / "startup_test.txt"
try:
    with open(test_path, "w", encoding="utf-8") as f:
        f.write("VenturePulse startup verification")
except Exception as e:
    st.error(f"Failed to write test file to analyses folder: {e}")
PROMPTS_DIR = Path("/app/prompts") if os.path.exists("/app/prompts") else Path("./prompts")

# Retry and parallelization configuration
MAX_RETRIES = int(os.getenv("MAXRETRY", "3"))
MAX_PARALLEL_SECTIONS = int(os.getenv("MAX_PARALLEL_SECTIONS", "10"))

# Default model for new analyses
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "anthropic/claude-sonnet-4")
RETRY_BASE_DELAY = 2  # Base delay in seconds for exponential backoff
RETRY_JITTER_MAX = 2  # Maximum random jitter in seconds

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

# Top models for business analysis - verified on OpenRouter
POPULAR_MODELS = [
    # Anthropic Claude - excellent for detailed analysis
    "anthropic/claude-sonnet-4",
    "anthropic/claude-3.5-sonnet",
    # OpenAI GPT-4 family - reliable and fast
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    # Google Gemini Pro - more reliable than Flash for long sessions
    "google/gemini-2.5-pro",
    # DeepSeek - excellent value, GPT-5 class reasoning
    "deepseek/deepseek-chat",
    "deepseek/deepseek-v3.2",
    # xAI Grok - fast with 2M context
    "x-ai/grok-4.1-fast",
    "x-ai/grok-4-fast",
    # Qwen - strong reasoning and multilingual
    "qwen/qwen3-max",
    "qwen/qwen-2.5-72b-instruct",
    # Zhipu GLM - excellent for coding (73.8% SWE-bench)
    "z-ai/glm-4.7",
    "z-ai/glm-4.5-air",
    # Mistral - strong European alternative
    "mistralai/mistral-large",
    # Meta Llama - open source, capable
    "meta-llama/llama-3.3-70b-instruct",
]


def init_session_state():
    """Initialize session state variables"""
    if "api_key" not in st.session_state:
        st.session_state.api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if "api_key_confirmed" not in st.session_state:
        st.session_state.api_key_confirmed = bool(os.environ.get("OPENROUTER_API_KEY", ""))
    if "current_analysis" not in st.session_state:
        st.session_state.current_analysis = None
    if "analysis_progress" not in st.session_state:
        st.session_state.analysis_progress = {}
    if "is_analyzing" not in st.session_state:
        st.session_state.is_analyzing = False
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = 0
    if "spec_collapsed" not in st.session_state:
        st.session_state.spec_collapsed = False
    if "current_project_name" not in st.session_state:
        st.session_state.current_project_name = ""


def clean_html_output(content: str) -> str:
    """Clean LLM output by removing markdown code fences"""
    # Remove ```html at start and ``` at end
    content = content.strip()
    
    # Remove opening code fence with language
    if content.startswith("```html"):
        content = content[7:]
    elif content.startswith("```HTML"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    
    # Remove closing code fence
    if content.endswith("```"):
        content = content[:-3]
    
    return content.strip()


def delete_analysis(analysis_path: str) -> bool:
    """Delete an analysis directory"""
    import shutil
    try:
        path = Path(analysis_path)
        if path.exists() and path.is_dir():
            shutil.rmtree(path)
            return True
    except Exception as e:
        st.error(f"Failed to delete: {e}")
    return False


def load_prompt(section_num: str, section_slug: str) -> str:
    """Load section prompt from file"""
    prompt_file = PROMPTS_DIR / "sections" / f"section{section_num}-{section_slug}.md"
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")
    return ""


def load_common_instructions() -> str:
    """Load common instructions"""
    common_file = PROMPTS_DIR / "common-instructions.md"
    if common_file.exists():
        return common_file.read_text(encoding="utf-8")
    return ""


def fetch_generation_cost(api_key: str, generation_id: str) -> dict:
    """Fetch cost/usage info for a generation via separate API call"""
    try:
        response = requests.get(
            f"https://openrouter.ai/api/v1/generation?id={generation_id}",
            headers={
                "Authorization": f"Bearer {api_key}",
            },
            timeout=30,
        )
        data = response.json()
        if "data" in data:
            gen_data = data["data"]
            return {
                "prompt_tokens": gen_data.get("native_tokens_prompt", gen_data.get("tokens_prompt", 0)),
                "completion_tokens": gen_data.get("native_tokens_completion", gen_data.get("tokens_completion", 0)),
                "total_tokens": gen_data.get("native_tokens_prompt", 0) + gen_data.get("native_tokens_completion", 0),
                "cost": float(gen_data.get("total_cost", 0)),
            }
    except Exception:
        pass
    return None


def is_retryable_error(error_code: str, error_message: str) -> bool:
    """Determine if an error is transient and should be retried"""
    # Don't retry permanent errors
    permanent_errors = [
        "invalid_api_key",
        "invalid_model",
        "model_not_found",
        "insufficient_quota",
        "content_policy_violation",
        "invalid_request",
    ]
    if error_code and error_code.lower() in permanent_errors:
        return False

    # Retry rate limits, timeouts, and server errors
    retryable_patterns = [
        "rate_limit",
        "rate limit",
        "too many requests",
        "timeout",
        "server_error",
        "service_unavailable",
        "503",
        "502",
        "504",
        "overloaded",
        "capacity",
    ]
    error_lower = (error_message or "").lower()
    return any(pattern in error_lower for pattern in retryable_patterns)


def calculate_retry_delay(attempt: int) -> float:
    """Calculate delay with exponential backoff and jitter"""
    # Exponential backoff: base_delay * (2 ^ attempt)
    base_delay = RETRY_BASE_DELAY * (2 ** attempt)
    # Add random jitter to prevent thundering herd
    jitter = random.uniform(0, RETRY_JITTER_MAX)
    return base_delay + jitter


def call_openrouter(api_key: str, model: str, prompt: str) -> tuple[bool, str, float, dict]:
    """Call OpenRouter API with retry logic. Returns (success, content, elapsed_seconds, usage_info)

    usage_info contains:
        - prompt_tokens: int
        - completion_tokens: int
        - total_tokens: int
        - cost: float (in USD, if available from API)
        - retries: int (number of retry attempts made)
    """
    start_time = time.time()
    empty_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "cost": 0.0, "retries": 0}

    last_error = None
    last_error_code = None

    for attempt in range(MAX_RETRIES + 1):  # +1 for initial attempt
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "https://github.com/knightsri/VenturePulse",
                    "X-Title": "VenturePulse Web v2.0",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 25192,
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "usage": {"include": True},  # Request cost/usage info in response
                },
                timeout=600,  # 10 minutes for slower models
            )

            data = response.json()

            if "error" in data:
                error_msg = data["error"].get("message", "Unknown error")
                error_code = data["error"].get("code", "unknown")
                last_error = error_msg
                last_error_code = error_code

                # Check if error is retryable
                if attempt < MAX_RETRIES and is_retryable_error(error_code, error_msg):
                    delay = calculate_retry_delay(attempt)
                    time.sleep(delay)
                    continue
                else:
                    elapsed = time.time() - start_time
                    empty_usage["retries"] = attempt
                    return False, f"API Error ({error_code}): {error_msg}", elapsed, empty_usage

            if "choices" not in data or len(data["choices"]) == 0:
                elapsed = time.time() - start_time
                empty_usage["retries"] = attempt
                return False, "Invalid response format from API", elapsed, empty_usage

            content = data["choices"][0]["message"]["content"]

            # Extract usage/cost information from response
            usage = data.get("usage", {})
            usage_info = {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "cost": 0.0,
                "retries": attempt,
            }

            # OpenRouter may include native token counts for more accuracy
            if "native_tokens_prompt" in usage:
                usage_info["prompt_tokens"] = usage.get("native_tokens_prompt", usage_info["prompt_tokens"])
            if "native_tokens_completion" in usage:
                usage_info["completion_tokens"] = usage.get("native_tokens_completion", usage_info["completion_tokens"])

            # Extract cost from usage object (requires "usage": {"include": true} in request)
            # OpenRouter returns cost as usage.cost (total charged to account)
            if "cost" in usage:
                usage_info["cost"] = float(usage.get("cost", 0))
            elif "total_cost" in usage:
                usage_info["cost"] = float(usage.get("total_cost", 0))
            elif "cost" in data:
                usage_info["cost"] = float(data.get("cost", 0))

            # If cost is still 0, try fetching via generation ID
            generation_id = data.get("id")
            if usage_info["cost"] == 0 and generation_id:
                # Small delay to allow OpenRouter to finalize the generation
                time.sleep(0.5)
                gen_usage = fetch_generation_cost(api_key, generation_id)
                if gen_usage and gen_usage.get("cost", 0) > 0:
                    gen_usage["retries"] = attempt
                    usage_info = gen_usage

            elapsed = time.time() - start_time
            return True, content, elapsed, usage_info

        except requests.exceptions.Timeout:
            last_error = "Request timed out"
            if attempt < MAX_RETRIES:
                delay = calculate_retry_delay(attempt)
                time.sleep(delay)
                continue
            elapsed = time.time() - start_time
            empty_usage["retries"] = attempt
            return False, "Request timed out (10 min limit). Try a faster model or shorter spec.", elapsed, empty_usage

        except requests.exceptions.RequestException as e:
            last_error = str(e)
            if attempt < MAX_RETRIES:
                delay = calculate_retry_delay(attempt)
                time.sleep(delay)
                continue
            elapsed = time.time() - start_time
            empty_usage["retries"] = attempt
            return False, f"Network error: {str(e)}", elapsed, empty_usage

        except Exception as e:
            last_error = str(e)
            elapsed = time.time() - start_time
            empty_usage["retries"] = attempt
            return False, f"Unexpected error: {str(e)}", elapsed, empty_usage

    # Should not reach here, but just in case
    elapsed = time.time() - start_time
    empty_usage["retries"] = MAX_RETRIES
    return False, f"Max retries exceeded. Last error: {last_error}", elapsed, empty_usage


def format_cost(cost: float) -> str:
    """Format cost in USD with appropriate precision"""
    if cost == 0:
        return "$0.00"
    elif cost < 0.01:
        return f"${cost:.4f}"
    elif cost < 1:
        return f"${cost:.3f}"
    else:
        return f"${cost:.2f}"


def generate_provenance(project_name: str, model: str, cost_data: dict = None, timing_data: dict = None,
                        execution_mode: str = None, parallel_workers: int = None, failed_sections: list = None) -> str:
    """Generate provenance HTML section with cost, timing, and execution information

    Args:
        project_name: Name of the project
        model: AI model used
        cost_data: Dict with keys: total_cost, section_costs (list of dicts with name, cost, tokens, retries)
        timing_data: Dict with keys: total_seconds, total_formatted
        execution_mode: "sequential" or "parallel"
        parallel_workers: Number of parallel workers used (if parallel mode)
        failed_sections: List of dicts with section, error, retries for failed sections
    """
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Build cost section if data available
    cost_section = ""
    total_retries = cost_data.get("total_retries", 0) if cost_data else 0

    if cost_data and cost_data.get("total_cost", 0) > 0:
        section_rows = ""
        for section in cost_data.get("section_costs", []):
            retry_badge = ""
            if section.get("retries", 0) > 0:
                retry_badge = f' <span style="background: #ffc107; color: #000; padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.75rem;">↻{section["retries"]}</span>'
            section_rows += f'''
                <tr>
                    <td style="padding: 0.5rem 0.75rem; border-bottom: 1px solid #e9ecef;">{html.escape(section.get('name', 'Unknown'))}{retry_badge}</td>
                    <td style="padding: 0.5rem 0.75rem; border-bottom: 1px solid #e9ecef; text-align: right;">{section.get('tokens', 0):,}</td>
                    <td style="padding: 0.5rem 0.75rem; border-bottom: 1px solid #e9ecef; text-align: right;">{format_cost(section.get('cost', 0))}</td>
                </tr>'''

        retry_note = f' <span style="font-size: 0.85rem; color: #856404;">(includes {total_retries} retries)</span>' if total_retries > 0 else ""
        cost_section = f'''
        <div style="margin-top: 2rem;">
            <h3 style="color: #2d3748; font-size: 1.3rem; margin-bottom: 1rem;">💰 Cost Breakdown{retry_note}</h3>
            <div style="background: #f8f9fa; border-radius: 8px; padding: 1rem; overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
                    <thead>
                        <tr style="background: #e9ecef;">
                            <th style="padding: 0.75rem; text-align: left; font-weight: 600;">Section</th>
                            <th style="padding: 0.75rem; text-align: right; font-weight: 600;">Tokens</th>
                            <th style="padding: 0.75rem; text-align: right; font-weight: 600;">Cost (USD)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {section_rows}
                    </tbody>
                    <tfoot>
                        <tr style="background: #d4edda; font-weight: 600;">
                            <td style="padding: 0.75rem;">TOTAL</td>
                            <td style="padding: 0.75rem; text-align: right;">{cost_data.get('total_tokens', 0):,}</td>
                            <td style="padding: 0.75rem; text-align: right;">{format_cost(cost_data.get('total_cost', 0))}</td>
                        </tr>
                    </tfoot>
                </table>
            </div>
        </div>'''
    elif cost_data:
        # Show "Free" if cost is 0
        retry_note = f' ({total_retries} retries)' if total_retries > 0 else ""
        cost_section = f'''
        <div style="margin-top: 2rem;">
            <h3 style="color: #2d3748; font-size: 1.3rem; margin-bottom: 1rem;">💰 Cost</h3>
            <div style="background: #d4edda; border-radius: 8px; padding: 1rem; text-align: center;">
                <span style="font-size: 1.5rem; font-weight: 600; color: #155724;">FREE</span>
                <p style="margin: 0.5rem 0 0 0; color: #155724;">Total tokens used: {cost_data.get('total_tokens', 0):,}{retry_note}</p>
            </div>
        </div>'''

    # Build timing row
    timing_row = ""
    if timing_data:
        timing_row = f'''
                <tr>
                    <td style="padding: 0.75rem; border-bottom: 1px solid #e9ecef; font-weight: 600;">Total Time</td>
                    <td style="padding: 0.75rem; border-bottom: 1px solid #e9ecef;">{timing_data.get('total_formatted', 'N/A')}</td>
                </tr>'''

    # Build execution mode row
    exec_mode_row = ""
    if execution_mode:
        mode_display = execution_mode.capitalize()
        if execution_mode == "parallel" and parallel_workers:
            mode_display = f"Parallel ({parallel_workers} workers)"
        exec_mode_row = f'''
                <tr>
                    <td style="padding: 0.75rem; border-bottom: 1px solid #e9ecef; font-weight: 600;">Execution Mode</td>
                    <td style="padding: 0.75rem; border-bottom: 1px solid #e9ecef;">{mode_display}</td>
                </tr>'''

    # Build failed sections display
    failures_section = ""
    if failed_sections and len(failed_sections) > 0:
        failure_rows = ""
        for fail in failed_sections:
            retry_info = f" (after {fail.get('retries', 0)} retries)" if fail.get('retries', 0) > 0 else ""
            failure_rows += f'''
                <tr>
                    <td style="padding: 0.5rem 0.75rem; border-bottom: 1px solid #f5c6cb;">{html.escape(fail.get('section', 'Unknown'))}</td>
                    <td style="padding: 0.5rem 0.75rem; border-bottom: 1px solid #f5c6cb; font-size: 0.85rem;">{html.escape(str(fail.get('error', 'Unknown error')))[:100]}{retry_info}</td>
                </tr>'''

        failures_section = f'''
        <div style="margin-top: 2rem;">
            <h3 style="color: #721c24; font-size: 1.3rem; margin-bottom: 1rem;">⚠️ Failed Sections ({len(failed_sections)})</h3>
            <div style="background: #f8d7da; border-radius: 8px; padding: 1rem; overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
                    <thead>
                        <tr style="background: #f5c6cb;">
                            <th style="padding: 0.75rem; text-align: left; font-weight: 600;">Section</th>
                            <th style="padding: 0.75rem; text-align: left; font-weight: 600;">Error</th>
                        </tr>
                    </thead>
                    <tbody>
                        {failure_rows}
                    </tbody>
                </table>
            </div>
        </div>'''

    return f'''
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 900px; margin: 0 auto; padding: 2rem;">
        <h2 style="color: #2d3748; font-size: 1.8rem; border-bottom: 3px solid #667eea; padding-bottom: 0.5rem;">
            📜 Analysis Provenance
        </h2>

        <div style="background: #f8f9fa; border-radius: 8px; padding: 1.5rem; margin-top: 1.5rem;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 0.75rem; border-bottom: 1px solid #e9ecef; font-weight: 600; width: 200px;">Project Name</td>
                    <td style="padding: 0.75rem; border-bottom: 1px solid #e9ecef;">{html.escape(project_name)}</td>
                </tr>
                <tr>
                    <td style="padding: 0.75rem; border-bottom: 1px solid #e9ecef; font-weight: 600;">Generated At</td>
                    <td style="padding: 0.75rem; border-bottom: 1px solid #e9ecef;">{timestamp}</td>
                </tr>
                <tr>
                    <td style="padding: 0.75rem; border-bottom: 1px solid #e9ecef; font-weight: 600;">AI Model</td>
                    <td style="padding: 0.75rem; border-bottom: 1px solid #e9ecef;">{html.escape(model)}</td>
                </tr>
                {exec_mode_row}
                {timing_row}
                <tr>
                    <td style="padding: 0.75rem; font-weight: 600;">Tool Version</td>
                    <td style="padding: 0.75rem;">VenturePulse Web v2.0</td>
                </tr>
            </table>
        </div>

        {cost_section}

        {failures_section}

        <div style="margin-top: 2rem; padding: 1rem; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;">
            <strong>⚠️ Disclaimer:</strong> This analysis was generated by AI and should be used as a starting point for decision-making, not as definitive business advice. Always validate assumptions with real market research and domain experts.
        </div>
    </div>
    '''


def format_time(seconds: float) -> str:
    """Format seconds into human readable string"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"


def generate_section(api_key: str, model: str, section: dict, common_instructions: str, project_data: str, output_dir: Path) -> dict:
    """Generate a single section - used by both sequential and parallel execution.

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

    # Call API with retry logic
    success, content, elapsed, usage_info = call_openrouter(api_key, model, full_prompt)

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


def run_analysis(api_key: str, model: str, project_name: str, project_data: str, progress_callback, section_status_callback=None, sections_to_run=None, parallel_sections=False):
    """Run the full analysis and save results

    Args:
        sections_to_run: List of section dicts to generate. If None, uses all SECTIONS.
        parallel_sections: If True, run sections in parallel using ThreadPoolExecutor.
    """
    analysis_start = time.time()

    # Use provided sections or default to all
    if sections_to_run is None:
        sections_to_run = SECTIONS

    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    model_slug = re.sub(r'[^A-Za-z0-9_]', '-', model.split('/')[-1])
    model_slug = re.sub(r'-+', '-', model_slug)
    output_dir = ANALYSES_DIR / f"{project_name}-{model_slug}-{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save project spec
    (output_dir / "project-spec.md").write_text(project_data, encoding="utf-8")

    # Determine execution mode
    execution_mode = "parallel" if parallel_sections else "sequential"
    parallel_workers = min(MAX_PARALLEL_SECTIONS, len(sections_to_run)) if parallel_sections else 1

    # Initialize metadata
    metadata = {
        "project_name": project_name,
        "model": model,
        "timestamp": timestamp,
        "created_at": datetime.now().isoformat(),
        "sections": {},
        "sections_requested": [s["num"] for s in sections_to_run],
        "execution_mode": execution_mode,
        "parallel_workers": parallel_workers if parallel_sections else None,
        "max_retries": MAX_RETRIES,
        "timing": {},
        "cost": {},
        "failures": [],
        "status": "in_progress",
    }

    # Helper to save metadata incrementally (for progress tracking)
    def save_metadata():
        (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    # Write initial metadata so progress polling can find it
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

    if parallel_sections:
        # Parallel execution using ThreadPoolExecutor
        progress_callback(0, total_sections + 1, f"Starting parallel generation ({parallel_workers} workers)...")

        completed_count = 0

        with ThreadPoolExecutor(max_workers=parallel_workers) as executor:
            # Submit all section generation tasks
            future_to_section = {
                executor.submit(
                    generate_section, api_key, model, section, common_instructions, project_data, output_dir
                ): section
                for section in sections_to_run
            }

            # Process results as they complete
            for future in as_completed(future_to_section):
                section = future_to_section[future]
                section_key = f"section{section['num']}-{section['slug']}"

                try:
                    result = future.result()
                    completed_count += 1

                    # Track timing
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
                            "content": result["content"],
                            "elapsed": result["elapsed"],
                            "cost": section_cost,
                            "tokens": section_tokens,
                            "retries": result.get("retries", 0),
                        }
                        metadata["sections"][section_key] = {
                            "status": "success",
                            "words": result.get("words", 0),
                            "elapsed_seconds": result["elapsed"],
                            "cost": section_cost,
                            "tokens": section_tokens,
                            "prompt_tokens": result.get("prompt_tokens", 0),
                            "completion_tokens": result.get("completion_tokens", 0),
                            "retries": result.get("retries", 0),
                        }
                        if section_status_callback:
                            section_status_callback(section['name'], 'success', result["elapsed"])
                    else:
                        error_msg = result.get("error", "Unknown error")
                        results[section_key] = {
                            "success": False,
                            "error": error_msg,
                            "elapsed": result["elapsed"],
                            "cost": section_cost,
                            "tokens": section_tokens,
                            "retries": result.get("retries", 0),
                        }
                        metadata["sections"][section_key] = {
                            "status": "failed",
                            "error": error_msg,
                            "elapsed_seconds": result["elapsed"],
                            "cost": section_cost,
                            "tokens": section_tokens,
                            "retries": result.get("retries", 0),
                        }
                        failed_sections.append({
                            "section": result["section_name"],
                            "error": error_msg,
                            "retries": result.get("retries", 0),
                        })
                        if section_status_callback:
                            section_status_callback(section['name'], 'error', result["elapsed"])

                    # Save metadata incrementally for progress tracking
                    save_metadata()

                    # Update progress
                    total_elapsed = time.time() - analysis_start
                    cost_info = f" | Cost: {format_cost(total_cost)}" if total_cost > 0 else ""
                    retry_info = f" | Retries: {total_retries}" if total_retries > 0 else ""
                    progress_callback(
                        completed_count, total_sections + 1,
                        f"Completed {completed_count}/{total_sections} sections | Elapsed: {format_time(total_elapsed)}{cost_info}{retry_info}"
                    )

                except Exception as e:
                    completed_count += 1
                    error_msg = str(e)
                    results[section_key] = {"success": False, "error": error_msg, "elapsed": 0, "cost": 0, "tokens": 0}
                    metadata["sections"][section_key] = {"status": "failed", "error": error_msg, "elapsed_seconds": 0}
                    failed_sections.append({"section": f"{section['num']}. {section['name']}", "error": error_msg, "retries": 0})
                    save_metadata()  # Save even on exception
                    if section_status_callback:
                        section_status_callback(section['name'], 'error', 0)

    else:
        # Sequential execution (original behavior)
        for i, section in enumerate(sections_to_run):
            section_key = f"section{section['num']}-{section['slug']}"
            total_elapsed = time.time() - analysis_start

            # Calculate estimated time remaining based on average
            if section_times:
                avg_time = sum(section_times) / len(section_times)
                remaining_sections = total_sections - i
                est_remaining = avg_time * remaining_sections
                time_info = f" | Elapsed: {format_time(total_elapsed)} | Est. remaining: {format_time(est_remaining)}"
            else:
                time_info = f" | Elapsed: {format_time(total_elapsed)}"

            # Show running cost and retry count if available
            cost_info = f" | Cost: {format_cost(total_cost)}" if total_cost > 0 else ""
            retry_info = f" | Retries: {total_retries}" if total_retries > 0 else ""

            progress_callback(i, total_sections + 1, f"Generating {section['num']}. {section['name']}...{time_info}{cost_info}{retry_info}")

            if section_status_callback:
                section_status_callback(section['name'], 'running', None)

            # Generate section
            result = generate_section(api_key, model, section, common_instructions, project_data, output_dir)
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
                    "content": result["content"],
                    "elapsed": result["elapsed"],
                    "cost": section_cost,
                    "tokens": section_tokens,
                    "retries": result.get("retries", 0),
                }
                metadata["sections"][section_key] = {
                    "status": "success",
                    "words": result.get("words", 0),
                    "elapsed_seconds": result["elapsed"],
                    "cost": section_cost,
                    "tokens": section_tokens,
                    "prompt_tokens": result.get("prompt_tokens", 0),
                    "completion_tokens": result.get("completion_tokens", 0),
                    "retries": result.get("retries", 0),
                }
                if section_status_callback:
                    section_status_callback(section['name'], 'success', result["elapsed"])
            else:
                error_msg = result.get("error", "Unknown error")
                results[section_key] = {
                    "success": False,
                    "error": error_msg,
                    "elapsed": result["elapsed"],
                    "cost": section_cost,
                    "tokens": section_tokens,
                    "retries": result.get("retries", 0),
                }
                metadata["sections"][section_key] = {
                    "status": "failed",
                    "error": error_msg,
                    "elapsed_seconds": result["elapsed"],
                    "cost": section_cost,
                    "tokens": section_tokens,
                    "retries": result.get("retries", 0),
                }
                failed_sections.append({
                    "section": result["section_name"],
                    "error": error_msg,
                    "retries": result.get("retries", 0),
                })
                if section_status_callback:
                    section_status_callback(section['name'], 'error', result["elapsed"])

            # Save metadata incrementally for progress tracking
            save_metadata()

            # Small delay to avoid rate limits (sequential only)
            time.sleep(0.5)

    # Record failures in metadata
    metadata["failures"] = failed_sections

    # Generate provenance (section 20) with cost data and failure info
    total_elapsed = time.time() - analysis_start
    retry_info = f" | Total retries: {total_retries}" if total_retries > 0 else ""
    progress_callback(total_sections, total_sections + 1, f"Generating Provenance... | Total elapsed: {format_time(total_elapsed)} | Total cost: {format_cost(total_cost)}{retry_info}")

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
        project_name, model,
        cost_data=cost_data,
        timing_data=timing_data,
        execution_mode=execution_mode,
        parallel_workers=parallel_workers if parallel_sections else None,
        failed_sections=failed_sections,
    )
    (output_dir / "section20-provenance.html").write_text(provenance_html, encoding="utf-8")
    results["section20-provenance"] = {"success": True, "content": provenance_html}
    metadata["sections"]["section20-provenance"] = {"status": "success"}

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

    # Mark analysis complete and save final metadata
    metadata["status"] = "complete"
    save_metadata()

    fail_info = f" | {len(failed_sections)} failed" if failed_sections else ""
    retry_info = f" | {total_retries} retries" if total_retries > 0 else ""
    progress_callback(total_sections + 1, total_sections + 1, f"Analysis Complete! Total time: {format_time(total_time)} | Total cost: {format_cost(total_cost)}{fail_info}{retry_info}")

    return str(output_dir), results, total_time, total_cost


def regenerate_sections(api_key: str, analysis_path: str, sections_to_regenerate: list, progress_callback=None) -> dict:
    """Regenerate specific sections in an existing analysis folder.

    Args:
        api_key: OpenRouter API key
        analysis_path: Path to existing analysis folder
        sections_to_regenerate: List of section dicts to regenerate
        progress_callback: Optional callback(current, total, message)

    Returns:
        Dict with results: {section_key: {success, content/error, cost, ...}}
    """
    path = Path(analysis_path)
    metadata_file = path / "metadata.json"

    if not metadata_file.exists():
        return {"error": "Analysis metadata not found"}

    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    model = metadata.get("model", "")
    project_name = metadata.get("project_name", "")

    # Load project spec
    spec_file = path / "project-spec.md"
    if not spec_file.exists():
        return {"error": "Project spec not found"}
    project_data = spec_file.read_text(encoding="utf-8")

    # Load common instructions
    common_instructions = load_common_instructions()

    results = {}
    total = len(sections_to_regenerate)

    for i, section in enumerate(sections_to_regenerate):
        section_key = f"section{section['num']}-{section['slug']}"

        if progress_callback:
            progress_callback(i, total, f"Regenerating {section['num']}. {section['name']}...")

        # Generate section
        result = generate_section(api_key, model, section, common_instructions, project_data, path)

        if result["success"]:
            # Update metadata
            metadata["sections"][section_key] = {
                "status": "success",
                "words": result.get("words", 0),
                "elapsed_seconds": result["elapsed"],
                "cost": result.get("cost", 0),
                "tokens": result.get("tokens", 0),
                "prompt_tokens": result.get("prompt_tokens", 0),
                "completion_tokens": result.get("completion_tokens", 0),
                "retries": result.get("retries", 0),
                "regenerated_at": datetime.now().isoformat(),
            }
            results[section_key] = {"success": True, "elapsed": result["elapsed"], "cost": result.get("cost", 0)}
        else:
            metadata["sections"][section_key] = {
                "status": "failed",
                "error": result.get("error", "Unknown error"),
                "elapsed_seconds": result["elapsed"],
                "retries": result.get("retries", 0),
                "regenerated_at": datetime.now().isoformat(),
            }
            results[section_key] = {"success": False, "error": result.get("error")}

        # Save metadata incrementally
        metadata_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    # Remove regenerated sections from failures list
    regenerated_nums = [s["num"] for s in sections_to_regenerate]
    metadata["failures"] = [
        f for f in metadata.get("failures", [])
        if not any(f.get("section", "").startswith(num) for num in regenerated_nums)
    ]

    # Update cost totals
    section_costs = []
    total_cost = 0
    total_tokens = 0
    for sec_key, sec_data in metadata.get("sections", {}).items():
        if sec_key != "section20-provenance":
            cost = sec_data.get("cost", 0)
            tokens = sec_data.get("tokens", 0)
            total_cost += cost
            total_tokens += tokens
            # Extract section name from key
            sec_name = sec_key.replace("section", "").replace("-", ". ", 1).replace("-", " ").title()
            section_costs.append({"name": sec_name, "cost": cost, "tokens": tokens})

    metadata["cost"]["total_cost"] = total_cost
    metadata["cost"]["total_cost_formatted"] = format_cost(total_cost)
    metadata["cost"]["total_tokens"] = total_tokens
    metadata["cost"]["section_costs"] = section_costs

    # Save final metadata
    metadata_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    if progress_callback:
        progress_callback(total, total, "Regeneration complete!")

    return results


def get_past_analyses() -> list:
    """Get list of past analyses"""
    analyses = []
    if ANALYSES_DIR.exists():
        for dir_path in sorted(ANALYSES_DIR.iterdir(), reverse=True):
            if dir_path.is_dir():
                metadata_file = dir_path / "metadata.json"
                if metadata_file.exists():
                    try:
                        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
                        cost_info = metadata.get("cost", {})
                        timing_info = metadata.get("timing", {})
                        analyses.append({
                            "path": str(dir_path),
                            "name": dir_path.name,
                            "project_name": metadata.get("project_name", "Unknown"),
                            "model": metadata.get("model", "Unknown"),
                            "created_at": metadata.get("created_at", ""),
                            "sections": metadata.get("sections", {}),
                            "cost": cost_info.get("total_cost", 0),
                            "cost_formatted": cost_info.get("total_cost_formatted", "$0.00"),
                            "tokens": cost_info.get("total_tokens", 0),
                            "timing": timing_info,
                        })
                    except:
                        pass
    return analyses


def render_section_viewer(analysis_path: str, api_key: str = None):
    """Render section viewer for an analysis"""
    path = Path(analysis_path)

    # Load metadata
    metadata_file = path / "metadata.json"
    if not metadata_file.exists():
        st.error("Analysis metadata not found")
        return

    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))

    # Header
    st.markdown(f"### 🎯 {metadata.get('project_name', 'Analysis')}")

    # Build caption with available info
    caption_parts = [f"Model: `{metadata.get('model', 'Unknown')}`"]
    caption_parts.append(f"Generated: {metadata.get('created_at', 'Unknown')}")

    timing_info = metadata.get("timing", {})
    if timing_info.get("total_formatted"):
        caption_parts.append(f"⏱️ {timing_info['total_formatted']}")

    cost_info = metadata.get("cost", {})
    if cost_info.get("total_cost_formatted"):
        caption_parts.append(f"💰 {cost_info['total_cost_formatted']}")
    elif cost_info.get("total_cost", 0) > 0:
        caption_parts.append(f"💰 {format_cost(cost_info['total_cost'])}")

    st.caption(" | ".join(caption_parts))

    # Check for failed sections
    failed_sections = metadata.get("failures", [])
    sections_metadata = metadata.get("sections", {})

    # Also check sections with status "failed" in case failures list is out of sync
    failed_section_keys = [
        key for key, data in sections_metadata.items()
        if data.get("status") == "failed" and key != "section20-provenance"
    ]

    # Section navigation with grouping
    all_sections = SECTIONS + [{"num": "20", "name": "Provenance", "slug": "provenance", "group": "Meta"}]

    # Use selectbox for section navigation (better UX than 20 tabs)
    col1, col2 = st.columns([1, 3])

    with col1:
        # Group sections for easier navigation
        group_options = ["All Sections"] + list(SECTION_GROUPS.keys()) + ["Meta"]
        selected_group = st.selectbox("📂 Section Group", group_options, index=0)

        if selected_group == "All Sections":
            filtered_sections = all_sections
        else:
            filtered_sections = [s for s in all_sections if s.get("group") == selected_group]

        section_options = [f"{s['num']}. {s['name']}" for s in filtered_sections]
        selected_section_idx = st.selectbox(
            "📄 Select Section",
            range(len(section_options)),
            format_func=lambda x: section_options[x],
        )
        selected_section = filtered_sections[selected_section_idx]

        # Show section status indicator
        section_key = f"section{selected_section['num']}-{selected_section['slug']}"
        section_status = sections_metadata.get(section_key, {}).get("status", "unknown")
        if section_status == "success":
            st.caption("✅ Generated successfully")
        elif section_status == "failed":
            st.caption("❌ Generation failed")
        elif section_key not in sections_metadata:
            st.caption("⚪ Not generated")

        # Regeneration options
        st.divider()
        st.markdown("**🔄 Regeneration Options**")

        # Retry Failed Sections button
        if failed_section_keys:
            st.warning(f"⚠️ {len(failed_section_keys)} section(s) failed")
            if api_key:
                if st.button("🔄 Retry Failed Sections", type="primary", key="retry_failed"):
                    # Find the section dicts for failed sections
                    failed_to_retry = []
                    for key in failed_section_keys:
                        # Extract section num from key like "section07-technical-feasibility"
                        num = key.replace("section", "").split("-")[0]
                        section_dict = next((s for s in SECTIONS if s["num"] == num), None)
                        if section_dict:
                            failed_to_retry.append(section_dict)

                    if failed_to_retry:
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        def progress_cb(current, total, message):
                            progress_bar.progress(current / total if total > 0 else 0)
                            status_text.info(f"⏳ {message}")

                        results = regenerate_sections(api_key, analysis_path, failed_to_retry, progress_cb)

                        success_count = sum(1 for r in results.values() if isinstance(r, dict) and r.get("success"))
                        if success_count == len(failed_to_retry):
                            st.success(f"✅ All {success_count} sections regenerated successfully!")
                        else:
                            st.warning(f"⚠️ {success_count}/{len(failed_to_retry)} sections regenerated")
                        st.rerun()
            else:
                st.info("Enter API key in sidebar to retry")

        # Regenerate single section dropdown
        st.markdown("**Regenerate specific section:**")
        regen_options = ["Select section..."] + [f"{s['num']}. {s['name']}" for s in SECTIONS]
        selected_regen = st.selectbox(
            "Section to regenerate",
            regen_options,
            index=0,
            key="regen_section_select",
            label_visibility="collapsed",
        )

        if selected_regen != "Select section..." and api_key:
            # Find the section dict
            regen_num = selected_regen.split(".")[0]
            section_to_regen = next((s for s in SECTIONS if s["num"] == regen_num), None)

            if section_to_regen:
                if st.button(f"🔄 Regenerate {selected_regen}", key="regen_single"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    def progress_cb(current, total, message):
                        progress_bar.progress(current / total if total > 0 else 0)
                        status_text.info(f"⏳ {message}")

                    results = regenerate_sections(api_key, analysis_path, [section_to_regen], progress_cb)

                    if results.get(f"section{section_to_regen['num']}-{section_to_regen['slug']}", {}).get("success"):
                        st.success(f"✅ Section regenerated successfully!")
                    else:
                        error = results.get(f"section{section_to_regen['num']}-{section_to_regen['slug']}", {}).get("error", "Unknown error")
                        st.error(f"❌ Failed: {error}")
                    st.rerun()
        elif selected_regen != "Select section..." and not api_key:
            st.info("Enter API key in sidebar to regenerate")

    with col2:
        # Display selected section
        section_file = path / f"section{selected_section['num']}-{selected_section['slug']}.html"
        if section_file.exists():
            content = section_file.read_text(encoding="utf-8")
            # Clean any markdown fences from content
            content = clean_html_output(content)
            # Render HTML in iframe-like container
            st.components.v1.html(
                f"""
                <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
                    {content}
                </div>
                """,
                height=800,
                scrolling=True,
            )
        else:
            st.warning(f"Section not available: {selected_section['name']}")
            # Check for legacy section09-provenance.html
            if selected_section['num'] == '20':
                legacy_file = path / "section09-provenance.html"
                if legacy_file.exists():
                    content = legacy_file.read_text(encoding="utf-8")
                    content = clean_html_output(content)
                    st.components.v1.html(
                        f'<div style="font-family: -apple-system, sans-serif;">{content}</div>',
                        height=800,
                        scrolling=True,
                    )


def main():
    """Main application"""
    st.set_page_config(
        page_title="VenturePulse - AI Product Analysis",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    init_session_state()
    
    # Custom CSS
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 2rem;
        }
        .main-header h1 {
            margin: 0;
            font-size: 2.5rem;
        }
        .main-header p {
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
        }
        .stProgress > div > div > div > div {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .success-box {
            background: #d4edda;
            border-left: 4px solid #28a745;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
        }
        .error-box {
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
        }
        /* Style sidebar buttons as text links */
        [data-testid="stSidebar"] button[kind="secondary"] {
            background: none !important;
            border: none !important;
            padding: 0 !important;
            color: #0066cc !important;
            text-decoration: underline !important;
            cursor: pointer !important;
            font-size: 0.9rem !important;
        }
        [data-testid="stSidebar"] button[kind="secondary"]:hover {
            color: #004499 !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎯 VenturePulse</h1>
        <p>AI-Powered Product Viability Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key handling - hide if loaded from env or confirmed
        api_key_env = os.environ.get("OPENROUTER_API_KEY", "")
        
        if api_key_env:
            # Key from environment - don't show anything
            api_key = api_key_env
            st.session_state.api_key_confirmed = True
        elif st.session_state.api_key_confirmed and st.session_state.api_key:
            # Key was entered and confirmed - just show status
            api_key = st.session_state.api_key
            with st.expander("🔑 API Key (configured)", expanded=False):
                st.success("✅ API Key configured")
                if st.button("Change API Key"):
                    st.session_state.api_key_confirmed = False
                    st.rerun()
        else:
            # Need to enter key
            api_key = st.text_input(
                "🔑 OpenRouter API Key",
                type="password",
                value=st.session_state.api_key,
                help="Get your key at https://openrouter.ai/keys",
            )
            if api_key:
                st.session_state.api_key = api_key
                if st.button("✅ Confirm API Key"):
                    st.session_state.api_key_confirmed = True
                    st.rerun()
        
        # Model selection
        st.subheader("🤖 Model Selection")
        
        # Multi-model selection
        selected_models = st.multiselect(
            "Select Models",
            POPULAR_MODELS,
            default=[DEFAULT_MODEL],
            help="Select one or more models to run analysis with",
        )
        
        # Custom model input
        custom_model = st.text_input(
            "Add Custom Model",
            value="",
            placeholder="e.g., anthropic/claude-3-opus",
            help="Enter OpenRouter model path and press Enter",
        )
        
        if custom_model and custom_model not in selected_models:
            if st.button("➕ Add Custom Model", key="add_custom"):
                selected_models.append(custom_model)
        
        # Store models in session state
        if "selected_models" not in st.session_state:
            st.session_state.selected_models = selected_models
        st.session_state.selected_models = selected_models + ([custom_model] if custom_model and custom_model not in selected_models else [])
        
        # Execution mode for multiple models
        if len(st.session_state.selected_models) > 1:
            st.divider()
            st.subheader("⚡ Execution Mode")
            execution_mode = st.radio(
                "Run models:",
                ["Sequential", "Parallel"],
                help="Sequential: one after another (safer, lower cost). Parallel: all at once (faster, uses more API quota).",
                horizontal=True,
            )
            st.session_state.execution_mode = execution_mode
        else:
            st.session_state.execution_mode = "Sequential"
        
        st.divider()
        
        # Past Analyses with delete option
        st.subheader("📚 Past Analyses")
        past_analyses = get_past_analyses()
        
        if past_analyses:
            # Group by project name
            projects = {}
            for analysis in past_analyses:
                proj = analysis["project_name"]
                if proj not in projects:
                    projects[proj] = []
                projects[proj].append(analysis)
            
            for proj_name, proj_analyses in projects.items():
                with st.expander(f"{proj_name} ({len(proj_analyses)} runs)", expanded=False):
                    for analysis in proj_analyses[:5]:  # Show last 5 per project
                        model_short = analysis['model'].split('/')[-1]
                        # Format datetime with HH:MM using stored timestamp (already local)
                        if analysis['created_at']:
                            try:
                                dt = datetime.fromisoformat(analysis['created_at'])
                                # Convert to local timezone if tzinfo present
                                if dt.tzinfo:
                                    dt = dt.astimezone()
                                dt_str = dt.strftime("%Y-%m-%d %H:%M")
                            except Exception:
                                dt_str = analysis['created_at'][:16].replace('T', ' ')
                        else:
                            dt_str = ''
                        
                        # Single line: model - datetime
                        st.markdown(f"**{model_short}** — {dt_str}")
                        
                        # Text links as clickable markdown (using small buttons styled like links)
                        view_clicked = st.button("View Results →", key=f"view_{analysis['path']}", 
                                                  type="tertiary" if hasattr(st, 'button') else "secondary")
                        if view_clicked:
                            st.session_state.current_analysis = analysis["path"]
                            st.session_state.active_tab = 1
                            st.rerun()
                        
                        del_clicked = st.button("Delete", key=f"del_{analysis['path']}", 
                                                type="tertiary" if hasattr(st, 'button') else "secondary")
                        if del_clicked:
                            st.session_state[f"confirm_delete_{analysis['path']}"] = True
                        
                        # Confirmation
                        if st.session_state.get(f"confirm_delete_{analysis['path']}", False):
                            st.error("Delete this run?")
                            c1, c2 = st.columns(2)
                            with c1:
                                if st.button("Yes", key=f"yes_{analysis['path']}"):
                                    if delete_analysis(analysis["path"]):
                                        del st.session_state[f"confirm_delete_{analysis['path']}"]
                                        st.rerun()
                            with c2:
                                if st.button("No", key=f"no_{analysis['path']}"):
                                    del st.session_state[f"confirm_delete_{analysis['path']}"]
                                    st.rerun()
                        
                        st.write("")  # Spacer
        else:
            st.info("No past analyses found")
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["📝 New Analysis", "📊 View Results", "🔬 Compare Results"])
    
    with tab1:
        if not api_key:
            st.warning("⚠️ Please enter your OpenRouter API key in the sidebar to start analysis.")
        elif not st.session_state.api_key_confirmed:
            st.warning("⚠️ Please confirm your API key in the sidebar.")
        else:
            # Check if we have an existing project to add runs to
            past_analyses = get_past_analyses()
            existing_projects = {}
            for a in past_analyses:
                if a["project_name"] not in existing_projects:
                    existing_projects[a["project_name"]] = a
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Option to use existing project or new
                if existing_projects:
                    use_existing = st.radio(
                        "Project Source",
                        ["New Project", "Add Run to Existing Project"],
                        horizontal=True,
                    )
                else:
                    use_existing = "New Project"
                
                if use_existing == "Add Run to Existing Project" and existing_projects:
                    selected_project = st.selectbox(
                        "Select Existing Project",
                        list(existing_projects.keys()),
                    )
                    
                    if selected_project:
                        # Load spec from existing project
                        existing_path = Path(existing_projects[selected_project]["path"])
                        spec_file = existing_path / "project-spec.md"
                        if spec_file.exists():
                            project_spec = spec_file.read_text(encoding="utf-8")
                            project_name = selected_project
                            st.session_state.spec_collapsed = True
                            with st.expander("📄 Project Specification (click to expand)", expanded=False):
                                st.text_area("Spec (read-only)", project_spec, height=200, disabled=True)
                            st.success(f"✅ Loaded spec from: {selected_project}")
                        else:
                            project_spec = ""
                            st.error("Could not find original spec file")
                else:
                    # New project - upload or paste
                    spec_expanded = not st.session_state.spec_collapsed
                    
                    with st.expander("📄 Project Specification", expanded=spec_expanded):
                        uploaded_file = st.file_uploader(
                            "Upload your project spec (Markdown or Text)",
                            type=["md", "txt"],
                            help="Upload a markdown or text file describing your product/project idea",
                        )
                        
                        st.markdown("**Or paste your specification:**")
                        project_spec = st.text_area(
                            "Project Specification",
                            height=250,
                            placeholder="Describe your product idea, target market, key features, etc...",
                            label_visibility="collapsed",
                        )
                        
                        # Use uploaded file if available
                        if uploaded_file:
                            project_spec = uploaded_file.read().decode("utf-8")
                            st.success(f"✅ Loaded: {uploaded_file.name}")
                        
                        if project_spec:
                            if st.button("✅ Confirm Spec"):
                                st.session_state.spec_collapsed = True
                                st.rerun()
                    
                    project_name = st.text_input(
                        "Project Name",
                        value=st.session_state.current_project_name or "my-project",
                        help="Short name for your project (used in filenames)",
                    )
                    project_name = re.sub(r'[^a-zA-Z0-9-]', '-', project_name).lower()
                    st.session_state.current_project_name = project_name
            
            with col2:
                st.subheader("Analysis Settings")

                models_to_run = st.session_state.get("selected_models", [DEFAULT_MODEL])
                exec_mode = st.session_state.get("execution_mode", "Sequential")

                # Display selected models
                st.markdown(f"**Selected Models ({len(models_to_run)}):**")
                for m in models_to_run:
                    st.markdown(f"• `{m}`")

                st.markdown(f"**Execution Mode:** {exec_mode}")

                # Parallel section execution toggle
                st.divider()
                parallel_sections = st.toggle(
                    "⚡ Parallel Section Generation",
                    value=False,
                    help=f"Generate sections in parallel using up to {MAX_PARALLEL_SECTIONS} workers. Faster but uses more API quota simultaneously.",
                )
                st.session_state.parallel_sections = parallel_sections
                if parallel_sections:
                    st.caption(f"Using up to {MAX_PARALLEL_SECTIONS} parallel workers (configurable via MAX_PARALLEL_SECTIONS env var)")

                # Section selection
                st.divider()
                analysis_type = st.radio(
                    "📊 Analysis Depth",
                    ["Full Analysis (19 sections)", "Quick Analysis (7 sections)", "Custom"],
                    help="Full: Comprehensive VC-ready analysis. Quick: Core validation sections. Custom: Choose your own.",
                    horizontal=True,
                )

                if analysis_type == "Full Analysis (19 sections)":
                    selected_section_nums = [s["num"] for s in SECTIONS]
                elif analysis_type == "Quick Analysis (7 sections)":
                    selected_section_nums = QUICK_SECTIONS
                else:
                    # Custom selection
                    with st.expander("🔧 Select Sections", expanded=True):
                        selected_section_nums = []
                        for group_name in SECTION_GROUPS.keys():
                            st.caption(f"**{group_name}:** {SECTION_GROUPS[group_name]}")
                            group_sections = [s for s in SECTIONS if s["group"] == group_name]
                            for s in group_sections:
                                if st.checkbox(f"{s['num']}. {s['name']}", value=s["num"] in QUICK_SECTIONS, key=f"sec_{s['num']}"):
                                    selected_section_nums.append(s["num"])

                # Store selected sections
                st.session_state.selected_section_nums = selected_section_nums
                sections_to_run = [s for s in SECTIONS if s["num"] in selected_section_nums]

                with st.expander(f"📋 Sections to Generate ({len(sections_to_run)} + Provenance)", expanded=False):
                    for group_name in ["Foundation", "Strategy", "Execution", "Future"]:
                        group_secs = [s for s in sections_to_run if s["group"] == group_name]
                        if group_secs:
                            st.markdown(f"**{group_name}:**")
                            for s in group_secs:
                                st.markdown(f"- {s['num']}. {s['name']}")
            
            st.divider()
            
            # Run analysis button
            models_to_run = st.session_state.get("selected_models", [])
            if not models_to_run:
                st.warning("⚠️ Please select at least one model in the sidebar.")
            elif st.button("🚀 Start Analysis", type="primary", disabled=not project_spec or st.session_state.is_analyzing):
                if not project_spec.strip():
                    st.error("Please provide a project specification")
                else:
                    st.session_state.is_analyzing = True
                    st.session_state.spec_collapsed = True  # Collapse spec during analysis
                    exec_mode = st.session_state.get("execution_mode", "Sequential")
                    use_parallel_sections = st.session_state.get("parallel_sections", False)

                    all_results = {}

                    # Get sections to run
                    sections_to_run = [s for s in SECTIONS if s["num"] in st.session_state.get("selected_section_nums", [s["num"] for s in SECTIONS])]
                    num_sections = len(sections_to_run) + 1  # +1 for provenance

                    if exec_mode == "Sequential":
                        # Sequential execution - run one model at a time
                        for model_idx, model in enumerate(models_to_run):
                            st.markdown(f"### 🤖 Model {model_idx + 1}/{len(models_to_run)}: `{model}`")

                            # Create compact progress display
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            section_list = st.empty()

                            def progress_callback(current, total, message):
                                progress = current / total
                                progress_bar.progress(progress)
                                status_text.info(f"⏳ {message}")
                                # Show compact section progress
                                completed = "✅ " * current
                                remaining = "⏳ " * (total - current)
                                section_list.caption(f"Progress: {completed}{remaining} ({current}/{total})")

                            try:
                                output_dir, results, total_time, total_cost = run_analysis(
                                    api_key, model, project_name, project_spec, progress_callback,
                                    sections_to_run=sections_to_run,
                                    parallel_sections=use_parallel_sections
                                )

                                all_results[model] = {
                                    "output_dir": output_dir,
                                    "results": results,
                                    "total_time": total_time,
                                    "total_cost": total_cost,
                                    "success": True,
                                }

                                successful = sum(1 for r in results.values() if r.get("success"))
                                cost_str = f" | 💰 {format_cost(total_cost)}" if total_cost > 0 else ""
                                st.success(f"✅ {model}: Complete! ({successful}/{num_sections} sections, {format_time(total_time)}{cost_str})")
                                
                            except Exception as e:
                                all_results[model] = {"success": False, "error": str(e)}
                                st.error(f"❌ {model}: Failed - {str(e)}")
                    
                    else:
                        # Parallel execution using threading
                        import concurrent.futures

                        st.info(f"🚀 Running {len(models_to_run)} models in parallel...")
                        progress_containers = {}

                        for model in models_to_run:
                            with st.container():
                                st.markdown(f"**{model}**")
                                progress_containers[model] = {
                                    "progress": st.progress(0),
                                    "status": st.empty(),
                                }

                        # Capture sections_to_run for closure
                        sections_for_parallel = sections_to_run
                        use_parallel_for_closure = use_parallel_sections

                        def run_model_analysis(model):
                            def progress_callback(current, total, message):
                                # Can't update Streamlit UI from threads, but file writes still happen
                                pass

                            try:
                                output_dir, results, total_time, total_cost = run_analysis(
                                    api_key, model, project_name, project_spec, progress_callback,
                                    sections_to_run=sections_for_parallel,
                                    parallel_sections=use_parallel_for_closure
                                )
                                return {
                                    "model": model,
                                    "output_dir": output_dir,
                                    "results": results,
                                    "total_time": total_time,
                                    "total_cost": total_cost,
                                    "success": True,
                                }
                            except Exception as e:
                                return {"model": model, "success": False, "error": str(e)}

                        # Start all models in parallel
                        with concurrent.futures.ThreadPoolExecutor(max_workers=len(models_to_run)) as executor:
                            futures = {executor.submit(run_model_analysis, model): model for model in models_to_run}

                            # Poll for progress updates by checking metadata files
                            completed = set()
                            while len(completed) < len(models_to_run):
                                for model in models_to_run:
                                    if model in completed:
                                        continue

                                    # Try to read metadata.json to check progress
                                    model_slug = re.sub(r'[^A-Za-z0-9_]', '-', model.split('/')[-1])
                                    model_slug = re.sub(r'-+', '-', model_slug)

                                    # Find the latest analysis folder for this model
                                    matching_dirs = [d for d in ANALYSES_DIR.glob(f"{project_name}-{model_slug}-*") if d.is_dir()]
                                    if matching_dirs:
                                        latest_dir = max(matching_dirs, key=lambda d: d.name)
                                        metadata_path = latest_dir / "metadata.json"

                                        if metadata_path.exists():
                                            try:
                                                with open(metadata_path, "r", encoding="utf-8") as f:
                                                    metadata = json.load(f)
                                                    # Count both success and failed sections as completed
                                                    sections_done = sum(1 for s in metadata.get("sections", {}).values() if s.get("status") in ("success", "failed"))
                                                    progress = sections_done / num_sections

                                                    progress_containers[model]["progress"].progress(progress)
                                                    if sections_done < num_sections:
                                                        status_text = metadata.get("status", "in_progress")
                                                        progress_containers[model]["status"].info(
                                                            f"⏳ {sections_done}/{num_sections} sections complete"
                                                        )
                                            except Exception:
                                                pass
                                
                                # Check if any futures completed
                                for future in concurrent.futures.as_completed(futures, timeout=0.5):
                                    result = future.result()
                                    model = result["model"]
                                    if model not in completed:
                                        completed.add(model)
                                        all_results[model] = result
                                        
                                        if result["success"]:
                                            progress_containers[model]["progress"].progress(1.0)
                                            successful = sum(1 for r in result["results"].values() if r.get("success"))
                                            cost_str = f" | 💰 {format_cost(result.get('total_cost', 0))}" if result.get('total_cost', 0) > 0 else ""
                                            progress_containers[model]["status"].success(
                                                f"✅ Complete! ({successful}/{num_sections} sections, {format_time(result['total_time'])}{cost_str})"
                                            )
                                        else:
                                            progress_containers[model]["status"].error(f"❌ Failed: {result['error']}")
                                    break  # Process one completion per loop iteration
                                
                                if len(completed) < len(models_to_run):
                                    time.sleep(1)  # Poll every second
                    
                    # Store results for comparison
                    st.session_state.multi_model_results = all_results
                    st.session_state.is_analyzing = False
                    
                    # Set first successful analysis as current
                    for model, result in all_results.items():
                        if result.get("success"):
                            st.session_state.current_analysis = result["output_dir"]
                            break
                    
                    # Summary
                    st.divider()
                    st.subheader("📊 Analysis Summary")

                    success_count = sum(1 for r in all_results.values() if r.get("success"))
                    total_analysis_cost = sum(r.get("total_cost", 0) for r in all_results.values() if r.get("success"))

                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Models Run", len(models_to_run))
                    col2.metric("Successful", success_count)
                    col3.metric("Failed", len(models_to_run) - success_count)
                    col4.metric("Total Cost", format_cost(total_analysis_cost))
                    
                    if success_count > 1:
                        st.info("💡 Multiple analyses complete! Use the **Compare Results** tab to compare outputs.")
                    
                    # Auto-navigate to View Results
                    if st.button("📊 View Results", type="primary"):
                        st.session_state.active_tab = 1  # View Results tab
                        st.rerun()
    
    with tab2:
        if st.session_state.current_analysis:
            render_section_viewer(st.session_state.current_analysis, api_key=api_key)
        else:
            st.info("👆 Run a new analysis or select a past analysis from the sidebar to view results.")
            
            # Quick access to recent analyses
            past_analyses = get_past_analyses()
            if past_analyses:
                st.subheader("Recent Analyses")
                cols = st.columns(3)
                for i, analysis in enumerate(past_analyses[:6]):
                    with cols[i % 3]:
                        with st.container(border=True):
                            st.markdown(f"**{analysis['project_name']}**")
                            st.caption(f"Model: {analysis['model']}")
                            if st.button("View", key=f"quick_{analysis['path']}"):
                                st.session_state.current_analysis = analysis["path"]
                                st.rerun()
    
    # Comparison tab (tab3)
    with tab3:
        st.subheader("🔬 Model Comparison")
        
        # Get available analyses for comparison
        past_analyses = get_past_analyses()
        
        if len(past_analyses) < 2:
            st.info("Run analyses with multiple models to compare results here. You need at least 2 analyses to compare.")
        else:
            st.markdown("Select analyses to compare side-by-side:")
            
            # Group analyses by project name
            projects = {}
            for analysis in past_analyses:
                proj = analysis["project_name"]
                if proj not in projects:
                    projects[proj] = []
                projects[proj].append(analysis)
            
            # Project selector
            selected_project = st.selectbox(
                "Select Project",
                list(projects.keys()),
                help="Choose a project to compare its analyses across different models",
            )
            
            if selected_project and len(projects[selected_project]) >= 2:
                project_analyses = projects[selected_project]
                
                # Analysis selector (multi-select)
                analysis_options = {
                    f"{a['model']} ({a['created_at'][:10] if a['created_at'] else 'Unknown'})": a
                    for a in project_analyses
                }
                
                selected_analyses = st.multiselect(
                    "Select Analyses to Compare",
                    list(analysis_options.keys()),
                    default=list(analysis_options.keys())[:2],
                    max_selections=4,
                    help="Select 2-4 analyses to compare",
                )
                
                if len(selected_analyses) >= 2:
                    # Section selector for comparison
                    all_sections = SECTIONS + [{"num": "09", "name": "Provenance", "slug": "provenance"}]
                    section_to_compare = st.selectbox(
                        "Select Section to Compare",
                        [s["name"] for s in all_sections],
                        index=0,
                    )
                    
                    # Find the section details
                    section_info = next(s for s in all_sections if s["name"] == section_to_compare)
                    section_filename = f"section{section_info['num']}-{section_info['slug']}.html"
                    
                    st.divider()
                    
                    # Comparison view mode
                    view_mode = st.radio(
                        "View Mode",
                        ["Side by Side", "Tabbed"],
                        horizontal=True,
                    )
                    
                    if view_mode == "Side by Side":
                        # Create columns for each analysis
                        cols = st.columns(len(selected_analyses))
                        
                        for i, (analysis_key, col) in enumerate(zip(selected_analyses, cols)):
                            analysis = analysis_options[analysis_key]
                            
                            with col:
                                st.markdown(f"**{analysis['model']}**")
                                
                                # Load timing and cost info if available
                                metadata_file = Path(analysis["path"]) / "metadata.json"
                                if metadata_file.exists():
                                    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
                                    timing = metadata.get("timing", {})
                                    cost = metadata.get("cost", {})
                                    info_parts = []
                                    if timing.get("total_formatted"):
                                        info_parts.append(f"⏱️ {timing['total_formatted']}")
                                    if cost.get("total_cost_formatted"):
                                        info_parts.append(f"💰 {cost['total_cost_formatted']}")
                                    elif cost.get("total_cost", 0) > 0:
                                        info_parts.append(f"💰 {format_cost(cost['total_cost'])}")
                                    if info_parts:
                                        st.caption(" | ".join(info_parts))
                                
                                # Load section content
                                section_file = Path(analysis["path"]) / section_filename
                                if section_file.exists():
                                    content = section_file.read_text(encoding="utf-8")
                                    st.components.v1.html(
                                        f'<div style="font-family: -apple-system, sans-serif; font-size: 12px;">{content}</div>',
                                        height=600,
                                        scrolling=True,
                                    )
                                else:
                                    st.warning("Section not available")
                    
                    else:  # Tabbed view
                        tabs = st.tabs([analysis_options[k]["model"][:30] for k in selected_analyses])

                        for tab, analysis_key in zip(tabs, selected_analyses):
                            analysis = analysis_options[analysis_key]

                            with tab:
                                # Load timing and cost info
                                metadata_file = Path(analysis["path"]) / "metadata.json"
                                if metadata_file.exists():
                                    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
                                    timing = metadata.get("timing", {})
                                    cost = metadata.get("cost", {})
                                    info_parts = []
                                    if timing.get("total_formatted"):
                                        info_parts.append(f"⏱️ Total: {timing['total_formatted']}")
                                    if timing.get("avg_section_seconds"):
                                        info_parts.append(f"Avg/section: {format_time(timing['avg_section_seconds'])}")
                                    if cost.get("total_cost_formatted"):
                                        info_parts.append(f"💰 {cost['total_cost_formatted']}")
                                    elif cost.get("total_cost", 0) > 0:
                                        info_parts.append(f"💰 {format_cost(cost['total_cost'])}")
                                    if info_parts:
                                        st.caption(" | ".join(info_parts))
                                
                                # Load section content
                                section_file = Path(analysis["path"]) / section_filename
                                if section_file.exists():
                                    content = section_file.read_text(encoding="utf-8")
                                    st.components.v1.html(
                                        f'<div style="font-family: -apple-system, sans-serif;">{content}</div>',
                                        height=700,
                                        scrolling=True,
                                    )
                                else:
                                    st.warning("Section not available")
                    
                    # Timing and Cost comparison table
                    st.divider()
                    st.subheader("⏱️ Timing & 💰 Cost Comparison")

                    comparison_data = []
                    for analysis_key in selected_analyses:
                        analysis = analysis_options[analysis_key]
                        metadata_file = Path(analysis["path"]) / "metadata.json"
                        if metadata_file.exists():
                            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
                            timing = metadata.get("timing", {})
                            cost = metadata.get("cost", {})
                            comparison_data.append({
                                "Model": analysis["model"],
                                "Total Time": timing.get("total_formatted", "N/A"),
                                "Time (sec)": round(timing.get("total_seconds", 0), 1),
                                "Avg/Section (sec)": round(timing.get("avg_section_seconds", 0), 1),
                                "Total Cost": cost.get("total_cost_formatted", "$0.00"),
                                "Tokens": f"{cost.get('total_tokens', 0):,}",
                            })

                    if comparison_data:
                        import pandas as pd
                        df = pd.DataFrame(comparison_data)
                        st.dataframe(df, width='stretch', hide_index=True)
                
                else:
                    st.info("Select at least 2 analyses to compare.")
            
            elif selected_project:
                st.info(f"Only 1 analysis found for '{selected_project}'. Run with more models to compare.")


if __name__ == "__main__":
    main()
