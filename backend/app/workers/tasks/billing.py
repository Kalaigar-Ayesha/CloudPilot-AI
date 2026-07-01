import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from celery.utils.log import get_task_logger

from app.database.session import db_session_manager
from app.repositories.cloud import cloud_account_repository
from app.services.billing import BillingService
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
    name="jobs.billing.sync_accounts",
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def sync_billing_task(self) -> str:
    """
    Periodic background job collecting billing logs for all active integrations.
    """
    logger.info("Starting background billing logs sync task...")

    async def execute_sync():
        async with db_session_manager._sessionmaker() as session:
            # Query all registered accounts
            from sqlalchemy import select
            from app.models.cloud import CloudAccount
            q = select(CloudAccount).where(
                CloudAccount.status == "CONNECTED",
                CloudAccount.deleted_at.is_(None)
            )
            accounts = (await session.execute(q)).scalars().all()
            
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=7)

            sync_count = 0
            for acc in accounts:
                try:
                    await BillingService.sync_billing(
                        session,
                        acc.id,
                        start_time,
                        end_time
                    )
                    sync_count += 1
                except Exception as e:
                    logger.error(f"Failed to sync billing logs for account {acc.id}: {str(e)}")
            
            await session.commit()
            return f"Synchronized billing for {sync_count} active accounts."

    try:
        result = run_async(execute_sync())
        return result
    except Exception as exc:
        logger.warning(f"Retrying billing sync task: {str(exc)}")
        raise self.retry(exc=exc)


@celery_app.task(
    name="jobs.billing.refresh_pricing",
    bind=True,
    max_retries=2,
    default_retry_delay=3600
)
def refresh_pricing_task(self) -> str:
    """
    Weekly background task refreshing local public catalog retail rates database tables.
    """
    logger.info("Starting background pricing catalogs refresh task...")

    async def execute_refresh():
        async with db_session_manager._sessionmaker() as session:
            # Refresh AWS and Azure pricing databases (default regions)
            aws_count = await BillingService.refresh_pricing(session, "aws", "us-east-1")
            azure_count = await BillingService.refresh_pricing(session, "azure", "eastus")
            
            await session.commit()
            return f"Refreshed pricing: AWS ({aws_count}), Azure ({azure_count})."

    try:
        result = run_async(execute_refresh())
        return result
    except Exception as exc:
        logger.warning(f"Retrying pricing refresh task: {str(exc)}")
        raise self.retry(exc=exc)


@celery_app.task(
    name="jobs.billing.generate_forecast",
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def generate_forecast_task(self, project_id_str: str) -> str:
    """
    Daily forecasting task running linear regression calculations.
    """
    logger.info(f"Generating billing forecast projections for project {project_id_str}...")
    project_id = uuid.UUID(project_id_str)

    async def execute_forecast():
        async with db_session_manager._sessionmaker() as session:
            try:
                report = await BillingService.generate_forecast(session, project_id)
                await session.commit()
                return f"Forecast computed successfully. Baseline: {report.baseline_cost}"
            except Exception as e:
                await session.rollback()
                logger.error(f"Forecasting calculation failed: {str(e)}")
                raise e

    try:
        result = run_async(execute_forecast())
        return result
    except Exception as exc:
        logger.warning(f"Retrying forecasting computation: {str(exc)}")
        raise self.retry(exc=exc)
