import logging
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

logger = logging.getLogger("app.database.session")


class DatabaseSessionManager:
    """
    Manages SQLAlchemy asynchronous engine, session factories,
    connection pooling, and health verification checks.
    """
    def __init__(self, database_url: str):
        # Configure the Async Engine with appropriate pooling limits
        self._engine = create_async_engine(
            database_url,
            pool_pre_ping=True,
            pool_size=20,
            max_overflow=10,
            pool_recycle=1800,  # 30 minutes
        )
        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    @property
    def engine(self):
        return self._engine

    async def close(self) -> None:
        """Tear down and dispose connection pools."""
        if self._engine is None:
            return
        await self._engine.dispose()
        logger.info("Database session engine pools disposed successfully.")

    async def verify_connection(self) -> None:
        """Runs a raw SQL ping to verify DB readiness."""
        async with self._sessionmaker() as session:
            await session.execute(text("SELECT 1"))

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        FastAPI dependency generator.
        Automatically yields a session and cleans it up on completion.
        """
        async with self._sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Instantiate singleton database session manager
db_session_manager = DatabaseSessionManager(settings.DATABASE_URL)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection helper for FastAPI endpoints."""
    async for session in db_session_manager.get_session():
        yield session
