"""Local LLM provider (Ollama / llama.cpp) via OpenAI-compatible endpoint."""
import json
import structlog
from openai import AsyncOpenAI
from nova_app.ai_engine.provider_base import AIIntentResponse, LLMProvider
from nova_app.config.settings import Settings, get_settings
from nova_app.tools.schema import ToolCall

logger = structlog.get_logger(__name__)


class LocalProvider(LLMProvider):
    """Provider for locally hosted models running via Ollama / llama.cpp server."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._client = AsyncOpenAI(
            base_url=self.settings.local_model_endpoint,
            api_key="ollama",  # dummy key required by client
        )

    def is_available(self) -> bool:
        return True

    async def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
        temperature: float = 0.2,
    ) -> AIIntentResponse:
        formatted_messages = [{"role": "system", "content": system_prompt}] + messages

        try:
            response = await self._client.chat.completions.create(
                model="mistral",
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
            logger.error("Local LLM call failed", endpoint=self.settings.local_model_endpoint, error=str(e))
            raise
