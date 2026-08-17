"""External tool and application integrations package."""
from nova_app.integrations.git_integration import GitClient, get_git_client
from nova_app.integrations.vscode import VSCodeClient, get_vscode_client

__all__ = [
    "VSCodeClient",
    "get_vscode_client",
    "GitClient",
    "get_git_client",
]
