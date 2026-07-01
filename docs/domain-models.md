# Normalized Domain Models & Enums

This document defines the normalized domain models and shared enums for **CloudPilot AI**. These models provide a cloud-agnostic interface representation of system objects.

---

## 1. Domain Enums

These enums represent fixed options across the system:

```python
from enum import Enum

class CloudProvider(str, Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ORACLE = "oracle"
    ALIBABA = "alibaba"
    DIGITALOCEAN = "digitalocean"
    HETZNER = "hetzner"
    LINODE = "linode"

class ResourceType(str, Enum):
    VIRTUAL_MACHINE = "virtual_machine"
    DATABASE = "database"
    OBJECT_STORAGE = "object_storage"
    LOAD_BALANCER = "load_balancer"
    CONTAINER_NODE = "container_node"
    KUBERNETES_CLUSTER = "kubernetes_cluster"

class ResourceState(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    TERMINATED = "terminated"
    PROVISIONING = "provisioning"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"

class BillingCategory(str, Enum):
    COMPUTE = "compute"
    STORAGE = "storage"
    DATABASE = "database"
    NETWORKING = "networking"
    DATA_TRANSFER = "data_transfer"
    TAX = "tax"
    OTHER = "other"

class MetricType(str, Enum):
    CPU_UTILIZATION = "cpu_utilization"
    MEMORY_UTILIZATION = "memory_utilization"
    DISK_IOPS = "disk_iops"
    NETWORK_THROUGHPUT = "network_throughput"

class RecommendationType(str, Enum):
    RIGHTSIZE = "rightsize"
    TERMINATE = "terminate"
    TIER_MIGRATION = "tier_migration"
    COMMITMENT = "commitment"

class OptimizationStatus(str, Enum):
    ACTIVE = "active"
    APPLIED = "applied"
    DISMISSED = "dismissed"
    STALE = "stale"

class NotificationType(str, Enum):
    RESOURCE_ALERT = "resource_alert"
    OPTIMIZATION_READY = "optimization_ready"
    BILLING_SPIKE = "billing_spike"
    SYSTEM_ALERT = "system_alert"

class Role(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    BILLING_ADMIN = "billing_admin"
    VIEWER = "viewer"

class Permission(str, Enum):
    CONNECT_PROVIDER = "connect_provider"
    DISCONNECT_PROVIDER = "disconnect_provider"
    VIEW_COSTS = "view_costs"
    VIEW_INVENTORY = "view_inventory"
    APPLY_OPTIMIZATION = "apply_optimization"
    DISMISS_OPTIMIZATION = "dismiss_optimization"
    READ_CHAT = "read_chat"
    WRITE_CHAT = "write_chat"
    EXPORT_REPORTS = "export_reports"
```

---

## 2. Normalized Domain Models

The core business logic interacts exclusively with these Python representation schemas.

```python
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, EmailStr

class CloudAccount(BaseModel):
    id: str
    project_id: str
    provider: CloudProvider
    name: str
    account_identifier: str  # AWS account ID, Azure Subscription ID
    status: str
    created_at: datetime
    updated_at: datetime


class MonitoringSource(BaseModel):
    id: str
    project_id: str
    provider_id: str
    name: str
    endpoint_url: str
    status: str
    created_at: datetime


class Resource(BaseModel):
    id: str
    cloud_account_id: str
    external_id: str  # Provider-specific ID/ARN
    name: str
    resource_type: ResourceType
    region: str
    status: ResourceState
    tags: Dict[str, str] = Field(default_factory=dict)
    specification: Dict[str, Any] = Field(
        ..., 
        description="Type-specific properties (e.g., vcpu_count, memory_gb)"
    )
    created_at: datetime
    updated_at: datetime


class BillingRecord(BaseModel):
    id: str
    cloud_account_id: str
    resource_id: Optional[str] = None
    usage_start: datetime
    usage_end: datetime
    cost: float
    currency: str = "USD"
    usage_type: str
    category: BillingCategory
    raw_payload: Dict[str, Any]


class Metric(BaseModel):
    resource_id: str
    metric_type: MetricType
    timestamp: datetime
    value: float
    unit: str


class Recommendation(BaseModel):
    id: str
    resource_id: str
    rule_id: str
    recommendation_type: RecommendationType
    savings_potential_monthly: float
    current_configuration: Dict[str, Any]
    target_configuration: Dict[str, Any]
    status: OptimizationStatus
    reasoning: str
    created_at: datetime
    resolved_at: Optional[datetime] = None


class Forecast(BaseModel):
    project_id: str
    cloud_account_id: Optional[str] = None
    forecast_type: str  # cost, usage
    baseline_cost: float
    optimistic_cost: float
    pessimistic_cost: float
    start_date: datetime
    end_date: datetime
    data_points: List[Dict[str, Any]] = Field(
        ...,
        description="List of date objects containing forecast values"
    )


class Pricing(BaseModel):
    sku: str
    provider: CloudProvider
    region: str
    service_code: str
    resource_specification: Dict[str, Any]
    unit_price_hourly: float
    currency: str = "USD"
```
