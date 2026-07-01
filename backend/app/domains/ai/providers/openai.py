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

logger = logging.getLogger("app.domains.ai.providers.openai")


class OpenAIProvider(LLMProvider):
    """
    OpenAI API LLM Provider.
    """
    def __init__(self):
        self._client = None
        self._api_key = None
        self._model = None

    def connect(self, api_key: str, model_name: str, settings: Dict[str, Any]) -> None:
        self._api_key = api_key
        self._model = model_name
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        self._client = httpx.Client(base_url="https://api.openai.com/v1", headers=headers, timeout=30.0)

    def validate_connection(self) -> bool:
        if not self._client:
            return False
        return True

    def chat(
        self,
        messages: List[LLMMessage],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        if not self._client:
            raise ProviderException("OpenAI client not connected.")

        # Build message payload
        payload_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            m: Dict[str, Any] = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                m["tool_calls"] = msg.tool_calls
            payload_messages.append(m)

        payload = {"model": self._model, "messages": payload_messages, "temperature": 0.2}
        if tools:
            payload["tools"] = tools

        try:
            resp = self._client.post("/chat/completions", json=payload)
            if resp.status_code != 200:
                raise ProviderException(f"OpenAI chat request failed: {resp.text}")
                
            data = resp.json()
            choice = data["choices"][0]["message"]
            usage = data.get("usage", {})
            
            tool_calls = None
            if "tool_calls" in choice:
                tool_calls = choice["tool_calls"]

            return LLMResponse(
                content=choice.get("content") or "",
                tool_calls=tool_calls,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0)
            )
        except Exception as e:
            logger.error(f"OpenAI chat exception: {str(e)}")
            raise ProviderException(f"OpenAI error: {str(e)}")

    def stream_chat(
        self,
        messages: List[LLMMessage],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Generator[Dict[str, Any], None, None]:
        # Yields delta chunks
        yield {"content": "Mock stream tokens generated."}

    def generate_summary(self, text: str) -> str:
        return text[:100] + "..."

    def health_check(self) -> bool:
        return True

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4


# Register in factory
LLMProviderFactory.register_provider("openai", OpenAIProvider)
