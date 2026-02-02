@echo off
chcp 65001 >nul
REM =====================================================================
REM EOI-PL v1.0-Prime Windows PC用 Web UI起動スクリプト
REM =====================================================================
REM 
REM 使用方法:
REM   1. このファイルを E:\eoi-pl\start_api_windows.bat として保存
REM   2. ダブルクリックして実行
REM   3. http://localhost:8001 が自動的に開く
REM   4. 終了するには Ctrl+C を押す
REM
REM 作成日: 2026-02-01
REM 最終更新: 2026-02-01
REM =====================================================================

echo.
echo =====================================================================
echo  EOI-PL v1.0-Prime Web UI 起動中...
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
echo  Web UI を起動します...
echo =====================================================================
echo.
echo  URL: http://localhost:8001
echo.
echo  ブラウザで自動的に開きます。
echo  終了するには Ctrl+C を押してください。
echo.
echo =====================================================================
echo.

REM 5秒待機してからブラウザを開く（バックグラウンドで）
start /B timeout /t 5 /nobreak >nul && start http://localhost:8001

REM 環境変数を設定（Windows用設定ファイルを使用）
set EOI_CONFIG=windows

REM FastAPI サーバーを起動
echo [INFO] API サーバーを起動中...
python -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload

echo.
echo [INFO] Web UI が終了しました。
pause
