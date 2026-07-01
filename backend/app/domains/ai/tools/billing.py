from typing import Any, Dict
import uuid
from app.domains.ai.tools.base import AITool, AIToolRegistry
from app.services.billing import BillingService


class BillingTool(AITool):
    """
    Tool retrieving cost summaries and forecasts.
    """
    @property
    def name(self) -> str:
        return "get_billing_summary"

    @property
    def description(self) -> str:
        return "Retrieves the cost summary, spend trends by category, and multi-cloud financial summaries for connected accounts."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    async def execute(self, db: Any, project_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        proj_uuid = uuid.UUID(project_id)
        
        try:
            summary = await BillingService.get_dashboard_summary(db, proj_uuid)
            return {"billing_summary": summary}
        except Exception as e:
            return {"error": f"Failed to retrieve billing summary: {str(e)}"}


# Register tool
AIToolRegistry.register_tool(BillingTool())
