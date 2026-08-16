"""Central Tool Registry and safe execution pipeline."""
import asyncio
import inspect
import time
from typing import Any
import structlog
from pydantic import ValidationError as PydanticValidationError

from nova_app.core.exceptions import (
    NovaError,
    PermissionDeniedError,
    ToolExecutionError,
    ValidationError,
)
from nova_app.permissions.engine import get_permission_engine
from nova_app.permissions.policy import PolicyDecision, RiskTier
from nova_app.security.audit_log import get_audit_logger
from nova_app.tools.executors import (
    GetFileInfoArgs,
    GetSystemStatsArgs,
    ListApplicationsArgs,
    OpenApplicationArgs,
    OpenFileArgs,
    OpenFolderArgs,
    PauseMusicArgs,
    PlayMusicArgs,
    SearchFilesArgs,
    SetVolumeArgs,
    StartTimerArgs,
    TakeScreenshotArgs,
    get_file_info_executor,
    get_system_stats_executor,
    list_applications_executor,
    open_application_executor,
    open_file_executor,
    open_folder_executor,
    pause_music_executor,
    play_music_executor,
    search_files_executor,
    set_volume_executor,
    start_timer_executor,
    take_screenshot_executor,
)
from nova_app.tools.schema import ToolCall, ToolDefinition, ToolResult

logger = structlog.get_logger(__name__)


class ToolRegistry:
    """Single source of truth for all registered tools and deterministic execution."""

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def register(self, definition: ToolDefinition) -> None:
        """Register a new tool definition."""
        self._tools[definition.name] = definition

    def get(self, name: str) -> ToolDefinition | None:
        """Retrieve a tool definition by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDefinition]:
        """List all registered tools."""
        return list(self._tools.values())

    def _register_default_tools(self) -> None:
        """Register core Phase 1 tools."""
        # Files
        self.register(
            ToolDefinition(
                name="open_file",
                description="Open a file with its default application",
                risk_tier=RiskTier.LOW,
                arg_schema=OpenFileArgs,
                executor=open_file_executor,
            )
        )
        self.register(
            ToolDefinition(
                name="open_folder",
                description="Open a folder in Windows Explorer",
                risk_tier=RiskTier.LOW,
                arg_schema=OpenFolderArgs,
                executor=open_folder_executor,
            )
        )
        self.register(
            ToolDefinition(
                name="search_files",
                description="Search for files by name in allowed directories",
                risk_tier=RiskTier.READ,
                arg_schema=SearchFilesArgs,
                executor=search_files_executor,
            )
        )
        self.register(
            ToolDefinition(
                name="get_file_info",
                description="Get metadata information about a file",
                risk_tier=RiskTier.READ,
                arg_schema=GetFileInfoArgs,
                executor=get_file_info_executor,
            )
        )

        # Apps
        self.register(
            ToolDefinition(
                name="open_application",
                description="Launch an installed Windows application",
                risk_tier=RiskTier.LOW,
                arg_schema=OpenApplicationArgs,
                executor=open_application_executor,
            )
        )
        self.register(
            ToolDefinition(
                name="list_installed_applications",
                description="List common or installed Windows applications",
                risk_tier=RiskTier.READ,
                arg_schema=ListApplicationsArgs,
                executor=list_applications_executor,
            )
        )

        # System
        self.register(
            ToolDefinition(
                name="get_system_stats",
                description="Get real-time CPU, RAM, Disk, and Battery metrics",
                risk_tier=RiskTier.READ,
                arg_schema=GetSystemStatsArgs,
                executor=get_system_stats_executor,
            )
        )
        self.register(
            ToolDefinition(
                name="set_volume",
                description="Set Windows master audio volume level (0-100)",
                risk_tier=RiskTier.LOW,
                arg_schema=SetVolumeArgs,
                executor=set_volume_executor,
            )
        )
        self.register(
            ToolDefinition(
                name="take_screenshot",
                description="Capture desktop screenshot and save to disk",
                risk_tier=RiskTier.READ,
                arg_schema=TakeScreenshotArgs,
                executor=take_screenshot_executor,
            )
        )

        # Media & Timers
        self.register(
            ToolDefinition(
                name="play_music",
                description="Play music or toggle media playback",
                risk_tier=RiskTier.LOW,
                arg_schema=PlayMusicArgs,
                executor=play_music_executor,
            )
        )
        self.register(
            ToolDefinition(
                name="pause_music",
                description="Pause current media playback",
                risk_tier=RiskTier.LOW,
                arg_schema=PauseMusicArgs,
                executor=pause_music_executor,
            )
        )
        self.register(
            ToolDefinition(
                name="start_timer",
                description="Start a countdown timer with label",
                risk_tier=RiskTier.LOW,
                arg_schema=StartTimerArgs,
                executor=start_timer_executor,
            )
        )

    async def execute_tool_call(
        self,
        call: ToolCall,
        actor: str = "ai",
        confirmed_by_user: bool | None = None,
    ) -> ToolResult:
        """
        Deterministic execution pipeline:
        1. Validate tool exists
        2. Validate arguments against Pydantic schema
        3. Evaluate permissions / risk tier
        4. Execute executor safely
        5. Write append-only audit log entry
        6. Return structured ToolResult
        """
        start_time = time.perf_counter()
        tool_def = self.get(call.tool_name)

        if not tool_def:
            err_msg = f"Tool '{call.tool_name}' is not registered in NOVA registry."
            duration = (time.perf_counter() - start_time) * 1000.0
            await get_audit_logger().log_action(
                tool_name=call.tool_name,
                arguments=call.arguments,
                risk_tier="UNKNOWN",
                actor=actor,
                error_message=err_msg,
                duration_ms=duration,
            )
            return ToolResult(
                tool_name=call.tool_name,
                success=False,
                error=err_msg,
                duration_ms=duration,
            )

        # 1. Validate arguments schema
        try:
            parsed_args = tool_def.arg_schema(**call.arguments)
        except PydanticValidationError as e:
            err_msg = f"Argument validation error for '{call.tool_name}': {str(e)}"
            duration = (time.perf_counter() - start_time) * 1000.0
            await get_audit_logger().log_action(
                tool_name=call.tool_name,
                arguments=call.arguments,
                risk_tier=tool_def.risk_tier.value,
                actor=actor,
                error_message=err_msg,
                duration_ms=duration,
            )
            return ToolResult(
                tool_name=call.tool_name,
                success=False,
                error=err_msg,
                duration_ms=duration,
            )

        # 2. Evaluate Permissions
        perm_engine = get_permission_engine()
        eval_result = perm_engine.evaluate(call.tool_name, tool_def.risk_tier)

        if eval_result.decision == PolicyDecision.DENY:
            err_msg = f"Action '{call.tool_name}' was DENIED by policy: {eval_result.reason}"
            duration = (time.perf_counter() - start_time) * 1000.0
            await get_audit_logger().log_action(
                tool_name=call.tool_name,
                arguments=call.arguments,
                risk_tier=tool_def.risk_tier.value,
                actor=actor,
                confirmation_required=False,
                error_message=err_msg,
                duration_ms=duration,
            )
            return ToolResult(
                tool_name=call.tool_name,
                success=False,
                error=err_msg,
                duration_ms=duration,
            )

        if eval_result.requires_confirmation and not confirmed_by_user:
            err_msg = f"Action '{call.tool_name}' requires explicit user confirmation."
            duration = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                tool_name=call.tool_name,
                success=False,
                error=err_msg,
                duration_ms=duration,
            )

        # 3. Execute deterministic executor
        try:
            if inspect.iscoroutinefunction(tool_def.executor):
                data = await tool_def.executor(parsed_args)
            else:
                data = tool_def.executor(parsed_args)

            duration = (time.perf_counter() - start_time) * 1000.0
            await get_audit_logger().log_action(
                tool_name=call.tool_name,
                arguments=call.arguments,
                risk_tier=tool_def.risk_tier.value,
                actor=actor,
                confirmation_required=eval_result.requires_confirmation,
                confirmed_by_user=confirmed_by_user,
                result_data=data,
                duration_ms=duration,
            )
            return ToolResult(
                tool_name=call.tool_name,
                success=True,
                data=data,
                duration_ms=duration,
            )
        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000.0
            err_msg = str(e)
            await get_audit_logger().log_action(
                tool_name=call.tool_name,
                arguments=call.arguments,
                risk_tier=tool_def.risk_tier.value,
                actor=actor,
                confirmation_required=eval_result.requires_confirmation,
                confirmed_by_user=confirmed_by_user,
                error_message=err_msg,
                duration_ms=duration,
            )
            return ToolResult(
                tool_name=call.tool_name,
                success=False,
                error=err_msg,
                duration_ms=duration,
            )


_registry_instance: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """Get singleton ToolRegistry instance."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ToolRegistry()
    return _registry_instance
