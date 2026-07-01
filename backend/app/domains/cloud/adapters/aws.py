import logging
from typing import Any, Dict, List
try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    boto3 = None
    class BotoCoreError(Exception): pass
    class ClientError(Exception): pass

from app.domains.cloud.adapters.base import (
    CloudProviderAdapter,
    ConnectionConfig,
    NormalizedResourceDTO,
)
from app.domains.cloud.adapters.factory import ProviderAdapterFactory
from app.exceptions.base import AuthenticationException, ProviderException

logger = logging.getLogger("app.domains.cloud.adapters.aws")


class AWSProviderAdapter(CloudProviderAdapter):
    """
    AWS Adapter utilizing boto3 SDK.
    Connects, validates STS caller identity, and discovers resources.
    """
    def __init__(self):
        self._session = None
        self._config = None
        self._sts_client = None

    def connect(self, config: ConnectionConfig) -> None:
        self._config = config
        credentials = config.credentials
        
        try:
            # Handle IAM Role ARN assumption patterns or Access Keys
            if "role_arn" in credentials:
                # STS role assumption (standard enterprise pattern)
                sts = boto3.client("sts")
                assumed_role = sts.assume_role(
                    RoleArn=credentials["role_arn"],
                    RoleSessionName="CloudPilotDiscoverySession",
                    ExternalId=credentials.get("external_id")
                )
                creds = assumed_role["Credentials"]
                self._session = boto3.Session(
                    aws_access_key_id=creds["AccessKeyId"],
                    aws_secret_access_key=creds["SecretAccessKey"],
                    aws_session_token=creds["SessionToken"]
                )
            else:
                # Direct access keys
                self._session = boto3.Session(
                    aws_access_key_id=credentials["access_key"],
                    aws_secret_access_key=credentials["secret_key"],
                    aws_session_token=credentials.get("session_token")
                )
            self._sts_client = self._session.client("sts")
        except Exception as e:
            raise AuthenticationException(f"Failed to establish AWS Session: {str(e)}")

    def validate_credentials(self) -> bool:
        if not self._sts_client:
            raise AuthenticationException("AWS adapter is not connected.")
        try:
            # STS validation dry-run check
            self._sts_client.get_caller_identity()
            return True
        except (ClientError, BotoCoreError) as e:
            raise AuthenticationException(f"AWS credentials validation failed: {str(e)}")

    def disconnect(self) -> None:
        self._session = None
        self._sts_client = None
        self._config = None

    def discover_resources(self) -> List[NormalizedResourceDTO]:
        if not self._session:
            raise ProviderException("AWS Session is uninitialized.")

        resources = []
        regions = self._config.settings.get("regions", ["us-east-1"])

        for region in regions:
            try:
                # 1. Discover EC2 instances
                ec2 = self._session.client("ec2", region_name=region)
                instances = ec2.describe_instances()
                for reservation in instances.get("Reservations", []):
                    for inst in reservation.get("Instances", []):
                        if inst.get("State", {}).get("Name") == "terminated":
                            continue
                            
                        # Tag normalization
                        tags = {t["Key"]: t["Value"] for t in inst.get("Tags", [])}
                        
                        spec = {
                            "instance_type": inst.get("InstanceType"),
                            "vcpu_count": 4,  # Map type parameters locally or lookup
                            "memory_gb": 16.0,
                            "operating_system": inst.get("Platform", "linux"),
                            "lifecycle": "SPOT" if inst.get("InstanceLifecycle") == "spot" else "ON_DEMAND"
                        }
                        
                        resources.append(
                            NormalizedResourceDTO(
                                external_id=inst["InstanceId"],
                                name=tags.get("Name", inst["InstanceId"]),
                                resource_type="virtual_machine",
                                region=region,
                                status=inst["State"]["Name"],
                                tags=tags,
                                specification=spec,
                                raw_payload=inst
                            )
                        )
            except Exception as e:
                logger.error(f"Error executing AWS resource discovery in region {region}: {str(e)}")
                # We log partial failures and continue to verify other regions / services

        return resources

    def discover_regions(self) -> List[Dict[str, Any]]:
        if not self._session:
            raise ProviderException("AWS Session is uninitialized.")
        try:
            ec2 = self._session.client("ec2", region_name="us-east-1")
            response = ec2.describe_regions()
            return [
                {
                    "region_name": reg["RegionName"],
                    "display_name": reg["RegionName"],
                    "status": reg["OptInStatus"]
                }
                for reg in response.get("Regions", [])
            ]
        except Exception as e:
            raise ProviderException(f"Failed to query AWS regions: {str(e)}")

    def discover_services(self) -> List[Dict[str, Any]]:
        return [
            {"service_code": "ec2", "service_name": "Elastic Compute Cloud"},
            {"service_code": "s3", "service_name": "Simple Storage Service"},
            {"service_code": "rds", "service_name": "Relational Database Service"}
        ]

    def fetch_account_information(self) -> Dict[str, Any]:
        if not self._sts_client:
            raise ProviderException("AWS STS Client is uninitialized.")
        try:
            identity = self._sts_client.get_caller_identity()
            return {
                "account_id": identity["Account"],
                "arn": identity["Arn"],
                "user_id": identity["UserId"]
            }
        except Exception as e:
            raise ProviderException(f"Failed to fetch AWS identity information: {str(e)}")

    def health_check(self) -> str:
        try:
            self.validate_credentials()
            return "healthy"
        except Exception:
            return "unhealthy"


# Register adapter in Factory registry on load
ProviderAdapterFactory.register_adapter("aws", AWSProviderAdapter)
