from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    UserRepository subclasses BaseRepository for custom operations on User entities.
    """
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        """
        Retrieves a user by their lowercase email address.
        """
        query = select(self.model).where(
            self.model.email == email.lower(),
            self.model.deleted_at.is_(None)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()


# Instantiate singleton userRepository instance
user_repository = UserRepository()
