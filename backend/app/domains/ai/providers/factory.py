from typing import Dict, Type
from app.domains.ai.providers.base import LLMProvider


class LLMProviderFactory:
    """
    Registry factory instantiating LLM adapters based on identifier keys.
    """
    _providers: Dict[str, Type[LLMProvider]] = {}

    @classmethod
    def register_provider(cls, name: str, provider_class: Type[LLMProvider]) -> None:
        """Registers a new LLM provider."""
        cls._providers[name.lower().strip()] = provider_class

    @classmethod
    def get_provider(cls, name: str) -> Type[LLMProvider]:
        """Resolves and returns the uninstantiated LLM provider class type."""
        clean_name = name.lower().strip()
        provider_class = cls._providers.get(clean_name)
        if not provider_class:
            raise NotImplementedError(f"LLM provider adapter for '{name}' is not registered.")
        return provider_class


# Dynamically load concrete LLM provider package modules to trigger registration checks
import app.domains.ai.providers
