@echo off
chcp 65001 >nul
REM =====================================================================
REM EOI-PL Auto-Start Setup (Task Scheduler)
REM =====================================================================

echo.
echo =====================================================================
echo  EOI-PL Auto-Start Setup
echo =====================================================================
echo.

REM Check administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] This script requires administrator privileges.
    echo [ERROR] Right-click and select "Run as administrator".
    echo.
    pause
    exit /b 1
)

echo [INFO] Creating auto-start task...
echo.

REM Remove existing task (if exists)
schtasks /Delete /TN "EOI-PL-API" /F >nul 2>&1

REM Get Python path
for /f "delims=" %%i in ('where python') do set PYTHON_PATH=%%i
echo [INFO] Python path: %PYTHON_PATH%
echo.

REM Create scheduled task
schtasks /Create /TN "EOI-PL-API" /TR "\"%PYTHON_PATH%\" -m uvicorn api.main:app --host 0.0.0.0 --port 8001" /SC ONLOGON /RL HIGHEST /F /RU "%USERNAME%" /IT

if %errorlevel% equ 0 (
    echo [SUCCESS] Auto-start task created successfully!
    echo.
    echo [INFO] Task will start automatically when you log in.
    echo.
) else (
    echo [ERROR] Failed to create task.
    pause
    exit /b 1
)

echo [INFO] Starting EOI-PL now...
echo.

REM Start the task immediately
schtasks /Run /TN "EOI-PL-API"

timeout /t 5 /nobreak >nul

echo.
echo =====================================================================
echo  Setup Complete!
echo =====================================================================
echo.
echo  Task Name: EOI-PL-API
echo  URL: http://localhost:8001
echo.
echo  Auto-start: Enabled (on user login)
echo.
echo  [Task Management Commands]
echo  Start:  schtasks /Run /TN "EOI-PL-API"
echo  Stop:   taskkill /F /IM python.exe /FI "WINDOWTITLE eq uvicorn*"
echo  Status: schtasks /Query /TN "EOI-PL-API"
echo  Delete: schtasks /Delete /TN "EOI-PL-API" /F
echo.
echo  [Task Scheduler GUI]
echo  Win + R - taskschd.msc - Task Scheduler Library - EOI-PL-API
echo.
echo =====================================================================
echo.

REM Open browser
echo [INFO] Opening browser...
timeout /t 3 /nobreak >nul
start http://localhost:8001

echo.
pause
