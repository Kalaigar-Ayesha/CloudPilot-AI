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

logger = logging.getLogger("app.domains.ai.providers.gemini")


class GeminiProvider(LLMProvider):
    """
    Google Gemini API LLM Provider.
    """
    def __init__(self):
        self._client = None
        self._api_key = None
        self._model = None

    def connect(self, api_key: str, model_name: str, settings: Dict[str, Any]) -> None:
        self._api_key = api_key
        self._model = model_name
        headers = {"Content-Type": "application/json"}
        # API key is passed as query parameters in Gemini endpoint API calls
        self._client = httpx.Client(
            base_url=f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}",
            headers=headers,
            timeout=30.0
        )

    def chat(
        self,
        messages: List[LLMMessage],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        if not self._client:
            raise ProviderException("Gemini client not connected.")

        # Re-map messages to Gemini format: {"role": "user"/"model", "parts": [{"text": ...}]}
        contents = []
        for msg in messages:
            role = "user" if msg.role == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg.content}]})

        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {"temperature": 0.2}
        }

        try:
            resp = self._client.post(f":generateContent?key={self._api_key}", json=payload)
            if resp.status_code != 200:
                raise ProviderException(f"Gemini API request failed: {resp.text}")
                
            data = resp.json()
            candidates = data.get("candidates", [{}])
            content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")

            return LLMResponse(
                content=content,
                input_tokens=0,
                output_tokens=0
            )
        except Exception as e:
            logger.error(f"Gemini chat exception: {str(e)}")
            raise ProviderException(f"Gemini error: {str(e)}")

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
LLMProviderFactory.register_provider("gemini", GeminiProvider)
