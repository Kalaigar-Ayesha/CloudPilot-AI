# Import concrete adapter implementations to trigger their registration with the ProviderAdapterFactory on application load
from app.domains.cloud.adapters.aws import AWSProviderAdapter
from app.domains.cloud.adapters.azure import AzureProviderAdapter
from app.domains.cloud.adapters.gcp import GCPProviderAdapter
