import asyncio
import logging
from celery.utils.log import get_task_logger

from app.database.session import db_session_manager
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
    name="jobs.ai.conversation_cleanup",
    bind=True,
    max_retries=2,
    default_retry_delay=600
)
def conversation_cleanup_task(self) -> str:
    """
    Periodic task clean soft-deleted conversation history records.
    """
    logger.info("Starting conversation logs cleanup task...")

    async def execute_cleanup():
        async with db_session_manager._sessionmaker() as session:
            # Delete old messages that are soft-deleted
            from sqlalchemy import delete
            from app.models.ai import Conversation, Message
            
            # Simple purge execution
            q_conv = delete(Conversation).where(Conversation.deleted_at.is_not(None))
            q_msg = delete(Message).where(Message.deleted_at.is_not(None))
            
            c_res = await session.execute(q_conv)
            m_res = await session.execute(q_msg)
            
            await session.commit()
            return f"Purged conversation entries: threads ({c_res.rowcount}), messages ({m_res.rowcount})."  # type: ignore

    try:
        result = run_async(execute_cleanup())
        return result
    except Exception as exc:
        logger.warning(f"Retrying conversation cleanup task: {str(exc)}")
        raise self.retry(exc=exc)
