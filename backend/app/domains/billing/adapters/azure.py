import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List
import httpx

from app.domains.billing.adapters.base import (
    BillingProvider,
    BillingRecordDTO,
    PricingProvider,
    PricingRecordDTO,
)
from app.domains.billing.adapters.factory import (
    BillingProviderFactory,
    PricingProviderFactory,
)
from app.exceptions.base import ProviderException

logger = logging.getLogger("app.domains.billing.adapters.azure")


class AzureBillingProvider(BillingProvider):
    """
    Azure Cost Management query Billing API.
    """
    def __init__(self):
        self._subscription_id = None
        self._tenant_id = None
        self._client_id = None
        self._client_secret = None
        self._token = None

    def connect(self, credentials: Dict[str, Any]) -> None:
        self._subscription_id = credentials["subscription_id"]
        self._tenant_id = credentials["tenant_id"]
        self._client_id = credentials["client_id"]
        self._client_secret = credentials["client_secret"]

    def _acquire_token(self) -> str:
        """Acquires an Azure AD access token for Resource Manager."""
        if self._token:
            return self._token
            
        url = f"https://login.microsoftonline.com/{self._tenant_id}/oauth2/v2.0/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "scope": "https://management.azure.com/.default"
        }
        
        try:
            resp = httpx.post(url, data=data, timeout=10.0)
            if resp.status_code != 200:
                raise ProviderException(f"OAuth token request failed: {resp.text}")
            self._token = resp.json()["access_token"]
            return self._token
        except Exception as e:
            raise ProviderException(f"OAuth token request exception: {str(e)}")

    def validate(self) -> bool:
        try:
            token = self._acquire_token()
            headers = {"Authorization": f"Bearer {token}"}
            # Verify using simple subscription query
            url = f"https://management.azure.com/subscriptions/{self._subscription_id}?api-version=2020-01-01"
            resp = httpx.get(url, headers=headers, timeout=10.0)
            return resp.status_code == 200
        except Exception as e:
            raise ProviderException(f"Azure validation failed: {str(e)}")

    def fetch_current_cost(self) -> float:
        now = datetime.now(timezone.utc)
        start = now.replace(day=1)
        # Fetch cost summary logic
        return 0.0

    def fetch_daily_cost(self, target_date: datetime) -> List[BillingRecordDTO]:
        return []

    def fetch_monthly_cost(self, start_date: datetime) -> List[BillingRecordDTO]:
        return []

    def fetch_historical_cost(self, start_time: datetime, end_time: datetime) -> List[BillingRecordDTO]:
        token = self._acquire_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Azure Cost Management API Query URL
        url = f"https://management.azure.com/subscriptions/{self._subscription_id}/providers/Microsoft.CostManagement/query?api-version=2019-11-01"
        
        payload = {
            "type": "Usage",
            "timeframe": "Custom",
            "timePeriod": {
                "from": start_time.strftime("%Y-%m-%dT00:00:00Z"),
                "to": end_time.strftime("%Y-%m-%dT23:59:59Z")
            },
            "dataset": {
                "granularity": "Daily",
                "aggregation": {
                    "totalCost": {"name": "PreTaxCost", "function": "Sum"}
                },
                "grouping": [
                    {"type": "Dimension", "name": "ServiceName"},
                    {"type": "Dimension", "name": "ResourceId"}
                ]
            }
        }

        try:
            resp = httpx.post(url, json=payload, headers=headers, timeout=15.0)
            if resp.status_code != 200:
                raise ProviderException(f"Cost Management query failed: {resp.text}")
                
            data = resp.json()
            rows = data.get("properties", {}).get("rows", [])
            
            records = []
            for row in rows:
                cost = float(row[0])
                date_str = str(row[1])  # Format: YYYYMMDD
                service = str(row[2])
                resource = str(row[3])
                
                t_start = datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=timezone.utc)
                t_end = t_start + timedelta(days=1)

                category = "compute"
                if "Storage" in service:
                    category = "storage"
                elif "Database" in service or "SQL" in service:
                    category = "database"
                elif "Virtual Network" in service or "ExpressRoute" in service:
                    category = "networking"

                records.append(
                    BillingRecordDTO(
                        resource_id=resource if "/" in resource else None,
                        usage_start=t_start,
                        usage_end=t_end,
                        cost=cost,
                        currency="USD",
                        usage_type=service,
                        category=category,
                        raw_payload={"row": row}
                    )
                )
            return records
        except Exception as e:
            logger.error(f"Failed to fetch Azure historical costs: {str(e)}")
            raise ProviderException(f"Azure query failed: {str(e)}")

    def fetch_forecast_cost(self, end_time: datetime) -> List[Dict[str, Any]]:
        return []

    def fetch_resource_cost(self, resource_id: str, start_time: datetime, end_time: datetime) -> float:
        return 0.0

    def fetch_service_cost(self, service_code: str, start_time: datetime, end_time: datetime) -> float:
        return 0.0

    def fetch_currency(self) -> str:
        return "USD"


class AzurePricingProvider(PricingProvider):
    """
    Azure Retail Prices API (Public lookup rate cards).
    """
    def connect(self, credentials: Dict[str, Any]) -> None:
        pass

    def fetch_compute_pricing(self, region: str) -> List[PricingRecordDTO]:
        # Retail Prices API URL (public - no authentication required)
        url = f"https://prices.azure.com/api/retail/prices?$filter=serviceName eq 'Virtual Machines' and armRegionName eq '{region}'"
        
        try:
            resp = httpx.get(url, timeout=15.0)
            if resp.status_code != 200:
                raise ProviderException(f"Azure retail pricing query failed: {resp.text}")
                
            data = resp.json()
            items = data.get("Items", [])
            
            pricing_records = []
            for item in items:
                sku = item.get("skuName")
                price = float(item.get("retailPrice", 0.0))
                meter = item.get("meterName")
                
                # Filter to standard on-demand compute rates
                if "Spot" in meter or "Reserved" in meter or price == 0.0:
                    continue

                pricing_records.append(
                    PricingRecordDTO(
                        sku=sku,
                        service_code="Virtual Machines",
                        region=region,
                        resource_specification={
                            "productName": item.get("productName"),
                            "meterName": meter
                        },
                        unit_price_hourly=price,
                        currency="USD"
                    )
                )
            return pricing_records
        except Exception as e:
            logger.error(f"Failed to query Azure pricing rates: {str(e)}")
            raise ProviderException(f"Azure retail pricing query failed: {str(e)}")

    def fetch_storage_pricing(self, region: str) -> List[PricingRecordDTO]:
        return []

    def fetch_database_pricing(self, region: str) -> List[PricingRecordDTO]:
        return []

    def fetch_network_pricing(self, region: str) -> List[PricingRecordDTO]:
        return []

    def fetch_serverless_pricing(self, region: str) -> List[PricingRecordDTO]:
        return []

    def fetch_kubernetes_pricing(self, region: str) -> List[PricingRecordDTO]:
        return []


# Register concrete adapters
BillingProviderFactory.register_adapter("azure", AzureBillingProvider)
PricingProviderFactory.register_adapter("azure", AzurePricingProvider)
