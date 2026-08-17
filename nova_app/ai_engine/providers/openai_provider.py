"""OpenAI API provider implementation."""
import json
import structlog
from openai import AsyncOpenAI
from nova_app.ai_engine.provider_base import AIIntentResponse, LLMProvider
from nova_app.config.settings import Settings, get_settings
from nova_app.tools.schema import ToolCall

logger = structlog.get_logger(__name__)


class OpenAIProvider(LLMProvider):
    """Provider for OpenAI models (GPT-4o, GPT-4o-mini)."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._client: AsyncOpenAI | None = None
        if self.settings.openai_api_key:
            self._client = AsyncOpenAI(api_key=self.settings.openai_api_key)

    def is_available(self) -> bool:
        return bool(self.settings.openai_api_key)

    async def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
        temperature: float = 0.2,
    ) -> AIIntentResponse:
        if not self._client:
            raise ValueError("OpenAI API Key is not configured.")

        formatted_messages = [{"role": "system", "content": system_prompt}] + messages

        try:
            response = await self._client.chat.completions.create(
                model=self.settings.openai_model,
                messages=formatted_messages,
                response_format={"type": "json_object"},
                temperature=temperature,
            )
            raw_content = response.choices[0].message.content or "{}"
            parsed = json.loads(raw_content)

            tool_calls = [
                ToolCall(
                    tool_name=tc.get("tool_name", ""),
                    arguments=tc.get("arguments", {}),
                    reasoning=tc.get("reasoning"),
                )
                for tc in parsed.get("tool_calls", [])
            ]

            return AIIntentResponse(
                thought=parsed.get("thought", ""),
                tool_calls=tool_calls,
                response=parsed.get("response", ""),
                raw_text=raw_content,
            )
        except Exception as e:
            logger.error("OpenAI API call failed", error=str(e))
            raise
