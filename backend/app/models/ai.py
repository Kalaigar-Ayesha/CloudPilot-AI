import uuid
from sqlalchemy import String, ForeignKey, Boolean, JSON, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Conversation(Base):
    """
    Conversation model representing a single chat thread.
    """
    __tablename__ = "conversations"

    project_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), default="New Conversation", nullable=False)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_info: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class Message(Base):
    """
    Message model representing a query or response within a thread.
    """
    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # system, user, assistant, tool
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tool_calls: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    citations: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ScheduledReport(Base):
    """
    ScheduledReport model for periodic markdown report generation.
    """
    __tablename__ = "scheduled_reports"

    project_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)  # executive, finops, technical
    format: Mapped[str] = mapped_column(String(20), default="markdown", nullable=False)  # markdown, html, pdf
    schedule_cron: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)
