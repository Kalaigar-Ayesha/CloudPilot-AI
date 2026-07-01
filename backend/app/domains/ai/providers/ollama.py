import logging
from typing import Any, Dict, Generator, List, Optional
import httpx

from app.domains.ai.providers.base import (
    LLMMessage,
    LLMProvider,
    LLMResponse,
)
from app.domains.ai.providers.factory import LLMProviderFactory
from app.exceptions.base import ProviderException

logger = logging.getLogger("app.domains.ai.providers.ollama")


class OllamaProvider(LLMProvider):
    """
    Ollama Local LLM Provider (running locally on worker or server).
    """
    def __init__(self):
        self._client = None
        self._model = None

    def connect(self, api_key: str, model_name: str, settings: Dict[str, Any]) -> None:
        self._model = model_name
        endpoint = settings.get("endpoint", "http://localhost:11434")
        self._client = httpx.Client(base_url=endpoint, timeout=60.0)

    def chat(
        self,
        messages: List[LLMMessage],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        if not self._client:
            raise ProviderException("Ollama client not connected.")

        payload_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            payload_messages.append({"role": msg.role, "content": msg.content})

        payload = {"model": self._model, "messages": payload_messages, "stream": False}

        try:
            resp = self._client.post("/api/chat", json=payload)
            if resp.status_code != 200:
                raise ProviderException(f"Ollama local chat request failed: {resp.text}")
                
            data = resp.json()
            content = data.get("message", {}).get("content", "")

            return LLMResponse(
                content=content,
                input_tokens=data.get("prompt_eval_count", 0),
                output_tokens=data.get("eval_count", 0)
            )
        except Exception as e:
            logger.error(f"Ollama local chat exception: {str(e)}")
            raise ProviderException(f"Ollama error: {str(e)}")

    def stream_chat(
        self,
        messages: List[LLMMessage],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Generator[Dict[str, Any], None, None]:
        yield {"content": "Mock stream tokens generated."}

    def generate_summary(self, text: str) -> str:
        return text[:100] + "..."

    def health_check(self) -> bool:
        try:
            resp = self._client.get("/")
            return resp.status_code == 200
        except Exception:
            return False

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4


# Register in factory
LLMProviderFactory.register_provider("ollama", OllamaProvider)
