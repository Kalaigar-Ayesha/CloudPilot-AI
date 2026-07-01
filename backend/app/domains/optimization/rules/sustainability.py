import logging
from typing import List
from app.domains.optimization.rules.base import (
    OptimizationRule,
    RuleEvaluationContext,
    RuleEvaluationResult,
)
from app.domains.optimization.rules.registry import RuleRegistry

logger = logging.getLogger("app.domains.optimization.rules.sustainability")


class GreenRegionRecommendationRule(OptimizationRule):
    """
    Suggests migrating workloads to regions running on lower-intensity grid energy.
    """
    @property
    def name(self) -> str:
        return "green_region_recommendation"

    @property
    def category(self) -> str:
        return "sustainability"

    @property
    def applicable_providers(self) -> List[str]:
        return ["aws", "azure", "gcp"]

    @property
    def applicable_resource_types(self) -> List[str]:
        return ["virtual_machine", "database"]

    def evaluate(self, context: RuleEvaluationContext) -> RuleEvaluationResult:
        res = context.resource
        region = res.get("region", "").lower()
        
        # High carbon grid regions (e.g. us-east-1, ap-southeast-1) compared to green grid regions (e.g. eu-west-1 (Ireland), us-west-2 (Oregon), etc.)
        high_carbon_regions = ("us-east-1", "ap-southeast-1", "ap-east-1")
        
        if region in high_carbon_regions:
            return RuleEvaluationResult(
                is_applicable=True,
                current_state={"region": region, "grid_intensity": "high_carbon_grid"},
                recommended_state={"region": "us-west-2", "grid_intensity": "low_carbon_grid", "action": "Migrate virtual machine/database workloads to a carbon-efficient green region."},
                estimated_savings=0.0,  # Sustainability focus
                severity="low",
                priority="low",
                business_impact="None, but reduces corporate carbon footprint.",
                technical_impact="Cross-region migration requires snapshot replication and DNS redirect cuts.",
                risk_level="medium",
                rollback_complexity="high"
            )

        return RuleEvaluationResult(is_applicable=False, current_state={}, recommended_state={})


# Register sustainability rules
RuleRegistry.register_rule(GreenRegionRecommendationRule())
