@echo off
chcp 65001 >nul
REM =====================================================================
REM EOI-PL v1.0-Prime Windows PC用 バックグラウンド起動スクリプト
REM =====================================================================
REM 
REM 使用方法:
REM   1. このファイルを E:\eoi-pl\start_api_windows_background.bat として保存
REM   2. ダブルクリックして実行
REM   3. ウィンドウを閉じてもバックグラウンドで動作し続けます
REM   4. 停止するには stop_api_windows.bat を実行
REM
REM 作成日: 2026-02-02
REM =====================================================================

echo.
echo =====================================================================
echo  EOI-PL v1.0-Prime バックグラウンド起動中...
echo =====================================================================
echo.

REM カレントディレクトリを E:\eoi-pl に移動
cd /d E:\eoi-pl

REM Python仮想環境の確認（存在する場合は有効化）
if exist venv\Scripts\activate.bat (
    echo [INFO] Python仮想環境を有効化...
    call venv\Scripts\activate.bat
)

REM Pythonバージョン確認
echo [INFO] Python環境チェック...
python --version
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python が見つかりません！
    echo [ERROR] Python 3.8以上をインストールしてください。
    echo.
    pause
    exit /b 1
)

echo.
echo [INFO] 必要なパッケージを確認...
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] FastAPI がインストールされていません。
    echo [INFO] 必要なパッケージをインストール中...
    pip install fastapi uvicorn psycopg2-binary numpy pandas
)

echo.
echo [INFO] PostgreSQL 接続テスト...
python api\config_windows.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] データベース接続に失敗しました。
    echo [ERROR] PostgreSQL が起動しているか確認してください。
    echo.
    pause
    exit /b 1
)

echo.
echo =====================================================================
echo  Web UI をバックグラウンドで起動します...
echo =====================================================================
echo.
echo  URL: http://localhost:8001
echo.
echo  このウィンドウを閉じても動作し続けます。
echo  停止するには stop_api_windows.bat を実行してください。
echo.
echo =====================================================================
echo.

REM 環境変数を設定（Windows用設定ファイルを使用）
set EOI_CONFIG=windows

REM PM2でAPIサーバーをバックグラウンド起動
echo [INFO] API サーバーをバックグラウンド起動中...
pm2 delete eoi-pl-api 2>nul
pm2 start ecosystem.config.cjs --name eoi-pl-api

echo.
echo [SUCCESS] バックグラウンド起動完了！
echo.
echo [INFO] ステータス確認: pm2 status
echo [INFO] ログ確認: pm2 logs eoi-pl-api --nostream
echo [INFO] 停止: pm2 stop eoi-pl-api
echo.
echo [INFO] ブラウザで http://localhost:8001 にアクセスしてください
echo.

REM ブラウザを開く
timeout /t 2 /nobreak >nul
start http://localhost:8001

echo.
echo このウィンドウは5秒後に自動的に閉じます...
timeout /t 5 /nobreak >nul
