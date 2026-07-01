import logging
import json
import uuid
from typing import Any, Dict, List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.providers.base import LLMMessage, LLMResponse
from app.domains.ai.providers.factory import LLMProviderFactory
from app.domains.ai.tools.base import AIToolRegistry
from app.domains.ai.prompts.templates import SYSTEM_PROMPTS
from app.exceptions.base import ValidationException, ProviderException
from app.models.ai import Conversation, Message
from app.repositories.ai import conversation_repository, message_repository

logger = logging.getLogger("app.services.ai")


class AIService:
    """
    Coordinates chat thread contexts, resolves LLM providers, parses dynamic
    agent tool calling loops, and handles report generations.
    """

    @staticmethod
    async def start_conversation(db: AsyncSession, project_id: uuid.UUID, title: str) -> Conversation:
        """Registers a new conversation thread."""
        conv_data = {
            "project_id": project_id,
            "title": title,
            "pinned": False,
            "metadata_info": {}
        }
        db_conv = await conversation_repository.create(db, obj_in=conv_data)
        await db.flush()
        return db_conv

    @staticmethod
    async def get_conversations(db: AsyncSession, project_id: uuid.UUID) -> Sequence[Conversation]:
        """Fetch all active threads under a project."""
        return await conversation_repository.get_by_project(db, project_id)

    @staticmethod
    async def delete_conversation(db: AsyncSession, conversation_id: uuid.UUID) -> None:
        """Removes a thread connection."""
        conv = await conversation_repository.get(db, conversation_id)
        if not conv:
            raise ValidationException("Conversation thread not found.")
        await conversation_repository.remove(db, id=conversation_id)

    @staticmethod
    async def execute_chat(
        db: AsyncSession,
        conversation_id: uuid.UUID,
        project_id: uuid.UUID,
        user_content: str,
        provider_name: str = "openai",
        persona: str = "devops"
    ) -> Message:
        """
        Coordinates full LLM agent loops including context assembly and tool executions.
        """
        conv = await conversation_repository.get(db, conversation_id)
        if not conv:
            raise ValidationException("Conversation thread not found.")

        # 1. Fetch historical thread log
        db_messages = await message_repository.get_by_conversation(db, conversation_id)
        
        # 2. Append new user query
        user_msg_data = {
            "conversation_id": conversation_id,
            "role": "user",
            "content": user_content,
            "token_count": len(user_content) // 4
        }
        await message_repository.create(db, obj_in=user_msg_data)
        await db.flush()

        # Build message history payload
        llm_messages = []
        for msg in db_messages:
            llm_messages.append(LLMMessage(role=msg.role, content=msg.content))
        llm_messages.append(LLMMessage(role="user", content=user_content))

        # 3. Resolve LLM Provider
        try:
            provider_class = LLMProviderFactory.get_provider(provider_name)
            provider = provider_class()
            # Configure using dummy settings for verification
            provider.connect(api_key="mock_key", model_name="gpt-4o", settings={})
        except Exception as e:
            raise ProviderException(f"LLM integration resolution failed: {str(e)}")

        # Retrieve system prompt
        system_prompt = SYSTEM_PROMPTS.get(persona, SYSTEM_PROMPTS["devops"])

        # Format tool descriptions schemas
        registered_tools = AIToolRegistry.get_tools()
        tools_schema = []
        for t in registered_tools:
            tools_schema.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters
                }
            })

        # 4. Invoke LLM (First Turn check)
        response = provider.chat(
            messages=llm_messages,
            system_prompt=system_prompt,
            tools=tools_schema
        )

        citations_metadata = {}

        # 5. Handle LLM Tool Calling request loops
        if response.tool_calls:
            logger.info(f"LLM requested tool calls: {[tc['function']['name'] for tc in response.tool_calls]}")
            
            tool_messages = []
            for tool_call in response.tool_calls:
                func_name = tool_call["function"]["name"]
                func_args_str = tool_call["function"].get("arguments", "{}")
                
                try:
                    func_args = json.loads(func_args_str)
                except Exception:
                    func_args = {}

                # Resolve and execute tool
                try:
                    tool = AIToolRegistry.get_tool(func_name)
                    tool_result = await tool.execute(db, str(project_id), func_args)
                    citations_metadata[func_name] = tool_result
                except Exception as te:
                    tool_result = {"error": f"Tool execution failed: {str(te)}"}

                tool_messages.append(
                    LLMMessage(
                        role="tool",
                        content=json.dumps(tool_result),
                        tool_calls=[tool_call]
                    )
                )

            # Append tool outputs to messages log
            llm_messages.extend(tool_messages)

            # Re-submit messages to get final text
            response = provider.chat(
                messages=llm_messages,
                system_prompt=system_prompt,
                tools=None
            )

        # 6. Save assistant output
        assistant_msg_data = {
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": response.content,
            "token_count": response.output_tokens,
            "citations": citations_metadata
        }
        db_assistant_msg = await message_repository.create(db, obj_in=assistant_msg_data)
        await db.flush()

        # Update conversation updated_at trigger
        conv.title = user_content[:50] + ("..." if len(user_content) > 50 else "")
        
        return db_assistant_msg

    @staticmethod
    async def generate_report(
        db: AsyncSession,
        project_id: uuid.UUID,
        report_type: str = "finops"
    ) -> str:
        """
        Compiles structural inventories and metric summaries and formats a markdown summary report.
        """
        # Execute tools context assembly
        resource_tool = AIToolRegistry.get_tool("list_resources")
        billing_tool = AIToolRegistry.get_tool("get_billing_summary")
        opt_tool = AIToolRegistry.get_tool("get_optimization_recommendations")

        resources = await resource_tool.execute(db, str(project_id), {})
        billing = await billing_tool.execute(db, str(project_id), {})
        opts = await opt_tool.execute(db, str(project_id), {})

        # Formulate direct prompt context
        report_prompt = (
            f"Generate a formal {report_type.upper()} report based on: \n"
            f"Active Resources: {json.dumps(resources)}\n"
            f"Financial Summary: {json.dumps(billing)}\n"
            f"Optimization Options: {json.dumps(opts)}\n"
            "Format the output cleanly in markdown detailing sections: "
            "Executive Summary, Cost Drivers, Potential Savings, and Recommendations."
        )

        try:
            # Resolve OpenAI fallback client
            provider_class = LLMProviderFactory.get_provider("openai")
            provider = provider_class()
            provider.connect(api_key="mock_key", model_name="gpt-4o", settings={})
            
            response = provider.chat(
                messages=[LLMMessage(role="user", content=report_prompt)],
                system_prompt=SYSTEM_PROMPTS["finops"]
            )
            return response.content
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            return f"# CloudPilot AI Report \n\nFailed to compile live API data: {str(e)}"
