from typing import Any, Dict
import uuid
from app.domains.ai.tools.base import AITool, AIToolRegistry
from app.repositories.cloud import resource_repository, cloud_account_repository


class ResourceTool(AITool):
    """
    Tool listing project resource inventories to feed context grids.
    """
    @property
    def name(self) -> str:
        return "list_resources"

    @property
    def description(self) -> str:
        return "List all active cloud infrastructure resources (virtual machines, disks, databases) connected under the project workspace."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    async def execute(self, db: Any, project_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        proj_uuid = uuid.UUID(project_id)
        
        # Fetch accounts
        accounts = await cloud_account_repository.get_by_project(db, proj_uuid)
        
        resources_list = []
        for acc in accounts:
            res_items = await resource_repository.get_by_account(db, acc.id)
            for res in res_items:
                resources_list.append({
                    "id": str(res.id),
                    "name": res.name,
                    "type": res.resource_type,
                    "region": res.region,
                    "status": res.status,
                    "provider": acc.provider_id
                })

        return {"resources": resources_list}


# Register tool
AIToolRegistry.register_tool(ResourceTool())
