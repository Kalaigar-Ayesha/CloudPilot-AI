# Import concrete monitoring adapter implementations to trigger their registration with factory registry on application load
from app.domains.monitoring.adapters.prometheus import PrometheusAdapter
from app.domains.monitoring.adapters.cloudwatch import CloudWatchAdapter
from app.domains.monitoring.adapters.azure_monitor import AzureMonitorAdapter
from app.domains.monitoring.adapters.google_monitor import GCPMonitorAdapter
from app.domains.monitoring.adapters.datadog import DatadogAdapter
from app.domains.monitoring.adapters.new_relic import NewRelicAdapter
