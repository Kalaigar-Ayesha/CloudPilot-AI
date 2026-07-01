import logging
from datetime import datetime
from typing import Any, Dict, List

# Fallback imports checking
try:
    from azure.identity import ClientSecretCredential
    from azure.mgmt.monitor import MonitorManagementClient
except ImportError:
    ClientSecretCredential = None
    MonitorManagementClient = None

from app.domains.monitoring.adapters.base import (
    MetricDataPoint,
    MonitoringAdapter,
)
from app.domains.monitoring.adapters.factory import MonitoringProviderFactory
from app.exceptions.base import ProviderException

logger = logging.getLogger("app.domains.monitoring.adapters.azure_monitor")


class AzureMonitorAdapter(MonitoringAdapter):
    """
    Azure Monitor telemetry Adapter.
    """
    def __init__(self):
        self._credential = None
        self._subscription_id = None
        self._client = None

    def connect(self, endpoint_url: str, credentials: Dict[str, Any]) -> None:
        try:
            self._subscription_id = credentials["subscription_id"]
            self._credential = ClientSecretCredential(  # type: ignore
                tenant_id=credentials["tenant_id"],
                client_id=credentials["client_id"],
                client_secret=credentials["client_secret"]
            )
            self._client = MonitorManagementClient(self._credential, self._subscription_id)  # type: ignore
        except Exception as e:
            raise ProviderException(f"Failed to authenticate Azure Monitor: {str(e)}")

    def validate(self) -> bool:
        if not self._client:
            raise ProviderException("Azure Monitor client is not connected.")
        try:
            # Running list checking
            self._client.metric_definitions.list(
                resource_uri=f"/subscriptions/{self._subscription_id}"
            )
            return True
        except Exception as e:
            raise ProviderException(f"Azure Monitor credentials validation failed: {str(e)}")

    def disconnect(self) -> None:
        self._client = None
        self._credential = None

    def health_check(self) -> str:
        try:
            self.validate()
            return "healthy"
        except Exception:
            return "unhealthy"

    def discover_targets(self) -> List[Dict[str, Any]]:
        return []

    def fetch_time_series(
        self,
        query: str,
        start_time: datetime,
        end_time: datetime,
        step_seconds: int
    ) -> List[MetricDataPoint]:
        return []

    def fetch_resource_metrics(
        self,
        resource_id: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[MetricDataPoint]:
        if not self._client:
            raise ProviderException("Azure Monitor client is not connected.")

        # Map types
        metric_names = "Percentage CPU" if metric_type == "cpu_utilization" else "Available Memory Bytes"
        timespan = f"{start_time.isoformat()}/{end_time.isoformat()}"

        try:
            metrics_data = self._client.metrics.list(
                resource_uri=resource_id,
                timespan=timespan,
                interval="PT1M",
                metricnames=metric_names,
                aggregation="Average"
            )
            
            points = []
            for metric in metrics_data.value:
                for timeseries in metric.timeseries:
                    for data in (timeseries.data or []):
                        if data.average is not None:
                            unit_str = getattr(metric.unit, "value", str(metric.unit or "percent"))
                            points.append(
                                MetricDataPoint(
                                    timestamp=data.time_stamp,
                                    value=float(data.average),
                                    unit=unit_str
                                )
                            )
            return points
        except Exception as e:
            logger.error(f"Failed to query Azure Monitor metric data: {str(e)}")
            raise ProviderException(f"Azure Monitor query failed: {str(e)}")

    def fetch_cluster_metrics(self, cluster_id: str, metric_type: str, start_time: datetime, end_time: datetime) -> List[MetricDataPoint]:
        return []

    def fetch_namespace_metrics(self, cluster_id: str, namespace: str, metric_type: str, start_time: datetime, end_time: datetime) -> List[MetricDataPoint]:
        return []

    def fetch_pod_metrics(self, cluster_id: str, pod_name: str, metric_type: str, start_time: datetime, end_time: datetime) -> List[MetricDataPoint]:
        return []

    def fetch_node_metrics(self, cluster_id: str, node_name: str, metric_type: str, start_time: datetime, end_time: datetime) -> List[MetricDataPoint]:
        return []


# Register in factory
MonitoringProviderFactory.register_adapter("azure_monitor", AzureMonitorAdapter)
