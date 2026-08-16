"""Security and safety unit tests for Phase 1."""
import os
from pathlib import Path
import pytest
from nova_app.config.settings import Settings
from nova_app.core.exceptions import EmergencyStopActiveError, SecurityError
from nova_app.permissions.engine import PermissionEngine
from nova_app.permissions.policy import PolicyDecision, RiskTier
from nova_app.security.audit_log import AuditLogger
from nova_app.security.emergency_stop import EmergencyStop
from nova_app.security.sandbox import sanitize_and_validate_binary
from nova_app.tools.validators.path_validator import PathValidator


def test_path_validator_traversal_prevention(tmp_path):
    user_root = tmp_path / "allowed_user_root"
    user_root.mkdir()
    secret_file = user_root / "test.txt"
    secret_file.write_text("hello")

    settings = Settings(
        allowed_roots=[str(user_root)],
        blocked_paths=["C:\\Windows", "C:\\Program Files"]
    )
    validator = PathValidator(settings=settings)

    # Valid path inside allowed root
    valid = validator.validate_path(str(secret_file))
    assert valid == secret_file.resolve()

    # Outside allowed root
    with pytest.raises(SecurityError, match="outside allowed user roots"):
        validator.validate_path("C:\\nonexistent_or_unallowed_path\\secret.txt", allow_create=True)

    # Path with traversal attempting to leave allowed root
    traversal_attempt = str(user_root / ".." / "outside.txt")
    with pytest.raises(SecurityError, match="outside allowed user roots"):
        validator.validate_path(traversal_attempt, allow_create=True)


def test_path_validator_blocked_system_paths():
    settings = Settings(
        allowed_roots=["C:\\"],
        blocked_paths=["C:\\Windows", "C:\\Program Files"]
    )
    validator = PathValidator(settings=settings)

    with pytest.raises(SecurityError, match="protected system path"):
        validator.validate_path("C:\\Windows\\System32\\cmd.exe", allow_create=True)

    with pytest.raises(SecurityError, match="protected system path"):
        validator.validate_path("C:\\Program Files\\app.exe", allow_create=True)


def test_sandbox_binary_allowlist():
    assert sanitize_and_validate_binary("code") == "code"
    assert sanitize_and_validate_binary("notepad.exe") == "notepad.exe"
    assert sanitize_and_validate_binary("explorer.exe") == "explorer.exe"

    with pytest.raises(SecurityError, match="not in the safe allowlist"):
        sanitize_and_validate_binary("malicious_hacker_tool.exe")

    with pytest.raises(SecurityError, match="not in the safe allowlist"):
        sanitize_and_validate_binary("powershell.exe -ExecutionPolicy Bypass")


def test_emergency_stop():
    stop = EmergencyStop()
    assert not stop.is_active

    stop.trigger("User clicked Emergency Stop")
    assert stop.is_active
    assert "User clicked" in stop.reason

    stop.reset()
    assert not stop.is_active


@pytest.mark.asyncio
async def test_audit_log_recording(tmp_path):
    logger = AuditLogger()
    entry = await logger.log_action(
        tool_name="get_system_stats",
        arguments={"include_disks": True},
        risk_tier="READ",
        actor="user",
        result_data={"cpu": 15.2},
        duration_ms=12.5,
    )

    assert entry.id is not None
    assert entry.tool_name == "get_system_stats"
    assert entry.risk_tier == "READ"
    assert "include_disks" in entry.arguments_json
    assert entry.duration_ms == 12.5
