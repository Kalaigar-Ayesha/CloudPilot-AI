import asyncio
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.database.session import get_db
from app.models.base import Base
from app.main import app

# Create a dedicated test database engine
test_db_url = settings.DATABASE_URL
if "sqlite" in test_db_url:
    if "dev.db" in test_db_url:
        test_db_url = test_db_url.replace("dev.db", "test_db.db")
    else:
        test_db_url = test_db_url.rsplit("/", 1)[0] + "/test_db.db"

test_engine = create_async_engine(
    test_db_url,
    poolclass=None  # No pooling needed for single tests run
)

test_sessionmaker = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db() -> AsyncGenerator[None, None]:
    """
    Initializes test database by creating and dropping schemas.
    """
    async with test_engine.begin() as conn:
        # Clean slate at start of session
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    yield
    
    async with test_engine.begin() as conn:
        # Drop all tables after testing session finishes
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yields clean transaction session, rolling back updates on completion."""
    connection = await test_engine.connect()
    transaction = await connection.begin()
    
    async with AsyncSession(bind=connection, expire_on_commit=False) as session:
        yield session
        await session.rollback()
        
    await transaction.rollback()
    await connection.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Yields Async HTTPX client, overriding the database session dependency injection.
    """
    async def override_get_db():
        yield db_session

    # Apply database dependency override
    app.dependency_overrides[get_db] = override_get_db
    
    # Configure Async transport
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver"
    ) as ac:
        yield ac
        
    app.dependency_overrides.clear()
