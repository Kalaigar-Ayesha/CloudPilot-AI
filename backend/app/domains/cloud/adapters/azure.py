import logging
from typing import Any, Dict, List

# Fallback imports or dynamic imports checking
try:
    from azure.identity import ClientSecretCredential
    from azure.mgmt.subscription import SubscriptionClient
    from azure.mgmt.compute import ComputeManagementClient
except ImportError:
    # Set mock classes if azure packages are not installed in testing environments
    ClientSecretCredential = None
    SubscriptionClient = None
    ComputeManagementClient = None

from app.domains.cloud.adapters.base import (
    CloudProviderAdapter,
    ConnectionConfig,
    NormalizedResourceDTO,
)
from app.domains.cloud.adapters.factory import ProviderAdapterFactory
from app.exceptions.base import AuthenticationException, ProviderException

logger = logging.getLogger("app.domains.cloud.adapters.azure")


class AzureProviderAdapter(CloudProviderAdapter):
    """
    Azure Adapter utilizing the Azure SDK client packages.
    """
    def __init__(self):
        self._credential = None
        self._subscription_id = None
        self._config = None

    def connect(self, config: ConnectionConfig) -> None:
        self._config = config
        creds = config.credentials
        
        try:
            self._subscription_id = creds["subscription_id"]
            # Connect via client secret credentials (standard Active Directory app registrations)
            self._credential = ClientSecretCredential(  # type: ignore
                tenant_id=creds["tenant_id"],
                client_id=creds["client_id"],
                client_secret=creds["client_secret"]
            )
        except Exception as e:
            raise AuthenticationException(f"Failed to authenticate Azure Credentials: {str(e)}")

    def validate_credentials(self) -> bool:
        if not self._credential:
            raise AuthenticationException("Azure credentials are not initialized.")
        try:
            # Validate credentials using the Subscription Client check
            sub_client = SubscriptionClient(self._credential)  # type: ignore
            sub_client.subscriptions.get(self._subscription_id or "")
            return True
        except Exception as e:
            raise AuthenticationException(f"Azure subscription check validation failed: {str(e)}")

    def disconnect(self) -> None:
        self._credential = None
        self._subscription_id = None
        self._config = None

    def discover_resources(self) -> List[NormalizedResourceDTO]:
        if not self._credential:
            raise ProviderException("Azure credentials uninitialized.")

        resources = []
        try:
            # Query compute VMs via resource management
            compute_client = ComputeManagementClient(self._credential, self._subscription_id or "")  # type: ignore
            vms = compute_client.virtual_machines.list_all()
            for vm in vms:
                spec = {
                    "instance_type": vm.hardware_profile.vm_size if vm.hardware_profile else "Standard_D2s_v3",
                    "vcpu_count": 2,
                    "memory_gb": 8.0,
                    "operating_system": vm.storage_profile.os_disk.os_type.value.lower() if vm.storage_profile and vm.storage_profile.os_disk and vm.storage_profile.os_disk.os_type else "linux",
                    "lifecycle": "ON_DEMAND"  # Check spot designations in properties
                }
                
                # Tags mapping (Azure Tags are simple dict string structures)
                tags = vm.tags if vm.tags else {}
                
                resources.append(
                    NormalizedResourceDTO(
                        external_id=vm.id or "",
                        name=vm.name or "",
                        resource_type="virtual_machine",
                        region=vm.location,
                        status="running",  # Fetch VM Instance View status if required
                        tags=tags,
                        specification=spec,
                        raw_payload={"id": vm.id, "name": vm.name, "type": vm.type}
                    )
                )
        except Exception as e:
            logger.error(f"Error querying Azure compute resources: {str(e)}")
            
        return resources

    def discover_regions(self) -> List[Dict[str, Any]]:
        if not self._credential:
            raise ProviderException("Azure credentials uninitialized.")
        try:
            sub_client = SubscriptionClient(self._credential)  # type: ignore
            locations = sub_client.subscriptions.list_locations(self._subscription_id or "")
            return [
                {
                    "region_name": loc.name,
                    "display_name": loc.display_name,
                    "status": "OptInNotRequired"
                }
                for loc in locations
            ]
        except Exception as e:
            raise ProviderException(f"Failed to fetch Azure regions: {str(e)}")

    def discover_services(self) -> List[Dict[str, Any]]:
        return [
            {"service_code": "Microsoft.Compute", "service_name": "Virtual Machines"},
            {"service_code": "Microsoft.Storage", "service_name": "Storage Accounts"},
            {"service_code": "Microsoft.Sql", "service_name": "SQL Databases"}
        ]

    def fetch_account_information(self) -> Dict[str, Any]:
        if not self._credential:
            raise ProviderException("Azure credentials uninitialized.")
        try:
            sub_client = SubscriptionClient(self._credential)  # type: ignore
            sub = sub_client.subscriptions.get(self._subscription_id or "")
            return {
                "subscription_id": sub.subscription_id,
                "display_name": sub.display_name,
                "tenant_id": getattr(sub, "tenant_id", None)
            }
        except Exception as e:
            raise ProviderException(f"Failed to fetch Azure subscription info: {str(e)}")

    def health_check(self) -> str:
        try:
            self.validate_credentials()
            return "healthy"
        except Exception:
            return "unhealthy"


# Register in factory
ProviderAdapterFactory.register_adapter("azure", AzureProviderAdapter)
