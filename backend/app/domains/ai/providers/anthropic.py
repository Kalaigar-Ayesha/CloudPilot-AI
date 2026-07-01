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

logger = logging.getLogger("app.domains.ai.providers.anthropic")


class AnthropicProvider(LLMProvider):
    """
    Anthropic Claude API LLM Provider.
    """
    def __init__(self):
        self._client = None
        self._api_key = None
        self._model = None

    def connect(self, api_key: str, model_name: str, settings: Dict[str, Any]) -> None:
        self._api_key = api_key
        self._model = model_name
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        self._client = httpx.Client(base_url="https://api.anthropic.com/v1", headers=headers, timeout=30.0)

    def chat(
        self,
        messages: List[LLMMessage],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        if not self._client:
            raise ProviderException("Anthropic client not connected.")

        # Re-map messages (system is passed separately in Claude API)
        payload_messages = []
        for msg in messages:
            payload_messages.append({"role": "user" if msg.role == "user" else "assistant", "content": msg.content})

        payload = {
            "model": self._model,
            "system": system_prompt,
            "messages": payload_messages,
            "max_tokens": 1024,
            "temperature": 0.2
        }

        try:
            resp = self._client.post("/messages", json=payload)
            if resp.status_code != 200:
                raise ProviderException(f"Anthropic request failed: {resp.text}")
                
            data = resp.json()
            content = data.get("content", [{}])[0].get("text", "")
            usage = data.get("usage", {})

            return LLMResponse(
                content=content,
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0)
            )
        except Exception as e:
            logger.error(f"Anthropic chat exception: {str(e)}")
            raise ProviderException(f"Anthropic error: {str(e)}")

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
        return True

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4


# Register in factory
LLMProviderFactory.register_provider("anthropic", AnthropicProvider)
