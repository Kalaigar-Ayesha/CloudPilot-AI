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

logger = logging.getLogger("app.domains.monitoring.adapters.prometheus")


class PrometheusAdapter(MonitoringAdapter):
    """
    Prometheus Adapter utilizing direct HTTP PromQL queries.
    """
    def __init__(self):
        self._client = None
        self._endpoint_url = None

    def connect(self, endpoint_url: str, credentials: Dict[str, Any]) -> None:
        self._endpoint_url = endpoint_url.rstrip("/")
        # Setup HTTP Client (support authorization headers if passed)
        headers = {}
        if "token" in credentials:
            headers["Authorization"] = f"Bearer {credentials['token']}"
        elif "username" in credentials and "password" in credentials:
            auth_str = f"{credentials['username']}:{credentials['password']}"
            import base64
            auth_bytes = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
            headers["Authorization"] = f"Basic {auth_bytes}"
            
        self._client = httpx.Client(base_url=self._endpoint_url, headers=headers, timeout=10.0)

    def validate(self) -> bool:
        if not self._client:
            raise ProviderException("Prometheus client is not connected.")
        try:
            # Query standard status config API
            resp = self._client.get("/api/v1/status/config")
            return resp.status_code == 200
        except Exception as e:
            raise ProviderException(f"Prometheus validation check failed: {str(e)}")

    def disconnect(self) -> None:
        if self._client:
            self._client.close()
        self._client = None
        self._endpoint_url = None

    def health_check(self) -> str:
        try:
            resp = self._client.get("/-/healthy")
            return "healthy" if resp.status_code == 200 else "unhealthy"
        except Exception:
            return "unhealthy"

    def discover_targets(self) -> List[Dict[str, Any]]:
        if not self._client:
            raise ProviderException("Prometheus client is not connected.")
        try:
            resp = self._client.get("/api/v1/targets")
            if resp.status_code != 200:
                raise ProviderException("Failed to fetch targets from Prometheus API.")
            data = resp.json()
            return data.get("data", {}).get("activeTargets", [])
        except Exception as e:
            raise ProviderException(f"Target discovery failed: {str(e)}")

    def fetch_time_series(
        self,
        query: str,
        start_time: datetime,
        end_time: datetime,
        step_seconds: int
    ) -> List[MetricDataPoint]:
        if not self._client:
            raise ProviderException("Prometheus client is not connected.")
        try:
            params = {
                "query": query,
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "step": f"{step_seconds}s"
            }
            resp = self._client.get("/api/v1/query_range", params=params)
            if resp.status_code != 200:
                raise ProviderException(f"Query range API failed: {resp.text}")
                
            data = resp.json()
            results = data.get("data", {}).get("result", [])
            
            points = []
            if results:
                # Map metric values (format: [timestamp, value_string])
                for pt in results[0].get("values", []):
                    points.append(
                        MetricDataPoint(
                            timestamp=datetime.fromtimestamp(float(pt[0])),
                            value=float(pt[1]),
                            unit="value"
                        )
                    )
            return points
        except Exception as e:
            logger.error(f"PromQL Range query execution error: {str(e)}")
            raise ProviderException(f"Prometheus query failed: {str(e)}")

    def fetch_resource_metrics(
        self,
        resource_id: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[MetricDataPoint]:
        # Generate target PromQL expression based on generic type mapping
        if metric_type == "cpu_utilization":
            query = f'100 - (avg by(instance) (rate(node_cpu_seconds_total{{mode="idle",instance=~"{resource_id}.*"}}[5m])) * 100)'
        elif metric_type == "memory_utilization":
            query = f'(node_memory_MemTotal_bytes{{instance=~"{resource_id}.*"}} - node_memory_MemAvailable_bytes{{instance=~"{resource_id}.*"}}) / node_memory_MemTotal_bytes * 100'
        else:
            query = f'avg_over_time({metric_type}{{instance=~"{resource_id}.*"}}[5m])'
            
        return self.fetch_time_series(query, start_time, end_time, step_seconds=60)

    def fetch_cluster_metrics(
        self,
        cluster_id: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[MetricDataPoint]:
        # E.g. Query EKS/Kube-State average node count or cluster utilization
        query = f'sum(kube_node_status_condition{{condition="Ready",status="true"}})'
        return self.fetch_time_series(query, start_time, end_time, step_seconds=300)

    def fetch_namespace_metrics(
        self,
        cluster_id: str,
        namespace: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[MetricDataPoint]:
        query = f'sum(container_memory_usage_bytes{{namespace="{namespace}"}})'
        return self.fetch_time_series(query, start_time, end_time, step_seconds=300)

    def fetch_pod_metrics(
        self,
        cluster_id: str,
        pod_name: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[MetricDataPoint]:
        query = f'sum(rate(container_cpu_usage_seconds_total{{pod="{pod_name}"}}[5m])) * 100'
        return self.fetch_time_series(query, start_time, end_time, step_seconds=60)

    def fetch_node_metrics(
        self,
        cluster_id: str,
        node_name: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[MetricDataPoint]:
        query = f'kubelet_node_name{{node="{node_name}"}}'
        return self.fetch_time_series(query, start_time, end_time, step_seconds=60)


# Register in factory
MonitoringProviderFactory.register_adapter("prometheus", PrometheusAdapter)
