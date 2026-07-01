import uuid
from datetime import datetime, timezone, date
import pytest
from httpx import AsyncClient

from app.domains.billing.adapters.base import BillingProvider, BillingRecordDTO, PricingProvider, PricingRecordDTO
from app.domains.billing.adapters.factory import BillingProviderFactory, PricingProviderFactory


# Mock billing adapter class
class MockBillingProvider(BillingProvider):
    def connect(self, credentials) -> None: pass
    def validate(self) -> bool: return True
    def disconnect(self) -> None: pass
    def fetch_current_cost(self) -> float: return 120.50
    def fetch_daily_cost(self, target_date) -> list: return []
    def fetch_monthly_cost(self, start_date) -> list: return []
    def fetch_historical_cost(self, start_time, end_time) -> list[BillingRecordDTO]:
        return [
            BillingRecordDTO(
                usage_start=datetime.now(timezone.utc),
                usage_end=datetime.now(timezone.utc),
                cost=15.25,
                currency="USD",
                usage_type="AmazonEC2",
                category="compute",
                raw_payload={}
            )
        ]
    def fetch_forecast_cost(self, end_time) -> list: return []
    def fetch_resource_cost(self, resource_id, start_time, end_time) -> float: return 0.0
    def fetch_service_cost(self, service_code, start_time, end_time) -> float: return 0.0
    def fetch_currency(self) -> str: return "USD"


# Mock pricing adapter class
class MockPricingProvider(PricingProvider):
    def connect(self, credentials) -> None: pass
    def fetch_compute_pricing(self, region) -> list[PricingRecordDTO]:
        return [
            PricingRecordDTO(
                sku="mock-sku-999",
                service_code="AmazonEC2",
                region=region,
                resource_specification={"instance": "t3.large"},
                unit_price_hourly=0.083,
                currency="USD"
            )
        ]
    def fetch_storage_pricing(self, region) -> list: return []
    def fetch_database_pricing(self, region) -> list: return []
    def fetch_network_pricing(self, region) -> list: return []
    def fetch_serverless_pricing(self, region) -> list: return []
    def fetch_kubernetes_pricing(self, region) -> list: return []


# Register mock adapters
if "mock-billing" not in BillingProviderFactory._adapters:
    BillingProviderFactory.register_adapter("mock-billing", MockBillingProvider)
if "mock-pricing" not in PricingProviderFactory._adapters:
    PricingProviderFactory.register_adapter("mock-pricing", MockPricingProvider)


@pytest.mark.asyncio
async def test_billing_factory_resolution():
    """Verify registry factory resolves the correct uninstantiated adapter types."""
    adapter_class = BillingProviderFactory.get_adapter("mock-billing")
    assert adapter_class == MockBillingProvider
    
    pricing_class = PricingProviderFactory.get_adapter("mock-pricing")
    assert pricing_class == MockPricingProvider


@pytest.mark.asyncio
async def test_get_billing_dashboard_endpoint(client: AsyncClient):
    """Test cost summary aggregation endpoints."""
    register_payload = {
        "email": "billing_user@example.com",
        "password": "BillingPassword123!"
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    
    login_resp = await client.post("/api/v1/auth/login", json=register_payload)
    access_token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    project_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/billing/dashboard?project_id={project_id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "total_cost" in body["data"]
    assert body["data"]["currency"] == "USD"


@pytest.mark.asyncio
async def test_get_forecast_predictions_endpoint(client: AsyncClient):
    """Test regression forecast generation endpoints."""
    register_payload = {
        "email": "forecaster_user@example.com",
        "password": "ForecastPassword123!"
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    
    login_resp = await client.post("/api/v1/auth/login", json=register_payload)
    access_token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    project_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/billing/forecast?project_id={project_id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "baseline_cost" in body["data"]
    assert "predictions" in body["data"]
