from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pydantic import BaseModel


class ConnectionConfig(BaseModel):
    """
    Standardized payload format passed to initialize adapter connections.
    """
    account_id: str
    provider_name: str
    credentials: Dict[str, Any]
    settings: Dict[str, Any]


class NormalizedResourceDTO(BaseModel):
    """Normalized data transport object returned from adapter discovery."""
    external_id: str
    name: str
    resource_type: str
    region: str
    status: str
    tags: Dict[str, str]
    specification: Dict[str, Any]
    raw_payload: Dict[str, Any]


class CloudProviderAdapter(ABC):
    """
    Abstract Base Class representing the Common Interface for all Cloud Adapters.
    """
    
    @abstractmethod
    def connect(self, config: ConnectionConfig) -> None:
        """
        Initializes connection session credentials.
        Raises AuthenticationException on failure.
        """
        pass

    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        Performs STS / account check dry-runs to verify connection parameters.
        Returns True if authorization credentials are correct.
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Tears down connections and sessions."""
        pass

    @abstractmethod
    def discover_resources(self) -> List[NormalizedResourceDTO]:
        """Discovers inventory catalog and returns a list of normalized resource DTOs."""
        pass

    @abstractmethod
    def discover_regions(self) -> List[Dict[str, Any]]:
        """Returns lists of regions available for resource provisioning."""
        pass

    @abstractmethod
    def discover_services(self) -> List[Dict[str, Any]]:
        """Returns supported cloud services."""
        pass

    @abstractmethod
    def fetch_account_information(self) -> Dict[str, Any]:
        """Retrieves details of connected accounts (IDs, organizational tags)."""
        pass

    @abstractmethod
    def health_check(self) -> str:
        """Runs basic heartbeats to check remote API availability."""
        pass
