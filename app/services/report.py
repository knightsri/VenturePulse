"""
Report generation service for VenturePulse v2.
Handles HTML output cleanup, formatting, and provenance generation.
"""

import html
from datetime import datetime
from typing import Dict, List, Optional


def clean_html_output(content: str) -> str:
    """Clean LLM output by removing markdown code fences."""
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


def format_cost(cost: float) -> str:
    """Format cost in USD with appropriate precision."""
    if cost == 0:
        return "$0.00"
    elif cost < 0.01:
        return f"${cost:.4f}"
    elif cost < 1:
        return f"${cost:.3f}"
    else:
        return f"${cost:.2f}"


def format_time(seconds: float) -> str:
    """Format seconds into human readable string."""
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


def generate_provenance(
    project_name: str,
    model: str,
    cost_data: Optional[Dict] = None,
    timing_data: Optional[Dict] = None,
    execution_mode: str = None,
    parallel_workers: int = None,
    failed_sections: Optional[List[Dict]] = None,
) -> str:
    """
    Generate provenance HTML section with cost, timing, and execution information.

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
            <h3 style="color: #2d3748; font-size: 1.3rem; margin-bottom: 1rem;">Cost Breakdown{retry_note}</h3>
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
            <h3 style="color: #2d3748; font-size: 1.3rem; margin-bottom: 1rem;">Cost</h3>
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
            <h3 style="color: #721c24; font-size: 1.3rem; margin-bottom: 1rem;">Failed Sections ({len(failed_sections)})</h3>
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
        <h2 style="color: #2d3748; font-size: 1.8rem; border-bottom: 3px solid #1E88E5; padding-bottom: 0.5rem;">
            Analysis Provenance
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
                    <td style="padding: 0.75rem;">VenturePulse v2.0</td>
                </tr>
            </table>
        </div>

        {cost_section}

        {failures_section}

        <div style="margin-top: 2rem; padding: 1rem; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;">
            <strong>Disclaimer:</strong> This analysis was generated by AI and should be used as a starting point for decision-making, not as definitive business advice. Always validate assumptions with real market research and domain experts.
        </div>
    </div>
    '''
