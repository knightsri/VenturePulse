# VenturePulse Multi-Model Comparison Feature - Implementation Plan

## Overview

Restore the rich multi-model comparison feature from the original Next.js implementation into the current FastAPI + web app. The goal is to provide users with insightful visualizations and analysis when comparing analysis runs across different AI models.

## Current State

The existing comparison functionality is basic:
- Project selector
- Analysis selector (2-4 analyses)
- Section selector
- Side-by-side or tabbed view
- Simple timing/cost comparison table

## Target Features

### 1. Summary Dashboard Cards
Display key metrics at a glance:
- **Average Overall Score** across all selected models
- **Best Value Model** (highest quality-to-cost ratio)
- **Highest Quality Model** (best scores)
- **Lowest Cost Model**
- **Owner's Pick** (highest author rating, if available)

### 2. Recommendation Banner
Auto-generated recommendation based on:
- Consensus detection (models agree on dimensions)
- Disagreement detection (high spread in scores)
- Cost-efficiency analysis
- Author ratings (if available)
- Actionable guidance for the user

### 3. Interactive Charts

#### 3.1 Radar Chart
- 6 dimensions: Market, Technical, Competitive, Business, Execution, Author Rating
- One line per model with different colors
- Shows strength/weakness patterns at a glance
- Author Rating dimension only shown if ratings exist

#### 3.2 Cost vs Quality Scatter Plot
- X-axis: Total Cost
- Y-axis: Overall Quality Score
- One point per model
- Helps identify value leaders

#### 3.3 Average Scores Bar Chart
- Bar for each dimension
- Shows average score across models
- Error bars or annotations for spread (disagreement indicator)

### 4. Consensus & Disagreement Analysis
- **Consensus areas**: Dimensions where models agree (spread < 1.0)
- **Disagreement areas**: Dimensions with high spread (spread > 2.0)
- Displayed as badges/tags with explanations

### 5. Author Feedback System (Thumbs Up/Down)

Simple per-section quality rating by the **project owner**.

#### 5.1 Key Principle: Project Owner = Author

| User | Rates Their Own Runs | Rates Others' Runs | Used in Comparison? |
|------|---------------------|-------------------|---------------------|
| Project Owner (X) | ✅ Author rating | ✅ Author rating | ✅ Yes |
| Other Users (Y) | Viewer rating | Viewer rating | ❌ No (supplementary only) |

**Rationale:** The project owner is the authority on "which model best explains MY idea." Their ratings drive comparison metrics. Other users' ratings are tracked but shown separately as supplementary info.

#### 5.2 Multi-User Scenario

When multiple users run analyses on the same project:
- User X creates Project 1, runs Model A, Model B
- User Y runs Model C, Model D on Project 1 (public project)
- Project 1 now has 4 analyses

**Rating behavior:**
- X (project owner) can rate ALL 4 analyses → all count as "author" ratings
- Y can rate all 4 analyses → all count as "viewer" ratings (supplementary)
- Comparison shows X's perspective: "Owner prefers Model A (8/10) over Model C (6/10)"

#### 5.3 Data Model (New SectionFeedback table)

```sql
CREATE TABLE section_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    section_key VARCHAR(100) NOT NULL,  -- e.g., "section01-executive-summary"
    rating INTEGER NOT NULL,            -- 1 = thumbs up, -1 = thumbs down
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(analysis_id, user_id, section_key)  -- one rating per user per section
);
```

**Note:** No `is_author` column needed. We derive it at query time:
```sql
-- Author ratings only
SELECT * FROM section_feedback sf
JOIN analyses a ON sf.analysis_id = a.id
JOIN projects p ON a.project_id = p.id
WHERE sf.user_id = p.user_id;
```

#### 5.4 Author Rating Calculation

```
Author Rating = (thumbs_up_count / total_rated_sections) * 10
```

- Shown immediately when project owner rates any section
- Scale: 0-10 (0 = all thumbs down, 10 = all thumbs up)
- Example: 7 thumbs up, 3 thumbs down = 7/10 * 10 = 7.0

#### 5.5 UI Display

**In View Results (single analysis):**
```
┌─────────────────────────────────────────────────┐
│ Section: Executive Summary                      │
│ [HTML content...]                               │
│                                                 │
│ Rate this section: [👍] [👎]                    │
│ ─────────────────────────────────────────────── │
│ 📊 Owner's Rating: 👍                           │
│ 👥 2 other users also rated (supplementary)     │
└─────────────────────────────────────────────────┘
```

**In Compare Results:**
```
┌──────────────────────────────────────────────────────┐
│ Project: SmartPlate (Owner: sri@example.com)         │
│                                                      │
│ Owner's Ratings:                                     │
│ ─────────────────────────────────────────────────── │
│ Model              Run By    Sections   Rating      │
│ claude-sonnet-4    Owner     👍 8/10    8.0/10      │
│ gpt-4o             Owner     👍 6/10    6.0/10      │
│ deepseek-chat      UserY     👍 7/10    7.0/10  ←   │
│ gemini-2.5-pro     UserY     Not rated  —           │
└──────────────────────────────────────────────────────┘

Note: Owner rated UserY's deepseek run
```

### 6. Detailed Model Breakdown Table
Enhanced table showing:
- Model name
- Run by (who ran the analysis)
- Per-dimension proxy scores
- **Author rating** (if available)
- Overall score
- Total cost
- Total tokens
- Generation time
- Value score (quality/cost ratio)

---

## Implementation Approach

### Phase 1: Dependencies & Setup
- Add `plotly>=5.0.0` to requirements
- Verify Docker build works

### Phase 2: Score Extraction System
Create functions to extract metrics from analyses:
- Parse metadata.json for cost, tokens, timing
- Calculate proxy quality scores from word counts
- Return standardized score structure

### Phase 3: Comparison Engine
Port comparison logic:
- Calculate averages and spreads
- Detect consensus/disagreements
- Generate recommendations
- Analyze cost vs quality

### Phase 4: Feedback System
- Add SectionFeedback database model
- Create API endpoints for rating
- Build feedback UI components

### Phase 5: Charts & Visualization
- Radar chart (plotly)
- Scatter plot (plotly)
- Bar chart (plotly)

### Phase 6: UI Integration
- Summary dashboard cards
- Recommendation banner
- Enhanced comparison tab with sub-tabs
- Detailed metrics table

---

## Tasks Breakdown

### Task 1: Add plotly dependency
- Add `plotly>=5.0.0` to `requirements.txt`
- Test Docker build

### Task 2: Create score extraction function
- Parse metadata.json for cost, tokens, timing
- Read section HTML files for word counts
- Calculate proxy quality scores per dimension
- Return standardized score structure

### Task 3: Create comparison engine functions
- `calculate_averages(analyses)` - average scores across models
- `calculate_spreads(analyses)` - score spread per dimension
- `detect_consensus_disagreements(spreads)` - identify agreement/disagreement
- `generate_recommendation(metrics)` - actionable guidance text
- `analyze_cost_vs_quality(analyses)` - best value, highest quality, lowest cost

### Task 4: Build summary dashboard UI
- 4-5 column metric cards (Avg Score, Best Value, Highest Q, Lowest $, Owner's Pick)
- Recommendation banner with dynamic text
- Project/analysis selectors (enhance existing)

### Task 5: Create radar chart component
- Use `plotly.graph_objects.Scatterpolar`
- 6 dimensions (5 proxy + Author Rating)
- Configure colors, legend, responsive sizing
- Handle missing Author Rating gracefully

### Task 6: Create scatter plot component
- Cost (X) vs Quality (Y) scatter
- Hover info with model details
- Color coding per model

### Task 7: Create bar chart component
- Average scores per dimension
- Spread indicators (error bars or annotations)
- Color coding by dimension

### Task 8: Enhance section comparison
- Keep existing side-by-side and tabbed views
- Move to sub-tab within comparison page
- Add word count display per section

### Task 9: Create detailed metrics table
- Sortable columns
- All metrics: model, run by, dimensions, author rating, cost, tokens, time
- Value score calculation
- Export capability (CSV download)

### Task 10: Add consensus/disagreement badges
- Visual indicators (green for consensus, orange for disagreement)
- Tooltips with explanations
- Display in summary area

### Task 11: Add SectionFeedback database model
- Create `SectionFeedback` model in `app/db/models.py`
- Add relationship to Analysis model
- Create Alembic migration
- Add indexes for efficient queries

### Task 12: Add feedback API endpoints
- `POST /api/analyses/{id}/sections/{section_key}/feedback` - submit/update rating
- `GET /api/analyses/{id}/feedback` - get all feedback for analysis
- `GET /api/analyses/{id}/feedback/summary` - aggregated stats
- `DELETE /api/analyses/{id}/sections/{section_key}/feedback` - remove rating
- Determine author vs viewer from session user vs project owner

### Task 13: Add feedback UI to section viewer
- Thumbs up/down buttons below each section
- Show current user's rating state (highlighted button)
- Show owner's rating if different user is viewing
- Show viewer count as supplementary info
- Real-time update on click via API

### Task 14: Integrate feedback into comparison metrics
- Add "Author Rating" as 6th dimension in radar chart
- Include in detailed metrics table
- Factor into recommendation generation ("Owner prefers X")
- Show "Not rated" gracefully when no author ratings

### Task 15: Testing and polish
- Test with 2, 3, 4 analyses
- Test with analyses from multiple users on same project
- Test with analyses that have no ratings
- Test rating persistence across sessions
- Responsive layout adjustments
- Error handling for edge cases

---

## Metrics/Dimensions

Proxy metrics (since we don't have LLM-scored dimensions):

| Dimension | Proxy Metric | Sections Used | Rationale |
|-----------|-------------|---------------|-----------|
| Market | Word count | 02, 03 | More detail = deeper market analysis |
| Technical | Word count | 07 | Technical depth |
| Competitive | Word count | 04, 08 | Competition coverage |
| Business | Word count | 09 | Business model detail |
| Execution | Word count | 11, 13 | Execution planning |
| **Author Rating** | Thumbs up % | All rated | **Real quality signal from owner** |

**Normalization:** All metrics scaled to 0-10 for visualization.

**Word count scoring:**
- Calculate word count per relevant section(s)
- Normalize across all analyses being compared
- Map to 0-10 scale (min = 0, max = 10)

**Author Rating scoring:**
- `(thumbs_up / total_rated) * 10`
- Only included when owner has rated at least 1 section
- Shown as "Not rated" otherwise

---

## API Endpoints (New)

### Feedback Endpoints

```
POST   /api/analyses/{analysis_id}/sections/{section_key}/feedback
Body:  { "rating": 1 }  // 1 = thumbs up, -1 = thumbs down
Response: { "success": true, "is_author": true }

GET    /api/analyses/{analysis_id}/feedback
Response: {
  "ratings": [
    { "section_key": "section01-executive-summary", "rating": 1, "is_author": true },
    ...
  ],
  "summary": {
    "author_thumbs_up": 7,
    "author_thumbs_down": 2,
    "author_rating": 7.8,
    "viewer_count": 3
  }
}

DELETE /api/analyses/{analysis_id}/sections/{section_key}/feedback
Response: { "success": true }
```

### Comparison Endpoints (Enhancement)

```
GET    /api/projects/{project_id}/comparison
Query: ?analysis_ids=1,2,3
Response: {
  "metrics": { ... },
  "recommendation": "...",
  "consensus": [...],
  "disagreements": [...]
}
```

---

## UI Wireframe

```
┌─────────────────────────────────────────────────────────────────┐
│ 🔬 Multi-Model Comparison                                       │
├─────────────────────────────────────────────────────────────────┤
│ Project: [SmartPlate ▼]    Analyses: [☑ claude ☑ gpt ☑ deep]   │
├─────────────────────────────────────────────────────────────────┤
│ 📊 RECOMMENDATION                                               │
│ "Strong consensus on technical feasibility. Owner prefers       │
│  Claude for depth. DeepSeek offers best value at $0.45."        │
├─────────────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│ │Avg Score │ │Best Value│ │Highest Q │ │Lowest $  │ │Owner's │ │
│ │  7.2/10  │ │ deepseek │ │ claude   │ │ deepseek │ │ claude │ │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ [📊 Charts] [📋 Sections] [📈 Details]                          │
│                                                                 │
│ ═══════════════════════════════════════════════════════════════ │
│                                                                 │
│ CHARTS TAB:                                                     │
│ ┌─────────────────────┐  ┌─────────────────────┐               │
│ │    Radar Chart      │  │  Cost vs Quality    │               │
│ │  ╱╲    Market       │  │       •claude       │               │
│ │ ╱  ╲   ╱╲           │  │    •gpt            │               │
│ │╱    ╲_╱  ╲          │  │  •deep              │               │
│ │ Tech    Exec        │  │  $──────────────→   │               │
│ └─────────────────────┘  └─────────────────────┘               │
│                                                                 │
│ ┌───────────────────────────────────────────────┐              │
│ │           Average Scores by Dimension          │              │
│ │ Market    ████████░░ 8.0                       │              │
│ │ Technical ███████░░░ 7.0                       │              │
│ │ Business  ██████░░░░ 6.0                       │              │
│ └───────────────────────────────────────────────┘              │
│                                                                 │
│ ═══════════════════════════════════════════════════════════════ │
│                                                                 │
│ SECTIONS TAB:                                                   │
│ Section: [01. Executive Summary ▼]  View: (•) Side-by-Side ( ) Tab│
│ ┌──────────────────────┐  ┌──────────────────────┐             │
│ │ claude-sonnet-4      │  │ gpt-4o               │             │
│ │ [HTML content...]    │  │ [HTML content...]    │             │
│ │                      │  │                      │             │
│ │ [👍 ✓] [👎]  Owner  │  │ [👍] [👎 ✓]  Owner  │             │
│ └──────────────────────┘  └──────────────────────┘             │
│                                                                 │
│ ═══════════════════════════════════════════════════════════════ │
│                                                                 │
│ DETAILS TAB:                                                    │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │ Model       │ Market│ Tech │ Biz │ Author │ Cost  │ Value │  │
│ │─────────────│───────│──────│─────│────────│───────│───────│  │
│ │ claude      │  8.5  │ 7.2  │ 8.0 │ 8.0/10 │ $4.50 │  1.8  │  │
│ │ gpt-4o      │  7.8  │ 7.5  │ 7.2 │ 6.0/10 │ $3.20 │  2.2  │  │
│ │ deepseek    │  7.0  │ 6.8  │ 6.5 │  —     │ $0.45 │ 14.4  │  │
│ └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│ Consensus: ✅ Technical Feasibility (spread: 0.7)              │
│ Disagreement: ⚠️ Business Model (spread: 2.3)                  │
│                                                                 │
│ [📥 Export CSV]                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Acceptance Criteria

1. User can select 2-4 analyses from the same project
2. Summary cards show: average score, best value, highest quality, lowest cost, owner's pick
3. Recommendation banner provides actionable guidance
4. Radar chart shows all models (6 dimensions: 5 proxy + Author Rating when available)
5. Scatter plot shows cost vs quality
6. Bar chart shows average scores per dimension
7. Existing section comparison (side-by-side, tabbed) still works
8. Detailed table is sortable with all metrics
9. Works with both new and existing analyses
10. No breaking changes to existing functionality
11. **Thumbs up/down buttons appear on each section in View Results**
12. **Feedback is persisted to database via SectionFeedback model**
13. **Only project owner's ratings count as "author" in comparison metrics**
14. **Other users' ratings are tracked but shown as supplementary info**
15. **Owner can rate analyses run by other users on their project**
16. **Comparison shows "Owner prefers X" when author ratings exist**

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Proxy scores may not reflect actual quality | Clearly label as "proxy metrics based on report characteristics" |
| Some analyses may have incomplete data | Handle gracefully with N/A values, don't break charts |
| No author ratings exist | Show "Not rated" in table, exclude from radar chart dimension |
| Charts may not render in some environments | Provide table fallback, test across browsers |
| Multiple users rating same analysis | Clear UI showing whose rating counts for comparison |

---

## Future Enhancements (Out of Scope)

1. **LLM-based scoring**: Use a cheap model to score each section 1-10
2. **Sentiment analysis**: Detect optimism/pessimism in reports
3. **Key insight extraction**: Pull specific quotes from each model
4. **Export to PDF**: Generate comparison report document
5. **Historical trending**: Track scores across idea versions
6. **Viewer rating aggregation**: "Community favorite" badge when many viewers agree

---

## File Changes Summary

| File | Changes |
|------|---------|
| `requirements.txt` | Add `plotly>=5.0.0` |
| `app/db/models.py` | Add `SectionFeedback` model |
| `alembic/versions/xxx_add_section_feedback.py` | New migration |
| `app/routes/analyses.py` | Add feedback endpoints |
| `app/routes/comparison.py` | New file for comparison API |
| `app/services/comparison.py` | New file for comparison engine |
| `app/services/scoring.py` | New file for score extraction |
| `frontend/` or `templates/` | UI components for comparison |

---

---

## Implementation Status

**COMPLETED** - All core features have been implemented.

### Implemented Files

| File | Description |
|------|-------------|
| `requirements.txt` | Added `plotly>=5.18.0` |
| `app/db/models.py` | Added `SectionFeedback` model with relationships |
| `app/db/migrations.py` | Added `migration_003_create_section_feedbacks()` |
| `app/services/scoring.py` | Score extraction with word count proxy metrics |
| `app/services/comparison.py` | Comparison engine with Plotly chart generation |
| `app/routes/analysis.py` | Feedback endpoints and comparison API |
| `app/routes/public.py` | Comparison page route |
| `app/templates/pages/project_view.html` | Analysis selection with checkboxes |
| `app/templates/pages/comparison.html` | Full comparison UI with charts |
| `app/templates/pages/analysis_view.html` | Thumbs up/down feedback bar |
| `app/static/css/bauhaus.css` | Added light color variants |

### How to Use

1. Go to a project with 2+ completed analyses
2. Check the analyses you want to compare
3. Click "Compare Selected"
4. View summary cards, charts, and detailed comparison
5. Rate sections with thumbs up/down while viewing analysis results
