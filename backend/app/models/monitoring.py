import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Double, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.core.config import settings


class MonitoringSource(Base):
    """
    MonitoringSource model representing connection configurations to metrics providers (Datadog, Prometheus, etc.).
    """
    __tablename__ = "monitoring_sources"

    project_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    provider_id: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    endpoint_url: Mapped[str] = mapped_column(String(500), nullable=False)
    encrypted_credentials: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)


class ResourceMetric(Base):
    """
    ResourceMetric represents historical time-series telemetry records.
    Conforms to PostgreSQL monthly partitioned logic definitions.
    """
    __tablename__ = "resource_metrics"

    # Primary key is composite (id, timestamp) for partitioning
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    resource_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=not settings.DATABASE_URL.startswith("sqlite"),
        nullable=False
    )
    value: Mapped[float] = mapped_column(Double, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)

