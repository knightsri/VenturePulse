"""
Configuration settings for VenturePulse v2.
Loads environment variables and provides typed access to settings.
"""

import os
import secrets
from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # Base paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    PROMPTS_DIR: Path = BASE_DIR / "prompts"

    # Required
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

    # OAuth - Google
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # OAuth - GitHub
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")

    # App Config
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_hex(32))
    PORT: int = int(os.getenv("PORT", "8080"))
    BASE_URL: str = os.getenv("BASE_URL", f"http://localhost:{os.getenv('PORT', '8080')}")

    # Development mode - allows dev login without OAuth
    DEV_MODE: bool = os.getenv("DEV_MODE", "false").lower() == "true"

    # Analysis settings
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "anthropic/claude-sonnet-4")
    MAX_PARALLEL_SECTIONS: int = int(os.getenv("MAX_PARALLEL_SECTIONS", "10"))
    MAXRETRY: int = int(os.getenv("MAXRETRY", "3"))

    # Session settings
    SESSION_EXPIRE_HOURS: int = int(os.getenv("SESSION_EXPIRE_HOURS", "168"))  # 7 days
    SESSION_COOKIE_NAME: str = "venturepulse_session"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DATA_DIR}/venturepulse.db")

    # OpenRouter API settings
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    API_TIMEOUT: int = 600  # 10 minutes
    MAX_TOKENS: int = 25192
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.95

    @property
    def database_path(self) -> Path:
        """Get the SQLite database file path."""
        return self.DATA_DIR / "venturepulse.db"

    @property
    def reports_dir(self) -> Path:
        """Get the reports storage directory."""
        return self.DATA_DIR / "reports"

    @property
    def specs_dir(self) -> Path:
        """Get the project specs storage directory."""
        return self.DATA_DIR / "specs"

    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.specs_dir.mkdir(parents=True, exist_ok=True)

    def validate(self) -> list[str]:
        """Validate required settings. Returns list of missing/invalid settings."""
        errors = []

        if not self.OPENROUTER_API_KEY:
            errors.append("OPENROUTER_API_KEY is required")

        # OAuth is required in production (non-dev mode)
        if not self.DEV_MODE:
            if not self.GOOGLE_CLIENT_ID and not self.GITHUB_CLIENT_ID:
                errors.append("At least one OAuth provider (Google or GitHub) must be configured")

        return errors


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
