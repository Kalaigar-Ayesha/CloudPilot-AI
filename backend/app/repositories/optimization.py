from typing import Sequence
import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.optimization import Recommendation
from app.repositories.base import BaseRepository


class RecommendationRepository(BaseRepository[Recommendation]):
    """Repository managing optimization recommendation items."""
    def __init__(self):
        super().__init__(Recommendation)

    async def get_by_project(
        self, db: AsyncSession, project_id: uuid.UUID
    ) -> Sequence[Recommendation]:
        """Fetch all active recommendations for a project."""
        query = select(self.model).where(
            self.model.project_id == project_id,
            self.model.status == "ACTIVE",
            self.model.deleted_at.is_(None)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_resource(
        self, db: AsyncSession, resource_id: uuid.UUID
    ) -> Sequence[Recommendation]:
        """Fetch active recommendations targeting a specific resource UUID."""
        query = select(self.model).where(
            self.model.resource_id == resource_id,
            self.model.status == "ACTIVE",
            self.model.deleted_at.is_(None)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_total_savings(self, db: AsyncSession, project_id: uuid.UUID) -> float:
        """Sums estimated monthly savings for active recommendations in a project."""
        query = select(func.sum(self.model.estimated_savings)).where(
            self.model.project_id == project_id,
            self.model.status == "ACTIVE",
            self.model.deleted_at.is_(None)
        )
        result = await db.execute(query)
        return float(result.scalar() or 0.0)


# Instantiate singleton repository
recommendation_repository = RecommendationRepository()
