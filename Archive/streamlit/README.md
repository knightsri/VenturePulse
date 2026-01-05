# VenturePulse Streamlit Version (Legacy)

> **Note:** This is the archived legacy version. The main project has moved to a FastAPI-based architecture with authentication. See the [main README](../../README.md) for the current version.

## About This Version

This standalone Streamlit app was the original web interface for VenturePulse before the v2 rewrite. It's preserved here for users who prefer a simpler, single-file deployment without authentication requirements.

## Features

- Single-file Streamlit application
- No authentication required (bring your own API key)
- File-based storage (no database needed)
- Multi-model analysis and comparison
- All 19 analysis sections supported

## Quick Start

```bash
# From the repository root
cd Archive/streamlit

# Install dependencies
pip install streamlit requests python-dotenv pandas

# Run the app
streamlit run venturepulse.py --server.port=8501

# Open http://localhost:8501
```

## Requirements

- Python 3.11+
- OpenRouter API key
- Dependencies: `streamlit`, `requests`, `python-dotenv`, `pandas`

## Limitations Compared to V2

| Feature | Streamlit (Legacy) | V2 (FastAPI) |
|---------|-------------------|--------------|
| Authentication | None | OAuth (Google/GitHub) |
| User Management | None | Full user system |
| Data Storage | Local files | SQLite/PostgreSQL |
| Multi-user | No | Yes |
| Public/Private Projects | No | Yes |
| Section Feedback | No | Yes (planned) |
| API | None | Full REST API |

## Why It Was Archived

The v2 rewrite added:
- User authentication and authorization
- Persistent database storage
- Multi-user support with project sharing
- Public/private project visibility
- Admin dashboard
- Planned: Section feedback and enhanced comparison

For new deployments, use the main v2 version with Docker.
