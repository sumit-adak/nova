# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Collect all data & binaries for PySide6, alembic, speech_recognition
datas = [
    ('../nova_app/db/migrations', 'nova_app/db/migrations'),
    ('../alembic.ini', '.'),
]
binaries = []
hiddenimports = [
    'aiosqlite',
    'sqlalchemy.dialects.sqlite',
    'sqlalchemy.dialects.sqlite.aiosqlite',
    'pyttsx3.drivers',
    'pyttsx3.drivers.sapi5',
    'speech_recognition',
    'psutil',
    'git',
]

pyside6_datas, pyside6_binaries, pyside6_hidden = collect_all('PySide6')
datas += pyside6_datas
binaries += pyside6_binaries
hiddenimports += pyside6_hidden

a = Analysis(
    ['../nova_app/main.py'],
    pathex=['..'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NOVA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NOVA',
)
