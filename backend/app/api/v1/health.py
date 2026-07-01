import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis

from app.core.config import settings
from app.database.session import get_db
from app.schemas.base import UnifiedResponse

logger = logging.getLogger("app.api.v1.health")
router = APIRouter()


@router.get("/live", response_model=UnifiedResponse[dict])
async def live_probe() -> dict:
    """Fast liveness check indicating API process is running."""
    return {
        "status": "success",
        "message": "CloudPilot AI core server is live.",
        "data": {"status": "UP"},
        "metadata": {},
        "errors": []
    }


@router.get("/ready", response_model=UnifiedResponse[dict])
async def readiness_probe(db: AsyncSession = Depends(get_db)) -> dict:
    """Checks database and Redis connection readiness."""
    health_status = {"db": "DOWN", "redis": "DOWN"}
    errors = []

    # 1. Verify PostgreSQL DB connection
    try:
        await db.execute(text("SELECT 1"))
        health_status["db"] = "UP"
    except Exception as e:
        logger.error(f"Readiness check failed for DB: {str(e)}")
        errors.append(f"PostgreSQL connection unavailable: {str(e)}")

    # 2. Verify Redis cache connection
    try:
        redis_client = redis.from_url(settings.REDIS_URL, socket_timeout=2)
        async with redis_client:
            await redis_client.ping()
        health_status["redis"] = "UP"
    except Exception as e:
        logger.error(f"Readiness check failed for Redis: {str(e)}")
        errors.append(f"Redis connection unavailable: {str(e)}")

    # Determine overall status
    is_ready = all(v == "UP" for v in health_status.values())
    status_label = "success" if is_ready else "error"
    message = "All integration streams are healthy." if is_ready else "One or more integrations are unavailable."

    return {
        "status": status_label,
        "message": message,
        "data": health_status,
        "metadata": {},
        "errors": errors
    }


@router.get("/health", response_model=UnifiedResponse[dict])
async def health_probe(db: AsyncSession = Depends(get_db)) -> dict:
    """Combined health overview endpoint."""
    ready_data = await readiness_probe(db)
    return {
        "status": ready_data["status"],
        "message": ready_data["message"],
        "data": {
            "application": "CloudPilot AI",
            "version": "1.0.0",
            "services": ready_data["data"]
        },
        "metadata": {},
        "errors": ready_data["errors"]
    }
