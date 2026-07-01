import logging
from typing import List
from app.domains.optimization.rules.base import (
    OptimizationRule,
    RuleEvaluationContext,
    RuleEvaluationResult,
)
from app.domains.optimization.rules.registry import RuleRegistry

logger = logging.getLogger("app.domains.optimization.rules.security")


class PublicStorageBucketRule(OptimizationRule):
    """
    Identifies object storage buckets exposed publicly to the internet.
    """
    @property
    def name(self) -> str:
        return "public_storage_bucket"

    @property
    def category(self) -> str:
        return "security"

    @property
    def applicable_providers(self) -> List[str]:
        return ["aws", "azure", "gcp"]

    @property
    def applicable_resource_types(self) -> List[str]:
        return ["storage_bucket", "bucket"]

    def evaluate(self, context: RuleEvaluationContext) -> RuleEvaluationResult:
        res = context.resource
        acl = res.get("raw_payload", {}).get("acl", "").lower()
        public_block = res.get("raw_payload", {}).get("public_access_block_enabled", True)

        # If bucket ACL is public or public access block is missing
        if acl in ("public-read", "public-read-write") or not public_block:
            return RuleEvaluationResult(
                is_applicable=True,
                current_state={"acl": acl, "public_block": public_block},
                recommended_state={"acl": "private", "public_block": True, "action": "Enable public access block and set private ACLs."},
                estimated_savings=0.0,  # Security recommendations do not estimate savings
                severity="critical",
                priority="high",
                business_impact="Critical protection against sensitive data leakage.",
                technical_impact="Changes bucket access permissions. May break public image assets.",
                risk_level="high",
                rollback_complexity="low"
            )

        return RuleEvaluationResult(is_applicable=False, current_state={}, recommended_state={})


# Register security rules
RuleRegistry.register_rule(PublicStorageBucketRule())
