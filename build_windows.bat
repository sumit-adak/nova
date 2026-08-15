@echo off
REM Build NOVA Windows executable
echo ========================================
echo  NOVA - Windows Build Script
echo ========================================

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Installing dependencies...
".venv\Scripts\pip.exe" install -r requirements.txt
".venv\Scripts\pip.exe" install pyinstaller

echo Building NOVA.exe...
".venv\Scripts\pyinstaller.exe" nova.spec --clean --noconfirm

if exist "dist\NOVA.exe" (
    echo.
    echo SUCCESS: dist\NOVA.exe created!
    echo.
) else (
    echo.
    echo ERROR: Build failed. Check output above.
    exit /b 1
)

pause
