from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pydantic import BaseModel


class AITool(ABC):
    """
    Abstract Base Class representing an AI agent tool.
    Tools execute business logic by calling clean service layers.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the tool passed to the LLM model."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Detailed description explaining when to invoke the tool."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """JSON schema defining expected arguments."""
        pass

    @abstractmethod
    async def execute(self, db: Any, project_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the tool by calling normalized services layers."""
        pass


class AIToolRegistry:
    """
    Factory registry holding all registered tools.
    """
    _tools: Dict[str, AITool] = {}

    @classmethod
    def register_tool(cls, tool: AITool) -> None:
        """Registers a new tool in the factory."""
        cls._tools[tool.name.lower().strip()] = tool

    @classmethod
    def get_tools(cls) -> List[AITool]:
        """Returns all registered tool instances."""
        return list(cls._tools.values())

    @classmethod
    def get_tool(cls, name: str) -> AITool:
        """Resolves a tool by name."""
        clean_name = name.lower().strip()
        tool = cls._tools.get(clean_name)
        if not tool:
            raise NotImplementedError(f"AI Tool '{name}' is not registered.")
        return tool


# Dynamically load concrete tools package modules to trigger registration checks
import app.domains.ai.tools
