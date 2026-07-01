import logging
from typing import List
from app.domains.optimization.rules.base import (
    OptimizationRule,
    RuleEvaluationContext,
    RuleEvaluationResult,
)
from app.domains.optimization.rules.registry import RuleRegistry

logger = logging.getLogger("app.domains.optimization.rules.kubernetes")


class MissingResourceRequestsRule(OptimizationRule):
    """
    Identifies Kubernetes workloads missing limits/requests configurations.
    """
    @property
    def name(self) -> str:
        return "missing_resource_requests"

    @property
    def category(self) -> str:
        return "kubernetes"

    @property
    def applicable_providers(self) -> List[str]:
        return ["aws", "azure", "gcp"]

    @property
    def applicable_resource_types(self) -> List[str]:
        return ["container_workload", "pod"]

    def evaluate(self, context: RuleEvaluationContext) -> RuleEvaluationResult:
        res = context.resource
        spec = res.get("raw_payload", {}).get("specification", {})
        
        # Check if limits or requests mappings are missing
        if not spec.get("cpu_request") or not spec.get("memory_request"):
            return RuleEvaluationResult(
                is_applicable=True,
                current_state={"requests": "configured_none"},
                recommended_state={"requests": "cpu_mem_limit_reqs", "action": "Define CPU/Memory request parameters to ensure pod scheduler stability."},
                estimated_savings=0.0,  # Stability rule (no financial savings estimate)
                severity="medium",
                priority="medium",
                business_impact="Improves pod scheduling predictability.",
                technical_impact="Requires updating workload YAML configurations.",
                risk_level="low",
                rollback_complexity="low"
            )

        return RuleEvaluationResult(is_applicable=False, current_state={}, recommended_state={})


# Register kubernetes rules
RuleRegistry.register_rule(MissingResourceRequestsRule())
