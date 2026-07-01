from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, List, Optional
from pydantic import BaseModel


class LLMMessage(BaseModel):
    """Message DTO passed to LLM adapters."""
    role: str  # system, user, assistant, tool
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None


class LLMResponse(BaseModel):
    """Structured response from LLM chat generation."""
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    input_tokens: int = 0
    output_tokens: int = 0


class LLMProvider(ABC):
    """
    Abstract Base Class representing the Common Interface for all LLM platforms.
    """
    
    @abstractmethod
    def connect(self, api_key: str, model_name: str, settings: Dict[str, Any]) -> None:
        """Configures client credentials and model settings."""
        pass

    @abstractmethod
    def chat(
        self,
        messages: List[LLMMessage],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        """Synchronous chat completion."""
        pass

    @abstractmethod
    def stream_chat(
        self,
        messages: List[LLMMessage],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """Streaming chat completions returning delta token chunks."""
        pass

    @abstractmethod
    def generate_summary(self, text: str) -> str:
        """Helper to generate text summaries for conversation history compressions."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Pings the LLM API to check connectivity."""
        pass

    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """Token count estimator helper."""
        pass
class LLMProviderFactory(ABC): pass
