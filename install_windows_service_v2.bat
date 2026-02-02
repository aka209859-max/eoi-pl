@echo off
chcp 65001 >nul
REM =====================================================================
REM EOI-PL v1.0-Prime Windows Service Installer
REM =====================================================================

echo.
echo =====================================================================
echo  EOI-PL v1.0-Prime Windows Service Install
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

cd /d E:\eoi-pl

REM Download NSSM if not exists
if not exist nssm.exe (
    echo [INFO] Downloading NSSM...
    echo.
    
    powershell -Command "try { Invoke-WebRequest -Uri 'https://github.com/kirillkovalenko/nssm/releases/download/2.24-101-g897c7ad/nssm-2.24-101-g897c7ad.zip' -OutFile 'nssm.zip' -UseBasicParsing -TimeoutSec 30 } catch { exit 1 }"
    
    if not exist nssm.zip (
        echo [ERROR] NSSM download failed.
        echo [INFO] Please download manually from: https://nssm.cc/download
        echo [INFO] Extract nssm.exe to E:\eoi-pl\ and run this script again.
        echo.
        pause
        exit /b 1
    )
    
    echo [INFO] Extracting NSSM...
    powershell -Command "Expand-Archive -Path 'nssm.zip' -DestinationPath '.' -Force"
    copy /Y nssm-2.24-101-g897c7ad\win64\nssm.exe nssm.exe >nul
    del /F /Q nssm.zip >nul 2>&1
    rmdir /S /Q nssm-2.24-101-g897c7ad >nul 2>&1
    
    echo [SUCCESS] NSSM download complete.
    echo.
)

REM Get Python path
for /f "delims=" %%i in ('where python') do set PYTHON_PATH=%%i
echo [INFO] Python path: %PYTHON_PATH%
echo.

REM Check Python version
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python not found.
    pause
    exit /b 1
)

echo.
echo [INFO] Installing Windows service...
echo.

REM Remove existing service (if exists)
nssm remove EOI-PL-API confirm >nul 2>&1

REM Install service
nssm install EOI-PL-API "%PYTHON_PATH%" "-m" "uvicorn" "api.main:app" "--host" "0.0.0.0" "--port" "8001"

REM Set service configuration
nssm set EOI-PL-API AppDirectory "E:\eoi-pl"
nssm set EOI-PL-API Description "EOI-PL v1.0-Prime Horse Racing AI Prediction System"
nssm set EOI-PL-API DisplayName "EOI-PL API Server"
nssm set EOI-PL-API AppEnvironmentExtra EOI_CONFIG=windows
nssm set EOI-PL-API Start SERVICE_AUTO_START

REM Create logs directory
if not exist "E:\eoi-pl\logs" mkdir "E:\eoi-pl\logs"

REM Set log files
nssm set EOI-PL-API AppStdout "E:\eoi-pl\logs\service-stdout.log"
nssm set EOI-PL-API AppStderr "E:\eoi-pl\logs\service-stderr.log"

echo.
echo [SUCCESS] Service registration complete!
echo.
echo [INFO] Starting service...
nssm start EOI-PL-API

echo.
timeout /t 5 /nobreak >nul

echo [INFO] Checking service status...
nssm status EOI-PL-API

echo.
echo =====================================================================
echo  Installation Complete!
echo =====================================================================
echo.
echo  Service Name: EOI-PL-API
echo  URL: http://localhost:8001
echo.
echo  Auto-start on PC boot: Enabled
echo.
echo  [Service Management Commands]
echo  Start:   nssm start EOI-PL-API
echo  Stop:    nssm stop EOI-PL-API
echo  Restart: nssm restart EOI-PL-API
echo  Remove:  nssm remove EOI-PL-API confirm
echo  Status:  nssm status EOI-PL-API
echo.
echo  [Windows Service Manager]
echo  Win + R - services.msc - EOI-PL API Server
echo.
echo =====================================================================
echo.

REM Open browser
echo [INFO] Opening browser...
timeout /t 2 /nobreak >nul
start http://localhost:8001

echo.
pause
