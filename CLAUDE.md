# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**VenturePulse** is an AI-powered product viability analysis tool that generates comprehensive reports using LLM APIs through OpenRouter. FastAPI web application with OAuth authentication, deployed via Docker.

**Live Demo:** https://venturepulse.shalusri.com

## Development Commands

```bash
# Docker (recommended)
docker-compose up                    # Start app on PORT (default 8080)
docker-compose up --build            # Rebuild and start
docker-compose build --no-cache      # Force fresh build
docker-compose logs -f               # View logs

# Local development (without Docker)
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
```

**Note:** No test suite exists yet. Tests are a contribution opportunity.

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-...

# OAuth (optional if DEV_MODE=true)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...

# App settings
PORT=8080
DEV_MODE=false              # Set true for local dev without OAuth
BASE_URL=http://localhost:8080
SECRET_KEY=...              # Generate with command above
DEFAULT_MODEL=anthropic/claude-sonnet-4
MAXRETRY=3
MAX_PARALLEL_SECTIONS=10
```

## Architecture

### Application Flow

1. User authenticates via OAuth (Google/GitHub) or Dev mode
2. User sets their OpenRouter API key in Settings (stored in session cookie)
3. User creates a project with a product spec
4. User runs analysis selecting model(s) and sections
5. Background task calls OpenRouter API for each section
6. Results saved as HTML files + metadata.json

### Key Architectural Decisions

**Router Order Matters** (`app/main.py:102-111`): Specific routes must come before parameterized routes:
- `/project/new` (projects_router) before `/project/{slug}` (public_router)
- `/project/{slug}/share` (share_router) before `/project/{slug}` (public_router)

**API Key Storage**: Per-user keys stored in encrypted session cookie, NOT in database. `api_key_temp` field in Analysis model is only for recovery after container restarts (cleared on completion).

**Background Tasks**: Analyses run in asyncio background tasks (`app/services/background.py`). On startup, `recover_interrupted_analyses()` resumes any analyses interrupted by restarts.

### Section Framework

19 sections organized into 4 groups (defined in `app/routes/analysis.py:36-64`):

| Group | Sections | Numbers |
|-------|----------|---------|
| Foundation | Executive Summary, Market Landscape, User Stories, Comparable Companies, User Research, Validation Experiments | 01-06 |
| Strategy | Technical Feasibility, Competitive Advantage, Business Model, Legal & Compliance | 07-10 |
| Execution | MVP Roadmap, Customer Journey, Go-to-Market, Partnerships, Expansion Plan | 11-15 |
| Future | Success Metrics, Funding Strategy, Exit Strategy, Pitch Narrative | 16-19 |

**Quick Analysis** uses 7 core sections: 01, 02, 07, 09, 11, 13, 16

Section 20 (Provenance) is auto-generated with cost/timing metadata.

### Database Models (`app/db/models.py`)

- **User** - OAuth identity, role (admin/approved/pending), preferred_models JSON
- **Project** - Name, slug (unique), spec_content, is_public
- **Analysis** - project_id, model_name, status, sections_completed JSON, cost tracking
- **Session** - Token-based auth sessions with expiry
- **SectionFeedback** - User ratings on sections (thumbs up/down)
- **ShareableLink** - Temporary access tokens for private projects
- **ShareLinkVisitor** - Privacy-preserving visitor tracking

### File Structure

```
app/
├── main.py                 # FastAPI app, lifespan, middleware, exception handlers
├── config.py               # Settings class with env vars
├── __init__.py             # Version info (__version__, __version_date__, __version_name__)
├── auth/                   # OAuth setup, session management, decorators
├── db/                     # SQLAlchemy models, migrations, database init
├── routes/                 # API endpoints by domain
├── services/               # Business logic (analysis_engine, openrouter, background)
├── templates/              # Jinja2 HTML templates
└── static/                 # CSS, JS, images

prompts/
├── common-instructions.md  # Shared prompt context
└── sections/               # section{NN}-{slug}.md files (19 prompts)

data/                       # Runtime data (gitignored)
├── venturepulse.db         # SQLite database
├── reports/{user_id}/{project_slug}/{analysis_id}/  # Generated HTML reports
└── specs/                  # Project spec files
```

## Adding Features

### New API Endpoint
1. Add route in `app/routes/` (or new file)
2. Register router in `app/main.py` (watch ordering!)
3. Add template in `app/templates/` if needed

### New Database Model
1. Add model class in `app/db/models.py`
2. Add migration in `app/db/migrations.py`
3. Migrations run automatically on startup via `init_db()`

### New Analysis Section
1. Create `prompts/sections/section{NN}-{slug}.md`
2. Add to `SECTIONS` list in `app/routes/analysis.py`
3. Update `QUICK_SECTIONS` if it should be in quick analysis

### Version Updates
**IMPORTANT:** Update in TWO places:
1. `app/__init__.py` - `__version__`, `__version_date__`, `__version_name__`
2. `CHANGELOG.md` - New entry with date and changes

Version displays in site footer.

## Key Endpoints

### Auth
- `GET /auth/login` - Login page
- `GET /auth/google` - Google OAuth redirect
- `GET /auth/github` - GitHub OAuth redirect
- `POST /auth/logout` - Logout

### Projects
- `GET /projects` - List user's projects
- `POST /projects` - Create project
- `GET /project/{slug}` - View project
- `DELETE /project/{slug}` - Delete project

### Analysis
- `GET /project/{slug}/analyze` - Analysis config form
- `POST /project/{slug}/analyze` - Start analysis
- `GET /api/analysis/{id}/status` - Check status (JSON)
- `GET /api/analysis/{id}/section/{key}` - Get section HTML

### Admin
- `GET /admin` - Admin dashboard (admin role only)
- `POST /admin/users/{id}/role` - Update user role

## Output Format

Each analysis creates files in `data/reports/{user_id}/{project_slug}/{analysis_id}/`:
```
├── section{NN}-{slug}.html    # Individual report sections
├── section20-provenance.html  # Auto-generated metadata/cost report
├── project-spec.md            # Copy of input
└── metadata.json              # Analysis metadata, timing, costs
```

## Key Features

| Feature | Description |
|---------|-------------|
| Authentication | OAuth (Google/GitHub) or Dev mode |
| User Management | Full user system with roles (admin/approved/pending) |
| Data Storage | SQLite (default) or PostgreSQL |
| Multi-user | Yes, with project ownership |
| Public/Private | Projects can be shared or private; shareable links for private projects |
| Sections | 7 (Quick) / 19 (Full) / Custom selection |
| Multi-model | Run same analysis with multiple models, built-in comparison |
| Cost Tracking | Per-section + total costs in Provenance report |

## Legacy Versions

Archived in `Archive/` for reference (may not work with current prompts):
- `Archive/streamlit/` - Standalone Streamlit app (no auth, file-based)
- `Archive/cli/` - Bash CLI scripts
