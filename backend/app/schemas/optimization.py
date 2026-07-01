from datetime import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class RecommendationOut(BaseModel):
    """Outputs generated recommendation parameters."""
    id: uuid.UUID
    project_id: uuid.UUID
    resource_id: Optional[uuid.UUID] = None
    provider_id: str
    category: str
    rule_name: str
    severity: str
    priority: str
    current_state: Dict[str, Any]
    recommended_state: Dict[str, Any]
    estimated_savings: float
    confidence_score: int
    business_impact: Optional[str] = None
    technical_impact: Optional[str] = None
    risk_level: str
    rollback_complexity: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecommendationRunResponse(BaseModel):
    """Scan execution feedback summary."""
    recommendations_count: int
    total_savings: float
    scan_timestamp: datetime


class SavingsSummaryResponse(BaseModel):
    """Accrued savings summaries."""
    total_savings_monthly: float
    total_savings_yearly: float
    by_category: Dict[str, float]
