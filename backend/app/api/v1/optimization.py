import uuid
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import PermissionChecker
from app.schemas.base import UnifiedResponse
from app.schemas.optimization import (
    RecommendationOut,
    RecommendationRunResponse,
    SavingsSummaryResponse,
)
from app.services.optimization import OptimizationService
from app.repositories.optimization import recommendation_repository

router = APIRouter()


@router.post(
    "/run",
    response_model=UnifiedResponse[RecommendationRunResponse],
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(PermissionChecker("run_optimization"))]
)
async def run_optimization_scan(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Triggers a deterministic rule evaluation scan for a project workspace."""
    results = await OptimizationService.run_optimization_scan(db, project_id)
    await db.commit()
    return {
        "status": "success",
        "message": "Optimization scan completed successfully.",
        "data": results,
        "metadata": {},
        "errors": []
    }


@router.get(
    "/recommendations",
    response_model=UnifiedResponse[List[RecommendationOut]],
    dependencies=[Depends(PermissionChecker("view_optimization"))]
)
async def get_active_recommendations(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves active recommendations."""
    recs = await recommendation_repository.get_by_project(db, project_id)
    return {
        "status": "success",
        "message": f"Retrieved {len(recs)} active recommendations.",
        "data": recs,
        "metadata": {},
        "errors": []
    }


@router.get(
    "/savings",
    response_model=UnifiedResponse[SavingsSummaryResponse],
    dependencies=[Depends(PermissionChecker("view_optimization"))]
)
async def get_savings_summary(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves cumulative potential savings (monthly/yearly categories)."""
    summary = await OptimizationService.get_savings_summary(db, project_id)
    return {
        "status": "success",
        "message": "Retrieved potential savings summary.",
        "data": summary,
        "metadata": {},
        "errors": []
    }


@router.get(
    "/dashboard",
    response_model=UnifiedResponse[dict],
    dependencies=[Depends(PermissionChecker("view_optimization"))]
)
async def get_optimization_dashboard(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Aggregates dashboard widgets detailing status categories."""
    recs = await recommendation_repository.get_by_project(db, project_id)
    summary = await OptimizationService.get_savings_summary(db, project_id)

    critical_count = sum(1 for r in recs if r.severity == "critical")
    high_count = sum(1 for r in recs if r.severity == "high")
    medium_count = sum(1 for r in recs if r.severity == "medium")
    
    dashboard_data = {
        "total_active_recommendations": len(recs),
        "savings_summary": summary,
        "severities": {
            "critical": critical_count,
            "high": high_count,
            "medium": medium_count
        }
    }

    return {
        "status": "success",
        "message": "Retrieved optimization dashboard metrics.",
        "data": dashboard_data,
        "metadata": {},
        "errors": []
    }


@router.get(
    "/resource/{id}",
    response_model=UnifiedResponse[List[RecommendationOut]],
    dependencies=[Depends(PermissionChecker("view_optimization"))]
)
async def get_resource_recommendations(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves active recommendations targeting a single resource."""
    recs = await recommendation_repository.get_by_resource(db, id)
    return {
        "status": "success",
        "message": f"Retrieved {len(recs)} recommendations for resource.",
        "data": recs,
        "metadata": {},
        "errors": []
    }


@router.get(
    "/{id}",
    response_model=UnifiedResponse[RecommendationOut],
    dependencies=[Depends(PermissionChecker("view_optimization"))]
)
async def get_recommendation_details(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves recommendation detail specifications."""
    rec = await recommendation_repository.get(db, id)
    if not rec:
        return {"status": "error", "message": "Recommendation not found.", "data": None, "errors": ["Not found"]}

    return {
        "status": "success",
        "message": "Retrieved recommendation details.",
        "data": rec,
        "metadata": {},
        "errors": []
    }
