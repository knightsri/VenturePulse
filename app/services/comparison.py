"""
Comparison engine service for VenturePulse.

Calculates comparison metrics, generates recommendations,
and produces visualization data for multi-model analysis comparison.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Optional

import plotly.graph_objects as go

from app.services.scoring import AnalysisMetrics, DIMENSION_SECTIONS

logger = logging.getLogger(__name__)

# Thresholds for consensus/disagreement detection
CONSENSUS_THRESHOLD = 1.0  # spread < 1.0 = consensus
DISAGREEMENT_THRESHOLD = 2.0  # spread > 2.0 = disagreement


@dataclass
class ComparisonResult:
    """Complete comparison result for visualization."""
    analyses: list[AnalysisMetrics]
    averages: dict[str, float]  # dimension -> average score
    spreads: dict[str, float]  # dimension -> spread (max - min)
    consensus_areas: list[str]  # dimensions with consensus
    disagreement_areas: list[str]  # dimensions with disagreement
    recommendation: str  # Generated recommendation text
    best_value_model: Optional[str]  # Highest quality/cost ratio
    highest_quality_model: Optional[str]  # Highest average score
    lowest_cost_model: Optional[str]  # Lowest cost
    owners_pick_model: Optional[str]  # Highest author rating
    radar_chart_json: str  # Plotly radar chart as JSON
    scatter_chart_json: str  # Plotly scatter chart as JSON
    bar_chart_json: str  # Plotly bar chart as JSON
    # Warning fields for mismatched sections
    sections_differ: bool = False  # True if analyses have different section sets
    skipped_dimensions: list[str] = None  # Dimensions skipped due to missing sections
    warning_message: Optional[str] = None  # User-facing warning message

    def __post_init__(self):
        if self.skipped_dimensions is None:
            self.skipped_dimensions = []


def calculate_averages(analyses: list[AnalysisMetrics]) -> dict[str, float]:
    """Calculate average scores per dimension across all analyses."""
    if not analyses:
        return {}

    dimensions = list(DIMENSION_SECTIONS.keys())
    averages = {}

    for dim in dimensions:
        # Only include scores that are not None (skipped dimensions have None)
        scores = [
            a.dimension_scores.get(dim)
            for a in analyses
            if a.dimension_scores.get(dim) is not None
        ]
        if scores:
            averages[dim] = round(sum(scores) / len(scores), 1)

    # Add author rating average if any analyses have ratings
    author_ratings = [a.author_rating for a in analyses if a.author_rating is not None]
    if author_ratings:
        averages["author_rating"] = round(sum(author_ratings) / len(author_ratings), 1)

    return averages


def calculate_spreads(analyses: list[AnalysisMetrics]) -> dict[str, float]:
    """Calculate score spreads (max - min) per dimension."""
    if not analyses:
        return {}

    dimensions = list(DIMENSION_SECTIONS.keys())
    spreads = {}

    for dim in dimensions:
        # Only include scores that are not None (skipped dimensions have None)
        scores = [
            a.dimension_scores.get(dim)
            for a in analyses
            if a.dimension_scores.get(dim) is not None
        ]
        if scores:
            spreads[dim] = round(max(scores) - min(scores), 1)

    return spreads


def detect_consensus_disagreements(
    spreads: dict[str, float]
) -> tuple[list[str], list[str]]:
    """Detect areas of consensus and disagreement based on spreads."""
    consensus = []
    disagreements = []

    for dim, spread in spreads.items():
        if spread < CONSENSUS_THRESHOLD:
            consensus.append(dim)
        elif spread > DISAGREEMENT_THRESHOLD:
            disagreements.append(dim)

    return consensus, disagreements


def analyze_cost_vs_quality(
    analyses: list[AnalysisMetrics]
) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Analyze cost vs quality to find best value, highest quality, lowest cost,
    and owner's pick models.

    Returns:
        (best_value_model, highest_quality_model, lowest_cost_model, owners_pick_model)
    """
    if not analyses:
        return None, None, None, None

    # Calculate overall quality score (average of all dimensions)
    def overall_quality(a: AnalysisMetrics) -> float:
        scores = [s for s in a.dimension_scores.values() if s is not None]
        return sum(scores) / len(scores) if scores else 0

    # Best value: highest quality/cost ratio
    best_value = None
    best_value_ratio = 0
    for a in analyses:
        if a.total_cost_usd > 0:
            ratio = overall_quality(a) / a.total_cost_usd
            if ratio > best_value_ratio:
                best_value_ratio = ratio
                best_value = a.model_name

    # Highest quality: highest average dimension score
    highest_quality = max(analyses, key=overall_quality).model_name

    # Lowest cost
    lowest_cost = min(analyses, key=lambda a: a.total_cost_usd or float('inf')).model_name

    # Owner's pick: highest author rating
    owners_pick = None
    rated_analyses = [a for a in analyses if a.author_rating is not None]
    if rated_analyses:
        owners_pick = max(rated_analyses, key=lambda a: a.author_rating).model_name

    return best_value, highest_quality, lowest_cost, owners_pick


def generate_recommendation(
    analyses: list[AnalysisMetrics],
    consensus_areas: list[str],
    disagreement_areas: list[str],
    best_value: Optional[str],
    highest_quality: Optional[str],
    owners_pick: Optional[str]
) -> str:
    """Generate actionable recommendation text based on comparison analysis."""
    if not analyses:
        return "No analyses to compare."

    parts = []

    # Consensus insight
    if consensus_areas:
        areas_str = ", ".join(consensus_areas).replace("_", " ").title()
        parts.append(f"Strong consensus across models on {areas_str}.")

    # Disagreement insight
    if disagreement_areas:
        areas_str = ", ".join(disagreement_areas).replace("_", " ").title()
        parts.append(f"Models disagree on {areas_str} - review these sections carefully.")

    # Cost-quality insight
    if best_value and highest_quality:
        if best_value == highest_quality:
            parts.append(f"{best_value.split('/')[-1]} offers both highest quality and best value.")
        else:
            hq_short = highest_quality.split('/')[-1]
            bv_short = best_value.split('/')[-1]
            parts.append(f"{hq_short} provides highest quality; {bv_short} offers best value for cost.")

    # Owner's preference
    if owners_pick:
        op_short = owners_pick.split('/')[-1]
        parts.append(f"Owner prefers {op_short}.")

    if not parts:
        return "Compare the sections below to evaluate model outputs."

    return " ".join(parts)


def create_radar_chart(analyses: list[AnalysisMetrics]) -> str:
    """Create a Plotly radar chart comparing all analyses across dimensions."""
    if not analyses:
        return "{}"

    dimensions = list(DIMENSION_SECTIONS.keys())
    dimension_labels = [d.replace("_", " ").title() for d in dimensions]

    # Add author rating if any analysis has it
    has_author_ratings = any(a.author_rating is not None for a in analyses)
    if has_author_ratings:
        dimensions.append("author_rating")
        dimension_labels.append("Owner Rating")

    # Close the polygon
    dimension_labels.append(dimension_labels[0])

    fig = go.Figure()

    colors = [
        '#636EFA', '#EF553B', '#00CC96', '#AB63FA',
        '#FFA15A', '#19D3F3', '#FF6692', '#B6E880'
    ]

    for i, analysis in enumerate(analyses):
        values = []
        for dim in dimensions:
            if dim == "author_rating":
                values.append(analysis.author_rating or 0)
            else:
                values.append(analysis.dimension_scores.get(dim, 0))
        # Close the polygon
        values.append(values[0])

        model_short = analysis.model_name.split('/')[-1]
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=dimension_labels,
            fill='toself',
            name=model_short,
            line_color=colors[i % len(colors)],
            opacity=0.7
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=60, r=60, t=40, b=60),
        height=400
    )

    return fig.to_json()


def create_scatter_chart(analyses: list[AnalysisMetrics]) -> str:
    """Create a Plotly scatter chart showing cost vs quality."""
    if not analyses:
        return "{}"

    def overall_quality(a: AnalysisMetrics) -> float:
        scores = [s for s in a.dimension_scores.values() if s is not None]
        return sum(scores) / len(scores) if scores else 0

    fig = go.Figure()

    colors = [
        '#636EFA', '#EF553B', '#00CC96', '#AB63FA',
        '#FFA15A', '#19D3F3', '#FF6692', '#B6E880'
    ]

    for i, analysis in enumerate(analyses):
        model_short = analysis.model_name.split('/')[-1]
        quality = overall_quality(analysis)

        fig.add_trace(go.Scatter(
            x=[analysis.total_cost_usd],
            y=[quality],
            mode='markers+text',
            name=model_short,
            text=[model_short],
            textposition="top center",
            marker=dict(
                size=15,
                color=colors[i % len(colors)]
            ),
            hovertemplate=(
                f"<b>{model_short}</b><br>"
                f"Cost: ${analysis.total_cost_usd:.2f}<br>"
                f"Quality: {quality:.1f}/10<br>"
                f"Tokens: {analysis.total_tokens:,}<br>"
                "<extra></extra>"
            )
        ))

    fig.update_layout(
        title="Cost vs Quality",
        xaxis_title="Cost (USD)",
        yaxis_title="Quality Score (0-10)",
        yaxis=dict(range=[0, 10]),
        showlegend=False,
        margin=dict(l=60, r=40, t=60, b=60),
        height=350
    )

    return fig.to_json()


def create_bar_chart(
    averages: dict[str, float],
    spreads: dict[str, float]
) -> str:
    """Create a Plotly bar chart showing average scores per dimension with spread indicators."""
    if not averages:
        return "{}"

    # Filter out author_rating for this chart (it's shown separately)
    dimensions = [d for d in averages.keys() if d != "author_rating"]
    dimension_labels = [d.replace("_", " ").title() for d in dimensions]
    values = [averages[d] for d in dimensions]
    spread_values = [spreads.get(d, 0) for d in dimensions]

    # Color based on consensus/disagreement
    colors = []
    for d in dimensions:
        spread = spreads.get(d, 0)
        if spread < CONSENSUS_THRESHOLD:
            colors.append('#00CC96')  # Green for consensus
        elif spread > DISAGREEMENT_THRESHOLD:
            colors.append('#EF553B')  # Red for disagreement
        else:
            colors.append('#636EFA')  # Blue for neutral

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=dimension_labels,
        y=values,
        marker_color=colors,
        error_y=dict(
            type='data',
            array=spread_values,
            visible=True,
            color='rgba(0,0,0,0.3)'
        ),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Average: %{y:.1f}<br>"
            "Spread: %{error_y.array:.1f}<br>"
            "<extra></extra>"
        )
    ))

    fig.update_layout(
        title="Average Scores by Dimension",
        yaxis_title="Score (0-10)",
        yaxis=dict(range=[0, 10]),
        showlegend=False,
        margin=dict(l=60, r=40, t=60, b=80),
        height=300
    )

    return fig.to_json()


def compare_analyses(
    analyses: list[AnalysisMetrics],
    comparable_dimensions: list[str] = None,
    skipped_dimensions: list[str] = None,
    sections_differ: bool = False
) -> ComparisonResult:
    """
    Main comparison function that calculates all metrics and generates visualizations.

    Args:
        analyses: List of AnalysisMetrics to compare
        comparable_dimensions: Dimensions that can be fairly compared (all analyses have required sections)
        skipped_dimensions: Dimensions skipped due to missing sections in some analyses
        sections_differ: True if analyses have different section sets

    Returns:
        ComparisonResult with all comparison data and charts
    """
    skipped_dimensions = skipped_dimensions or []
    comparable_dimensions = comparable_dimensions or list(DIMENSION_SECTIONS.keys())

    # Generate warning message if sections differ
    warning_message = None
    if sections_differ and skipped_dimensions:
        skipped_names = [d.replace("_", " ").title() for d in skipped_dimensions]
        warning_message = (
            f"These analyses have different sections selected. "
            f"Skipping {', '.join(skipped_names)} dimension(s) from comparison "
            f"because not all analyses include the required sections."
        )
    elif sections_differ:
        warning_message = (
            "These analyses have different sections selected, "
            "but all dimensions can still be compared."
        )

    # Calculate metrics
    averages = calculate_averages(analyses)
    spreads = calculate_spreads(analyses)
    consensus_areas, disagreement_areas = detect_consensus_disagreements(spreads)
    best_value, highest_quality, lowest_cost, authors_choice = analyze_cost_vs_quality(analyses)

    # Generate recommendation
    recommendation = generate_recommendation(
        analyses,
        consensus_areas,
        disagreement_areas,
        best_value,
        highest_quality,
        authors_choice
    )

    # Generate charts
    radar_chart = create_radar_chart(analyses)
    scatter_chart = create_scatter_chart(analyses)
    bar_chart = create_bar_chart(averages, spreads)

    return ComparisonResult(
        analyses=analyses,
        averages=averages,
        spreads=spreads,
        consensus_areas=consensus_areas,
        disagreement_areas=disagreement_areas,
        recommendation=recommendation,
        best_value_model=best_value,
        highest_quality_model=highest_quality,
        lowest_cost_model=lowest_cost,
        owners_pick_model=authors_choice,
        radar_chart_json=radar_chart,
        scatter_chart_json=scatter_chart,
        bar_chart_json=bar_chart,
        sections_differ=sections_differ,
        skipped_dimensions=skipped_dimensions,
        warning_message=warning_message,
    )
