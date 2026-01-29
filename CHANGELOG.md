# Changelog

All notable changes to VenturePulse will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.0] - 2026-01-28 - "Precision"

### Added
- **Per-section temperature control**: Each analysis section now has optimized temperature settings to reduce hallucination
- **Seed parameter for reproducibility**: Factual sections use fixed seed (42) for consistent, reproducible outputs
- **Four temperature tiers**:
  - 0.2 (Precision): Market data, competitors, financials, legal, metrics - with seed
  - 0.3 (Grounded): Research methodologies, experiment design, realistic planning
  - 0.5 (Balanced): Customer journey, go-to-market, expansion strategies
  - 0.7 (Creative): User personas, pitch narratives, storytelling

### Changed
- `openrouter.py`: Now accepts optional `temperature` and `seed` parameters per API call
- `analysis_engine.py`: Passes section-specific settings to OpenRouter API
- Sections 01, 02, 04, 07, 09, 10, 16, 17, 18 now use low temperature (0.2) with seed for factual accuracy
- Sections 05, 06, 08, 11, 14 use grounded temperature (0.3) for realistic methodologies
- Sections 12, 13, 15 use balanced temperature (0.5) for creative but realistic strategies
- Sections 03, 19 use creative temperature (0.7) for personas and storytelling

### Fixed
- Reduced risk of hallucinated competitor names, market sizes, and company data
- Improved consistency in financial projections and legal requirements

## [2.2.0] - 2026-01-08 - "Link Sharing"

### Added
- **Shareable links feature**: Create time-limited links to share private projects with anyone
- **Multiple links per project**: Create different links with different expiration dates (1-90 days)
- **Unique visitor tracking**: Track number of unique visitors and total visits per link
- **Link management UI**: View active/expired links, copy links, extend expiration, deactivate links
- **Session-based allowkey access**: Once validated, allowkey is stored in session for seamless navigation
- **Admin pending badge**: Admin button shows count of pending user approvals

### Changed
- Project view page now includes "Share" button for project owners

## [2.1.1] - 2026-01-08

### Added
- Project count display on dashboard and browse pages
- Dashboard shows user's project count with public/private breakdown
- Browse page shows site-wide project count with public/private breakdown

## [2.1.0] - 2026-01-05 - "Comparison"

### Added
- **Multi-model comparison feature**: Compare 2-8 analyses side-by-side
- **Dimension scoring**: Quality scores for Market, Technical, Competitive, Business, and Execution dimensions
- **Interactive charts**: Radar chart, scatter plot (cost vs quality), and bar chart visualizations using Plotly
- **Section feedback**: Thumbs up/down ratings for individual analysis sections
- **Author's Choice badge**: Highlights the model preferred by the project creator
- **Smart comparison warnings**: Alerts when comparing analyses with different section selections
- **Best Value / Highest Quality / Lowest Cost indicators**: Quick identification of model strengths

### Fixed
- API error responses now return JSON instead of HTML for `/api/` routes
- Session state handling for user model preferences

### Changed
- Renamed "Owner's Pick" to "Author's Choice" for clarity

## [2.0.0] - 2026-01-01 - "Foundation"

### Added
- Complete rewrite as FastAPI web application
- OAuth authentication (Google, GitHub)
- Project management dashboard
- Multi-model analysis support via OpenRouter
- 19 analysis sections with group organization (Foundation/Strategy/Execution/Future)
- Quick (7 sections) and Full (19 sections) analysis presets
- Custom section selection
- Analysis history and management
- Public sharing with unique links
- Cost tracking per analysis
- Docker containerization
- SQLite database with migrations
- Bauhaus-inspired UI design

### Changed
- Migrated from CLI-only Bash scripts to full web application
- Improved section organization with logical groupings

## [1.0.0] - 2025-10-21 - "CLI"

### Added
- Initial CLI version using Bash scripts
- 8-section analysis via OpenRouter API
- HTML report generation with navigation wrapper
- Basic provenance tracking
