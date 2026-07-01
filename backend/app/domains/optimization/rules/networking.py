import logging
from typing import List
from app.domains.optimization.rules.base import (
    OptimizationRule,
    RuleEvaluationContext,
    RuleEvaluationResult,
)
from app.domains.optimization.rules.registry import RuleRegistry

logger = logging.getLogger("app.domains.optimization.rules.networking")


class UnusedPublicIPRule(OptimizationRule):
    """
    Identifies elastic/public IPs that are unassociated with any instances.
    """
    @property
    def name(self) -> str:
        return "unused_public_ip"

    @property
    def category(self) -> str:
        return "networking"

    @property
    def applicable_providers(self) -> List[str]:
        return ["aws", "azure", "gcp"]

    @property
    def applicable_resource_types(self) -> List[str]:
        return ["ip_address", "network_interface"]

    def evaluate(self, context: RuleEvaluationContext) -> RuleEvaluationResult:
        res = context.resource
        association = res.get("raw_payload", {}).get("association_id")
        
        # If public IP has no active allocation association bound to VM
        if not association and res.get("resource_type") == "ip_address":
            # Unassociated IP cost is approx $0.005/hour ($3.60/month)
            savings = 3.60

            return RuleEvaluationResult(
                is_applicable=True,
                current_state={"association": "unassociated"},
                recommended_state={"association": "released", "action": "Release the unassociated Elastic IP address."},
                estimated_savings=savings,
                severity="low",
                priority="low",
                business_impact="None. Public IP is unused.",
                technical_impact="IP allocation returns to provider pools.",
                risk_level="low",
                rollback_complexity="low"
            )

        return RuleEvaluationResult(is_applicable=False, current_state={}, recommended_state={})


# Register networking rules
RuleRegistry.register_rule(UnusedPublicIPRule())
