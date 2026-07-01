import uuid
from unittest.mock import MagicMock, patch
import pytest
from httpx import AsyncClient

from app.domains.cloud.adapters.base import CloudProviderAdapter, NormalizedResourceDTO
from app.domains.cloud.adapters.factory import ProviderAdapterFactory


# Simple mock adapter class mapping
class MockCloudAdapter(CloudProviderAdapter):
    def connect(self, config) -> None: pass
    def validate_credentials(self) -> bool: return True
    def disconnect(self) -> None: pass
    def discover_regions(self) -> list: return [{"region_name": "us-test-1", "display_name": "Test Region", "status": "UP"}]
    def discover_services(self) -> list: return []
    def fetch_account_information(self) -> dict: return {"account_id": "test-account"}
    def health_check(self) -> str: return "healthy"
    def discover_resources(self) -> list[NormalizedResourceDTO]:
        return [
            NormalizedResourceDTO(
                external_id="i-testinstance123",
                name="test-server",
                resource_type="virtual_machine",
                region="us-test-1",
                status="running",
                tags={"Env": "Test"},
                specification={"instance_type": "t3.micro", "vcpu_count": 2, "memory_gb": 4.0},
                raw_payload={"id": "i-testinstance123"}
            )
        ]


# Register mock adapter in test setup
ProviderAdapterFactory.register_adapter("mock-cloud", MockCloudAdapter)


@pytest.mark.asyncio
async def test_adapter_factory_resolution():
    """Verify registry factory resolves the correct uninstantiated adapter types."""
    adapter_class = ProviderAdapterFactory.get_adapter("mock-cloud")
    assert adapter_class == MockCloudAdapter
    
    with pytest.raises(NotImplementedError):
        ProviderAdapterFactory.get_adapter("unregistered-provider")


@pytest.mark.asyncio
async def test_validate_credentials_endpoint(client: AsyncClient):
    """Test validation endpoint checks credentials validations."""
    register_payload = {
        "email": "admin_user@example.com",
        "password": "AdminPassword123!"
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    
    login_resp = await client.post("/api/v1/auth/login", json=register_payload)
    access_token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    validate_payload = {
        "provider_id": "mock-cloud",
        "credentials": {"api_key": "some_dummy_key"}
    }
    
    resp = await client.post("/api/v1/cloud/validate", json=validate_payload, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["data"]["valid"] is True


@pytest.mark.asyncio
@patch("app.workers.tasks.discovery.discover_resources_task.delay")
async def test_connect_cloud_account_endpoint(mock_task_delay, client: AsyncClient):
    """Test connecting cloud integration stores models and dispatches discovery task."""
    register_payload = {
        "email": "operator_user@example.com",
        "password": "OperatorPassword123!"
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    
    login_resp = await client.post("/api/v1/auth/login", json=register_payload)
    access_token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    connect_payload = {
        "project_id": str(uuid.uuid4()),
        "provider_id": "mock-cloud",
        "name": "Testing Integration",
        "account_identifier": "test-account-123",
        "credentials": {"api_key": "secret"},
        "settings": {"regions": ["us-test-1"]}
    }

    resp = await client.post("/api/v1/cloud/connect", json=connect_payload, headers=headers)
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "success"
    assert body["data"]["name"] == "Testing Integration"
    assert body["data"]["status"] == "CONNECTED"
    
    # Assert background celery discovery was dispatched
    assert mock_task_delay.called
