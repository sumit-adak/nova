"""Automated distribution build script for NOVA."""
import os
import subprocess
import sys
from pathlib import Path


def build_package() -> int:
    """Build PyInstaller standalone application."""
    root_dir = Path(__file__).resolve().parent.parent
    spec_path = root_dir / "packaging" / "nova.spec"

    print("=" * 60)
    print("  Building Standalone Binary with PyInstaller")
    print(f"  Spec: {spec_path}")
    print("=" * 60)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_path),
    ]

    try:
        res = subprocess.run(cmd, cwd=str(root_dir))
        return res.returncode
    except Exception as e:
        print(f"Build failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(build_package())
