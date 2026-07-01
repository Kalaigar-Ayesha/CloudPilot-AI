from typing import Dict, Type
from app.domains.billing.adapters.base import BillingProvider, PricingProvider


class BillingProviderFactory:
    """
    Registry factory instantiating billing adapters based on identifier keys.
    """
    _adapters: Dict[str, Type[BillingProvider]] = {}

    @classmethod
    def register_adapter(cls, provider_name: str, adapter_class: Type[BillingProvider]) -> None:
        """Registers a new billing adapter."""
        cls._adapters[provider_name.lower().strip()] = adapter_class

    @classmethod
    def get_adapter(cls, provider_name: str) -> Type[BillingProvider]:
        """Resolves and returns the uninstantiated billing adapter class type."""
        clean_name = provider_name.lower().strip()
        adapter_class = cls._adapters.get(clean_name)
        if not adapter_class:
            raise NotImplementedError(f"Billing provider adapter for '{provider_name}' is not registered.")
        return adapter_class


class PricingProviderFactory:
    """
    Registry factory instantiating pricing lookup adapters based on identifier keys.
    """
    _adapters: Dict[str, Type[PricingProvider]] = {}

    @classmethod
    def register_adapter(cls, provider_name: str, adapter_class: Type[PricingProvider]) -> None:
        """Registers a new pricing adapter."""
        cls._adapters[provider_name.lower().strip()] = adapter_class

    @classmethod
    def get_adapter(cls, provider_name: str) -> Type[PricingProvider]:
        """Resolves and returns the uninstantiated pricing adapter class type."""
        clean_name = provider_name.lower().strip()
        adapter_class = cls._adapters.get(clean_name)
        if not adapter_class:
            raise NotImplementedError(f"Pricing provider adapter for '{provider_name}' is not registered.")
        return adapter_class


# Dynamically load concrete billing adapters package to trigger registration checks
import app.domains.billing.adapters
