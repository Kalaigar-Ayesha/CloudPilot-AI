import logging
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.core.config import settings
from app.domains.monitoring.adapters.factory import MonitoringProviderFactory
from app.exceptions.base import ValidationException, ProviderException
from app.models.monitoring import MonitoringSource, ResourceMetric
from app.repositories.monitoring import (
    monitoring_source_repository,
    metric_repository,
)
from app.repositories.cloud import resource_repository
from app.schemas.monitoring import MonitoringSourceConnect, MonitoringSourceValidate
from app.utils.security import encrypt_payload, decrypt_payload

logger = logging.getLogger("app.services.monitoring")


class MonitoringService:
    """
    Coordinates APM metrics integrations, query range aggregations,
    database writing, and Redis caching.
    """
    
    @staticmethod
    async def validate_credentials(payload: MonitoringSourceValidate) -> bool:
        """Standalone validation check."""
        try:
            adapter_class = MonitoringProviderFactory.get_adapter(payload.provider_id)
            adapter = adapter_class()
            adapter.connect(payload.endpoint_url, payload.credentials)
            is_valid = adapter.validate()
            adapter.disconnect()
            return is_valid
        except Exception as e:
            logger.warning(f"Monitoring validation failed: {str(e)}")
            raise ValidationException(f"Connection validation failed: {str(e)}")

    @staticmethod
    async def connect_source(db: AsyncSession, payload: MonitoringSourceConnect) -> MonitoringSource:
        """Connects and registers a new monitoring source integration."""
        # 1. Run validation
        validate_payload = MonitoringSourceValidate(
            provider_id=payload.provider_id,
            endpoint_url=payload.endpoint_url,
            credentials=payload.credentials
        )
        await MonitoringService.validate_credentials(validate_payload)

        # 2. Encrypt credentials
        plaintext = json.dumps(payload.credentials)
        encrypted = encrypt_payload(plaintext)

        # 3. Save database entry
        source_data = {
            "project_id": payload.project_id,
            "provider_id": payload.provider_id,
            "name": payload.name,
            "endpoint_url": payload.endpoint_url,
            "encrypted_credentials": encrypted,
            "status": "ACTIVE"
        }
        db_source = await monitoring_source_repository.create(db, obj_in=source_data)
        await db.flush()

        logger.info(f"Connected monitoring integration {payload.name} ({payload.provider_id}) for project {payload.project_id}")
        return db_source

    @staticmethod
    async def get_sources(db: AsyncSession, project_id: uuid.UUID) -> Sequence[MonitoringSource]:
        """Fetch all connected monitoring sources for a project."""
        return await monitoring_source_repository.get_by_project(db, project_id)

    @staticmethod
    async def delete_source(db: AsyncSession, source_id: uuid.UUID) -> None:
        """Removes a monitoring integration."""
        source = await monitoring_source_repository.get(db, source_id)
        if not source:
            raise ValidationException("Monitoring source integration not found.")
        await monitoring_source_repository.remove(db, id=source_id)
        logger.info(f"Removed monitoring integration {source_id}")

    @staticmethod
    async def get_source_health(db: AsyncSession, source_id: uuid.UUID) -> Dict[str, Any]:
        """Runs live health ping check using adapter."""
        source = await monitoring_source_repository.get(db, source_id)
        if not source:
            raise ValidationException("Monitoring source not found.")

        try:
            # Recover credentials
            plaintext = decrypt_payload(source.encrypted_credentials)
            creds = json.loads(plaintext)

            # Resolve adapter
            adapter_class = MonitoringProviderFactory.get_adapter(source.provider_id)
            adapter = adapter_class()

            adapter.connect(source.endpoint_url, creds)
            health = adapter.health_check()
            adapter.disconnect()

            return {
                "monitoring_source_id": source_id,
                "status": "ACTIVE" if health == "healthy" else "ERROR",
                "health": health
            }
        except Exception as e:
            logger.error(f"Monitoring health check failed for source {source_id}: {str(e)}")
            return {
                "monitoring_source_id": source_id,
                "status": "ERROR",
                "health": "unhealthy",
                "error": str(e)
            }

    @staticmethod
    async def sync_resource_metrics(
        db: AsyncSession,
        resource_id: uuid.UUID,
        metric_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[ResourceMetric]:
        """
        Polls telemetry metrics via adapter, saves to time-series DB tables,
        and manages Redis cache.
        """
        # 1. Fetch resource metadata mapping
        resource = await resource_repository.get(db, resource_id)
        if not resource:
            raise ValidationException(f"Resource {resource_id} not found.")

        # 2. Retrieve connected monitoring integrations under the project
        from app.repositories.cloud import cloud_account_repository
        account = await cloud_account_repository.get(db, resource.cloud_account_id)
        if not account:
            raise ValidationException(f"Cloud account {resource.cloud_account_id} not found.")
        project_id = account.project_id
        
        sources = await monitoring_source_repository.get_by_project(db, project_id)
        if not sources:
            logger.warning(f"No active monitoring source integrations registered for project {project_id}")
            return []

        # Use the first active source connection as primary
        source = sources[0]

        # 3. Recover credentials and resolve adapter
        plaintext = decrypt_payload(source.encrypted_credentials)
        creds = json.loads(plaintext)

        adapter_class = MonitoringProviderFactory.get_adapter(source.provider_id)
        adapter = adapter_class()

        # Execute metric fetch
        adapter.connect(source.endpoint_url, creds)
        
        # Check custom type mapping
        try:
            points = adapter.fetch_resource_metrics(
                resource_id=resource.external_id,
                metric_type=metric_type,
                start_time=start_time,
                end_time=end_time
            )
        except Exception as e:
            logger.error(f"Failed to fetch metrics via adapter {source.provider_id}: {str(e)}")
            points = []
        finally:
            adapter.disconnect()

        # 4. Insert data points to database
        db_metrics = []
        for pt in points:
            db_metric = await metric_repository.save_metric(
                db,
                resource_id=resource_id,
                metric_type=metric_type,
                timestamp=pt.timestamp.replace(tzinfo=timezone.utc),
                value=pt.value,
                unit=pt.unit
            )
            db_metrics.append(db_metric)

        # 5. Evict Redis caches
        try:
            r = redis.from_url(settings.REDIS_URL)
            async with r:
                cache_key = f"cloudpilot:res:{resource_id}:metrics:{metric_type}:*"
                keys = await r.keys(cache_key)
                if keys:
                    await r.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {str(e)}")

        return db_metrics

    @staticmethod
    async def get_dashboard_metrics(db: AsyncSession, project_id: uuid.UUID) -> Dict[str, Any]:
        """Fetches aggregated averages for workspace dashboard widgets (Cache-aside pattern)."""
        cache_key = f"cloudpilot:proj:{project_id}:metrics:dashboard"
        
        # 1. Query Redis Cache
        try:
            r = redis.from_url(settings.REDIS_URL, socket_timeout=2)
            async with r:
                cached = await r.get(cache_key)
                if cached:
                    return json.loads(cached)
        except Exception as e:
            logger.warning(f"Redis cache query failed: {str(e)}")

        # 2. Cache Miss - Query DB
        # Fetch all account resources
        from app.repositories.cloud import cloud_account_repository
        accounts = await cloud_account_repository.get_by_project(db, project_id)
        
        resource_ids = []
        for acc in accounts:
            resources = await resource_repository.get_by_account(db, acc.id)
            resource_ids.extend([res.id for res in resources])

        summary = await metric_repository.get_dashboard_summary(db, resource_ids)

        # 3. Write cache with 5 minute expiration
        try:
            r = redis.from_url(settings.REDIS_URL)
            async with r:
                await r.set(cache_key, json.dumps(summary), ex=300)
        except Exception as e:
            logger.warning(f"Writing dashboard metrics cache failed: {str(e)}")

        return summary
