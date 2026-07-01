import logging
from typing import List
from app.domains.optimization.rules.base import (
    OptimizationRule,
    RuleEvaluationContext,
    RuleEvaluationResult,
)
from app.domains.optimization.rules.registry import RuleRegistry

logger = logging.getLogger("app.domains.optimization.rules.storage")


class UnattachedVolumeRule(OptimizationRule):
    """
    Identifies volumes that are not attached to any compute instances.
    """
    @property
    def name(self) -> str:
        return "unattached_storage_volume"

    @property
    def category(self) -> str:
        return "storage"

    @property
    def applicable_providers(self) -> List[str]:
        return ["aws", "azure", "gcp"]

    @property
    def applicable_resource_types(self) -> List[str]:
        return ["volume", "disk"]

    def evaluate(self, context: RuleEvaluationContext) -> RuleEvaluationResult:
        res = context.resource
        status = res.get("status", "").lower()
        
        # If disk state indicates it is unattached/available
        if status in ("available", "unattached"):
            size_gb = res.get("raw_payload", {}).get("size_gb", 100)
            # AWS EBS rate: ~$0.10/GB-month
            savings = round(float(size_gb) * 0.10, 2)

            return RuleEvaluationResult(
                is_applicable=True,
                current_state={"status": "unattached", "size_gb": size_gb},
                recommended_state={"status": "deleted", "action": "Delete the unattached volume to stop block storage fees."},
                estimated_savings=savings,
                severity="high",
                priority="high",
                business_impact="None. Volume is completely unattached.",
                technical_impact="Volume will be deleted permanently. Take snapshot before deleting if needed.",
                risk_level="low",
                rollback_complexity="low"
            )

        return RuleEvaluationResult(is_applicable=False, current_state={}, recommended_state={})


# Register storage rules
RuleRegistry.register_rule(UnattachedVolumeRule())
