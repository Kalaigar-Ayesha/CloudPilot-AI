from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class BillingRecordDTO(BaseModel):
    """Normalized billing record transport object."""
    resource_id: Optional[str] = None
    usage_start: datetime
    usage_end: datetime
    cost: float
    currency: str = "USD"
    usage_type: str
    category: str
    raw_payload: Dict[str, Any]


class PricingRecordDTO(BaseModel):
    """Normalized pricing rate transport object."""
    sku: str
    service_code: str
    region: str
    resource_specification: Dict[str, Any]
    unit_price_hourly: float
    currency: str = "USD"


class BillingProvider(ABC):
    """
    Abstract Base Class representing the Common Interface for Billing Integrations.
    """
    @abstractmethod
    def connect(self, credentials: Dict[str, Any]) -> None:
        """Initializes provider credentials."""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Runs validation checks on billing session scopes."""
        pass

    @abstractmethod
    def fetch_current_cost(self) -> float:
        """Pulls cumulative cost for the current month."""
        pass

    @abstractmethod
    def fetch_daily_cost(self, target_date: datetime) -> List[BillingRecordDTO]:
        """Pulls detailed cost metrics for a single day."""
        pass

    @abstractmethod
    def fetch_monthly_cost(self, start_date: datetime) -> List[BillingRecordDTO]:
        """Pulls detailed cost logs for a month."""
        pass

    @abstractmethod
    def fetch_historical_cost(self, start_time: datetime, end_time: datetime) -> List[BillingRecordDTO]:
        """Pulls billing logs for a custom time range."""
        pass

    @abstractmethod
    def fetch_forecast_cost(self, end_time: datetime) -> List[Dict[str, Any]]:
        """Pulls future baseline projections from provider APIs."""
        pass

    @abstractmethod
    def fetch_resource_cost(self, resource_id: str, start_time: datetime, end_time: datetime) -> float:
        """Pulls accrued cost for a specific resource ID."""
        pass

    @abstractmethod
    def fetch_service_cost(self, service_code: str, start_time: datetime, end_time: datetime) -> float:
        """Pulls accrued cost for a specific service code."""
        pass

    @abstractmethod
    def fetch_currency(self) -> str:
        """Returns standard billing currency (e.g. USD)."""
        pass


class PricingProvider(ABC):
    """
    Abstract Base Class representing the Common Interface for Pricing Lookup catalogs.
    """
    @abstractmethod
    def connect(self, credentials: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def fetch_compute_pricing(self, region: str) -> List[PricingRecordDTO]:
        """Lookup virtual machine compute rate cards."""
        pass

    @abstractmethod
    def fetch_storage_pricing(self, region: str) -> List[PricingRecordDTO]:
        """Lookup block, disk, and object storage rate cards."""
        pass

    @abstractmethod
    def fetch_database_pricing(self, region: str) -> List[PricingRecordDTO]:
        """Lookup managed DB pricing catalogs."""
        pass

    @abstractmethod
    def fetch_network_pricing(self, region: str) -> List[PricingRecordDTO]:
        """Lookup bandwidth and Load balancer pricing catalogs."""
        pass

    @abstractmethod
    def fetch_serverless_pricing(self, region: str) -> List[PricingRecordDTO]:
        """Lookup serverless functions execution catalog maps."""
        pass

    @abstractmethod
    def fetch_kubernetes_pricing(self, region: str) -> List[PricingRecordDTO]:
        """Lookup container orchestration system catalog maps."""
        pass
class BillingProviderFactory(ABC): pass
class PricingProviderFactory(ABC): pass
