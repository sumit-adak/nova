"""Command registry and action definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

from app.core.state import PermissionLevel


@dataclass
class ActionResult:
    """Result of executing a registered action."""

    success: bool
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False
    confirmation_message: str = ""


ActionHandler = Callable[..., Awaitable[ActionResult]]


@dataclass
class RegisteredAction:
    """A safe, registered action that NOVA can execute."""

    name: str
    description: str
    permission_level: PermissionLevel
    handler: ActionHandler
    parameters: list[str] = field(default_factory=list)


class CommandRegistry:
    """Registry of approved actions - AI cannot execute arbitrary commands."""

    def __init__(self) -> None:
        self._actions: dict[str, RegisteredAction] = {}

    def register(
        self,
        name: str,
        description: str,
        permission_level: PermissionLevel,
        handler: ActionHandler,
        parameters: list[str] | None = None,
    ) -> None:
        """Register an approved action."""
        self._actions[name] = RegisteredAction(
            name=name,
            description=description,
            permission_level=permission_level,
            handler=handler,
            parameters=parameters or [],
        )

    def get(self, name: str) -> RegisteredAction | None:
        return self._actions.get(name)

    def list_actions(self) -> list[RegisteredAction]:
        return list(self._actions.values())

    def get_action_descriptions(self) -> list[dict[str, str]]:
        """Return action metadata for AI intent parsing."""
        return [
            {
                "name": a.name,
                "description": a.description,
                "parameters": ", ".join(a.parameters),
                "permission": a.permission_level.value,
            }
            for a in self._actions.values()
        ]

    async def execute(self, name: str, parameters: dict[str, Any] | None = None) -> ActionResult:
        """Execute a registered action by name."""
        action = self.get(name)
        if not action:
            return ActionResult(success=False, message=f"Unknown action: {name}")

        params = parameters or {}
        try:
            return await action.handler(**params)
        except TypeError as exc:
            return ActionResult(success=False, message=f"Invalid parameters for {name}: {exc}")
        except Exception as exc:
            return ActionResult(success=False, message=f"Action failed: {exc}")
