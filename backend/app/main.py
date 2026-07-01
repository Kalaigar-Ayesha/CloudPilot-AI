import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging
from app.database.session import db_session_manager
from app.middleware.logging import LoggingMiddleware
from app.middleware.exceptions import GlobalExceptionMiddleware
from app.api.v1.router import api_v1_router

logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    App lifespan context manager handling startup and shutdown actions.
    """
    # 1. Initialize Logging
    configure_logging()
    logger.info("Starting CloudPilot AI backend application server...", extra={"env": settings.APP_ENV})

    # 2. Database Connection Pool Check
    try:
        if settings.DATABASE_URL.startswith("sqlite"):
            from app.models.base import Base
            async with db_session_manager.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("SQLite database tables created successfully.")
        else:
            # Check connection pooling session manager status
            await db_session_manager.verify_connection()
            logger.info("PostgreSQL database connection pool verified successfully.")
    except Exception as e:
        logger.critical("Database initialization failure during startup.", exc_info=True)
        raise SystemExit("Fatal: Database unavailable.") from e

    yield

    # Shutdown
    logger.info("Shutting down CloudPilot AI backend application server...")
    await db_session_manager.close()
    logger.info("Database connection pools closed successfully.")


# Instantiate FastAPI Application
app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise-Grade Multi-Cloud DevOps Copilot API Engine",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG or settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.DEBUG or settings.APP_ENV != "production" else None,
)

# Enforce Middlewares
app.add_middleware(GlobalExceptionMiddleware)
app.add_middleware(LoggingMiddleware)

# Enable CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route mounting
app.include_router(api_v1_router, prefix="/api/v1")
