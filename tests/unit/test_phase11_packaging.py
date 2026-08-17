"""Unit tests for Phase 11: Packaging & Distribution."""
from pathlib import Path
import pytest
from nova_app.cli.doctor import DiagnosticResult, run_diagnostics


@pytest.mark.asyncio
async def test_doctor_diagnostics():
    results = await run_diagnostics()
    assert len(results) >= 6

    names = [r.name for r in results]
    assert "Python Version" in names
    assert "Operating System" in names
    assert "SQLite Database" in names
    assert "Secret Redaction Engine" in names

    # Redaction engine test check should pass
    redact_res = [r for r in results if r.name == "Secret Redaction Engine"][0]
    assert redact_res.passed is True


def test_packaging_spec_files_exist():
    root = Path(__file__).resolve().parent.parent.parent
    spec_file = root / "packaging" / "nova.spec"
    iss_file = root / "packaging" / "inno_setup.iss"
    build_file = root / "packaging" / "build.py"

    assert spec_file.exists()
    assert iss_file.exists()
    assert build_file.exists()

    spec_content = spec_file.read_text()
    assert "Analysis" in spec_content
    assert "PySide6" in spec_content
    assert "nova_app" in spec_content

    iss_content = iss_file.read_text()
    assert "MyAppName" in iss_content
    assert "NOVA-Setup" in iss_content
