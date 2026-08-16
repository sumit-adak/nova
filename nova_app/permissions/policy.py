"""Risk tiers and permission policy definitions for NOVA."""
from enum import Enum


class RiskTier(str, Enum):
    """Declared risk tiers for all NOVA actions."""
    READ = "READ"          # Read-only operations, auto-executed (e.g. search_files, get_system_stats)
    LOW = "LOW"            # Non-destructive safe actions (e.g. open_app, open_website, play_music)
    MEDIUM = "MEDIUM"      # Low-impact writes (e.g. create_file, move_file)
    HIGH = "HIGH"          # Destructive or external actions (e.g. delete_file, send_email, git_push)
    CRITICAL = "CRITICAL"  # High-impact system commands (e.g. shutdown, restart, token change)


class PolicyDecision(str, Enum):
    """Outcome of permission evaluation."""
    ALLOW = "ALLOW"
    CONFIRM = "CONFIRM"
    DENY = "DENY"


# Default policy mapping
DEFAULT_TIER_POLICIES = {
    RiskTier.READ: PolicyDecision.ALLOW,
    RiskTier.LOW: PolicyDecision.ALLOW,
    RiskTier.MEDIUM: PolicyDecision.CONFIRM,
    RiskTier.HIGH: PolicyDecision.CONFIRM,
    RiskTier.CRITICAL: PolicyDecision.CONFIRM,
}
