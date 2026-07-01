from typing import Generic, Type, TypeVar, Any, Sequence
import uuid
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic Base Repository implementing standard async CRUD operations.
    Supports soft deletes automatically.
    """
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: uuid.UUID) -> ModelType | None:
        """Fetch a single record by UUID, excluding soft-deleted ones."""
        query = select(self.model).where(
            self.model.id == id,
            self.model.deleted_at.is_(None)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> Sequence[ModelType]:
        """Fetch multiple active records with pagination constraints."""
        query = (
            select(self.model)
            .where(self.model.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: dict[str, Any] | ModelType) -> ModelType:
        """Creates a new record database instance."""
        if isinstance(obj_in, dict):
            db_obj = self.model(**obj_in)
        else:
            db_obj = obj_in
            
        db.add(db_obj)
        await db.flush()
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: ModelType, obj_in: dict[str, Any]
    ) -> ModelType:
        """Updates an existing database record."""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
                
        db.add(db_obj)
        await db.flush()
        return db_obj

    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> ModelType | None:
        """Hard deletes a record from the database."""
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.flush()
        return db_obj

    async def soft_delete(self, db: AsyncSession, *, id: uuid.UUID) -> ModelType | None:
        """Applies soft deletion by setting deleted_at to func.now()."""
        query = (
            update(self.model)
            .where(self.model.id == id)
            .values(deleted_at=func.now())
            .returning(self.model)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def count(self, db: AsyncSession) -> int:
        """Returns count of all active database instances."""
        query = select(func.count()).select_from(self.model).where(self.model.deleted_at.is_(None))
        result = await db.execute(query)
        return result.scalar() or 0
