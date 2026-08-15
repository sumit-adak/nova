# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for NOVA."""

import sys
from pathlib import Path

block_cipher = None
root = Path(SPECPATH)

a = Analysis(
    ['app/main.py'],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / 'assets'), 'assets'),
        (str(root / 'data'), 'data'),
        (str(root / '.env.example'), '.'),
    ],
    hiddenimports=[
        'app', 'app.core', 'app.ai', 'app.commands', 'app.voice',
        'app.system_monitor', 'app.memory', 'app.ui', 'app.services',
        'app.ui.widgets.common', 'PySide6', 'psutil', 'speech_recognition',
        'pyttsx3', 'pydantic_settings', 'dotenv',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NOVA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
