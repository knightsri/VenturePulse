"""
SQLAlchemy models for VenturePulse v2.
Defines User, Project, Analysis, Session, SectionFeedback, ShareableLink, and ShareLinkVisitor tables.
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
    UniqueConstraint,
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
    shareable_links: Mapped[list["ShareableLink"]] = relationship(
        "ShareableLink", back_populates="project", cascade="all, delete-orphan"
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
    # Temporary API key storage for recovery after restarts (cleared on completion)
    api_key_temp: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
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
    feedbacks: Mapped[list["SectionFeedback"]] = relationship(
        "SectionFeedback", back_populates="analysis", cascade="all, delete-orphan"
    )

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


class SectionFeedback(Base):
    """
    Section feedback model for tracking user ratings on analysis sections.

    Key principle: Project Owner = Author
    - Only project owner's ratings count as "author" ratings in comparisons
    - Other users' ratings are tracked but shown as supplementary info
    """

    __tablename__ = "section_feedbacks"
    __table_args__ = (
        UniqueConstraint(
            "analysis_id", "user_id", "section_key",
            name="uq_analysis_user_section"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_key: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # e.g., "section01-executive-summary"
    rating: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # 1 = thumbs up, -1 = thumbs down
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="feedbacks")
    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        rating_str = "👍" if self.rating == 1 else "👎"
        return f"<SectionFeedback {self.section_key} {rating_str} by user {self.user_id}>"

    @property
    def is_thumbs_up(self) -> bool:
        """Check if rating is thumbs up."""
        return self.rating == 1

    @property
    def is_thumbs_down(self) -> bool:
        """Check if rating is thumbs down."""
        return self.rating == -1


class ShareableLink(Base):
    """
    Shareable link model for private project access.
    Allows project owners to share temporary access to private projects.
    Multiple links can be created per project with different expiration dates.
    """

    __tablename__ = "shareable_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(String(42), unique=True, index=True, nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    visit_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="shareable_links")
    created_by: Mapped["User"] = relationship("User")
    visitors: Mapped[list["ShareLinkVisitor"]] = relationship(
        "ShareLinkVisitor", back_populates="shareable_link", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ShareableLink {self.key[:8]}... (project_id={self.project_id})>"

    @property
    def is_expired(self) -> bool:
        """Check if link is expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def unique_visitor_count(self) -> int:
        """Get count of unique visitors."""
        return len(self.visitors)


class ShareLinkVisitor(Base):
    """
    Tracks unique visitors to shareable links.
    Uses hash of IP + User-Agent for privacy-preserving visitor tracking.
    """

    __tablename__ = "share_link_visitors"
    __table_args__ = (
        UniqueConstraint(
            "shareable_link_id", "visitor_hash",
            name="uq_link_visitor"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shareable_link_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("shareable_links.id", ondelete="CASCADE"), nullable=False, index=True
    )
    visitor_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # SHA-256
    first_visit_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    last_visit_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    visit_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    shareable_link: Mapped["ShareableLink"] = relationship("ShareableLink", back_populates="visitors")

    def __repr__(self) -> str:
        return f"<ShareLinkVisitor {self.visitor_hash[:8]}... (link_id={self.shareable_link_id})>"
