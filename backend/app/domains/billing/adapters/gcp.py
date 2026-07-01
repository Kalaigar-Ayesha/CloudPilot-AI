import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List
import json

# Fallback checking
try:
    from google.oauth2 import service_account
    from google.cloud import billing_v1
except ImportError:
    service_account = None
    billing_v1 = None

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

logger = logging.getLogger("app.domains.billing.adapters.gcp")


class GCPBillingProvider(BillingProvider):
    """
    Google Cloud Billing API integration.
    """
    def __init__(self):
        self._credentials = None
        self._project_id = None
        self._client = None

    def connect(self, credentials: Dict[str, Any]) -> None:
        try:
            service_account_info = credentials.get("service_account_json")
            if isinstance(service_account_info, str):
                service_account_info = json.loads(service_account_info)
                
            self._project_id = service_account_info["project_id"]
            self._credentials = service_account.Credentials.from_service_account_info(
                service_account_info
            )
            self._client = billing_v1.CloudBillingClient(credentials=self._credentials)
        except Exception as e:
            raise ProviderException(f"Failed to authenticate GCP Billing: {str(e)}")

    def validate(self) -> bool:
        if not self._client:
            raise ProviderException("GCP Billing Client is not connected.")
        try:
            # Query simple lookup list check
            self._client.list_billing_accounts()
            return True
        except Exception as e:
            raise ProviderException(f"GCP Billing validation check failed: {str(e)}")

    def fetch_current_cost(self) -> float:
        return 0.0

    def fetch_daily_cost(self, target_date: datetime) -> List[BillingRecordDTO]:
        return []

    def fetch_monthly_cost(self, start_date: datetime) -> List[BillingRecordDTO]:
        return []

    def fetch_historical_cost(self, start_time: datetime, end_time: datetime) -> List[BillingRecordDTO]:
        # Typically billing data in GCP is exported to BigQuery for analysis,
        # fallback is return mocked or query endpoints if configured.
        return []

    def fetch_forecast_cost(self, end_time: datetime) -> List[Dict[str, Any]]:
        return []

    def fetch_resource_cost(self, resource_id: str, start_time: datetime, end_time: datetime) -> float:
        return 0.0

    def fetch_service_cost(self, service_code: str, start_time: datetime, end_time: datetime) -> float:
        return 0.0

    def fetch_currency(self) -> str:
        return "USD"


class GCPPricingProvider(PricingProvider):
    """
    GCP Billing Catalog pricing API.
    """
    def __init__(self):
        self._credentials = None
        self._client = None

    def connect(self, credentials: Dict[str, Any]) -> None:
        try:
            service_account_info = credentials.get("service_account_json")
            if isinstance(service_account_info, str):
                service_account_info = json.loads(service_account_info)
                
            self._credentials = service_account.Credentials.from_service_account_info(
                service_account_info
            )
            self._client = billing_v1.CloudCatalogClient(credentials=self._credentials)
        except Exception as e:
            raise ProviderException(f"Failed to authenticate GCP Catalog: {str(e)}")

    def fetch_compute_pricing(self, region: str) -> List[PricingRecordDTO]:
        if not self._client:
            raise ProviderException("GCP Catalog Client is not connected.")

        try:
            # List compute engine services (Service ID: 6F81-5844-456A)
            services = self._client.list_skus(parent="services/6F81-5844-456A")
            
            pricing_records = []
            for sku in services:
                sku_id = sku.name.split("/")[-1] if "/" in sku.name else sku.name
                
                # Check region
                if region not in sku.service_regions:
                    continue

                # Extract pricing details
                pricing_info = sku.pricing_info
                if not pricing_info:
                    continue
                
                # Retrieve rates
                rates = pricing_info[0].pricing_expression.tiered_rates
                if not rates:
                    continue
                
                price_hourly = float(rates[0].unit_price.nanos or 0) / 1e9 + float(rates[0].unit_price.units or 0)

                pricing_records.append(
                    PricingRecordDTO(
                        sku=sku_id,
                        service_code="6F81-5844-456A",
                        region=region,
                        resource_specification={
                            "description": sku.description,
                            "category": sku.category.resource_family
                        },
                        unit_price_hourly=price_hourly,
                        currency="USD"
                    )
                )
            return pricing_records
        except Exception as e:
            logger.error(f"Failed to query GCP SKU pricing catalog: {str(e)}")
            raise ProviderException(f"GCP Catalog query failed: {str(e)}")

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
BillingProviderFactory.register_adapter("gcp", GCPBillingProvider)
PricingProviderFactory.register_adapter("gcp", GCPPricingProvider)
