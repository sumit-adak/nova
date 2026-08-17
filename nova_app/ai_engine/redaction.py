"""Redaction engine for removing PII, API keys, passwords, and tokens before cloud calls."""
import re
from typing import Pattern

# Common credential & token regex patterns
SECRET_PATTERNS: list[tuple[str, Pattern[str]]] = [
    ("OpenAI Key", re.compile(r"sk-[a-zA-Z0-9]{20,T3BlbkFJ[a-zA-Z0-9]{20,}", re.IGNORECASE)),
    ("Generic sk- Key", re.compile(r"sk-[a-zA-Z0-9_\-]{20,}", re.IGNORECASE)),
    ("GitHub Token", re.compile(r"gh[pousr][_-][a-zA-Z0-9]{36,}", re.IGNORECASE)),
    ("Bearer Token", re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE)),
    ("Generic API Key", re.compile(r"(?:api_key|apikey|secret|password|token)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{12,})['\"]?", re.IGNORECASE)),
    ("AWS Access Key", re.compile(r"(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}", re.IGNORECASE)),
    ("Private Key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----.*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.DOTALL | re.IGNORECASE)),
]


class RedactionEngine:
    """Detects and redacts sensitive data from text payloads before dispatching to external LLM providers."""

    def __init__(self, custom_patterns: list[tuple[str, Pattern[str]]] | None = None):
        self.patterns = custom_patterns or SECRET_PATTERNS

    def contains_secrets(self, text: str) -> bool:
        """Check if text contains secret tokens."""
        if not text:
            return False
        for _, pattern in self.patterns:
            if pattern.search(text):
                return True
        return False

    def redact(self, text: str) -> str:
        """Redact detected secrets with [REDACTED_SECRET]."""
        if not text:
            return ""

        redacted_text = text
        for name, pattern in self.patterns:
            redacted_text = pattern.sub(f"[REDACTED_{name.upper().replace(' ', '_')}]", redacted_text)

        return redacted_text


_redaction_engine_instance: RedactionEngine | None = None


def get_redaction_engine() -> RedactionEngine:
    """Get singleton RedactionEngine instance."""
    global _redaction_engine_instance
    if _redaction_engine_instance is None:
        _redaction_engine_instance = RedactionEngine()
    return _redaction_engine_instance
