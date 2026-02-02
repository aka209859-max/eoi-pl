@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
REM =====================================================================
REM EOI-PL Auto-Start Setup v3 (Fixed)
REM =====================================================================

echo.
echo =====================================================================
echo  EOI-PL Auto-Start Setup v3
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

echo [INFO] Detecting Python installation...
echo.

REM Try to find real Python (not Windows Store alias)
set PYTHON_PATH=
for /f "delims=" %%i in ('where python 2^>nul') do (
    set "TEMP_PATH=%%i"
    echo Checking: !TEMP_PATH!
    
    REM Skip Windows Store version
    echo !TEMP_PATH! | findstr /C:"WindowsApps" >nul
    if !errorlevel! neq 0 (
        REM Test if Python works
        "%%i" --version >nul 2>&1
        if !errorlevel! equ 0 (
            set "PYTHON_PATH=%%i"
            echo [SUCCESS] Found: !PYTHON_PATH!
            goto :found_python
        )
    )
)

:found_python
if "%PYTHON_PATH%"=="" (
    echo [ERROR] Real Python installation not found.
    echo [ERROR] Windows Store Python detected but not usable for services.
    echo [ERROR] Please install Python from python.org
    echo.
    pause
    exit /b 1
)

echo.
echo [INFO] Using Python: %PYTHON_PATH%
echo.

REM Remove existing task
schtasks /Delete /TN "EOI-PL-API" /F >nul 2>&1

REM Get current user
set CURRENT_USER=%USERNAME%

REM Create batch file wrapper for task scheduler
echo @echo off > E:\eoi-pl\eoi_pl_start.bat
echo cd /d E:\eoi-pl >> E:\eoi-pl\eoi_pl_start.bat
echo set EOI_CONFIG=windows >> E:\eoi-pl\eoi_pl_start.bat
echo "%PYTHON_PATH%" -m uvicorn api.main:app --host 0.0.0.0 --port 8001 >> E:\eoi-pl\eoi_pl_start.bat

echo [INFO] Created: E:\eoi-pl\eoi_pl_start.bat
echo.

echo [INFO] Creating scheduled task...
echo.

REM Create scheduled task with batch file
schtasks /Create /TN "EOI-PL-API" /TR "E:\eoi-pl\eoi_pl_start.bat" /SC ONLOGON /RL HIGHEST /F /RU "%CURRENT_USER%"

if %errorlevel% equ 0 (
    echo [SUCCESS] Auto-start task created!
    echo.
) else (
    echo [ERROR] Failed to create task.
    pause
    exit /b 1
)

echo [INFO] Starting EOI-PL now...
echo.

REM Start the task
schtasks /Run /TN "EOI-PL-API"

echo.
echo [INFO] Waiting for server to start...
timeout /t 10 /nobreak >nul

REM Check if running
netstat -ano | findstr :8001 >nul
if %errorlevel% equ 0 (
    echo [SUCCESS] Server is running on port 8001!
) else (
    echo [WARNING] Server may not be running yet.
    echo [INFO] Please wait a moment and check: http://localhost:8001
)

echo.
echo =====================================================================
echo  Setup Complete!
echo =====================================================================
echo.
echo  Task Name: EOI-PL-API
echo  URL: http://localhost:8001
echo  Python: %PYTHON_PATH%
echo  Startup Script: E:\eoi-pl\eoi_pl_start.bat
echo.
echo  Auto-start: Enabled (on user login)
echo.
echo  [Management Commands]
echo  Start:  schtasks /Run /TN "EOI-PL-API"
echo  Stop:   E:\eoi-pl\stop_eoi_pl.bat
echo  Manual: E:\eoi-pl\start_manual.bat
echo  Status: schtasks /Query /TN "EOI-PL-API"
echo  Delete: schtasks /Delete /TN "EOI-PL-API" /F
echo.
echo  [Task Scheduler GUI]
echo  Win + R - taskschd.msc - EOI-PL-API
echo.
echo =====================================================================
echo.

REM Open browser
echo [INFO] Opening browser...
timeout /t 3 /nobreak >nul
start http://localhost:8001

echo.
pause
endlocal
