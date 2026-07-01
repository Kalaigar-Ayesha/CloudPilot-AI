from typing import Any, Dict
import uuid
from app.domains.ai.tools.base import AITool, AIToolRegistry
from app.services.optimization import OptimizationService


class OptimizationTool(AITool):
    """
    Tool retrieving active optimization recommendations.
    """
    @property
    def name(self) -> str:
        return "get_optimization_recommendations"

    @property
    def description(self) -> str:
        return "Retrieves potential savings opportunities, active optimization recommendations, confidence scores, and action priorities."

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
            summary = await OptimizationService.get_savings_summary(db, proj_uuid)
            return {"optimization_summary": summary}
        except Exception as e:
            return {"error": f"Failed to retrieve optimization summary: {str(e)}"}


# Register tool
AIToolRegistry.register_tool(OptimizationTool())
