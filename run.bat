@echo off
title NOVA — Personal AI Operating Layer
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Please create one with: python -m venv .venv
    pause
    exit /b 1
)

echo Starting NOVA Desktop Assistant...
".venv\Scripts\python.exe" -m nova_app.main
pause
