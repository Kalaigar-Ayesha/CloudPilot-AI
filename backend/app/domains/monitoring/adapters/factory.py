from typing import Dict, Type
from app.domains.monitoring.adapters.base import MonitoringAdapter


class MonitoringProviderFactory:
    """
    Registry factory instantiating monitoring adapters based on identifier keys.
    """
    _adapters: Dict[str, Type[MonitoringAdapter]] = {}

    @classmethod
    def register_adapter(cls, provider_name: str, adapter_class: Type[MonitoringAdapter]) -> None:
        """Registers a new monitoring adapter implementation."""
        cls._adapters[provider_name.lower().strip()] = adapter_class

    @classmethod
    def get_adapter(cls, provider_name: str) -> Type[MonitoringAdapter]:
        """Resolves and returns the uninstantiated adapter class type."""
        clean_name = provider_name.lower().strip()
        adapter_class = cls._adapters.get(clean_name)
        if not adapter_class:
            raise NotImplementedError(f"Monitoring adapter for '{provider_name}' is not registered.")
        return adapter_class


# Dynamically load concrete monitoring adapters package to trigger registration checks
import app.domains.monitoring.adapters
