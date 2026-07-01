from typing import Sequence
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import Conversation, Message, ScheduledReport
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """Repository managing chat conversations."""
    def __init__(self):
        super().__init__(Conversation)

    async def get_by_project(
        self, db: AsyncSession, project_id: uuid.UUID
    ) -> Sequence[Conversation]:
        """Fetch all active chat threads for a project."""
        query = (
            select(self.model)
            .where(
                self.model.project_id == project_id,
                self.model.deleted_at.is_(None)
            )
            .order_by(self.model.pinned.desc(), self.model.updated_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()


class MessageRepository(BaseRepository[Message]):
    """Repository managing conversation messages."""
    def __init__(self):
        super().__init__(Message)

    async def get_by_conversation(
        self, db: AsyncSession, conversation_id: uuid.UUID
    ) -> Sequence[Message]:
        """Fetch all chronological messages inside a conversation thread."""
        query = (
            select(self.model)
            .where(
                self.model.conversation_id == conversation_id,
                self.model.deleted_at.is_(None)
            )
            .order_by(self.model.created_at.asc())
        )
        result = await db.execute(query)
        return result.scalars().all()


class ScheduledReportRepository(BaseRepository[ScheduledReport]):
    """Repository managing scheduled reports."""
    def __init__(self):
        super().__init__(ScheduledReport)

    async def get_by_project(
        self, db: AsyncSession, project_id: uuid.UUID
    ) -> Sequence[ScheduledReport]:
        """Fetch all report schedules configured for a project."""
        query = select(self.model).where(
            self.model.project_id == project_id,
            self.model.deleted_at.is_(None)
        )
        result = await db.execute(query)
        return result.scalars().all()


# Instantiate singleton repositories
conversation_repository = ConversationRepository()
message_repository = MessageRepository()
scheduled_report_repository = ScheduledReportRepository()
