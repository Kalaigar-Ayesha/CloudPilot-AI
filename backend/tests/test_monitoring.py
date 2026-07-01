import uuid
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient

from app.domains.monitoring.adapters.base import MonitoringAdapter, MetricDataPoint
from app.domains.monitoring.adapters.factory import MonitoringProviderFactory


# Mock monitoring adapter class mapping
class MockMonitoringAdapter(MonitoringAdapter):
    def connect(self, endpoint_url, credentials) -> None: pass
    def validate(self) -> bool: return True
    def disconnect(self) -> None: pass
    def health_check(self) -> str: return "healthy"
    def discover_targets(self) -> list: return []
    def fetch_time_series(self, query, start_time, end_time, step_seconds) -> list: return []
    def fetch_resource_metrics(self, resource_id, metric_type, start_time, end_time) -> list[MetricDataPoint]:
        return [
            MetricDataPoint(timestamp=datetime.now(timezone.utc), value=12.5, unit="percent")
        ]
    def fetch_cluster_metrics(self, cluster_id, metric_type, start_time, end_time) -> list: return []
    def fetch_namespace_metrics(self, cluster_id, namespace, metric_type, start_time, end_time) -> list: return []
    def fetch_pod_metrics(self, cluster_id, pod_name, metric_type, start_time, end_time) -> list: return []
    def fetch_node_metrics(self, cluster_id, node_name, metric_type, start_time, end_time) -> list: return []


# Register mock adapter in test setup
if "mock-monitoring" not in MonitoringProviderFactory._adapters:
    MonitoringProviderFactory.register_adapter("mock-monitoring", MockMonitoringAdapter)


@pytest.mark.asyncio
async def test_monitoring_factory_resolution():
    """Verify registry factory resolves the correct uninstantiated adapter types."""
    adapter_class = MonitoringProviderFactory.get_adapter("mock-monitoring")
    assert adapter_class == MockMonitoringAdapter


@pytest.mark.asyncio
async def test_validate_monitoring_endpoint(client: AsyncClient):
    """Test validation endpoint checks credentials validations."""
    register_payload = {
        "email": "monitoring_admin@example.com",
        "password": "AdminPassword123!"
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    
    login_resp = await client.post("/api/v1/auth/login", json=register_payload)
    access_token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    validate_payload = {
        "provider_id": "mock-monitoring",
        "endpoint_url": "https://api.testmonitoring.com",
        "credentials": {"api_key": "some_dummy_key"}
    }
    
    resp = await client.post("/api/v1/monitoring/validate", json=validate_payload, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["data"]["valid"] is True


@pytest.mark.asyncio
async def test_connect_monitoring_endpoint(client: AsyncClient):
    """Test connecting monitoring integration stores models."""
    register_payload = {
        "email": "monitoring_operator@example.com",
        "password": "OperatorPassword123!"
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    
    login_resp = await client.post("/api/v1/auth/login", json=register_payload)
    access_token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    connect_payload = {
        "project_id": str(uuid.uuid4()),
        "provider_id": "mock-monitoring",
        "name": "Testing Telemetry",
        "endpoint_url": "https://api.testmonitoring.com",
        "credentials": {"api_key": "secret"}
    }

    resp = await client.post("/api/v1/monitoring/connect", json=connect_payload, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "success"
    assert body["data"]["name"] == "Testing Telemetry"
    assert body["data"]["status"] == "ACTIVE"
