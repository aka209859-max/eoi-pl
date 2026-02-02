@echo off
chcp 65001 >nul
REM =====================================================================
REM EOI-PL v1.0-Prime Windows PC用 停止スクリプト
REM =====================================================================

echo.
echo =====================================================================
echo  EOI-PL v1.0-Prime を停止します...
echo =====================================================================
echo.

cd /d E:\eoi-pl

echo [INFO] API サーバーを停止中...
pm2 stop eoi-pl-api
pm2 delete eoi-pl-api

echo.
echo [SUCCESS] 停止完了！
echo.
pause
