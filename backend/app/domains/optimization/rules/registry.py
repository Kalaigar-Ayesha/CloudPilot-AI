from typing import List
from app.domains.optimization.rules.base import OptimizationRule


class RuleRegistry:
    """
    Registry for dynamic optimization rule additions.
    Allows registering rules without changing core runtime systems.
    """
    _rules: List[OptimizationRule] = []

    @classmethod
    def register_rule(cls, rule: OptimizationRule) -> None:
        """Registers a new rule class instance."""
        # Ensure we don't register duplicates by name
        if not any(r.name == rule.name for r in cls._rules):
            cls._rules.append(rule)

    @classmethod
    def get_rules(cls) -> List[OptimizationRule]:
        """Returns all registered rule instances."""
        return cls._rules


# Dynamically load concrete rules packages to trigger registration hooks
import app.domains.optimization.rules
