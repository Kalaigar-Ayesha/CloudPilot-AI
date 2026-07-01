from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class UnifiedResponse(BaseModel, Generic[T]):
    """
    Standardized API Response wrapper matching objective format standards.
    """
    status: str = Field(..., description="API execution status: success or error")
    message: str = Field(..., description="Human-readable informational message")
    data: Optional[T] = Field(default=None, description="Response payload container")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dynamic contextual details (e.g. pagination, request ID)"
    )
    errors: List[Any] = Field(
        default_factory=list,
        description="Array containing structural or operational error details"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC time the response was generated"
    )


class PaginationMetadata(BaseModel):
    """Metadata payload describing paginated collection states."""
    total_count: int
    skip: int
    limit: int
    has_next: bool
