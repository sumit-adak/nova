"""Conventional commit message generator."""

def format_commit_message(change_type: str, scope: str | None, summary: str, details: list[str] | None = None) -> str:
    """Format a clean conventional commit message."""
    scope_str = f"({scope.strip()})" if scope and scope.strip() else ""
    header = f"{change_type.strip().lower()}{scope_str}: {summary.strip()}"

    if details and len(details) > 0:
        bullet_points = "\n".join([f"- {d.strip()}" for d in details if d.strip()])
        return f"{header}\n\n{bullet_points}"

    return header
