"""NOVA CLI package."""
from nova_app.cli.doctor import main as doctor_main, run_diagnostics

__all__ = ["doctor_main", "run_diagnostics"]
