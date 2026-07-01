from typing import Any, Dict
import uuid
from app.domains.ai.tools.base import AITool, AIToolRegistry
from app.services.monitoring import MonitoringService


class MonitoringTool(AITool):
    """
    Tool retrieving active telemetry CPU/memory averages.
    """
    @property
    def name(self) -> str:
        return "get_telemetry_metrics"

    @property
    def description(self) -> str:
        return "Retrieves aggregated average CPU and memory utilization summaries for active resources."

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
            metrics = await MonitoringService.get_dashboard_metrics(db, proj_uuid)
            return {"telemetry_metrics": metrics}
        except Exception as e:
            return {"error": f"Failed to retrieve telemetry metrics: {str(e)}"}


# Register tool
AIToolRegistry.register_tool(MonitoringTool())
