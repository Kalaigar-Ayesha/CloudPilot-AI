import logging
from typing import Any, Dict, List
import json

# Fallback imports or dynamic imports checking
try:
    from google.oauth2 import service_account
    from google.cloud import compute_v1
except ImportError:
    service_account = None
    compute_v1 = None

from app.domains.cloud.adapters.base import (
    CloudProviderAdapter,
    ConnectionConfig,
    NormalizedResourceDTO,
)
from app.domains.cloud.adapters.factory import ProviderAdapterFactory
from app.exceptions.base import AuthenticationException, ProviderException

logger = logging.getLogger("app.domains.cloud.adapters.gcp")


class GCPProviderAdapter(CloudProviderAdapter):
    """
    GCP Adapter utilizing google-cloud Python libraries.
    """
    def __init__(self):
        self._credentials = None
        self._project_id = None
        self._config = None

    def connect(self, config: ConnectionConfig) -> None:
        self._config = config
        creds = config.credentials
        
        try:
            # Load credential information from the service account JSON structure
            service_account_info = creds.get("service_account_json")
            if isinstance(service_account_info, str):
                service_account_info = json.loads(service_account_info)
                
            if not service_account_info or not isinstance(service_account_info, dict):
                raise AuthenticationException("GCP service account JSON is invalid or missing.")
                
            self._project_id = service_account_info.get("project_id")
            self._credentials = service_account.Credentials.from_service_account_info(  # type: ignore
                service_account_info
            )
        except Exception as e:
            raise AuthenticationException(f"Failed to authenticate GCP Credentials: {str(e)}")

    def validate_credentials(self) -> bool:
        if not self._credentials:
            raise AuthenticationException("GCP credentials are not initialized.")
        try:
            # Query GCP zones to verify authentication credentials
            zone_client = compute_v1.ZonesClient(credentials=self._credentials)  # type: ignore
            zone_client.list(project=self._project_id)
            return True
        except Exception as e:
            raise AuthenticationException(f"GCP project validation check failed: {str(e)}")

    def disconnect(self) -> None:
        self._credentials = None
        self._project_id = None
        self._config = None

    def discover_resources(self) -> List[NormalizedResourceDTO]:
        if not self._credentials:
            raise ProviderException("GCP credentials uninitialized.")

        resources = []
        try:
            # Query instance zones using VM lists API
            instance_client = compute_v1.InstancesClient(credentials=self._credentials)  # type: ignore
            instances = instance_client.aggregated_list(project=self._project_id)
            
            for zone, instances_in_zone in instances:
                if not instances_in_zone.instances:
                    continue
                for inst in instances_in_zone.instances:
                    # Parse zone from URL
                    clean_zone = zone.split("/")[-1] if "/" in zone else zone
                    
                    spec = {
                        "instance_type": inst.machine_type.split("/")[-1] if inst.machine_type else "n1-standard-1",
                        "vcpu_count": 1,
                        "memory_gb": 3.75,
                        "operating_system": "linux",
                        "lifecycle": "SPOT" if inst.scheduling and inst.scheduling.preemptible else "ON_DEMAND"
                    }
                    
                    # Labels (GCP Labels are maps of key-value properties)
                    labels = dict(inst.labels) if inst.labels else {}
                    
                    resources.append(
                        NormalizedResourceDTO(
                            external_id=str(inst.id),
                            name=inst.name,
                            resource_type="virtual_machine",
                            region=clean_zone,
                            status=inst.status.lower(),
                            tags=labels,
                            specification=spec,
                            raw_payload={"id": inst.id, "name": inst.name, "status": inst.status}
                        )
                    )
        except Exception as e:
            logger.error(f"Error querying GCP compute resources: {str(e)}")
            
        return resources

    def discover_regions(self) -> List[Dict[str, Any]]:
        if not self._credentials:
            raise ProviderException("GCP credentials uninitialized.")
        try:
            region_client = compute_v1.RegionsClient(credentials=self._credentials)  # type: ignore
            regions = region_client.list(project=self._project_id)
            return [
                {
                    "region_name": reg.name,
                    "display_name": reg.name,
                    "status": reg.status
                }
                for reg in regions
            ]
        except Exception as e:
            raise ProviderException(f"Failed to fetch GCP regions: {str(e)}")

    def discover_services(self) -> List[Dict[str, Any]]:
        return [
            {"service_code": "compute", "service_name": "Compute Engine"},
            {"service_code": "storage", "service_name": "Cloud Storage"},
            {"service_code": "sql", "service_name": "Cloud SQL"}
        ]

    def fetch_account_information(self) -> Dict[str, Any]:
        return {
            "project_id": self._project_id,
            "client_email": self._credentials.service_account_email if self._credentials else None
        }

    def health_check(self) -> str:
        try:
            self.validate_credentials()
            return "healthy"
        except Exception:
            return "unhealthy"


# Register in factory
ProviderAdapterFactory.register_adapter("gcp", GCPProviderAdapter)
