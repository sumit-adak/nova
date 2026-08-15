@echo off
title NOVA - AI Desktop Assistant
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Setting up...
    python -m venv .venv
    ".venv\Scripts\pip.exe" install -r requirements.txt
)
echo Starting NOVA Desktop Assistant...
".venv\Scripts\python.exe" -m app.main
pause
