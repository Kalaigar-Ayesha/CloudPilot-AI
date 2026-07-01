import asyncio
import logging
import uuid
from celery.utils.log import get_task_logger

from app.database.session import db_session_manager
from app.services.optimization import OptimizationService
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
    name="jobs.optimization.daily_scan",
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def daily_scan_task(self, project_id_str: str) -> str:
    """
    Daily optimization rule evaluator scanning active resources inventory.
    """
    logger.info(f"Starting daily optimization scan for project {project_id_str}...")
    project_id = uuid.UUID(project_id_str)

    async def execute_scan():
        async with db_session_manager._sessionmaker() as session:
            try:
                results = await OptimizationService.run_optimization_scan(session, project_id)
                await session.commit()
                return f"Optimization scan finished. Recommendations: {results['recommendations_count']}."
            except Exception as e:
                await session.rollback()
                logger.error(f"Daily optimization scan failed: {str(e)}")
                raise e

    try:
        result = run_async(execute_scan())
        return result
    except Exception as exc:
        logger.warning(f"Retrying optimization scan: {str(exc)}")
        raise self.retry(exc=exc)
