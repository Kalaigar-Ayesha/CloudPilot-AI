from datetime import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MonitoringSourceConnect(BaseModel):
    """Schema validating inputs when connecting a telemetry provider."""
    project_id: uuid.UUID
    provider_id: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=100)
    endpoint_url: str = Field(..., min_length=10, max_length=500)
    credentials: Dict[str, Any] = Field(
        ...,
        description="Encrypted credentials wrapper payload (e.g. API keys, secrets)"
    )


class MonitoringSourceValidate(BaseModel):
    """Schema validating stand-alone connection verification runs."""
    provider_id: str
    endpoint_url: str
    credentials: Dict[str, Any]


class MonitoringSourceOut(BaseModel):
    """Outputs registered monitoring integrations details."""
    id: uuid.UUID
    project_id: uuid.UUID
    provider_id: str
    name: str
    endpoint_url: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class NormalizedMetricOut(BaseModel):
    """Telemetry data point schema."""
    timestamp: datetime
    value: float
    unit: str


class MetricQueryResponse(BaseModel):
    """Collection wrapper payload returning time-series logs."""
    resource_id: uuid.UUID
    metric_type: str
    unit: str
    data_points: List[NormalizedMetricOut]
