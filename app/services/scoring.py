"""
Score extraction service for VenturePulse comparison feature.

Extracts metrics from analyses and calculates proxy quality scores
for visualization in the comparison dashboard.
"""

import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Section to dimension mapping for proxy scores
DIMENSION_SECTIONS = {
    "market": ["section02-market-landscape", "section03-user-stories"],
    "technical": ["section07-technical-feasibility"],
    "competitive": ["section04-comparable-companies", "section08-competitive-advantage"],
    "business": ["section09-business-model"],
    "execution": ["section11-mvp-roadmap", "section13-go-to-market"],
}

# All known section keys (for word count extraction)
ALL_SECTIONS = [
    "section01-executive-summary",
    "section02-market-landscape",
    "section03-user-stories",
    "section04-comparable-companies",
    "section05-user-research-validation",
    "section06-validation-experiments",
    "section07-technical-feasibility",
    "section08-competitive-advantage",
    "section09-business-model",
    "section10-legal-ip-compliance",
    "section11-mvp-roadmap",
    "section12-customer-journey",
    "section13-go-to-market",
    "section14-partnerships-ecosystem",
    "section15-expansion-plan",
    "section16-success-metrics",
    "section17-funding-investment",
    "section18-exit-strategy",
    "section19-pitch-narrative",
]


@dataclass
class AnalysisMetrics:
    """Metrics extracted from an analysis."""
    analysis_id: int
    model_name: str
    total_cost_usd: float
    total_tokens: int
    generation_time_seconds: float
    section_word_counts: dict[str, int]
    dimension_scores: dict[str, float]  # 0-10 scale
    author_rating: Optional[float]  # 0-10 scale, None if not rated
    author_sections_rated: int
    viewer_count: int
    available_sections: set[str] = None  # Sections that exist in report folder

    def __post_init__(self):
        if self.available_sections is None:
            self.available_sections = set()


def extract_word_count_from_html(html_content: str) -> int:
    """Extract word count from HTML content, stripping tags."""
    if not html_content:
        return 0
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html_content)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Count words
    words = text.split()
    return len(words)


def load_section_html(report_folder: str, section_key: str) -> Optional[str]:
    """Load HTML content for a section."""
    # Try different filename patterns
    patterns = [
        f"{section_key}.html",
        f"{section_key.replace('-', '_')}.html",
    ]

    for pattern in patterns:
        filepath = os.path.join(report_folder, pattern)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Error reading {filepath}: {e}")

    return None


def load_metadata(report_folder: str) -> Optional[dict]:
    """Load metadata.json from report folder."""
    metadata_path = os.path.join(report_folder, "metadata.json")
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading metadata.json: {e}")
    return None


def calculate_dimension_score(
    word_counts: dict[str, int],
    dimension: str,
    all_analyses_word_counts: list[dict[str, int]]
) -> float:
    """
    Calculate a dimension score (0-10) based on word counts.

    Normalizes word count relative to other analyses being compared.
    Higher word count = deeper analysis = higher score.
    """
    sections = DIMENSION_SECTIONS.get(dimension, [])
    if not sections:
        return 5.0  # Default middle score

    # Sum word counts for this dimension's sections
    total_words = sum(word_counts.get(s, 0) for s in sections)

    if not all_analyses_word_counts:
        return 5.0

    # Get min/max across all analyses for normalization
    all_totals = []
    for wc in all_analyses_word_counts:
        t = sum(wc.get(s, 0) for s in sections)
        all_totals.append(t)

    min_total = min(all_totals) if all_totals else 0
    max_total = max(all_totals) if all_totals else 1

    # Normalize to 0-10 scale
    if max_total == min_total:
        return 7.0  # All same = above average

    normalized = (total_words - min_total) / (max_total - min_total)
    # Map to 4-10 range (we don't want scores below 4 for word count proxy)
    score = 4.0 + (normalized * 6.0)
    return round(score, 1)


def extract_analysis_metrics(
    analysis_id: int,
    model_name: str,
    report_folder: str,
    total_cost_usd: float,
    total_tokens: int,
    started_at,
    completed_at,
    author_feedbacks: list[dict],
    viewer_count: int,
    all_analyses_word_counts: Optional[list[dict[str, int]]] = None
) -> AnalysisMetrics:
    """
    Extract all metrics from an analysis.

    Args:
        analysis_id: Database ID of the analysis
        model_name: Name of the model used
        report_folder: Path to the report folder
        total_cost_usd: Total cost from database
        total_tokens: Total tokens from database
        started_at: Analysis start time
        completed_at: Analysis completion time
        author_feedbacks: List of author's feedback dicts with 'section_key' and 'rating'
        viewer_count: Number of non-author users who rated
        all_analyses_word_counts: Word counts from all analyses (for normalization)

    Returns:
        AnalysisMetrics with all extracted data
    """
    # Calculate generation time
    if started_at and completed_at:
        generation_time = (completed_at - started_at).total_seconds()
    else:
        generation_time = 0.0

    # Extract word counts for all sections
    section_word_counts = {}
    available_sections = set()
    if report_folder and os.path.exists(report_folder):
        for section_key in ALL_SECTIONS:
            html_content = load_section_html(report_folder, section_key)
            if html_content:
                section_word_counts[section_key] = extract_word_count_from_html(html_content)
                available_sections.add(section_key)

    # Calculate dimension scores
    dimension_scores = {}
    for dimension in DIMENSION_SECTIONS.keys():
        dimension_scores[dimension] = calculate_dimension_score(
            section_word_counts,
            dimension,
            all_analyses_word_counts or [section_word_counts]
        )

    # Calculate author rating from feedbacks
    author_rating = None
    author_sections_rated = 0
    if author_feedbacks:
        thumbs_up = sum(1 for f in author_feedbacks if f.get('rating') == 1)
        total_rated = len(author_feedbacks)
        author_sections_rated = total_rated
        if total_rated > 0:
            author_rating = round((thumbs_up / total_rated) * 10, 1)

    return AnalysisMetrics(
        analysis_id=analysis_id,
        model_name=model_name,
        total_cost_usd=total_cost_usd or 0.0,
        total_tokens=total_tokens or 0,
        generation_time_seconds=generation_time,
        section_word_counts=section_word_counts,
        dimension_scores=dimension_scores,
        author_rating=author_rating,
        author_sections_rated=author_sections_rated,
        viewer_count=viewer_count,
        available_sections=available_sections,
    )


def get_comparable_dimensions(
    analyses_metrics: list[AnalysisMetrics]
) -> tuple[list[str], list[str], bool]:
    """
    Determine which dimensions can be fairly compared across all analyses.

    A dimension is comparable only if ALL analyses have ALL sections required
    for that dimension.

    Returns:
        (comparable_dimensions, skipped_dimensions, sections_differ)
    """
    if not analyses_metrics:
        return [], [], False

    # Check if all analyses have the same sections
    first_sections = analyses_metrics[0].available_sections
    sections_differ = any(
        m.available_sections != first_sections
        for m in analyses_metrics[1:]
    )

    comparable = []
    skipped = []

    for dimension, required_sections in DIMENSION_SECTIONS.items():
        # Check if all analyses have all required sections for this dimension
        all_have_sections = all(
            all(sec in m.available_sections for sec in required_sections)
            for m in analyses_metrics
        )

        if all_have_sections:
            comparable.append(dimension)
        else:
            skipped.append(dimension)

    return comparable, skipped, sections_differ


def recalculate_dimension_scores(
    analyses_metrics: list[AnalysisMetrics],
    only_dimensions: list[str] = None
) -> list[AnalysisMetrics]:
    """
    Recalculate dimension scores across all analyses for proper normalization.

    Should be called after extracting metrics from all analyses to ensure
    scores are properly normalized relative to each other.

    Args:
        analyses_metrics: List of metrics to recalculate
        only_dimensions: If provided, only calculate scores for these dimensions
    """
    if not analyses_metrics:
        return analyses_metrics

    # Gather all word counts for normalization
    all_word_counts = [m.section_word_counts for m in analyses_metrics]

    # Determine which dimensions to calculate
    dimensions_to_calc = only_dimensions or list(DIMENSION_SECTIONS.keys())

    # Recalculate dimension scores
    for metrics in analyses_metrics:
        for dimension in DIMENSION_SECTIONS.keys():
            if dimension in dimensions_to_calc:
                metrics.dimension_scores[dimension] = calculate_dimension_score(
                    metrics.section_word_counts,
                    dimension,
                    all_word_counts
                )
            else:
                # Set to None for skipped dimensions
                metrics.dimension_scores[dimension] = None

    return analyses_metrics
