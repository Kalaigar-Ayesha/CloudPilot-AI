import logging
import uuid
from typing import List

logger = logging.getLogger("app.api.v1.monitoring")
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import PermissionChecker
from app.schemas.base import UnifiedResponse
from app.schemas.monitoring import (
    MonitoringSourceConnect,
    MonitoringSourceOut,
    MonitoringSourceValidate,
    MetricQueryResponse,
    NormalizedMetricOut,
)
from app.services.monitoring import MonitoringService
from app.repositories.monitoring import metric_repository

router = APIRouter()


@router.post(
    "/connect",
    response_model=UnifiedResponse[MonitoringSourceOut],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(PermissionChecker("connect_provider"))]
)
async def connect_monitoring_source(
    payload: MonitoringSourceConnect,
    db: AsyncSession = Depends(get_db)
):
    """Connects and registers a new telemetry provider integration."""
    source = await MonitoringService.connect_source(db, payload)
    await db.commit()
    return {
        "status": "success",
        "message": "Monitoring integration connected successfully.",
        "data": source,
        "metadata": {},
        "errors": []
    }


@router.post(
    "/validate",
    response_model=UnifiedResponse[dict],
    dependencies=[Depends(PermissionChecker("connect_provider"))]
)
async def validate_monitoring_source(payload: MonitoringSourceValidate):
    """Dry-run validation checks for monitoring credentials."""
    is_valid = await MonitoringService.validate_credentials(payload)
    return {
        "status": "success" if is_valid else "error",
        "message": "Monitoring connection validated successfully." if is_valid else "Validation failed.",
        "data": {"valid": is_valid},
        "metadata": {},
        "errors": []
    }


@router.get(
    "/providers",
    response_model=UnifiedResponse[List[dict]],
    dependencies=[Depends(PermissionChecker("view_inventory"))]
)
async def get_monitoring_providers():
    """Lists supported monitoring platforms."""
    providers = [
        {"id": "prometheus", "name": "Prometheus", "is_active": True},
        {"id": "cloudwatch", "name": "AWS CloudWatch", "is_active": True},
        {"id": "azure_monitor", "name": "Azure Monitor", "is_active": True},
        {"id": "google_monitor", "name": "Google Cloud Monitoring", "is_active": True},
        {"id": "datadog", "name": "Datadog", "is_active": True},
        {"id": "new_relic", "name": "New Relic", "is_active": True}
    ]
    return {
        "status": "success",
        "message": "Retrieved supported monitoring providers.",
        "data": providers,
        "metadata": {},
        "errors": []
    }


@router.get(
    "/accounts",
    response_model=UnifiedResponse[List[MonitoringSourceOut]],
    dependencies=[Depends(PermissionChecker("view_inventory"))]
)
async def get_monitoring_accounts(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Lists registered monitoring connections in a workspace."""
    sources = await MonitoringService.get_sources(db, project_id)
    return {
        "status": "success",
        "message": f"Retrieved {len(sources)} monitoring integrations.",
        "data": sources,
        "metadata": {},
        "errors": []
    }


@router.delete(
    "/{id}",
    response_model=UnifiedResponse[None],
    dependencies=[Depends(PermissionChecker("disconnect_provider"))]
)
async def disconnect_monitoring_source(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Deletes a monitoring connection integration."""
    await MonitoringService.delete_source(db, id)
    await db.commit()
    return {
        "status": "success",
        "message": "Monitoring integration removed successfully.",
        "data": None,
        "metadata": {},
        "errors": []
    }


@router.get(
    "/{id}/health",
    response_model=UnifiedResponse[dict],
    dependencies=[Depends(PermissionChecker("view_inventory"))]
)
async def get_monitoring_source_health(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Runs live health checking on integration endpoint."""
    health_details = await MonitoringService.get_source_health(db, id)
    return {
        "status": "success",
        "message": "Retrieved live monitoring status checking.",
        "data": health_details,
        "metadata": {},
        "errors": []
    }


@router.get(
    "/metrics/dashboard",
    response_model=UnifiedResponse[dict],
    dependencies=[Depends(PermissionChecker("view_inventory"))]
)
async def get_dashboard_telemetry(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves workspace aggregated averages dashboard details."""
    metrics = await MonitoringService.get_dashboard_metrics(db, project_id)
    return {
        "status": "success",
        "message": "Dashboard utilization metrics retrieved.",
        "data": metrics,
        "metadata": {},
        "errors": []
    }


@router.get(
    "/metrics/resource/{id}",
    response_model=UnifiedResponse[MetricQueryResponse],
    dependencies=[Depends(PermissionChecker("view_inventory"))]
)
async def get_resource_metrics(
    id: uuid.UUID,
    metric_type: str = Query("cpu_utilization"),
    hours: int = Query(24, ge=1, le=720),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves metric range records for a single resource."""
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)

    # Sync fresh metrics first
    try:
        await MonitoringService.sync_resource_metrics(db, id, metric_type, start_time, end_time)
        await db.commit()
    except Exception as e:
        # Log error but fallback to local database results
        logger.warning(f"Failed to sync fresh resource metrics: {str(e)}")

    # Load from DB
    records = await metric_repository.get_metrics(db, id, metric_type, start_time, end_time)
    
    data_points = [
        NormalizedMetricOut(timestamp=r.timestamp, value=r.value, unit=r.unit)
        for r in records
    ]

    return {
        "status": "success",
        "message": f"Retrieved {len(data_points)} data points.",
        "data": MetricQueryResponse(
            resource_id=id,
            metric_type=metric_type,
            unit=data_points[0].unit if data_points else "percent",
            data_points=data_points
        ),
        "metadata": {},
        "errors": []
    }
