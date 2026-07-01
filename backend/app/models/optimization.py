import uuid
from sqlalchemy import String, ForeignKey, Numeric, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Recommendation(Base):
    """
    Recommendation model representing generated cost, security, or sustainability improvements.
    """
    __tablename__ = "recommendations"

    project_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("resources.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    provider_id: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # compute, storage, etc.
    rule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # critical, high, medium, low
    priority: Mapped[str] = mapped_column(String(20), nullable=False)  # high, medium, low
    current_state: Mapped[dict] = mapped_column(JSON, nullable=False)
    recommended_state: Mapped[dict] = mapped_column(JSON, nullable=False)
    estimated_savings: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0, nullable=False)
    confidence_score: Mapped[int] = mapped_column(default=100, nullable=False)
    business_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    technical_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(20), default="low", nullable=False)
    rollback_complexity: Mapped[str] = mapped_column(String(20), default="low", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)  # ACTIVE, APPLIED, DISMISSED
