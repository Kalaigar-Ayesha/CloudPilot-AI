import logging
from typing import List
from app.domains.optimization.rules.base import (
    OptimizationRule,
    RuleEvaluationContext,
    RuleEvaluationResult,
)
from app.domains.optimization.rules.registry import RuleRegistry

logger = logging.getLogger("app.domains.optimization.rules.finops")


class UnexpectedCostSpikeRule(OptimizationRule):
    """
    Identifies sudden unexpected spikes in cost compared to daily averages.
    """
    @property
    def name(self) -> str:
        return "unexpected_cost_spike"

    @property
    def category(self) -> str:
        return "finops"

    @property
    def applicable_providers(self) -> List[str]:
        return ["aws", "azure", "gcp"]

    @property
    def applicable_resource_types(self) -> List[str]:
        return ["billing_account", "cloud_account"]

    def evaluate(self, context: RuleEvaluationContext) -> RuleEvaluationResult:
        billing = context.historical_billing
        if len(billing) < 5:
            return RuleEvaluationResult(is_applicable=False, current_state={}, recommended_state={})

        daily_costs = [float(b.get("cost", 0.0)) for b in billing]
        last_day_cost = daily_costs[-1]
        previous_days_avg = sum(daily_costs[:-1]) / (len(daily_costs) - 1)

        # Spike detection threshold (cost increased by > 50% AND spike is larger than 10$)
        if last_day_cost > (previous_days_avg * 1.5) and (last_day_cost - previous_days_avg) > 10.0:
            drift = round(last_day_cost - previous_days_avg, 2)
            return RuleEvaluationResult(
                is_applicable=True,
                current_state={"last_day_cost": last_day_cost, "previous_days_avg": round(previous_days_avg, 2)},
                recommended_state={"status": "monitored", "action": "Investigate cost spike to locate drift causes (e.g. data transfer or compute scale)."},
                estimated_savings=0.0,  # Alert rule (no immediate savings)
                severity="critical",
                priority="high",
                business_impact="Unchecked drift could lead to cost overruns.",
                technical_impact="Requires manual investigation of audit log history.",
                risk_level="high",
                rollback_complexity="low"
            )

        return RuleEvaluationResult(is_applicable=False, current_state={}, recommended_state={})


# Register finops rules
RuleRegistry.register_rule(UnexpectedCostSpikeRule())
