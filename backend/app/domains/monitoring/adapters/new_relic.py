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

logger = logging.getLogger("app.domains.monitoring.adapters.new_relic")


class NewRelicAdapter(MonitoringAdapter):
    """
    New Relic observability telemetry Adapter utilizing NRQL queries.
    """
    def __init__(self):
        self._client = None
        self._endpoint_url = None
        self._account_id = None

    def connect(self, endpoint_url: str, credentials: Dict[str, Any]) -> None:
        self._endpoint_url = endpoint_url.rstrip("/")
        self._account_id = credentials["account_id"]
        headers = {
            "API-Key": credentials["api_key"],
            "Content-Type": "application/json"
        }
        self._client = httpx.Client(base_url=self._endpoint_url, headers=headers, timeout=10.0)

    def validate(self) -> bool:
        if not self._client:
            raise ProviderException("New Relic client is not connected.")
        try:
            # Query self account info validation via GraphQL
            graphql_query = "query { actor { user { name } } }"
            resp = self._client.post("/graphql", json={"query": graphql_query})
            return resp.status_code == 200
        except Exception as e:
            raise ProviderException(f"New Relic validation check failed: {str(e)}")

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
            raise ProviderException("New Relic client is not connected.")
            
        # Wrap NRQL query inside standard GraphQL wrapper payload
        graphql = """
        query($accountId: Int!, $nrql: Nrql!) {
          actor {
            account(id: $accountId) {
              nrql(query: $nrql) {
                results
              }
            }
          }
        }
        """
        
        variables = {
            "accountId": int(self._account_id),
            "nrql": query
        }

        try:
            resp = self._client.post("/graphql", json={"query": graphql, "variables": variables})
            if resp.status_code != 200:
                raise ProviderException(f"New Relic query failed: {resp.text}")
                
            data = resp.json()
            results = data.get("data", {}).get("actor", {}).get("account", {}).get("nrql", {}).get("results", [])
            points = []
            
            for res in results:
                # Expecting keys timestamp and average.cpuPercent or similar
                ts = datetime.fromtimestamp(res["timestamp"] / 1000.0)
                # Recover key dynamically
                val = next((v for k, v in res.items() if k not in ("timestamp", "endTime")), 0.0)
                points.append(
                    MetricDataPoint(
                        timestamp=ts,
                        value=float(val or 0.0),
                        unit="value"
                    )
                )
            return points
        except Exception as e:
            logger.error(f"NRQL Query execution failed: {str(e)}")
            raise ProviderException(f"New Relic query failed: {str(e)}")

    def fetch_resource_metrics(
        self,
        resource_id: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[MetricDataPoint]:
        # Formulate NRQL timeseries query
        field_name = "cpuPercent" if metric_type == "cpu_utilization" else "memoryUsedBytes"
        nrql_query = f"SELECT average({field_name}) FROM SystemSample WHERE entityGuid = '{resource_id}' TIMESERIES 1 minute SINCE {int(start_time.timestamp())} UNTIL {int(end_time.timestamp())}"
        return self.fetch_time_series(nrql_query, start_time, end_time, step_seconds=60)

    def fetch_cluster_metrics(self, cluster_id: str, metric_type: str, start_time: datetime, end_time: datetime) -> List[MetricDataPoint]:
        return []

    def fetch_namespace_metrics(self, cluster_id: str, namespace: str, metric_type: str, start_time: datetime, end_time: datetime) -> List[MetricDataPoint]:
        return []

    def fetch_pod_metrics(self, cluster_id: str, pod_name: str, metric_type: str, start_time: datetime, end_time: datetime) -> List[MetricDataPoint]:
        return []

    def fetch_node_metrics(self, cluster_id: str, node_name: str, metric_type: str, start_time: datetime, end_time: datetime) -> List[MetricDataPoint]:
        return []


# Register in factory
MonitoringProviderFactory.register_adapter("new_relic", NewRelicAdapter)
