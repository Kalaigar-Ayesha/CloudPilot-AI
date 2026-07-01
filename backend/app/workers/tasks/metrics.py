import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from celery.utils.log import get_task_logger

from app.database.session import db_session_manager
from app.repositories.cloud import resource_repository
from app.services.monitoring import MonitoringService
from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)


def run_async(coro):
    """Helper running asynchronous coroutines inside synchronous Celery worker processes."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(
    name="jobs.metrics.sync_resources",
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def sync_metrics_task(self) -> str:
    """
    Periodic job polling utilization metrics for all active virtual machines.
    """
    logger.info("Starting background metric synchronization task...")

    async def execute_sync():
        async with db_session_manager._sessionmaker() as session:
            # Query all running virtual machines
            from sqlalchemy import select
            from app.models.cloud import Resource
            q = select(Resource).where(
                Resource.resource_type == "virtual_machine",
                Resource.status == "running",
                Resource.deleted_at.is_(None)
            )
            resources = (await session.execute(q)).scalars().all()
            
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=15)

            sync_count = 0
            for res in resources:
                try:
                    await MonitoringService.sync_resource_metrics(
                        session,
                        res.id,
                        "cpu_utilization",
                        start_time,
                        end_time
                    )
                    sync_count += 1
                except Exception as e:
                    logger.error(f"Failed to sync metrics for resource {res.id}: {str(e)}")
            
            await session.commit()
            return f"Synchronized metrics for {sync_count} active resources."

    try:
        result = run_async(execute_sync())
        return result
    except Exception as exc:
        logger.warning(f"Retrying metrics sync task due to exception: {str(exc)}")
        raise self.retry(exc=exc)
