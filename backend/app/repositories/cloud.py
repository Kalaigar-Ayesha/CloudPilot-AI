from typing import Sequence
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cloud import CloudAccount, CloudCredentials, Resource
from app.repositories.base import BaseRepository


class CloudAccountRepository(BaseRepository[CloudAccount]):
    """Repository managing cloud integration configurations."""
    def __init__(self):
        super().__init__(CloudAccount)

    async def get_by_project(
        self, db: AsyncSession, project_id: uuid.UUID
    ) -> Sequence[CloudAccount]:
        """Fetch all cloud integrations registered under a project workspace."""
        query = select(self.model).where(
            self.model.project_id == project_id,
            self.model.deleted_at.is_(None)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_with_credentials(
        self, db: AsyncSession, account_id: uuid.UUID
    ) -> CloudAccount | None:
        """Fetch cloud integration including linked encrypted credentials."""
        query = (
            select(self.model)
            .options(selectinload(self.model.credentials))
            .where(
                self.model.id == account_id,
                self.model.deleted_at.is_(None)
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()


class CloudCredentialsRepository(BaseRepository[CloudCredentials]):
    def __init__(self):
        super().__init__(CloudCredentials)

    async def get_by_account(
        self, db: AsyncSession, cloud_account_id: uuid.UUID
    ) -> CloudCredentials | None:
        """Fetch credentials configuration registered under a cloud account."""
        query = select(self.model).where(self.model.cloud_account_id == cloud_account_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()


class ResourceRepository(BaseRepository[Resource]):
    """Repository managing discovered normalized cloud resources."""
    def __init__(self):
        super().__init__(Resource)

    async def get_by_external_id(
        self, db: AsyncSession, cloud_account_id: uuid.UUID, external_id: str
    ) -> Resource | None:
        """Fetch a single resource by its cloud provider identifier."""
        query = select(self.model).where(
            self.model.cloud_account_id == cloud_account_id,
            self.model.external_id == external_id,
            self.model.deleted_at.is_(None)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_account(
        self, db: AsyncSession, cloud_account_id: uuid.UUID
    ) -> Sequence[Resource]:
        """Fetch active resource inventory catalog discovered under an account."""
        query = (
            select(self.model)
            .options(
                selectinload(self.model.compute),
                selectinload(self.model.storage),
                selectinload(self.model.database),
                selectinload(self.model.networking)
            )
            .where(
                self.model.cloud_account_id == cloud_account_id,
                self.model.deleted_at.is_(None)
            )
        )
        result = await db.execute(query)
        return result.scalars().all()


# Instantiate singleton repositories
cloud_account_repository = CloudAccountRepository()
cloud_credentials_repository = CloudCredentialsRepository()
resource_repository = ResourceRepository()
