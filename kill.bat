@echo off
REM This script finds and kills the running video-transcriber Flask application on Windows.

echo Searching for running video-transcriber app processes...

REM Method 1: Find Python processes running main.py or app.py
echo Checking for Python processes...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| findstr /i "main.py\|app.py"') do (
    echo Found Python process: %%i
    taskkill /pid %%i /f >nul 2>&1
    if !errorlevel! equ 0 (
        echo   ✅ Process %%i killed successfully
    ) else (
        echo   ⚠️  Failed to kill process %%i ^(may already be stopped^)
    )
)

REM Method 2: Find processes using port 5001
echo Checking for processes using port 5001...
for /f "tokens=5" %%i in ('netstat -ano ^| findstr :5001') do (
    echo Found process using port 5001: %%i
    taskkill /pid %%i /f >nul 2>&1
    if !errorlevel! equ 0 (
        echo   ✅ Process %%i killed successfully
    ) else (
        echo   ⚠️  Failed to kill process %%i ^(may already be stopped^)
    )
)

REM Wait a moment and check if port 5001 is still in use
timeout /t 2 /nobreak >nul
netstat -ano | findstr :5001 >nul 2>&1
if !errorlevel! equ 0 (
    echo ⚠️  Port 5001 is still in use. You may need to manually stop remaining processes.
) else (
    echo ✅ Port 5001 is now free
)

echo.
echo Kill script completed.
pause
