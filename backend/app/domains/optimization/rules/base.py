from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class RuleEvaluationContext(BaseModel):
    """
    Holds resource records, historical utilization metrics, and prices
    required to run deterministic evaluation rules.
    """
    resource: Dict[str, Any]
    metrics: List[Dict[str, Any]]
    pricing: Optional[Dict[str, Any]] = None
    historical_billing: List[Dict[str, Any]] = []


class RuleEvaluationResult(BaseModel):
    """
    Deterministic result mapping generated recommendation specs.
    """
    is_applicable: bool
    current_state: Dict[str, Any]
    recommended_state: Dict[str, Any]
    estimated_savings: float = 0.0
    severity: str = "medium"  # critical, high, medium, low
    priority: str = "medium"  # high, medium, low
    business_impact: str = ""
    technical_impact: str = ""
    risk_level: str = "low"  # high, medium, low
    rollback_complexity: str = "low"  # high, medium, low


class OptimizationRule(ABC):
    """
    Abstract Base Class for all optimization checks.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the optimization check."""
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        """Rule category (compute, storage, database, networking, security, etc.)."""
        pass

    @property
    @abstractmethod
    def applicable_providers(self) -> List[str]:
        """Cloud systems supported by this rule (aws, azure, gcp, or *)."""
        pass

    @property
    @abstractmethod
    def applicable_resource_types(self) -> List[str]:
        """Target inventory model classification (virtual_machine, disk, etc.)."""
        pass

    @abstractmethod
    def evaluate(self, context: RuleEvaluationContext) -> RuleEvaluationResult:
        """
        Executes deterministic rules over resource properties and metric averages.
        """
        pass
