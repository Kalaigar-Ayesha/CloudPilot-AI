import asyncio
import logging
import uuid
from celery.utils.log import get_task_logger

from app.database.session import db_session_manager
from app.services.cloud import CloudAccountService
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
    name="jobs.discovery.sync_resources",
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def discover_resources_task(self, account_id_str: str) -> str:
    """
    Background worker task running cloud resource discovery.
    Retries automatically on networking or provider API timeouts.
    """
    logger.info(f"Received discovery task for cloud account integration: {account_id_str}")
    account_id = uuid.UUID(account_id_str)

    async def run_sync():
        # Open separate database session for task execution
        async with db_session_manager._sessionmaker() as session:
            try:
                sync_count = await CloudAccountService.discover_and_sync_resources(session, account_id)
                await session.commit()
                return f"Successfully synchronized {sync_count} resources."
            except Exception as e:
                await session.rollback()
                logger.error(f"Discovery sync task failed: {str(e)}")
                raise e

    try:
        result = run_async(run_sync())
        return result
    except Exception as exc:
        # Retry task on unexpected exceptions
        logger.warning(f"Retrying task due to discovery sync exception: {str(exc)}")
        raise self.retry(exc=exc)
