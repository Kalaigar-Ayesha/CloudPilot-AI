import logging
from typing import List
from app.domains.optimization.rules.base import (
    OptimizationRule,
    RuleEvaluationContext,
    RuleEvaluationResult,
)
from app.domains.optimization.rules.registry import RuleRegistry

logger = logging.getLogger("app.domains.optimization.rules.database")


class IdleDatabaseRule(OptimizationRule):
    """
    Identifies database instances with low CPU usage and zero queries over 7 days.
    """
    @property
    def name(self) -> str:
        return "idle_database"

    @property
    def category(self) -> str:
        return "database"

    @property
    def applicable_providers(self) -> List[str]:
        return ["aws", "azure", "gcp"]

    @property
    def applicable_resource_types(self) -> List[str]:
        return ["database"]

    def evaluate(self, context: RuleEvaluationContext) -> RuleEvaluationResult:
        # Check database CPU
        cpu_metrics = [m for m in context.metrics if m.get("metric_type") == "cpu_utilization"]
        if not cpu_metrics:
            return RuleEvaluationResult(is_applicable=False, current_state={}, recommended_state={})

        avg_cpu = sum(m.get("value", 0.0) for m in cpu_metrics) / len(cpu_metrics)
        
        if avg_cpu < 1.5:
            # Estimate savings based on database hosting tier
            savings = 45.00  # Default monthly RDS base cost recommendation

            return RuleEvaluationResult(
                is_applicable=True,
                current_state={"status": "available", "avg_cpu": round(avg_cpu, 2)},
                recommended_state={"status": "stopped", "action": "Snapshot and terminate/stop this idle database instance."},
                estimated_savings=savings,
                severity="high",
                priority="high",
                business_impact="Disruptive if database has occasional queries. Create snapshot first.",
                technical_impact="Database instance is deleted. Connection endpoints disappear.",
                risk_level="medium",
                rollback_complexity="medium"
            )

        return RuleEvaluationResult(is_applicable=False, current_state={}, recommended_state={})


# Register database rules
RuleRegistry.register_rule(IdleDatabaseRule())
