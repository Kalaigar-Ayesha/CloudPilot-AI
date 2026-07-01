from typing import Sequence
import uuid
from datetime import datetime, date
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import BillingRecord, PricingRecord, ForecastReport
from app.repositories.base import BaseRepository


class BillingRecordRepository(BaseRepository[BillingRecord]):
    """Repository managing billing logs."""
    def __init__(self):
        super().__init__(BillingRecord)

    async def get_summary(
        self, db: AsyncSession, account_ids: list[uuid.UUID], start: datetime, end: datetime
    ) -> dict:
        """Aggregates cost data by category and account."""
        if not account_ids:
            return {"total": 0.0, "by_category": {}, "by_account": {}}

        query = (
            select(
                self.model.category,
                self.model.cloud_account_id,
                func.sum(self.model.cost)
            )
            .where(
                self.model.cloud_account_id.in_(account_ids),
                self.model.usage_start >= start,
                self.model.usage_end <= end
            )
            .group_by(self.model.category, self.model.cloud_account_id)
        )
        
        result = await db.execute(query)
        rows = result.all()

        total = 0.0
        by_category = {}
        by_account = {}

        for category, acc_id, cost_val in rows:
            cost = float(cost_val or 0.0)
            total += cost
            
            by_category[category] = by_category.get(category, 0.0) + cost
            by_account[str(acc_id)] = by_account.get(str(acc_id), 0.0) + cost

        return {
            "total": total,
            "by_category": by_category,
            "by_account": by_account
        }

    async def get_trends(
        self, db: AsyncSession, account_ids: list[uuid.UUID], start: datetime, end: datetime, interval: str = "daily"
    ) -> Sequence[dict]:
        """Fetches daily or monthly cost history trends."""
        if not account_ids:
            return []

        trunc_field = func.date_trunc(interval, self.model.usage_start)
        query = (
            select(trunc_field, func.sum(self.model.cost))
            .where(
                self.model.cloud_account_id.in_(account_ids),
                self.model.usage_start >= start,
                self.model.usage_end <= end
            )
            .group_by(trunc_field)
            .order_by(trunc_field.asc())
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        return [
            {"date": row[0].isoformat() if isinstance(row[0], datetime) else str(row[0]), "cost": float(row[1])}
            for row in rows
        ]

    async def get_resource_costs(
        self, db: AsyncSession, resource_id: uuid.UUID, start: datetime, end: datetime
    ) -> float:
        """Fetches total aggregated cost for a single resource in a time window."""
        query = select(func.sum(self.model.cost)).where(
            self.model.resource_id == resource_id,
            self.model.usage_start >= start,
            self.model.usage_end <= end
        )
        result = await db.execute(query)
        return float(result.scalar() or 0.0)


class PricingRecordRepository(BaseRepository[PricingRecord]):
    """Repository managing pricing catalogs."""
    def __init__(self):
        super().__init__(PricingRecord)

    async def lookup_sku(
        self, db: AsyncSession, provider_id: str, sku: str, region: str
    ) -> PricingRecord | None:
        """Lookup direct pricing specification record."""
        query = select(self.model).where(
            self.model.provider_id == provider_id,
            self.model.sku == sku,
            self.model.region == region
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()


class ForecastReportRepository(BaseRepository[ForecastReport]):
    """Repository managing forecast data reports."""
    def __init__(self):
        super().__init__(ForecastReport)

    async def get_latest_forecast(
        self, db: AsyncSession, project_id: uuid.UUID
    ) -> ForecastReport | None:
        """Fetch the latest cost forecast generated for a project."""
        query = (
            select(self.model)
            .where(self.model.project_id == project_id)
            .order_by(self.model.created_at.desc())
            .limit(1)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()


# Instantiate singleton repositories
billing_record_repository = BillingRecordRepository()
pricing_record_repository = PricingRecordRepository()
forecast_report_repository = ForecastReportRepository()
