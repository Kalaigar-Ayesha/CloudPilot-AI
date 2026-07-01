import logging
from typing import List
from app.domains.optimization.rules.base import (
    OptimizationRule,
    RuleEvaluationContext,
    RuleEvaluationResult,
)
from app.domains.optimization.rules.registry import RuleRegistry

logger = logging.getLogger("app.domains.optimization.rules.compute")


class IdleVirtualMachineRule(OptimizationRule):
    """
    Identifies virtual machines with extremely low CPU usage (< 2%) and suggests stopping them.
    """
    @property
    def name(self) -> str:
        return "idle_virtual_machine"

    @property
    def category(self) -> str:
        return "compute"

    @property
    def applicable_providers(self) -> List[str]:
        return ["aws", "azure", "gcp"]

    @property
    def applicable_resource_types(self) -> List[str]:
        return ["virtual_machine"]

    def evaluate(self, context: RuleEvaluationContext) -> RuleEvaluationResult:
        # Determine average CPU utilization
        cpu_metrics = [m for m in context.metrics if m.get("metric_type") == "cpu_utilization"]
        if not cpu_metrics:
            return RuleEvaluationResult(is_applicable=False, current_state={}, recommended_state={})

        avg_cpu = sum(m.get("value", 0.0) for m in cpu_metrics) / len(cpu_metrics)
        
        # Rule threshold check
        if avg_cpu < 2.0:
            # Estimate savings (fallback 15$ monthly or look up pricing if available)
            hourly_rate = 0.045
            if context.pricing:
                hourly_rate = context.pricing.get("unit_price_hourly", 0.045)
            
            savings = round(hourly_rate * 730, 2)  # Stop fully (730 hours monthly)

            return RuleEvaluationResult(
                is_applicable=True,
                current_state={"status": "running", "avg_cpu": round(avg_cpu, 2)},
                recommended_state={"status": "stopped", "action": "Stop the idle instance to prevent compute charges."},
                estimated_savings=savings,
                severity="high",
                priority="high",
                business_impact="None, resource is currently under-utilized.",
                technical_impact="Instance will be stopped. Disks remain active.",
                risk_level="low",
                rollback_complexity="low"
            )

        return RuleEvaluationResult(is_applicable=False, current_state={}, recommended_state={})


class OversizedVirtualMachineRule(OptimizationRule):
    """
    Identifies virtual machines with low CPU usage (< 15%) and suggests downsizing.
    """
    @property
    def name(self) -> str:
        return "oversized_virtual_machine"

    @property
    def category(self) -> str:
        return "compute"

    @property
    def applicable_providers(self) -> List[str]:
        return ["aws", "azure", "gcp"]

    @property
    def applicable_resource_types(self) -> List[str]:
        return ["virtual_machine"]

    def evaluate(self, context: RuleEvaluationContext) -> RuleEvaluationResult:
        cpu_metrics = [m for m in context.metrics if m.get("metric_type") == "cpu_utilization"]
        if not cpu_metrics:
            return RuleEvaluationResult(is_applicable=False, current_state={}, recommended_state={})

        avg_cpu = sum(m.get("value", 0.0) for m in cpu_metrics) / len(cpu_metrics)
        
        if 2.0 <= avg_cpu < 15.0:
            # Estimate savings by downsizing to a half-sized compute SKU (50% savings)
            hourly_rate = 0.09
            if context.pricing:
                hourly_rate = context.pricing.get("unit_price_hourly", 0.09)
            
            savings = round((hourly_rate * 0.5) * 730, 2)

            return RuleEvaluationResult(
                is_applicable=True,
                current_state={"instance_type": "standard-size", "avg_cpu": round(avg_cpu, 2)},
                recommended_state={"instance_type": "downsized-sku", "action": "Downsize instance type by 50% to align with workloads."},
                estimated_savings=savings,
                severity="medium",
                priority="medium",
                business_impact="Minimal disruption. Fits resource peak limits.",
                technical_impact="Downsizing requires instance reboot/re-creation.",
                risk_level="medium",
                rollback_complexity="medium"
            )

        return RuleEvaluationResult(is_applicable=False, current_state={}, recommended_state={})


# Register compute rules
RuleRegistry.register_rule(IdleVirtualMachineRule())
RuleRegistry.register_rule(OversizedVirtualMachineRule())
