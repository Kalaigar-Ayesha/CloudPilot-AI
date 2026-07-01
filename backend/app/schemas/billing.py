from datetime import datetime, date
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CostSummaryResponse(BaseModel):
    """Cost summary details response envelope."""
    total_cost: float
    currency: str = "USD"
    by_provider: Dict[str, float]
    by_category: Dict[str, float]


class CostTrendPoint(BaseModel):
    """Date-cost pair time-series point representation."""
    date: str
    cost: float


class CostHistoryTrendsResponse(BaseModel):
    """Cost trends representation payload."""
    interval: str
    history: List[CostTrendPoint]


class ResourceCostResponse(BaseModel):
    """Cumulative resource cost representation details."""
    resource_id: uuid.UUID
    total_accumulated_cost: float
    currency: str = "USD"


class ForecastPoint(BaseModel):
    """Forecast record predicted points envelope."""
    month: str
    baseline: float
    optimistic: float
    pessimistic: float


class ForecastResponse(BaseModel):
    """Forecast prediction response representation."""
    baseline_cost: float
    optimistic_cost: float
    pessimistic_cost: float
    prediction_start: date
    prediction_end: date
    predictions: List[ForecastPoint]


class PricingInfoResponse(BaseModel):
    """Catalogs retail pricing representation details."""
    sku: str
    provider_id: str
    region: str
    service_code: str
    unit_price_hourly: float
    currency: str = "USD"
    resource_specification: Dict[str, Any]
