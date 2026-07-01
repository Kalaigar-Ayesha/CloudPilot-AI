import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List
import boto3

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

logger = logging.getLogger("app.domains.billing.adapters.aws")


class AWSBillingProvider(BillingProvider):
    """
    AWS Cost Explorer Billing Integration using boto3.
    """
    def __init__(self):
        self._client = None
        self._session = None

    def connect(self, credentials: Dict[str, Any]) -> None:
        try:
            self._session = boto3.Session(
                aws_access_key_id=credentials["access_key"],
                aws_secret_access_key=credentials["secret_key"],
                aws_session_token=credentials.get("session_token"),
                region_name="us-east-1"  # Cost Explorer runs in us-east-1
            )
            self._client = self._session.client("ce")
        except Exception as e:
            raise ProviderException(f"Failed to initialize AWS CE Session: {str(e)}")

    def validate(self) -> bool:
        if not self._client:
            raise ProviderException("AWS CE Client is not connected.")
        try:
            # Query standard CE check
            self._client.get_cost_and_usage(
                TimePeriod={
                    "Start": (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d"),
                    "End": datetime.now(timezone.utc).strftime("%Y-%m-%d")
                },
                Granularity="DAILY",
                Metrics=["UnblendedCost"]
            )
            return True
        except Exception as e:
            raise ProviderException(f"AWS CE validation check failed: {str(e)}")

    def fetch_current_cost(self) -> float:
        if not self._client:
            raise ProviderException("AWS CE Client is not connected.")
        now = datetime.now(timezone.utc)
        start = now.replace(day=1).strftime("%Y-%m-%d")
        end = now.strftime("%Y-%m-%d")
        
        # If today is first of the month, query yesterday
        if start == end:
            start = (now - timedelta(days=1)).strftime("%Y-%m-%d")

        try:
            resp = self._client.get_cost_and_usage(
                TimePeriod={"Start": start, "End": end},
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"]
            )
            results = resp.get("ResultsByTime", [])
            if results:
                return float(results[0]["Total"]["UnblendedCost"]["Amount"])
            return 0.0
        except Exception as e:
            raise ProviderException(f"AWS CE query failed: {str(e)}")

    def fetch_daily_cost(self, target_date: datetime) -> List[BillingRecordDTO]:
        start = target_date.strftime("%Y-%m-%d")
        end = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")
        return self.fetch_historical_cost(
            datetime.strptime(start, "%Y-%m-%d"),
            datetime.strptime(end, "%Y-%m-%d")
        )

    def fetch_monthly_cost(self, start_date: datetime) -> List[BillingRecordDTO]:
        start = start_date.replace(day=1)
        end = (start + timedelta(days=32)).replace(day=1)
        return self.fetch_historical_cost(start, end)

    def fetch_historical_cost(self, start_time: datetime, end_time: datetime) -> List[BillingRecordDTO]:
        if not self._client:
            raise ProviderException("AWS CE Client is not connected.")

        try:
            resp = self._client.get_cost_and_usage(
                TimePeriod={
                    "Start": start_time.strftime("%Y-%m-%d"),
                    "End": end_time.strftime("%Y-%m-%d")
                },
                Granularity="DAILY",
                Metrics=["UnblendedCost"],
                GroupBy=[
                    {"Type": "DIMENSION", "Key": "SERVICE"},
                    {"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}
                ]
            )
            
            records = []
            for result in resp.get("ResultsByTime", []):
                t_start = datetime.strptime(result["TimePeriod"]["Start"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                t_end = datetime.strptime(result["TimePeriod"]["End"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                
                for group in result.get("Groups", []):
                    service = group["Keys"][0]
                    account = group["Keys"][1]
                    cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
                    
                    # Normalize category
                    category = "compute"
                    if "S3" in service or "Storage" in service:
                        category = "storage"
                    elif "RDS" in service or "Database" in service:
                        category = "database"
                    elif "VPC" in service or "Route53" in service:
                        category = "networking"

                    records.append(
                        BillingRecordDTO(
                            usage_start=t_start,
                            usage_end=t_end,
                            cost=cost,
                            currency="USD",
                            usage_type=service,
                            category=category,
                            raw_payload=group
                        )
                    )
            return records
        except Exception as e:
            logger.error(f"Failed to fetch AWS CE historical costs: {str(e)}")
            raise ProviderException(f"AWS CE historical query failed: {str(e)}")

    def fetch_forecast_cost(self, end_time: datetime) -> List[Dict[str, Any]]:
        return []

    def fetch_resource_cost(self, resource_id: str, start_time: datetime, end_time: datetime) -> float:
        return 0.0

    def fetch_service_cost(self, service_code: str, start_time: datetime, end_time: datetime) -> float:
        return 0.0

    def fetch_currency(self) -> str:
        return "USD"


class AWSPricingProvider(PricingProvider):
    """
    AWS Retail Price List Service Query Integration using boto3.
    """
    def __init__(self):
        self._client = None
        self._session = None

    def connect(self, credentials: Dict[str, Any]) -> None:
        try:
            self._session = boto3.Session(
                aws_access_key_id=credentials["access_key"],
                aws_secret_access_key=credentials["secret_key"],
                aws_session_token=credentials.get("session_token"),
                region_name="us-east-1"  # Price List API runs in us-east-1
            )
            self._client = self._session.client("pricing")
        except Exception as e:
            raise ProviderException(f"Failed to initialize AWS Pricing Session: {str(e)}")

    def fetch_compute_pricing(self, region: str) -> List[PricingRecordDTO]:
        if not self._client:
            raise ProviderException("AWS Pricing Client is not connected.")

        # E.g. AWS regional mapping (us-east-1 -> US East (N. Virginia))
        region_map = {"us-east-1": "US East (N. Virginia)", "us-west-2": "US West (Oregon)"}
        location = region_map.get(region, "US East (N. Virginia)")

        try:
            response = self._client.get_products(
                ServiceCode="AmazonEC2",
                Filters=[
                    {"Type": "TERM_MATCH", "Field": "location", "Value": location},
                    {"Type": "TERM_MATCH", "Field": "tenancy", "Value": "Shared"},
                    {"Type": "TERM_MATCH", "Field": "operatingSystem", "Value": "Linux"},
                    {"Type": "TERM_MATCH", "Field": "preInstalledSw", "Value": "NA"}
                ],
                MaxResults=50
            )
            
            pricing_records = []
            for product_str in response.get("PriceList", []):
                import json
                product = json.loads(product_str)
                product_attr = product.get("product", {}).get("attributes", {})
                sku = product.get("product", {}).get("sku")
                instance_type = product_attr.get("instanceType")
                
                # Extract pricing terms (OnDemand)
                terms = product.get("terms", {}).get("OnDemand", {})
                if not terms:
                    continue
                term_details = list(terms.values())[0]
                price_dimension = list(term_details.get("priceDimensions", {}).values())[0]
                price_hourly = float(price_dimension.get("pricePerUnit", {}).get("USD", 0.0))

                pricing_records.append(
                    PricingRecordDTO(
                        sku=sku,
                        service_code="AmazonEC2",
                        region=region,
                        resource_specification={
                            "instance_type": instance_type,
                            "vcpu": product_attr.get("vcpu"),
                            "memory": product_attr.get("memory")
                        },
                        unit_price_hourly=price_hourly,
                        currency="USD"
                    )
                )
            return pricing_records
        except Exception as e:
            logger.error(f"Failed to query AWS pricing data: {str(e)}")
            raise ProviderException(f"AWS Pricing query failed: {str(e)}")

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
BillingProviderFactory.register_adapter("aws", AWSBillingProvider)
PricingProviderFactory.register_adapter("aws", AWSPricingProvider)
