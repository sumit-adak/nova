"""Conversation Manager orchestrating turns, AI intent, tool planning, and persistence."""
import json
import uuid
from datetime import datetime, timezone
import structlog
from sqlalchemy import select
from nova_app.ai_engine.intent_engine import get_intent_engine
from nova_app.conversation.models import ConversationTurn
from nova_app.conversation.session import ConversationSession
from nova_app.core.events import Event, get_event_bus
from nova_app.db.models.conversation import Conversation, Message
from nova_app.db.session import get_session_factory
from nova_app.memory.store import get_memory_store
from nova_app.tools.planner import get_tool_planner
from nova_app.tools.registry import get_tool_registry
from nova_app.tools.schema import ToolResult

logger = structlog.get_logger(__name__)


class ConversationManager:
    """Manages active conversation sessions, multi-turn state, and end-to-end execution flow."""

    def __init__(self):
        self._active_session: ConversationSession | None = None

    async def get_or_create_session(self, title: str = "New Conversation") -> ConversationSession:
        """Get or initialize the current active conversation session."""
        if self._active_session is None:
            session_factory = get_session_factory()
            async with session_factory() as session:
                conv = Conversation(title=title, started_at=datetime.now(timezone.utc))
                session.add(conv)
                await session.commit()
                await session.refresh(conv)
                self._active_session = ConversationSession(session_id=conv.id, title=title)
        return self._active_session

    async def process_user_input(
        self,
        user_text: str,
        confirmed_by_user: bool | None = None,
        auto_prompt_confirmation: bool = False,
    ) -> ConversationTurn:
        """
        Execute full conversational pipeline:
        1. Context & memory retrieval (preferences, recent projects)
        2. AI Intent analysis (with secret redaction)
        3. Tool planning & fuzzy index resolution
        4. Safe deterministic execution & append-only audit log
        5. Database message persistence
        """
        active_session = await self.get_or_create_session()
        turn_id = str(uuid.uuid4())

        # 1. Retrieve Memory Context
        memory_store = get_memory_store()
        memory_ctx = await memory_store.retrieve_context(query=user_text)

        # Build message history for AI context
        context_messages = active_session.to_message_list()
        
        # Inject memory context if present
        if memory_ctx.preferences or memory_ctx.recent_projects:
            mem_summary = f"[User Memory Context: Preferences={memory_ctx.preferences}, RecentProjects={memory_ctx.recent_projects}]"
            context_messages.append({"role": "system", "content": mem_summary})

        context_messages.append({"role": "user", "content": user_text})

        # 2. Analyze intent
        intent_engine = get_intent_engine()
        intent_resp = await intent_engine.analyze_intent(messages=context_messages)

        # 3. Plan and refine tool calls
        tool_planner = get_tool_planner()
        refined_tool_calls = await tool_planner.plan_and_refine(intent_resp.tool_calls)

        # 4. Execute planned tool calls safely
        tool_registry = get_tool_registry()
        tool_results: list[ToolResult] = []
        for call in refined_tool_calls:
            result = await tool_registry.execute_tool_call(
                call=call,
                actor="ai",
                confirmed_by_user=confirmed_by_user,
                auto_prompt_confirmation=auto_prompt_confirmation,
            )
            tool_results.append(result)

        # 5. Compose final response text if tools executed
        final_response = intent_resp.response
        if tool_results and not final_response:
            statuses = [
                f"{r.tool_name}: {'success' if r.success else f'failed ({r.error})'}"
                for r in tool_results
            ]
            final_response = f"Executed: {', '.join(statuses)}"

        # 6. Persist turn in memory session
        turn = ConversationTurn(
            id=turn_id,
            user_input=user_text,
            assistant_thought=intent_resp.thought,
            tool_calls=refined_tool_calls,
            tool_results=tool_results,
            assistant_response=final_response,
        )
        active_session.add_turn(turn)

        # 7. Persist messages to Database
        session_factory = get_session_factory()
        async with session_factory() as session:
            # User Message
            user_msg = Message(
                conversation_id=active_session.session_id,
                role="user",
                content=user_text,
                created_at=datetime.now(timezone.utc),
            )
            session.add(user_msg)

            # Assistant Message with tool calls json
            tool_calls_data = [tc.model_dump() for tc in refined_tool_calls]
            assistant_msg = Message(
                conversation_id=active_session.session_id,
                role="assistant",
                content=final_response,
                tool_calls_json=json.dumps(tool_calls_data) if tool_calls_data else None,
                created_at=datetime.now(timezone.utc),
            )
            session.add(assistant_msg)
            await session.commit()

        logger.info(
            "Processed conversation turn",
            turn_id=turn_id,
            tools_executed=len(tool_results),
            session_id=active_session.session_id
        )
        return turn


_conversation_manager_instance: ConversationManager | None = None


def get_conversation_manager() -> ConversationManager:
    """Get singleton ConversationManager instance."""
    global _conversation_manager_instance
    if _conversation_manager_instance is None:
        _conversation_manager_instance = ConversationManager()
    return _conversation_manager_instance
