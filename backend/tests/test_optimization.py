import uuid
import pytest
from httpx import AsyncClient

from app.domains.optimization.rules.base import OptimizationRule, RuleEvaluationContext, RuleEvaluationResult
from app.domains.optimization.rules.registry import RuleRegistry
from app.services.optimization import OptimizationService


# Mock rule class
class MockOptimizationRule(OptimizationRule):
    @property
    def name(self) -> str: return "mock_idle_rule"
    @property
    def category(self) -> str: return "compute"
    @property
    def applicable_providers(self) -> list: return ["*"]
    @property
    def applicable_resource_types(self) -> list: return ["virtual_machine"]
    def evaluate(self, context: RuleEvaluationContext) -> RuleEvaluationResult:
        return RuleEvaluationResult(
            is_applicable=True,
            current_state={"cpu": 1.2},
            recommended_state={"action": "Stop instance"},
            estimated_savings=35.0,
            severity="high",
            risk_level="low"
        )


# Register mock rule
if "mock_idle_rule" not in [r.name for r in RuleRegistry.get_rules()]:
    RuleRegistry.register_rule(MockOptimizationRule())


@pytest.mark.asyncio
async def test_rule_registry_listing():
    """Verify registry registry records rules correctly."""
    rules = RuleRegistry.get_rules()
    assert any(r.name == "mock_idle_rule" for r in rules)


@pytest.mark.asyncio
async def test_confidence_scoring_math():
    """Verify confidence score outputs math constraints."""
    context = RuleEvaluationContext(
        resource={"id": "res-123", "created_at": "2026-06-01T12:00:00Z"},
        metrics=[{"metric_type": "cpu_utilization", "value": 1.2}] * 10,
        pricing=None,
        historical_billing=[]
    )
    score = OptimizationService.calculate_confidence(context)
    # CPU standard deviation should be zero, resource is > 3 days old, monitoring has 10 points
    assert score == 80


@pytest.mark.asyncio
async def test_priority_engine_resolution():
    """Verify priority engine groups critical issues and high savings correctly."""
    p_crit = OptimizationService.calculate_priority(0.0, "high", "critical")
    assert p_crit == "high"

    p_high = OptimizationService.calculate_priority(125.0, "low", "medium")
    assert p_high == "high"

    p_low = OptimizationService.calculate_priority(5.0, "medium", "low")
    assert p_low == "low"


@pytest.mark.asyncio
async def test_get_optimization_dashboard_endpoint(client: AsyncClient):
    """Test dashboard widgets endpoints."""
    register_payload = {
        "email": "opt_user@example.com",
        "password": "OptPassword123!"
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    
    login_resp = await client.post("/api/v1/auth/login", json=register_payload)
    access_token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    project_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/optimization/dashboard?project_id={project_id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "total_active_recommendations" in body["data"]
    assert "savings_summary" in body["data"]
