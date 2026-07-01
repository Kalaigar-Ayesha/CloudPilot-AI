import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import PermissionChecker
from app.schemas.base import UnifiedResponse
from app.schemas.cloud import (
    CloudAccountConnect,
    CloudAccountOut,
    CloudAccountValidate,
)
from app.services.cloud import CloudAccountService

router = APIRouter()


@router.post(
    "/connect",
    response_model=UnifiedResponse[CloudAccountOut],
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(PermissionChecker("connect_provider"))]
)
async def connect_cloud_account(
    payload: CloudAccountConnect,
    db: AsyncSession = Depends(get_db)
):
    """
    Connects a new cloud provider account integration.
    Saves encrypted credentials and schedules initial resource discovery sync.
    """
    account = await CloudAccountService.connect_account(db, payload)
    await db.commit()
    
    return {
        "status": "success",
        "message": "Cloud account connection registered. Resource sync scheduled.",
        "data": account,
        "metadata": {},
        "errors": []
    }


@router.post(
    "/validate",
    response_model=UnifiedResponse[dict],
    dependencies=[Depends(PermissionChecker("connect_provider"))]
)
async def validate_credentials(payload: CloudAccountValidate):
    """Dry-run credentials authentication check."""
    is_valid = await CloudAccountService.validate_credentials(payload)
    return {
        "status": "success" if is_valid else "error",
        "message": "Credentials validated successfully." if is_valid else "Credentials verification failed.",
        "data": {"valid": is_valid},
        "metadata": {},
        "errors": []
    }


@router.get(
    "/accounts",
    response_model=UnifiedResponse[List[CloudAccountOut]],
    dependencies=[Depends(PermissionChecker("view_inventory"))]
)
async def get_cloud_accounts(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Fetches all registered cloud integrations for a project workspace."""
    accounts = await CloudAccountService.get_accounts(db, project_id)
    return {
        "status": "success",
        "message": f"Successfully retrieved {len(accounts)} accounts.",
        "data": accounts,
        "metadata": {},
        "errors": []
    }


@router.get(
    "/providers",
    response_model=UnifiedResponse[List[dict]],
    dependencies=[Depends(PermissionChecker("view_inventory"))]
)
async def get_cloud_providers():
    """Lists supported cloud platform integrations."""
    providers = [
        {"id": "aws", "name": "Amazon Web Services", "is_active": true},
        {"id": "azure", "name": "Microsoft Azure", "is_active": true},
        {"id": "gcp", "name": "Google Cloud Platform", "is_active": true}
    ]
    return {
        "status": "success",
        "message": "Retrieved supported providers list.",
        "data": providers,
        "metadata": {},
        "errors": []
    }


@router.delete(
    "/{id}",
    response_model=UnifiedResponse[None],
    dependencies=[Depends(PermissionChecker("disconnect_provider"))]
)
async def disconnect_cloud_account(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Removes a cloud integration and revokes credential mappings."""
    await CloudAccountService.delete_account(db, id)
    await db.commit()
    return {
        "status": "success",
        "message": "Cloud account integration removed successfully.",
        "data": None,
        "metadata": {},
        "errors": []
    }


@router.get(
    "/{id}/status",
    response_model=UnifiedResponse[dict],
    dependencies=[Depends(PermissionChecker("view_inventory"))]
)
async def get_cloud_account_status(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Returns live connection and credential verification checks."""
    status_details = await CloudAccountService.get_account_status(db, id)
    return {
        "status": "success",
        "message": "Retrieved live status verification check.",
        "data": status_details,
        "metadata": {},
        "errors": []
    }
