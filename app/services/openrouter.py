"""
OpenRouter API service for VenturePulse v2.
Handles API calls to OpenRouter with retry logic and cost tracking.
"""

import logging
import time
import random
from typing import Tuple, Dict, Optional
import httpx

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2  # Base delay in seconds for exponential backoff
RETRY_JITTER_MAX = 2  # Maximum random jitter in seconds

# API configuration
API_TIMEOUT = 600  # 10 minutes for slower models
MAX_TOKENS = 25192
TEMPERATURE = 0.7
TOP_P = 0.95


def is_retryable_error(error_code: str, error_message: str) -> bool:
    """Determine if an error is transient and should be retried."""
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
    """Calculate delay with exponential backoff and jitter."""
    # Exponential backoff: base_delay * (2 ^ attempt)
    base_delay = RETRY_BASE_DELAY * (2 ** attempt)
    # Add random jitter to prevent thundering herd
    jitter = random.uniform(0, RETRY_JITTER_MAX)
    return base_delay + jitter


async def fetch_generation_cost(api_key: str, generation_id: str) -> Optional[Dict]:
    """Fetch cost/usage info for a generation via separate API call."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://openrouter.ai/api/v1/generation?id={generation_id}",
                headers={"Authorization": f"Bearer {api_key}"},
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
    except Exception as e:
        logger.debug(f"Failed to fetch generation cost: {e}")
    return None


async def call_openrouter(
    api_key: str,
    model: str,
    prompt: str,
) -> Tuple[bool, str, float, Dict]:
    """
    Call OpenRouter API with retry logic.

    Args:
        api_key: OpenRouter API key
        model: Model name (e.g., "anthropic/claude-sonnet-4")
        prompt: The prompt to send

    Returns:
        Tuple of (success, content, elapsed_seconds, usage_info)

        usage_info contains:
            - prompt_tokens: int
            - completion_tokens: int
            - total_tokens: int
            - cost: float (in USD, if available from API)
            - retries: int (number of retry attempts made)
    """
    start_time = time.time()
    empty_usage = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "cost": 0.0,
        "retries": 0,
    }

    last_error = None

    for attempt in range(MAX_RETRIES + 1):  # +1 for initial attempt
        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}",
                        "HTTP-Referer": "https://github.com/knightsri/VenturePulse",
                        "X-Title": "VenturePulse v2.0",
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": MAX_TOKENS,
                        "temperature": TEMPERATURE,
                        "top_p": TOP_P,
                        "usage": {"include": True},  # Request cost/usage info in response
                    },
                )

                data = response.json()

                if "error" in data:
                    error_msg = data["error"].get("message", "Unknown error")
                    error_code = data["error"].get("code", "unknown")
                    last_error = error_msg

                    # Check if error is retryable
                    if attempt < MAX_RETRIES and is_retryable_error(error_code, error_msg):
                        delay = calculate_retry_delay(attempt)
                        logger.warning(f"Retryable error ({error_code}): {error_msg}. Retrying in {delay:.1f}s...")
                        await asyncio.sleep(delay)
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

                # Extract cost from usage object
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
                    await asyncio.sleep(0.5)
                    gen_usage = await fetch_generation_cost(api_key, generation_id)
                    if gen_usage and gen_usage.get("cost", 0) > 0:
                        gen_usage["retries"] = attempt
                        usage_info = gen_usage

                elapsed = time.time() - start_time
                return True, content, elapsed, usage_info

        except httpx.TimeoutException:
            last_error = "Request timed out"
            if attempt < MAX_RETRIES:
                delay = calculate_retry_delay(attempt)
                logger.warning(f"Timeout. Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
                continue
            elapsed = time.time() - start_time
            empty_usage["retries"] = attempt
            return False, "Request timed out (10 min limit). Try a faster model or shorter spec.", elapsed, empty_usage

        except httpx.RequestError as e:
            last_error = str(e)
            if attempt < MAX_RETRIES:
                delay = calculate_retry_delay(attempt)
                logger.warning(f"Network error: {e}. Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
                continue
            elapsed = time.time() - start_time
            empty_usage["retries"] = attempt
            return False, f"Network error: {str(e)}", elapsed, empty_usage

        except Exception as e:
            last_error = str(e)
            elapsed = time.time() - start_time
            empty_usage["retries"] = attempt
            logger.exception(f"Unexpected error in call_openrouter: {e}")
            return False, f"Unexpected error: {str(e)}", elapsed, empty_usage

    # Should not reach here, but just in case
    elapsed = time.time() - start_time
    empty_usage["retries"] = MAX_RETRIES
    return False, f"Max retries exceeded. Last error: {last_error}", elapsed, empty_usage


# Need to import asyncio for sleep
import asyncio
