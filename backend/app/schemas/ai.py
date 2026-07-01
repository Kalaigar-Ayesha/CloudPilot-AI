from datetime import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class MessageIn(BaseModel):
    """Input payload representing user queries."""
    content: str


class MessageOut(BaseModel):
    """Outputs messages details."""
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    token_count: int
    tool_calls: Optional[Dict[str, Any]] = None
    citations: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationOut(BaseModel):
    """Outputs chat threads parameters."""
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    pinned: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationConnect(BaseModel):
    """Payload registering a new chat thread."""
    project_id: uuid.UUID
    title: Optional[str] = "New Conversation"


class ScheduledReportConnect(BaseModel):
    """Payload scheduling a report configuration."""
    project_id: uuid.UUID
    name: str
    report_type: str  # executive, finops, technical
    format: Optional[str] = "markdown"  # markdown, html, pdf
    schedule_cron: str


class ScheduledReportOut(BaseModel):
    """Outputs report configurations."""
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    report_type: str
    format: str
    schedule_cron: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
