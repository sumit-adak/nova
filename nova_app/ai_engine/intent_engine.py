"""Central Intent Engine coordinating prompts, redaction, and provider execution."""
import json
import structlog
from nova_app.ai_engine.prompts.system_prompts import format_system_prompt
from nova_app.ai_engine.provider_base import AIIntentResponse, LLMProvider
from nova_app.ai_engine.providers import (
    AnthropicProvider,
    GeminiProvider,
    LocalProvider,
    OfflineProvider,
    OpenAIProvider,
)
from nova_app.ai_engine.redaction import get_redaction_engine
from nova_app.config.settings import Settings, get_settings
from nova_app.tools.registry import get_tool_registry

logger = structlog.get_logger(__name__)


class IntentEngine:
    """Orchestrates prompt creation, redaction, provider invocation, and intent extraction."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.redactor = get_redaction_engine()
        self._providers: dict[str, LLMProvider] = {
            "offline": OfflineProvider(),
            "openai": OpenAIProvider(self.settings),
            "gemini": GeminiProvider(self.settings),
            "anthropic": AnthropicProvider(self.settings),
            "local": LocalProvider(self.settings),
        }

    def get_active_provider(self) -> LLMProvider:
        """Resolve current provider based on settings or fallback to offline."""
        configured = self.settings.ai_provider
        provider = self._providers.get(configured)

        if provider and provider.is_available():
            return provider

        logger.warning(
            "Configured provider is unavailable or missing keys, falling back to offline",
            provider=configured
        )
        return self._providers["offline"]

    def _build_tools_description(self) -> str:
        """Format registered tools with their parameter schemas for LLM system prompt."""
        registry = get_tool_registry()
        tool_defs = registry.list_tools()
        lines = []

        for t in tool_defs:
            schema_json = json.dumps(t.arg_schema.model_json_schema().get("properties", {}), indent=2)
            lines.append(f"- Tool: {t.name}\n  Description: {t.description}\n  Risk Tier: {t.risk_tier.value}\n  Arguments Schema:\n{schema_json}\n")

        return "\n".join(lines)

    async def analyze_intent(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
    ) -> AIIntentResponse:
        """
        Analyze conversation turn:
        1. Redact secrets from messages
        2. Build formatted system prompt with registered tools
        3. Call active provider
        4. Return structured AIIntentResponse
        """
        # Redact messages before passing to provider
        sanitized_messages = [
            {"role": m["role"], "content": self.redactor.redact(m["content"])}
            for m in messages
        ]

        tools_desc = self._build_tools_description()
        system_prompt = format_system_prompt(
            tools_description=tools_desc,
            allowed_roots=self.settings.allowed_roots
        )

        provider = self.get_active_provider()

        try:
            return await provider.generate_response(
                messages=sanitized_messages,
                system_prompt=system_prompt,
                temperature=temperature
            )
        except Exception as e:
            logger.error("Primary AI provider failed, trying offline router", error=str(e))
            # Fallback to offline router
            return await self._providers["offline"].generate_response(
                messages=sanitized_messages,
                system_prompt=system_prompt,
                temperature=temperature
            )


_intent_engine_instance: IntentEngine | None = None


def get_intent_engine() -> IntentEngine:
    """Get singleton IntentEngine instance."""
    global _intent_engine_instance
    if _intent_engine_instance is None:
        _intent_engine_instance = IntentEngine()
    return _intent_engine_instance
