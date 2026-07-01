import logging
from datetime import datetime
from typing import Any, Dict, List
import httpx

from app.domains.monitoring.adapters.base import (
    MetricDataPoint,
    MonitoringAdapter,
)
from app.domains.monitoring.adapters.factory import MonitoringProviderFactory
from app.exceptions.base import ProviderException

logger = logging.getLogger("app.domains.monitoring.adapters.datadog")


class DatadogAdapter(MonitoringAdapter):
    """
    Datadog telemetry Adapter using direct HTTP endpoints.
    """
    def __init__(self):
        self._client = None
        self._endpoint_url = None
        self._api_key = None
        self._app_key = None

    def connect(self, endpoint_url: str, credentials: Dict[str, Any]) -> None:
        self._endpoint_url = endpoint_url.rstrip("/")
        self._api_key = credentials["api_key"]
        self._app_key = credentials["application_key"]
        
        headers = {
            "DD-API-KEY": self._api_key,
            "DD-APPLICATION-KEY": self._app_key,
            "Content-Type": "application/json"
        }
        self._client = httpx.Client(base_url=self._endpoint_url, headers=headers, timeout=10.0)

    def validate(self) -> bool:
        if not self._client:
            raise ProviderException("Datadog client is not connected.")
        try:
            # Query standard check API
            resp = self._client.get("/api/v1/validate")
            return resp.status_code == 200
        except Exception as e:
            raise ProviderException(f"Datadog validation check failed: {str(e)}")

    def disconnect(self) -> None:
        if self._client:
            self._client.close()
        self._client = None

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
        if not self._client:
            raise ProviderException("Datadog client is not connected.")
        
        params = {
            "from": int(start_time.timestamp()),
            "to": int(end_time.timestamp()),
            "query": query
        }

        try:
            resp = self._client.get("/api/v1/query", params=params)
            if resp.status_code != 200:
                raise ProviderException(f"Datadog query range failed: {resp.text}")
                
            data = resp.json()
            series = data.get("series", [])
            points = []
            
            if series:
                for pt in series[0].get("pointlist", []):
                    # Datadog point format is: [timestamp_ms, value]
                    points.append(
                        MetricDataPoint(
                            timestamp=datetime.fromtimestamp(pt[0] / 1000.0),
                            value=float(pt[1] or 0.0),
                            unit="value"
                        )
                    )
            return points
        except Exception as e:
            logger.error(f"Datadog API time-series query failed: {str(e)}")
            raise ProviderException(f"Datadog query failed: {str(e)}")

    def fetch_resource_metrics(
        self,
        resource_id: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[MetricDataPoint]:
        # Datadog system metric query string
        metric_name = "system.cpu.user" if metric_type == "cpu_utilization" else "system.mem.pct_usable"
        query = f"avg:{metric_name}{{host:{resource_id}}}"
        return self.fetch_time_series(query, start_time, end_time, step_seconds=60)

    def fetch_cluster_metrics(self, cluster_id: str, metric_type: str, start_time: datetime, end_time: datetime) -> List[MetricDataPoint]:
        return []

    def fetch_namespace_metrics(self, cluster_id: str, namespace: str, metric_type: str, start_time: datetime, end_time: datetime) -> List[MetricDataPoint]:
        return []

    def fetch_pod_metrics(self, cluster_id: str, pod_name: str, metric_type: str, start_time: datetime, end_time: datetime) -> List[MetricDataPoint]:
        return []

    def fetch_node_metrics(self, cluster_id: str, node_name: str, metric_type: str, start_time: datetime, end_time: datetime) -> List[MetricDataPoint]:
        return []


# Register in factory
MonitoringProviderFactory.register_adapter("datadog", DatadogAdapter)
