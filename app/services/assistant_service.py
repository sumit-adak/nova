"""Core assistant orchestration service."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from app.ai import create_provider
from app.ai.intent_parser import OfflineIntentParser
from app.ai.provider import AIProvider
from app.commands.registry import ActionResult, CommandRegistry
from app.commands import build_registry
from app.core.config import ConfigManager, get_settings
from app.core.logger import get_logger
from app.core.state import AssistantState
from app.memory.database import Database
from app.memory.memory_manager import MemoryManager

logger = get_logger("assistant")


@dataclass
class AssistantResponse:
    """Complete response from the assistant."""

    text: str
    state: AssistantState
    action_executed: str | None = None
    action_result: ActionResult | None = None
    requires_confirmation: bool = False
    confirmation_data: dict[str, Any] = field(default_factory=dict)


class AssistantService:
    """Orchestrates AI, commands, memory, and activity logging."""

    def __init__(
        self,
        registry: CommandRegistry | None = None,
        config: ConfigManager | None = None,
        provider: AIProvider | None = None,
    ) -> None:
        self.config = config or ConfigManager()
        self.registry = registry or build_registry(self.config)
        self.provider = provider or create_provider(get_settings())
        self.offline_parser = OfflineIntentParser()
        self.db = Database()
        self.memory = MemoryManager(self.db)
        self._state = AssistantState.IDLE
        self._state_callbacks: list[Callable[[AssistantState], None]] = []
        self._pending_confirmation: dict[str, Any] | None = None

    @property
    def state(self) -> AssistantState:
        return self._state

    def on_state_change(self, callback: Callable[[AssistantState], None]) -> None:
        self._state_callbacks.append(callback)

    def _set_state(self, state: AssistantState) -> None:
        self._state = state
        for cb in self._state_callbacks:
            try:
                cb(state)
            except Exception as exc:
                logger.error("State callback error: %s", exc)

    async def process_input(self, user_input: str) -> AssistantResponse:
        """Process user text input through intent parsing and action execution."""
        if not user_input.strip():
            return AssistantResponse(
                text="How can I help you?",
                state=AssistantState.IDLE,
            )

        self._set_state(AssistantState.THINKING)
        logger.info("Processing: %s", user_input)

        intent = await self._parse_intent(user_input)

        if intent.get("type") == "conversation":
            response_text = intent.get("response", "")
            if not response_text and self.provider.is_available:
                self._set_state(AssistantState.THINKING)
                response_text = await self.provider.chat(
                    [{"role": "user", "content": user_input}]
                )
            elif not response_text:
                response_text = (
                    "I can help with local commands like opening apps, checking system stats, "
                    "or launching projects. Try 'open VS Code' or 'what's my RAM usage'."
                )
            self._log_activity(user_input, None, {}, response_text, "conversation")
            self._set_state(AssistantState.SUCCESS)
            return AssistantResponse(text=response_text, state=AssistantState.SUCCESS)

        # Multi-action execution
        if intent.get("type") == "actions" or "actions" in intent:
            return await self._execute_multiple_actions(
                user_input, intent.get("actions", []), intent.get("response", "")
            )

        action_name = intent.get("action")
        parameters = intent.get("parameters", {})
        response_text = intent.get("response", "On it.")

        if not action_name:
            self._set_state(AssistantState.ERROR)
            return AssistantResponse(
                text="I couldn't understand that command.",
                state=AssistantState.ERROR,
            )

        return await self._execute_action(user_input, action_name, parameters, response_text)

    async def _execute_multiple_actions(
        self,
        user_input: str,
        actions: list[dict[str, Any]],
        response_text: str = "",
    ) -> AssistantResponse:
        """Execute a sequence of actions step-by-step."""
        self._set_state(AssistantState.EXECUTING)
        executed_messages: list[str] = []
        last_result = None
        all_success = True

        for item in actions:
            act_name = item.get("action")
            params = item.get("parameters", {})
            if not act_name:
                continue

            result = await self.registry.execute(act_name, params)
            last_result = result
            if not result.success:
                all_success = False
                executed_messages.append(f"Failed {act_name}: {result.message}")
                break
            else:
                executed_messages.append(f"{result.message}")

        status = "success" if all_success else "error"
        summary_lines = "\n".join(executed_messages)
        if response_text and all_success:
            final_text = f"{response_text}\n\n{summary_lines}" if summary_lines else response_text
        else:
            final_text = summary_lines or (response_text or "Done.")

        self._log_activity(
            user_input,
            ", ".join(a.get("action", "") for a in actions),
            {"actions_count": len(actions)},
            final_text,
            status,
        )
        self._set_state(
            AssistantState.SUCCESS if all_success else AssistantState.ERROR
        )
        return AssistantResponse(
            text=final_text,
            state=self._state,
            action_executed="multi_action",
            action_result=last_result,
        )

    async def confirm_pending_action(self) -> AssistantResponse:
        """Execute a previously pending confirmation action."""
        if not self._pending_confirmation:
            return AssistantResponse(
                text="No pending action to confirm.",
                state=AssistantState.IDLE,
            )

        data = self._pending_confirmation
        self._pending_confirmation = None
        action = data.get("action")
        params = data.get("parameters", {})
        user_input = data.get("user_input", "")

        return await self._execute_action(
            user_input, action, params, "Confirmed.", skip_confirmation=True
        )

    def cancel_pending_action(self) -> AssistantResponse:
        self._pending_confirmation = None
        self._set_state(AssistantState.IDLE)
        return AssistantResponse(text="Action cancelled.", state=AssistantState.IDLE)

    async def _parse_intent(self, user_input: str) -> dict[str, Any]:
        actions = self.registry.get_action_descriptions()

        if self.provider.name == "Offline":
            return self.offline_parser.parse(user_input)

        if not self.provider.is_available:
            return self.offline_parser.parse(user_input)

        intent = await self.provider.parse_intent(user_input, actions)

        if intent.get("type") in ("offline", "error") or (not intent.get("action") and not intent.get("actions")):
            offline = self.offline_parser.parse(user_input)
            if offline.get("action") or offline.get("actions"):
                return offline

        return intent

    async def _execute_action(
        self,
        user_input: str,
        action_name: str,
        parameters: dict[str, Any],
        response_text: str,
        skip_confirmation: bool = False,
    ) -> AssistantResponse:
        self._set_state(AssistantState.EXECUTING)

        result = await self.registry.execute(action_name, parameters)

        if result.requires_confirmation and not skip_confirmation:
            confirm_action = result.data.get("action", f"{action_name}_confirmed")
            confirm_params = {k: v for k, v in result.data.items() if k != "action"}
            self._pending_confirmation = {
                "action": confirm_action,
                "parameters": confirm_params,
                "user_input": user_input,
            }
            self._set_state(AssistantState.CONFIRMATION_REQUIRED)
            return AssistantResponse(
                text=result.confirmation_message,
                state=AssistantState.CONFIRMATION_REQUIRED,
                requires_confirmation=True,
                confirmation_data=self._pending_confirmation,
                action_executed=action_name,
            )

        final_text = result.message if result.message else response_text
        if result.success and result.message:
            final_text = result.message

        status = "success" if result.success else "error"
        self._log_activity(
            user_input, action_name, parameters, final_text, status
        )
        self._set_state(
            AssistantState.SUCCESS if result.success else AssistantState.ERROR
        )

        return AssistantResponse(
            text=final_text,
            state=self._state,
            action_executed=action_name,
            action_result=result,
        )

    def _log_activity(
        self,
        user_command: str,
        action: str | None,
        params: dict,
        message: str,
        status: str,
    ) -> None:
        self.db.log_activity(
            user_command=user_command,
            intent_action=action,
            intent_params=json.dumps(params),
            result_message=message,
            status=status,
        )

    def get_recent_activity(self, limit: int = 20) -> list[dict]:
        return self.db.get_activity(limit)

    def clear_activity(self) -> int:
        return self.db.clear_activity()
