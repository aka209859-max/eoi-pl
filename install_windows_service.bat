@echo off
chcp 65001 >nul
REM =====================================================================
REM EOI-PL v1.0-Prime Windowsサービスインストールスクリプト
REM =====================================================================
REM 
REM このスクリプトは EOI-PL をWindowsサービスとして登録します。
REM PC起動時に自動的に起動し、常に動作し続けます。
REM
REM 作成日: 2026-02-02
REM =====================================================================

echo.
echo =====================================================================
echo  EOI-PL v1.0-Prime Windowsサービス インストール
echo =====================================================================
echo.

REM 管理者権限チェック
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] このスクリプトは管理者権限で実行する必要があります。
    echo [ERROR] 右クリック → 「管理者として実行」を選択してください。
    echo.
    pause
    exit /b 1
)

cd /d E:\eoi-pl

echo [INFO] NSSM（Non-Sucking Service Manager）をダウンロード中...
echo [INFO] NSSMは任意のプログラムをWindowsサービス化するツールです。
echo.

REM NSSMダウンロード（GitHub Releaseから）
powershell -Command "& { if (!(Test-Path 'nssm.exe')) { try { Invoke-WebRequest -Uri 'https://github.com/kirillkovalenko/nssm/releases/download/2.24-101-g897c7ad/nssm-2.24-101-g897c7ad.zip' -OutFile 'nssm.zip' -UseBasicParsing; Expand-Archive -Path 'nssm.zip' -DestinationPath '.' -Force; Copy-Item 'nssm-2.24-101-g897c7ad\win64\nssm.exe' -Destination '.' -Force; Remove-Item 'nssm.zip' -Force; Remove-Item 'nssm-2.24-101-g897c7ad' -Recurse -Force } catch { Write-Host 'GitHub download failed, trying alternative...' -ForegroundColor Yellow; Invoke-WebRequest -Uri 'https://k-net.cf/nssm/nssm-2.24-101-g897c7ad.zip' -OutFile 'nssm.zip' -UseBasicParsing; Expand-Archive -Path 'nssm.zip' -DestinationPath '.' -Force; Copy-Item 'nssm-2.24-101-g897c7ad\win64\nssm.exe' -Destination '.' -Force; Remove-Item 'nssm.zip' -Force; Remove-Item 'nssm-2.24-101-g897c7ad' -Recurse -Force } } }"

if not exist nssm.exe (
    echo [ERROR] NSSMのダウンロードに失敗しました。
    echo [ERROR] 手動でダウンロードしてください: https://nssm.cc/download
    echo.
    pause
    exit /b 1
)

echo [SUCCESS] NSSMのダウンロード完了
echo.

REM Python実行パスを取得
for /f "delims=" %%i in ('where python') do set PYTHON_PATH=%%i
echo [INFO] Python パス: %PYTHON_PATH%
echo.

REM Pythonバージョン確認
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python が見つかりません。
    pause
    exit /b 1
)

echo.
echo [INFO] Windowsサービスを登録中...
echo.

REM 既存サービスを削除（存在する場合）
nssm remove EOI-PL-API confirm >nul 2>&1

REM サービスをインストール
nssm install EOI-PL-API "%PYTHON_PATH%" "-m" "uvicorn" "api.main:app" "--host" "0.0.0.0" "--port" "8001"

REM サービスの作業ディレクトリを設定
nssm set EOI-PL-API AppDirectory "E:\eoi-pl"

REM サービスの説明を設定
nssm set EOI-PL-API Description "EOI-PL v1.0-Prime 地方競馬AI予想システム"

REM サービスの表示名を設定
nssm set EOI-PL-API DisplayName "EOI-PL API Server"

REM 環境変数を設定
nssm set EOI-PL-API AppEnvironmentExtra EOI_CONFIG=windows

REM サービスの起動タイプを自動に設定
nssm set EOI-PL-API Start SERVICE_AUTO_START

REM ログファイルの設定
nssm set EOI-PL-API AppStdout "E:\eoi-pl\logs\service-stdout.log"
nssm set EOI-PL-API AppStderr "E:\eoi-pl\logs\service-stderr.log"

REM ログディレクトリを作成
if not exist "E:\eoi-pl\logs" mkdir "E:\eoi-pl\logs"

echo.
echo [SUCCESS] サービスの登録完了！
echo.
echo [INFO] サービスを起動中...
nssm start EOI-PL-API

echo.
timeout /t 5 /nobreak >nul

echo [INFO] サービスの状態を確認中...
nssm status EOI-PL-API

echo.
echo =====================================================================
echo  インストール完了！
echo =====================================================================
echo.
echo  サービス名: EOI-PL-API
echo  URL: http://localhost:8001
echo.
echo  PC起動時に自動的に起動します。
echo.
echo  【サービス管理コマンド】
echo  起動: nssm start EOI-PL-API
echo  停止: nssm stop EOI-PL-API
echo  再起動: nssm restart EOI-PL-API
echo  削除: nssm remove EOI-PL-API confirm
echo  状態確認: nssm status EOI-PL-API
echo.
echo  【Windowsサービス管理画面】
echo  Win + R → services.msc → EOI-PL API Server
echo.
echo =====================================================================
echo.

REM ブラウザを開く
echo [INFO] ブラウザを開きます...
timeout /t 2 /nobreak >nul
start http://localhost:8001

echo.
pause
