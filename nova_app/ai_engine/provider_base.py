"""Abstract Base Class for LLM providers."""
from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, Field
from nova_app.tools.schema import ToolCall


class AIIntentResponse(BaseModel):
    """Parsed structured response from LLM."""
    thought: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    response: str = ""
    raw_text: str = ""


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
        temperature: float = 0.2,
    ) -> AIIntentResponse:
        """
        Generate a structured AIIntentResponse given message history and system prompt.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider credentials/endpoints are configured."""
        pass
