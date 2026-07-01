# Import concrete billing and pricing adapter implementations to trigger their registration on application load
from app.domains.billing.adapters.aws import AWSBillingProvider, AWSPricingProvider
from app.domains.billing.adapters.azure import AzureBillingProvider, AzurePricingProvider
from app.domains.billing.adapters.gcp import GCPBillingProvider, GCPPricingProvider
