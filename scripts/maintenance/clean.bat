@echo off
REM Video Transcriber Environment Cleanup Script
REM Windows batch wrapper for the Python cleanup script

echo 🧹 Video Transcriber Environment Cleanup
echo ========================================

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

REM Run the Python cleanup script
%PYTHON_CMD% clean_environment.py

echo.
echo ✅ Cleanup script completed
pause
