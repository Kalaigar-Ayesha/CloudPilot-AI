import logging
import json
import uuid
from typing import Any, Dict, List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.core.config import settings
from app.domains.cloud.adapters.base import ConnectionConfig
from app.domains.cloud.adapters.factory import ProviderAdapterFactory
from app.exceptions.base import ValidationException, ProviderException
from app.models.cloud import CloudAccount, CloudCredentials, Resource, ComputeResource, StorageResource, DatabaseResource, NetworkingResource
from app.repositories.cloud import (
    cloud_account_repository,
    cloud_credentials_repository,
    resource_repository,
)
from app.schemas.cloud import CloudAccountConnect, CloudAccountValidate
from app.utils.security import encrypt_payload, decrypt_payload

logger = logging.getLogger("app.services.cloud")


class CloudAccountService:
    """
    Coordinates cloud credential storage, validations, resource syncs,
    and cache invalidations.
    """
    
    @staticmethod
    async def validate_credentials(payload: CloudAccountValidate) -> bool:
        """Standalone dry-run credential verification."""
        try:
            adapter_class = ProviderAdapterFactory.get_adapter(payload.provider_id)
            adapter = adapter_class()
            
            conn_config = ConnectionConfig(
                account_id="validation_test",
                provider_name=payload.provider_id,
                credentials=payload.credentials,
                settings={}
            )
            
            adapter.connect(conn_config)
            is_valid = adapter.validate_credentials()
            adapter.disconnect()
            return is_valid
        except Exception as e:
            logger.warning(f"Stand-alone validation failed for provider {payload.provider_id}: {str(e)}")
            raise ValidationException(f"Credential verification failed: {str(e)}")

    @staticmethod
    async def connect_account(db: AsyncSession, payload: CloudAccountConnect) -> CloudAccount:
        """Registers a new cloud integration and secures credentials."""
        # 1. Run validation check
        validate_payload = CloudAccountValidate(
            provider_id=payload.provider_id,
            credentials=payload.credentials
        )
        await CloudAccountService.validate_credentials(validate_payload)

        # 2. Encrypt credentials payload
        plaintext_creds = json.dumps(payload.credentials)
        encrypted_creds = encrypt_payload(plaintext_creds)

        # 3. Create CloudAccount row
        account_data = {
            "project_id": payload.project_id,
            "provider_id": payload.provider_id,
            "name": payload.name,
            "account_identifier": payload.account_identifier,
            "status": "CONNECTED"
        }
        db_account = await cloud_account_repository.create(db, obj_in=account_data)
        await db.flush()

        # 4. Create credentials payload linking to account
        creds_data = {
            "cloud_account_id": db_account.id,
            "encrypted_payload": encrypted_creds
        }
        await cloud_credentials_repository.create(db, obj_in=creds_data)
        await db.flush()

        logger.info(f"Connected cloud account {payload.name} ({payload.provider_id}) for project {payload.project_id}")
        
        # Trigger dynamic Celery background sync task after committing
        from app.workers.tasks.discovery import discover_resources_task
        discover_resources_task.delay(str(db_account.id))

        return db_account

    @staticmethod
    async def get_accounts(db: AsyncSession, project_id: uuid.UUID) -> Sequence[CloudAccount]:
        """Fetch all connected cloud integrations under a project."""
        return await cloud_account_repository.get_by_project(db, project_id)

    @staticmethod
    async def delete_account(db: AsyncSession, account_id: uuid.UUID) -> None:
        """Removes a cloud integration."""
        account = await cloud_account_repository.get(db, account_id)
        if not account:
            raise ValidationException("Cloud account integration not found.")
        await cloud_account_repository.remove(db, id=account_id)
        logger.info(f"Removed cloud account connection {account_id}")

    @staticmethod
    async def get_account_status(db: AsyncSession, account_id: uuid.UUID) -> Dict[str, Any]:
        """Returns live API status lookup via target adapter checks."""
        account_with_creds = await cloud_account_repository.get_with_credentials(db, account_id)
        if not account_with_creds or not account_with_creds.credentials:
            raise ValidationException("Cloud account or credentials missing.")

        try:
            # Recover plaintext credentials
            plaintext = decrypt_payload(account_with_creds.credentials.encrypted_payload)
            creds = json.loads(plaintext)

            # Resolve adapter
            adapter_class = ProviderAdapterFactory.get_adapter(account_with_creds.provider_id)
            adapter = adapter_class()

            conn_config = ConnectionConfig(
                account_id=str(account_id),
                provider_name=account_with_creds.provider_id,
                credentials=creds,
                settings={}
            )

            adapter.connect(conn_config)
            health = adapter.health_check()
            account_info = adapter.fetch_account_information()
            adapter.disconnect()

            return {
                "account_id": account_id,
                "status": "CONNECTED" if health == "healthy" else "DEGRADED",
                "health": health,
                "provider_info": account_info
            }
        except Exception as e:
            logger.error(f"Live status validation check failed for account {account_id}: {str(e)}")
            return {
                "account_id": account_id,
                "status": "DISCONNECTED",
                "health": "unhealthy",
                "error": str(e)
            }

    @staticmethod
    async def discover_and_sync_resources(db: AsyncSession, account_id: uuid.UUID) -> int:
        """Discovers inventory catalog, normalizes fields, and upserts DB models."""
        account_with_creds = await cloud_account_repository.get_with_credentials(db, account_id)
        if not account_with_creds or not account_with_creds.credentials:
            raise ProviderException(f"Account {account_id} not found or missing credentials.")

        # 1. Recover plaintext credentials
        plaintext_creds = decrypt_payload(account_with_creds.credentials.encrypted_payload)
        creds = json.loads(plaintext_creds)

        # 2. Resolve adapter
        adapter_class = ProviderAdapterFactory.get_adapter(account_with_creds.provider_id)
        adapter = adapter_class()

        # Connect adapter
        conn_config = ConnectionConfig(
            account_id=str(account_id),
            provider_name=account_with_creds.provider_id,
            credentials=creds,
            settings={"regions": ["us-east-1", "eastus", "us-central1-a"]}  # Default regions fallback
        )
        adapter.connect(conn_config)

        # 3. Discover resources
        discovered_resources = adapter.discover_resources()
        adapter.disconnect()

        # 4. Sync resources in DB
        sync_count = 0
        for dto in discovered_resources:
            # Query existing record
            existing_res = await resource_repository.get_by_external_id(
                db,
                cloud_account_id=account_id,
                external_id=dto.external_id
            )

            res_data = {
                "cloud_account_id": account_id,
                "external_id": dto.external_id,
                "name": dto.name,
                "resource_type": dto.resource_type,
                "region": dto.region,
                "status": dto.status,
                "tags": dto.tags,
                "raw_payload": dto.raw_payload
            }

            if existing_res:
                # Update base resource attributes
                await resource_repository.update(db, db_obj=existing_res, obj_in=res_data)
                db_res = existing_res
            else:
                # Create base resource
                db_res = await resource_repository.create(db, obj_in=res_data)
                await db.flush()

            # Concrete subclass model updates (ComputeResource specs maps)
            if dto.resource_type == "virtual_machine":
                spec = dto.specification
                compute_data = {
                    "resource_id": db_res.id,
                    "instance_type": spec.get("instance_type", "unknown"),
                    "vcpu_count": spec.get("vcpu_count", 0),
                    "memory_gb": spec.get("memory_gb", 0.0),
                    "operating_system": spec.get("operating_system", "linux"),
                    "lifecycle": spec.get("lifecycle", "ON_DEMAND")
                }
                
                # Check for existing compute specification
                from sqlalchemy import select
                q = select(ComputeResource).where(ComputeResource.resource_id == db_res.id)
                comp_res = (await db.execute(q)).scalar_one_or_none()
                if comp_res:
                    for k, v in compute_data.items():
                        setattr(comp_res, k, v)
                else:
                    db.add(ComputeResource(**compute_data))

            sync_count += 1

        # Clear Redis caches relating to the project resources
        try:
            r = redis.from_url(settings.REDIS_URL)
            async with r:
                cache_pattern = f"cloudpilot:proj:{account_with_creds.project_id}:res:*"
                keys = await r.keys(cache_pattern)
                if keys:
                    await r.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache eviction failure during resource sync: {str(e)}")

        logger.info(f"Synchronized {sync_count} resources for account {account_id}")
        return sync_count
