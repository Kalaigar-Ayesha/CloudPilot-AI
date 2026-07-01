import uuid
from datetime import datetime, date
from sqlalchemy import String, ForeignKey, DateTime, Numeric, JSON, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class BillingRecord(Base):
    """
    BillingRecord model representing cost entries synced from providers.
    """
    __tablename__ = "billing_records"

    cloud_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cloud_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("resources.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    usage_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    usage_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cost: Mapped[float] = mapped_column(Numeric(15, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    usage_type: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # Compute, Storage, etc.
    raw_billing_payload: Mapped[dict] = mapped_column(JSON, nullable=False)


class PricingRecord(Base):
    """
    PricingRecord storing public instance catalog retail price matrix rates.
    """
    __tablename__ = "pricing_records"

    provider_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    service_code: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_specification: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    unit_price_hourly: Mapped[float] = mapped_column(Numeric(15, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)


class ForecastReport(Base):
    """
    ForecastReport storing daily/monthly future projections.
    """
    __tablename__ = "forecast_reports"

    project_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    cloud_account_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("cloud_accounts.id", ondelete="CASCADE"),
        nullable=True
    )
    forecast_type: Mapped[str] = mapped_column(String(50), nullable=False)  # cost, usage
    baseline_cost: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    optimistic_cost: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    pessimistic_cost: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    forecast_data: Mapped[dict] = mapped_column(JSON, nullable=False)  # List of predicted points
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
