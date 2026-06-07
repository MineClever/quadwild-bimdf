@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if not errorlevel 1 (
    python scripts\quadwild_ui.py
    exit /b %errorlevel%
)

where py >nul 2>nul
if not errorlevel 1 (
    py -3 scripts\quadwild_ui.py
    exit /b %errorlevel%
)

echo [ERROR] Python was not found in PATH.
exit /b 1
