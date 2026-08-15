"""AI provider abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    """Abstract base for AI providers."""

    @abstractmethod
    async def chat(self, messages: list[dict[str, str]], system_prompt: str = "") -> str:
        """Send a chat completion request."""

    @abstractmethod
    async def parse_intent(
        self, user_input: str, available_actions: list[dict[str, str]]
    ) -> dict[str, Any]:
        """Parse user input into structured intent."""

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and reachable."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider display name."""
