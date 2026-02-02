@echo off
chcp 65001 >nul
REM =====================================================================
REM EOI-PL Stop Script
REM =====================================================================

echo.
echo [INFO] Stopping EOI-PL API Server...
echo.

REM Kill all Python processes running uvicorn
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq *uvicorn*" >nul 2>&1

REM Kill by port
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do taskkill /F /PID %%a >nul 2>&1

echo [SUCCESS] EOI-PL stopped.
echo.
pause
