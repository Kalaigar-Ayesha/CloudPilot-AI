from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class MetricDataPoint(BaseModel):
    """Normalized metric time-series record returned from adapter polling."""
    timestamp: datetime
    value: float
    unit: str


class MonitoringAdapter(ABC):
    """
    Abstract Base Class representing the Common Interface for all Telemetry Providers.
    """
    
    @abstractmethod
    def connect(self, endpoint_url: str, credentials: Dict[str, Any]) -> None:
        """Initializes endpoints and session parameters."""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Dry-run validation checks on credentials and connection scopes."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Tears down clients and sessions."""
        pass

    @abstractmethod
    def health_check(self) -> str:
        """Pings monitoring endpoint to verify uptime status."""
        pass

    @abstractmethod
    def discover_targets(self) -> List[Dict[str, Any]]:
        """Returns discoverable monitored workloads."""
        pass

    @abstractmethod
    def fetch_time_series(
        self,
        query: str,
        start_time: datetime,
        end_time: datetime,
        step_seconds: int
    ) -> List[MetricDataPoint]:
        """Core raw metric parser running dynamic query checks."""
        pass

    # Normalized metrics retrieval hooks
    @abstractmethod
    def fetch_resource_metrics(
        self,
        resource_id: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[MetricDataPoint]:
        """Dispatches queries for generic cloud resources (compute VM, DB, etc.)."""
        pass

    @abstractmethod
    def fetch_cluster_metrics(
        self,
        cluster_id: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[MetricDataPoint]:
        """Query Kubernetes cluster-wide utilization states."""
        pass

    @abstractmethod
    def fetch_namespace_metrics(
        self,
        cluster_id: str,
        namespace: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[MetricDataPoint]:
        """Query namespace quotas and utilizations."""
        pass

    @abstractmethod
    def fetch_pod_metrics(
        self,
        cluster_id: str,
        pod_name: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[MetricDataPoint]:
        """Query container-pod CPU, memory, and restarts metrics."""
        pass

    @abstractmethod
    def fetch_node_metrics(
        self,
        cluster_id: str,
        node_name: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[MetricDataPoint]:
        """Query Kubernetes physical Node utilizations and pressure logs."""
        pass
