"""
SQLAlchemy models for VenturePulse v2.
Defines User, Project, Analysis, and Session tables.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class User(Base):
    """User model for authenticated users."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)  # google, github
    provider_id: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # admin, approved, pending
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    preferred_models: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # User's saved model preferences

    # Relationships
    projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"

    @property
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == "admin"

    @property
    def is_approved(self) -> bool:
        """Check if user is approved (admin or approved role)."""
        return self.role in ("admin", "approved")

    @property
    def is_pending(self) -> bool:
        """Check if user is pending approval."""
        return self.role == "pending"


class Project(Base):
    """Project model for user-created analysis projects."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    spec_content: Mapped[str] = mapped_column(Text, nullable=False)
    spec_file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="projects")
    analyses: Mapped[list["Analysis"]] = relationship(
        "Analysis", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        visibility = "public" if self.is_public else "private"
        return f"<Project {self.slug} ({visibility})>"


class Analysis(Base):
    """Analysis model for tracking analysis runs."""

    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending, running, completed, failed
    report_folder_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    sections_completed: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    cost_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    total_cost_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="analyses")

    def __repr__(self) -> str:
        return f"<Analysis {self.id} ({self.status})>"

    @property
    def is_pending(self) -> bool:
        """Check if analysis is pending."""
        return self.status == "pending"

    @property
    def is_running(self) -> bool:
        """Check if analysis is running."""
        return self.status == "running"

    @property
    def is_completed(self) -> bool:
        """Check if analysis completed successfully."""
        return self.status == "completed"

    @property
    def is_failed(self) -> bool:
        """Check if analysis failed."""
        return self.status == "failed"


class Session(Base):
    """Session model for user authentication sessions."""

    __tablename__ = "sessions"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<Session {self.token[:8]}... (user_id={self.user_id})>"

    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at
