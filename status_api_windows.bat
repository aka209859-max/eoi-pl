@echo off
chcp 65001 >nul
REM =====================================================================
REM EOI-PL v1.0-Prime Windows PC用 ステータス確認スクリプト
REM =====================================================================

echo.
echo =====================================================================
echo  EOI-PL v1.0-Prime ステータス
echo =====================================================================
echo.

cd /d E:\eoi-pl

echo [INFO] PM2 ステータス:
pm2 status

echo.
echo [INFO] 最新ログ（最後の20行）:
pm2 logs eoi-pl-api --nostream --lines 20

echo.
echo =====================================================================
echo  コマンド一覧
echo =====================================================================
echo.
echo  起動: start_api_windows_background.bat
echo  停止: stop_api_windows.bat
echo  再起動: pm2 restart eoi-pl-api
echo  ログ確認: pm2 logs eoi-pl-api --nostream
echo  URL: http://localhost:8001
echo.
pause
