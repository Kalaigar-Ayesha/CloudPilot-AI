from datetime import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CloudAccountConnect(BaseModel):
    """Schema validating input when connecting a cloud account integration."""
    project_id: uuid.UUID
    provider_id: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=100)
    account_identifier: str = Field(..., min_length=2, max_length=100)
    credentials: Dict[str, Any] = Field(
        ...,
        description="Dynamic credentials payload (e.g. key/secret parameters)"
    )
    settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional config parameters (e.g., target regions list)"
    )


class CloudAccountValidate(BaseModel):
    """Schema validating standalone check credentials requests."""
    provider_id: str
    credentials: Dict[str, Any]


class CloudAccountOut(BaseModel):
    """Outputs basic cloud registration details."""
    id: uuid.UUID
    project_id: uuid.UUID
    provider_id: str
    name: str
    account_identifier: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class RegionInfoOut(BaseModel):
    """Normalized Region description representation."""
    region_name: str
    display_name: str
    status: str


class ServiceInfoOut(BaseModel):
    """Normalized Service metadata representation."""
    service_code: str
    service_name: str


class NormalizedResourceOut(BaseModel):
    """Normalized resource structure representing all cloud platforms uniformly."""
    id: uuid.UUID
    cloud_account_id: uuid.UUID
    external_id: str
    name: str
    resource_type: str
    region: str
    status: str
    tags: Dict[str, str]
    specification: Dict[str, Any]

    class Config:
        from_attributes = True
