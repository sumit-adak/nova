"""Tool Planner resolving fuzzy intents and context into validated ToolCalls."""
from pathlib import Path
from typing import Any
from sqlalchemy import select
from nova_app.db.models.computer_index import IndexedFile, InstalledApp
from nova_app.db.session import get_session_factory
from nova_app.tools.schema import ToolCall


class ToolPlanner:
    """Refines raw AI-emitted ToolCalls into executable calls with resolved context."""

    async def resolve_fuzzy_file_path(self, query: str) -> str | None:
        """Find the best matching indexed file path from SQLite."""
        session_factory = get_session_factory()
        async with session_factory() as session:
            # Query matching filename substring
            stmt = (
                select(IndexedFile)
                .where(IndexedFile.name.ilike(f"%{query}%"))
                .order_by(IndexedFile.modified_at.desc())
                .limit(1)
            )
            res = await session.execute(stmt)
            match = res.scalar_one_or_none()
            if match and Path(match.path).exists():
                return match.path
        return None

    async def resolve_fuzzy_app_name(self, app_name: str) -> str | None:
        """Find matching installed application name/path from SQLite."""
        session_factory = get_session_factory()
        async with session_factory() as session:
            stmt = (
                select(InstalledApp)
                .where(InstalledApp.name.ilike(f"%{app_name}%"))
                .limit(1)
            )
            res = await session.execute(stmt)
            match = res.scalar_one_or_none()
            if match:
                return match.exec_path if match.exec_path else match.name
        return None

    async def plan_and_refine(self, tool_calls: list[ToolCall]) -> list[ToolCall]:
        """
        Post-process and refine tool calls before passing to permission & execution engine.
        """
        refined_calls: list[ToolCall] = []

        for call in tool_calls:
            args = dict(call.arguments)

            # 1. Fuzzy file resolution for open_file / get_file_info
            if call.tool_name in ["open_file", "get_file_info"] and "path" in args:
                target_path = str(args["path"])
                # If target path does not directly exist on disk, attempt fuzzy resolution
                if not Path(target_path).exists():
                    resolved_file = await self.resolve_fuzzy_file_path(Path(target_path).stem)
                    if resolved_file:
                        args["path"] = resolved_file

            # 2. Fuzzy app resolution for open_application
            if call.tool_name == "open_application" and "app_name" in args:
                app_target = str(args["app_name"])
                resolved_app = await self.resolve_fuzzy_app_name(app_target)
                if resolved_app:
                    args["app_name"] = resolved_app

            refined_calls.append(
                ToolCall(
                    tool_name=call.tool_name,
                    arguments=args,
                    reasoning=call.reasoning,
                    requires_confirmation=call.requires_confirmation,
                )
            )

        return refined_calls


_planner_instance: ToolPlanner | None = None


def get_tool_planner() -> ToolPlanner:
    """Get singleton ToolPlanner instance."""
    global _planner_instance
    if _planner_instance is None:
        _planner_instance = ToolPlanner()
    return _planner_instance
