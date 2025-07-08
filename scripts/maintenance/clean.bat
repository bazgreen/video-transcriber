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
set CLEANUP_EXIT_CODE=%ERRORLEVEL%

echo.
if %CLEANUP_EXIT_CODE% equ 0 (
    echo ✅ Cleanup script completed successfully
    echo 🎯 Environment has been reset to pristine state
    echo 🚀 Ready for fresh installation testing
) else (
    echo ❌ Cleanup script encountered issues (exit code: %CLEANUP_EXIT_CODE%^)
    echo ⚠️  Some manual cleanup may be required
)
pause
