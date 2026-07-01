import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import PermissionChecker
from app.schemas.base import UnifiedResponse
from app.schemas.ai import (
    ConversationConnect,
    ConversationOut,
    MessageIn,
    MessageOut,
    ScheduledReportConnect,
    ScheduledReportOut,
)
from app.services.ai import AIService
from app.repositories.ai import conversation_repository, message_repository, scheduled_report_repository

router = APIRouter()


@router.post(
    "/chat",
    response_model=UnifiedResponse[ConversationOut],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(PermissionChecker("run_copilot"))]
)
async def start_conversation(
    payload: ConversationConnect,
    db: AsyncSession = Depends(get_db)
):
    """Creates a new conversation thread."""
    conv = await AIService.start_conversation(db, payload.project_id, payload.title)
    await db.commit()
    return {
        "status": "success",
        "message": "Conversation started successfully.",
        "data": conv,
        "metadata": {},
        "errors": []
    }


@router.get(
    "/history",
    response_model=UnifiedResponse[List[ConversationOut]],
    dependencies=[Depends(PermissionChecker("run_copilot"))]
)
async def get_conversation_history(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves conversation thread logs in a workspace."""
    convs = await AIService.get_conversations(db, project_id)
    return {
        "status": "success",
        "message": f"Retrieved {len(convs)} conversations.",
        "data": convs,
        "metadata": {},
        "errors": []
    }


@router.get(
    "/{conversationId}",
    response_model=UnifiedResponse[List[MessageOut]],
    dependencies=[Depends(PermissionChecker("run_copilot"))]
)
async def get_conversation_messages(
    conversationId: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves chronological messages inside a conversation thread."""
    messages = await message_repository.get_by_conversation(db, conversationId)
    return {
        "status": "success",
        "message": f"Retrieved {len(messages)} messages.",
        "data": messages,
        "metadata": {},
        "errors": []
    }


@router.post(
    "/{conversationId}/query",
    response_model=UnifiedResponse[MessageOut],
    dependencies=[Depends(PermissionChecker("run_copilot"))]
)
async def submit_query(
    conversationId: uuid.UUID,
    project_id: uuid.UUID,
    payload: MessageIn,
    provider: str = Query("openai"),
    persona: str = Query("devops"),
    db: AsyncSession = Depends(get_db)
):
    """Submits user query to agent context builder loop."""
    assistant_msg = await AIService.execute_chat(
        db, conversationId, project_id, payload.content, provider, persona
    )
    await db.commit()
    return {
        "status": "success",
        "message": "Assistant query execution completed.",
        "data": assistant_msg,
        "metadata": {},
        "errors": []
    }


@router.delete(
    "/{conversationId}",
    response_model=UnifiedResponse[None],
    dependencies=[Depends(PermissionChecker("run_copilot"))]
)
async def delete_conversation(
    conversationId: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Deletes a conversation thread."""
    await AIService.delete_conversation(db, conversationId)
    await db.commit()
    return {
        "status": "success",
        "message": "Conversation thread deleted successfully.",
        "data": None,
        "metadata": {},
        "errors": []
    }


@router.post(
    "/reports/generate",
    response_model=UnifiedResponse[dict],
    dependencies=[Depends(PermissionChecker("run_copilot"))]
)
async def generate_report(
    project_id: uuid.UUID,
    report_type: str = Query("finops"),
    db: AsyncSession = Depends(get_db)
):
    """Generates cost and resource metrics markdown report."""
    md_content = await AIService.generate_report(db, project_id, report_type)
    return {
        "status": "success",
        "message": "Report generated successfully.",
        "data": {"content": md_content},
        "metadata": {},
        "errors": []
    }
