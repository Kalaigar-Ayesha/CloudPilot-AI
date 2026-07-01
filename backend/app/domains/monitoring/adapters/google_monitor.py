import logging
from datetime import datetime
from typing import Any, Dict, List
import json

# Fallback imports checking
try:
    from google.oauth2 import service_account
    from google.cloud import monitoring_v3
except ImportError:
    service_account = None
    monitoring_v3 = None

from app.domains.monitoring.adapters.base import (
    MetricDataPoint,
    MonitoringAdapter,
)
from app.domains.monitoring.adapters.factory import MonitoringProviderFactory
from app.exceptions.base import ProviderException

logger = logging.getLogger("app.domains.monitoring.adapters.google_monitor")


class GCPMonitorAdapter(MonitoringAdapter):
    """
    Google Cloud Monitoring telemetry Adapter.
    """
    def __init__(self):
        self._credentials = None
        self._project_id = None
        self._client = None

    def connect(self, endpoint_url: str, credentials: Dict[str, Any]) -> None:
        try:
            service_account_info = credentials.get("service_account_json")
            if isinstance(service_account_info, str):
                service_account_info = json.loads(service_account_info)
                
            self._project_id = service_account_info["project_id"]
            self._credentials = service_account.Credentials.from_service_account_info(
                service_account_info
            )
            self._client = monitoring_v3.MetricServiceClient(credentials=self._credentials)
        except Exception as e:
            raise ProviderException(f"Failed to authenticate GCP Monitor: {str(e)}")

    def validate(self) -> bool:
        if not self._client:
            raise ProviderException("GCP Monitor client is not connected.")
        try:
            # list descriptors call check
            self._client.list_monitored_resource_descriptors(
                name=f"projects/{self._project_id}",
                page_size=1
            )
            return True
        except Exception as e:
            raise ProviderException(f"GCP Monitoring validation check failed: {str(e)}")

    def disconnect(self) -> None:
        self._client = None
        self._credentials = None

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
            raise ProviderException("GCP Monitor client is not connected.")

        # Map types
        metric_filter = 'metric.type = "compute.googleapis.com/instance/cpu/utilization"'
        if metric_type != "cpu_utilization":
            metric_filter = 'metric.type = "compute.googleapis.com/instance/disk/write_bytes_count"'

        # Full filter specifying instance ID resource target
        full_filter = f'{metric_filter} AND resource.label.instance_id = "{resource_id}"'

        interval = monitoring_v3.TimeInterval(
            {
                "end_time": {"seconds": int(end_time.timestamp())},
                "start_time": {"seconds": int(start_time.timestamp())}
            }
        )

        try:
            results = self._client.list_time_series(
                request={
                    "name": f"projects/{self._project_id}",
                    "filter": full_filter,
                    "interval": interval,
                    "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL
                }
            )
            
            points = []
            for series in results:
                for point in series.points:
                    points.append(
                        MetricDataPoint(
                            timestamp=point.interval.end_time.to_datetime(),
                            value=float(point.value.double_value),
                            unit="percent"
                        )
                    )
            return points
        except Exception as e:
            logger.error(f"Failed to query GCP Monitoring metric data: {str(e)}")
            raise ProviderException(f"GCP Monitoring query failed: {str(e)}")

    def fetch_cluster_metrics(self, cluster_id: str, metric_type: str, start_time: datetime, end_time: datetime) -> List[MetricDataPoint]:
        return []

    def fetch_namespace_metrics(self, cluster_id: str, namespace: str, metric_type: str, start_time: datetime, end_time: datetime) -> List[MetricDataPoint]:
        return []

    def fetch_pod_metrics(self, cluster_id: str, pod_name: str, metric_type: str, start_time: datetime, end_time: datetime) -> List[MetricDataPoint]:
        return []

    def fetch_node_metrics(self, cluster_id: str, node_name: str, metric_type: str, start_time: datetime, end_time: datetime) -> List[MetricDataPoint]:
        return []


# Register in factory
MonitoringProviderFactory.register_adapter("google_monitor", GCPMonitorAdapter)
