import uuid
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from httpx import AsyncClient

from app.domains.ai.providers.base import LLMProvider, LLMMessage, LLMResponse
from app.domains.ai.providers.factory import LLMProviderFactory
from app.domains.ai.tools.base import AIToolRegistry


@pytest.mark.asyncio
async def test_llm_factory_resolution():
    """Verify registry factory resolves the correct uninstantiated provider types."""
    provider_class = LLMProviderFactory.get_provider("openai")
    assert provider_class is not None

    with pytest.raises(NotImplementedError):
        LLMProviderFactory.get_provider("unregistered-llm")


@pytest.mark.asyncio
async def test_tools_registry_listing():
    """Verify registry stores and resolves active AI tools."""
    tools = AIToolRegistry.get_tools()
    assert len(tools) > 0
    
    resource_tool = AIToolRegistry.get_tool("list_resources")
    assert resource_tool.name == "list_resources"


@pytest.mark.asyncio
async def test_start_conversation_endpoint(client: AsyncClient):
    """Test registering conversation threads endpoints."""
    register_payload = {
        "email": "ai_user@example.com",
        "password": "AICopilotPassword123!"
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    
    login_resp = await client.post("/api/v1/auth/login", json=register_payload)
    access_token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    project_id = str(uuid.uuid4())
    connect_payload = {
        "project_id": project_id,
        "title": "Copilot Chat Test"
    }

    resp = await client.post("/api/v1/ai/chat", json=connect_payload, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "success"
    assert body["data"]["title"] == "Copilot Chat Test"


@pytest.mark.asyncio
async def test_generate_report_endpoint(client: AsyncClient):
    """Test generating summaries report endpoint."""
    register_payload = {
        "email": "report_user@example.com",
        "password": "ReportPassword123!"
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    
    login_resp = await client.post("/api/v1/auth/login", json=register_payload)
    access_token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    project_id = str(uuid.uuid4())
    resp = await client.post(f"/api/v1/ai/reports/generate?project_id={project_id}&report_type=finops", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "content" in body["data"]
