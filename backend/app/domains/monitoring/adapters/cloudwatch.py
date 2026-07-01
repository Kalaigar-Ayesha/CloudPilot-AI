import logging
from datetime import datetime
from typing import Any, Dict, List
import boto3

from app.domains.monitoring.adapters.base import (
    MetricDataPoint,
    MonitoringAdapter,
)
from app.domains.monitoring.adapters.factory import MonitoringProviderFactory
from app.exceptions.base import ProviderException

logger = logging.getLogger("app.domains.monitoring.adapters.cloudwatch")


class CloudWatchAdapter(MonitoringAdapter):
    """
    AWS CloudWatch Adapter using boto3 SDK.
    """
    def __init__(self):
        self._session = None
        self._client = None

    def connect(self, endpoint_url: str, credentials: Dict[str, Any]) -> None:
        try:
            self._session = boto3.Session(
                aws_access_key_id=credentials["access_key"],
                aws_secret_access_key=credentials["secret_key"],
                aws_session_token=credentials.get("session_token"),
                region_name=credentials.get("region", "us-east-1")
            )
            self._client = self._session.client("cloudwatch")
        except Exception as e:
            raise ProviderException(f"Failed to initialize AWS CloudWatch session: {str(e)}")

    def validate(self) -> bool:
        if not self._client:
            raise ProviderException("CloudWatch client is not connected.")
        try:
            # Standalone API call check
            self._client.list_metrics(Namespace="AWS/EC2", Limit=1)
            return True
        except Exception as e:
            raise ProviderException(f"CloudWatch credentials validation failed: {str(e)}")

    def disconnect(self) -> None:
        self._client = None
        self._session = None

    def health_check(self) -> str:
        try:
            self.validate()
            return "healthy"
        except Exception:
            return "unhealthy"

    def discover_targets(self) -> List[Dict[str, Any]]:
        if not self._client:
            raise ProviderException("CloudWatch client is not connected.")
        try:
            # Query ec2 dimensions
            resp = self._client.list_metrics(Namespace="AWS/EC2", MetricName="CPUUtilization")
            return [
                {"metric_name": m["MetricName"], "dimensions": m["Dimensions"]}
                for m in resp.get("Metrics", [])
            ]
        except Exception as e:
            raise ProviderException(f"AWS metric target discovery failed: {str(e)}")

    def fetch_time_series(
        self,
        query: str,
        start_time: datetime,
        end_time: datetime,
        step_seconds: int
    ) -> List[MetricDataPoint]:
        # Fallback queries parser
        return []

    def fetch_resource_metrics(
        self,
        resource_id: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[MetricDataPoint]:
        if not self._client:
            raise ProviderException("CloudWatch client is not connected.")

        # Map internal standard to AWS CloudWatch parameters
        metric_name = "CPUUtilization" if metric_type == "cpu_utilization" else "VolumeWriteBytes"
        namespace = "AWS/EC2"
        dimension_name = "InstanceId"

        try:
            # Query metric data
            response = self._client.get_metric_data(
                MetricDataQueries=[
                    {
                        "Id": "m1",
                        "MetricStat": {
                            "Metric": {
                                "Namespace": namespace,
                                "MetricName": metric_name,
                                "Dimensions": [{"Name": dimension_name, "Value": resource_id}]
                            },
                            "Period": 60,
                            "Stat": "Average"
                        }
                    }
                ],
                StartTime=start_time,
                EndTime=end_time
            )
            
            points = []
            results = response.get("MetricDataResults", [])
            if results:
                res = results[0]
                timestamps = res.get("Timestamps", [])
                values = res.get("Values", [])
                for t, v in zip(timestamps, values):
                    points.append(
                        MetricDataPoint(
                            timestamp=t,
                            value=float(v),
                            unit="percent" if "percent" in metric_type else "bytes"
                        )
                    )
            return points
        except Exception as e:
            logger.error(f"Failed to query AWS CloudWatch metric data: {str(e)}")
            raise ProviderException(f"CloudWatch query failed: {str(e)}")

    def fetch_cluster_metrics(self, cluster_id: str, metric_type: str, start_time: datetime, end_time: datetime) -> List[MetricDataPoint]:
        return []

    def fetch_namespace_metrics(self, cluster_id: str, namespace: str, metric_type: str, start_time: datetime, end_time: datetime) -> List[MetricDataPoint]:
        return []

    def fetch_pod_metrics(self, cluster_id: str, pod_name: str, metric_type: str, start_time: datetime, end_time: datetime) -> List[MetricDataPoint]:
        return []

    def fetch_node_metrics(self, cluster_id: str, node_name: str, metric_type: str, start_time: datetime, end_time: datetime) -> List[MetricDataPoint]:
        return []


# Register in factory
MonitoringProviderFactory.register_adapter("cloudwatch", CloudWatchAdapter)
