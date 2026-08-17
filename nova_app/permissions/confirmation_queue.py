"""Asynchronous confirmation queue for user approvals."""
import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import structlog
from nova_app.core.events import Event, get_event_bus
from nova_app.permissions.models import ConfirmationRequest
from nova_app.permissions.policy import RiskTier

logger = structlog.get_logger(__name__)


@dataclass
class ConfirmationRequestedEvent(Event):
    request_id: str = ""
    tool_name: str = ""
    arguments: dict = None
    risk_tier: str = "MEDIUM"
    reasoning: str | None = None
    timeout_sec: float = 60.0


@dataclass
class ConfirmationResolvedEvent(Event):
    request_id: str = ""
    approved: bool = False
    remember_choice: bool = False


class ConfirmationQueue:
    """Manages pending confirmation requests awaiting user resolution from UI or external prompt."""

    def __init__(self):
        self._pending_requests: dict[str, ConfirmationRequest] = {}
        self._futures: dict[str, asyncio.Future[tuple[bool, bool]]] = {}

    async def request_confirmation(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        risk_tier: RiskTier,
        reasoning: str | None = None,
        timeout_sec: float = 60.0,
    ) -> tuple[bool, bool]:
        """
        Request user confirmation asynchronously.
        Returns tuple: (approved: bool, remember_choice: bool)
        Defaults to (False, False) upon timeout.
        """
        req_id = str(uuid.uuid4())
        req = ConfirmationRequest(
            id=req_id,
            tool_name=tool_name,
            arguments=arguments,
            risk_tier=risk_tier,
            reasoning=reasoning,
            timeout_sec=timeout_sec,
        )

        loop = asyncio.get_running_loop()
        future: asyncio.Future[tuple[bool, bool]] = loop.create_future()

        self._pending_requests[req_id] = req
        self._futures[req_id] = future

        # Emit event to notify UI
        get_event_bus().publish_sync(
            ConfirmationRequestedEvent(
                request_id=req_id,
                tool_name=tool_name,
                arguments=arguments,
                risk_tier=risk_tier.value,
                reasoning=reasoning,
                timeout_sec=timeout_sec,
            )
        )

        logger.info(
            "Confirmation requested for tool call",
            request_id=req_id,
            tool=tool_name,
            risk=risk_tier.value,
            timeout=timeout_sec,
        )

        try:
            approved, remember = await asyncio.wait_for(future, timeout=timeout_sec)
            return approved, remember
        except asyncio.TimeoutError:
            logger.warning(
                "Confirmation timed out, defaulting to DENY",
                request_id=req_id,
                tool=tool_name
            )
            return False, False
        finally:
            self._pending_requests.pop(req_id, None)
            self._futures.pop(req_id, None)

    def resolve_confirmation(self, request_id: str, approved: bool, remember_choice: bool = False) -> bool:
        """Resolve a pending confirmation future."""
        future = self._futures.get(request_id)
        if future and not future.done():
            future.set_result((approved, remember_choice))
            get_event_bus().publish_sync(
                ConfirmationResolvedEvent(
                    request_id=request_id,
                    approved=approved,
                    remember_choice=remember_choice,
                )
            )
            logger.info("Confirmation resolved", request_id=request_id, approved=approved, remember=remember_choice)
            return True
        return False

    def list_pending(self) -> list[ConfirmationRequest]:
        """List current pending confirmation requests."""
        return list(self._pending_requests.values())


_confirmation_queue_instance: ConfirmationQueue | None = None


def get_confirmation_queue() -> ConfirmationQueue:
    """Get singleton ConfirmationQueue instance."""
    global _confirmation_queue_instance
    if _confirmation_queue_instance is None:
        _confirmation_queue_instance = ConfirmationQueue()
    return _confirmation_queue_instance
