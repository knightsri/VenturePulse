# Changelog

All notable changes to VenturePulse will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
