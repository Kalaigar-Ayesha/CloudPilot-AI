from typing import Sequence
import uuid
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.monitoring import MonitoringSource, ResourceMetric
from app.repositories.base import BaseRepository


class MonitoringSourceRepository(BaseRepository[MonitoringSource]):
    """Repository managing APM/telemetry integration connections."""
    def __init__(self):
        super().__init__(MonitoringSource)

    async def get_by_project(
        self, db: AsyncSession, project_id: uuid.UUID
    ) -> Sequence[MonitoringSource]:
        """Fetch all monitoring integrations configured under a project workspace."""
        query = select(self.model).where(
            self.model.project_id == project_id,
            self.model.deleted_at.is_(None)
        )
        result = await db.execute(query)
        return result.scalars().all()


class MetricRepository:
    """
    Repository executing time-series queries and bulk insertions
    for normalized metrics.
    """
    @staticmethod
    async def save_metric(
        db: AsyncSession,
        resource_id: uuid.UUID,
        metric_type: str,
        timestamp: datetime,
        value: float,
        unit: str
    ) -> ResourceMetric:
        """Saves a single telemetry data point."""
        metric = ResourceMetric(
            resource_id=resource_id,
            metric_type=metric_type,
            timestamp=timestamp,
            value=value,
            unit=unit
        )
        db.add(metric)
        await db.flush()
        return metric

    @staticmethod
    async def get_metrics(
        db: AsyncSession,
        resource_id: uuid.UUID,
        metric_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> Sequence[ResourceMetric]:
        """Queries historical metric logs within a time window."""
        query = (
            select(ResourceMetric)
            .where(
                ResourceMetric.resource_id == resource_id,
                ResourceMetric.metric_type == metric_type,
                ResourceMetric.timestamp >= start_time,
                ResourceMetric.timestamp <= end_time
            )
            .order_by(ResourceMetric.timestamp.asc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_dashboard_summary(
        db: AsyncSession,
        resource_ids: list[uuid.UUID]
    ) -> dict:
        """Aggregates CPU/Memory utilization averages across resources."""
        if not resource_ids:
            return {"avg_cpu": 0.0, "avg_memory": 0.0}
            
        cpu_query = select(func.avg(ResourceMetric.value)).where(
            ResourceMetric.resource_id.in_(resource_ids),
            ResourceMetric.metric_type == "cpu_utilization"
        )
        mem_query = select(func.avg(ResourceMetric.value)).where(
            ResourceMetric.resource_id.in_(resource_ids),
            ResourceMetric.metric_type == "memory_utilization"
        )
        
        cpu_res = await db.execute(cpu_query)
        mem_res = await db.execute(mem_query)
        
        return {
            "avg_cpu": float(cpu_res.scalar() or 0.0),
            "avg_memory": float(mem_res.scalar() or 0.0)
        }


# Instantiate singleton repositories
monitoring_source_repository = MonitoringSourceRepository()
metric_repository = MetricRepository()
