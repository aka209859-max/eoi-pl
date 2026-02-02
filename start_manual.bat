@echo off
chcp 65001 >nul
REM =====================================================================
REM EOI-PL Manual Start Script (Simple)
REM =====================================================================

echo.
echo =====================================================================
echo  EOI-PL v1.0-Prime Starting...
echo =====================================================================
echo.

cd /d E:\eoi-pl

echo [INFO] Starting API Server...
echo [INFO] URL: http://localhost:8001
echo.
echo [INFO] Press Ctrl+C to stop.
echo.

REM Start API server directly (blocking)
python -m uvicorn api.main:app --host 0.0.0.0 --port 8001
