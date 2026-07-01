from typing import Dict, Type
from app.domains.cloud.adapters.base import CloudProviderAdapter


class ProviderAdapterFactory:
    """
    Registry factory instantiating cloud adapters based on identifier keys.
    """
    _adapters: Dict[str, Type[CloudProviderAdapter]] = {}

    @classmethod
    def register_adapter(cls, provider_name: str, adapter_class: Type[CloudProviderAdapter]) -> None:
        """Registers a new cloud adapter implementation."""
        cls._adapters[provider_name.lower().strip()] = adapter_class

    @classmethod
    def get_adapter(cls, provider_name: str) -> Type[CloudProviderAdapter]:
        """Resolves and returns the uninstantiated adapter class type."""
        clean_name = provider_name.lower().strip()
        adapter_class = cls._adapters.get(clean_name)
        if not adapter_class:
            raise NotImplementedError(f"Cloud provider adapter for '{provider_name}' is not registered.")
        return adapter_class


# Dynamically load concrete adapters package to trigger registration checks
import app.domains.cloud.adapters

