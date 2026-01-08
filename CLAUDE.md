# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**VenturePulse** is an AI-powered product viability analysis tool that generates comprehensive reports using LLM APIs through OpenRouter. Deployed as a Docker web application.

**Live Demo:** https://venturepulse.shalusri.com

## Quick Start

```bash
# Configure environment
cp .env.example .env
# Edit .env: OPENROUTER_API_KEY, OAuth credentials, PORT

# Run with Docker Compose
docker-compose up

# Open http://localhost:8501
# Sign in with Google, GitHub, or Dev mode
```

## Core Architecture

### V2 Web Application (`app/`)

FastAPI-based application with OAuth authentication:

```
app/
├── main.py                 # FastAPI entry point
├── config.py               # Settings and configuration
├── auth/
│   ├── oauth.py            # Google/GitHub OAuth setup
│   ├── session.py          # Session management
│   └── decorators.py       # Auth decorators
├── db/
│   ├── database.py         # SQLite/PostgreSQL connection
│   ├── models.py           # SQLAlchemy models (User, Project, Analysis, Session)
│   └── migrations.py       # Database migrations
├── routes/
│   ├── auth.py             # Login/logout endpoints
│   ├── projects.py         # Project CRUD
│   ├── analysis.py         # Analysis management
│   ├── admin.py            # Admin dashboard
│   ├── settings.py         # User settings
│   └── public.py           # Public routes
├── services/
│   ├── openrouter.py       # OpenRouter API client
│   ├── analysis_engine.py  # Analysis orchestration
│   ├── report.py           # Report generation
│   └── background.py       # Background tasks
├── templates/              # Jinja2 HTML templates
└── static/                 # CSS, JS, images
```

### Database Models (`app/db/models.py`)
- **User** - OAuth users (Google/GitHub), roles (admin/approved/pending)
- **Project** - User projects with specs, public/private visibility
- **Analysis** - Analysis runs with model, status, cost tracking
- **Session** - Authentication sessions

### Prompt Structure (`prompts/`)
- **`common-instructions.md`** - Shared guidelines
- **`sections/section{NN}-{slug}.md`** - 19 specialized prompts

## Configuration

### Environment Variables (`.env`)
```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-...

# OAuth (optional for Dev mode)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...

# App settings
PORT=8501
DEFAULT_MODEL=anthropic/claude-sonnet-4
MAXRETRY=3
MAX_PARALLEL_SECTIONS=10
SECRET_KEY=your-secret-key
```

### Authentication Modes
- **Google OAuth** - Production login
- **GitHub OAuth** - Production login
- **Dev Mode** - Local development without OAuth setup

## Key Endpoints

### Auth
- `GET /auth/login` - Login page
- `GET /auth/google` - Google OAuth redirect
- `GET /auth/github` - GitHub OAuth redirect
- `POST /auth/logout` - Logout

### Projects
- `GET /projects` - List user's projects
- `POST /projects` - Create project
- `GET /projects/{slug}` - View project
- `DELETE /projects/{slug}` - Delete project

### Analysis
- `POST /projects/{slug}/analyze` - Start analysis
- `GET /api/analysis/{id}/status` - Check status
- `GET /api/analysis/{id}/section/{key}` - Get section HTML

### Admin
- `GET /admin` - Admin dashboard (admin role only)
- `POST /admin/users/{id}/role` - Update user role

## Output Format

Each analysis creates files in `data/reports/{user_id}/{project_slug}/{analysis_id}/`:
```
├── section{NN}-{slug}.html    # Individual report sections
├── project-spec.md            # Copy of input
└── metadata.json              # Analysis metadata
```

## Adding New Features

### New API Endpoint
1. Add route in `app/routes/`
2. Register in `app/main.py`
3. Add template if needed in `app/templates/`

### New Database Model
1. Add model in `app/db/models.py`
2. Create migration in `app/db/migrations.py`
3. Run migrations on startup

### New Section
1. Create `prompts/sections/section{NN}-{slug}.md`
2. Update section lists in analysis engine

### Version Updates
**IMPORTANT:** Version must be updated in TWO places and kept in sync:
1. `app/__init__.py` - Update `__version__`, `__version_date__`, and optionally `__version_name__`
2. `CHANGELOG.md` - Add new version entry with date and changes

The version from `app/__init__.py` is displayed in the site footer (bottom right corner).

## Dependencies

- Python 3.11+
- FastAPI, Uvicorn, SQLAlchemy
- Authlib (OAuth), Jinja2
- Docker and Docker Compose
- See `requirements.txt`

## Key Features

| Feature | Description |
|---------|-------------|
| Authentication | OAuth (Google/GitHub) or Dev mode |
| User Management | Full user system with roles |
| Data Storage | SQLite (default) or PostgreSQL |
| Multi-user | Yes, with project ownership |
| Public/Private | Projects can be shared or private |
| Sections | 7 (Quick) / 19 (Full) / Custom |
| Multi-model | Built-in comparison |
| Cost Tracking | Per-section + total in Provenance |

## Legacy Versions

Archived in `Archive/` for reference (may not work with current prompts):
- `Archive/streamlit/` - Standalone Streamlit app (no auth, file-based)
- `Archive/cli/` - Bash CLI scripts
