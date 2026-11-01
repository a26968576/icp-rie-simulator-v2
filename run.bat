@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"
title ICP-RIE Simulator V2
if not exist ".venv\Scripts\python.exe" goto :no_venv
call ".venv\Scripts\activate.bat"
echo 正在啟動 ICP-RIE Simulator V2 ...（第一次開啟約需 10~30 秒）
echo 使用期間請不要關閉這個黑色視窗；關閉程式視窗後它會自動結束。
python run_app.py
if errorlevel 1 goto :crashed
exit /b 0

:crashed
echo.
echo [錯誤] 程式異常結束。請把上面的錯誤訊息截圖寄給協助您的人。
echo        也可以先重新雙擊 install.bat 修復安裝，再試一次。
pause
exit /b 1

:no_venv
echo [尚未安裝] 找不到 .venv 資料夾。
echo   請先雙擊同一個資料夾裡的  install.bat  完成安裝，再雙擊 run.bat。
pause
exit /b 1
