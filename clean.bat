@echo off
REM Video Transcriber Environment Cleanup Launcher
REM Windows batch wrapper to run the maintenance cleanup from project root

echo 🧹 Video Transcriber Environment Cleanup
echo ========================================

REM Change to project root directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    python3 --version >nul 2>&1
    if errorlevel 1 (
        echo ❌ Error: Python is required but not found
        echo Please install Python 3.8 or higher
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=python3
    )
) else (
    set PYTHON_CMD=python
)

REM Run the Python cleanup script from the maintenance directory
echo 🔄 Launching cleanup script...
cd scripts\maintenance
%PYTHON_CMD% clean_environment.py

REM Return to project root
cd /d "%~dp0"

echo.
echo 🎯 Cleanup process completed!
echo 📁 You are now back in the project root directory
pause
