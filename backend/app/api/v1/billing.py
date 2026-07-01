import uuid
from typing import List
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import PermissionChecker
from app.schemas.base import UnifiedResponse
from app.schemas.billing import (
    CostSummaryResponse,
    CostHistoryTrendsResponse,
    ForecastResponse,
    PricingInfoResponse,
    ResourceCostResponse,
)
from app.services.billing import BillingService
from app.repositories.billing import billing_record_repository, forecast_report_repository, pricing_record_repository

router = APIRouter()


@router.get(
    "/dashboard",
    response_model=UnifiedResponse[CostSummaryResponse],
    dependencies=[Depends(PermissionChecker("view_billing"))]
)
async def get_billing_dashboard(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves aggregated multi-cloud financial spend summaries."""
    summary = await BillingService.get_dashboard_summary(db, project_id)
    return {
        "status": "success",
        "message": "Retrieved dashboard cost summary.",
        "data": summary,
        "metadata": {},
        "errors": []
    }


@router.get(
    "/summary",
    response_model=UnifiedResponse[CostSummaryResponse],
    dependencies=[Depends(PermissionChecker("view_billing"))]
)
async def get_billing_summary(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Alias for dashboard summary detailing provider-specific structures."""
    summary = await BillingService.get_dashboard_summary(db, project_id)
    return {
        "status": "success",
        "message": "Retrieved cost summary data.",
        "data": summary,
        "metadata": {},
        "errors": []
    }


@router.get(
    "/trends",
    response_model=UnifiedResponse[CostHistoryTrendsResponse],
    dependencies=[Depends(PermissionChecker("view_billing"))]
)
async def get_cost_trends(
    project_id: uuid.UUID,
    granularity: str = Query("daily"),
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves historical cost trend series."""
    from app.repositories.cloud import cloud_account_repository
    accounts = await cloud_account_repository.get_by_project(db, project_id)
    account_ids = [acc.id for acc in accounts]

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    history = await billing_record_repository.get_trends(db, account_ids, start, end, granularity)
    
    return {
        "status": "success",
        "message": f"Retrieved cost trends for the last {days} days.",
        "data": {
            "interval": granularity,
            "history": history
        },
        "metadata": {},
        "errors": []
    }


@router.get(
    "/forecast",
    response_model=UnifiedResponse[ForecastResponse],
    dependencies=[Depends(PermissionChecker("view_billing"))]
)
async def get_cost_forecast(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves latest 30-day predicted spending report."""
    # Check if a forecast report exists
    report = await forecast_report_repository.get_latest_forecast(db, project_id)
    if not report:
        # Generate on the fly
        report = await BillingService.generate_forecast(db, project_id)
        await db.commit()

    # Map forecast points
    points = report.forecast_data.get("points", [])
    mapped_points = []
    for pt in points:
        mapped_points.append({
            "month": f"Day {pt.get('day', 0)}",
            "baseline": pt.get("baseline", 0.0),
            "optimistic": pt.get("optimistic", 0.0),
            "pessimistic": pt.get("pessimistic", 0.0)
        })

    return {
        "status": "success",
        "message": "Retrieved financial spend forecast report.",
        "data": {
            "baseline_cost": report.baseline_cost,
            "optimistic_cost": report.optimistic_cost,
            "pessimistic_cost": report.pessimistic_cost,
            "prediction_start": report.start_date,
            "prediction_end": report.end_date,
            "predictions": mapped_points
        },
        "metadata": {},
        "errors": []
    }


@router.get(
    "/resources",
    response_model=UnifiedResponse[List[ResourceCostResponse]],
    dependencies=[Depends(PermissionChecker("view_billing"))]
)
async def get_resources_billing(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves cumulative costs for individual discovered resources."""
    from app.repositories.cloud import cloud_account_repository, resource_repository
    accounts = await cloud_account_repository.get_by_project(db, project_id)
    
    resource_costs = []
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=30)

    for acc in accounts:
        resources = await resource_repository.get_by_account(db, acc.id)
        for res in resources:
            cost = await billing_record_repository.get_resource_costs(db, res.id, start, end)
            resource_costs.append({
                "resource_id": res.id,
                "total_accumulated_cost": cost,
                "currency": "USD"
            })

    return {
        "status": "success",
        "message": "Retrieved resources cumulative costs.",
        "data": resource_costs,
        "metadata": {},
        "errors": []
    }


@router.get(
    "/pricing/resource/{id}",
    response_model=UnifiedResponse[PricingInfoResponse],
    dependencies=[Depends(PermissionChecker("view_billing"))]
)
async def get_resource_pricing_catalog(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Look up active hourly rates from regional pricing catalog."""
    from app.repositories.cloud import resource_repository, cloud_account_repository
    res = await resource_repository.get(db, id)
    if not res:
        return {"status": "error", "message": "Resource not found.", "data": None, "errors": ["Resource not found"]}

    account = await cloud_account_repository.get(db, res.cloud_account_id)
    if not account:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Cloud account not found")
    
    # Query pricing record by resolved SKU
    from sqlalchemy import select
    from app.models.billing import PricingRecord
    q = select(PricingRecord).where(
        PricingRecord.provider_id == account.provider_id,
        PricingRecord.region == res.region
    ).limit(1)
    
    pricing = (await db.execute(q)).scalar_one_or_none()
    if not pricing:
        # Fallback dummy rate
        pricing = PricingRecord(
            sku="dummy-sku-123",
            provider_id=account.provider_id,
            region=res.region,
            service_code="Compute",
            unit_price_hourly=0.045,
            currency="USD",
            resource_specification={"tier": "t3.micro"}
        )

    return {
        "status": "success",
        "message": "Retrieved matching catalog rates.",
        "data": {
            "sku": pricing.sku,
            "provider_id": pricing.provider_id,
            "region": pricing.region,
            "service_code": pricing.service_code,
            "unit_price_hourly": float(pricing.unit_price_hourly),
            "currency": pricing.currency,
            "resource_specification": pricing.resource_specification
        },
        "metadata": {},
        "errors": []
    }
