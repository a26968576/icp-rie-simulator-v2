@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"
title ICP-RIE Simulator V2 - 一鍵安裝
echo ==========================================================
echo    ICP-RIE Simulator V2  一鍵安裝  install.bat
echo    安裝過程約 3~10 分鐘，請不要關閉這個黑色視窗
echo ==========================================================
echo.

if not exist "requirements.txt" goto :not_extracted

rem ---------- [1/4] 尋找 Python 3.10 以上 ----------
echo [1/4] 尋找 Python ...
set "PY="
py -3.12 -c "import sys" >nul 2>&1 && set "PY=py -3.12" && goto :found_python
py -3.11 -c "import sys" >nul 2>&1 && set "PY=py -3.11" && goto :found_python
py -3.10 -c "import sys" >nul 2>&1 && set "PY=py -3.10" && goto :found_python
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1 && set "PY=python" && goto :found_python
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1 && set "PY=py -3" && goto :found_python
goto :no_python

:found_python
echo       找到：
%PY% --version
echo.

rem ---------- [2/4] 建立虛擬環境 .venv ----------
if exist ".venv\Scripts\python.exe" goto :venv_exists
echo [2/4] 建立虛擬環境 .venv ...
%PY% -m venv .venv
if errorlevel 1 goto :fail_venv
goto :venv_ok
:venv_exists
echo [2/4] 已有 .venv 資料夾，略過建立。
:venv_ok
set "VPY=.venv\Scripts\python.exe"
if not exist "%VPY%" goto :fail_venv
echo.

rem ---------- 公司 Proxy：若有 proxy.txt，第一行當作 proxy 位址 ----------
set "PIPOPT="
set "PROXYURL="
if exist "proxy.txt" set /p PROXYURL=<"proxy.txt"
if defined PROXYURL set "PIPOPT=--proxy %PROXYURL%"
if defined PROXYURL echo       使用 proxy.txt 內的 Proxy：%PROXYURL%

rem ---------- [3/4] 安裝必要套件 ----------
echo [3/4] 升級 pip 並安裝必要套件 PySide6 / matplotlib / numpy ...
"%VPY%" -m pip install --upgrade pip %PIPOPT%
if errorlevel 1 echo       [提醒] pip 升級失敗，繼續嘗試安裝套件 ...
"%VPY%" -m pip install -r requirements.txt %PIPOPT%
if errorlevel 1 goto :fail_pip
"%VPY%" -c "import PySide6, matplotlib, numpy" >nul 2>&1
if errorlevel 1 goto :fail_pip
echo.

rem ---------- [4/4] 選用：ViennaPS（失敗不影響使用）----------
echo [4/4] 嘗試安裝選用的 ViennaPS 物理引擎（失敗也沒關係）...
"%VPY%" -m pip install --only-binary=:all: viennaps %PIPOPT%
if errorlevel 1 goto :vps_fail
echo       ViennaPS 安裝成功。
goto :success
:vps_fail
echo       [提醒] ViennaPS 沒有裝成功 —— 不影響使用，
echo              程式會自動改用 DEMO 示範模型（畫面上方會顯示紅色 DEMO 標示）。

:success
echo.
echo ==========================================================
echo    安裝成功！
echo    下一步：關閉這個視窗，然後雙擊  run.bat  開啟程式。
echo ==========================================================
echo.
pause
exit /b 0

:not_extracted
echo [錯誤] 找不到 requirements.txt。
echo        您可能是在 ZIP 壓縮檔「裡面」直接雙擊。請先：
echo        在 ZIP 檔上按右鍵 → 全部解壓縮，再到解壓後的資料夾雙擊 install.bat。
goto :fail_end

:no_python
echo [錯誤] 找不到 Python 3.10 以上版本。請先安裝 Python：
echo   1. 打開瀏覽器，前往  https://www.python.org/downloads/windows/
echo   2. 下載 Python 3.12 的「Windows installer (64-bit)」
echo   3. 執行安裝程式，第一個畫面「務必勾選」 Add python.exe to PATH
echo   4. 按 Install Now，等它完成
echo   5. 安裝完成後，重新雙擊本檔案 install.bat
echo   ※ 若公司電腦需要管理員權限才能安裝，請洽 IT 協助。
goto :fail_end

:fail_venv
echo [錯誤] 建立虛擬環境 .venv 失敗。
echo        請確認資料夾不是唯讀（例如不要放在網路磁碟），可改放到  C:\icp_rie_sim_v2  再試一次。
goto :fail_end

:fail_pip
echo.
echo [錯誤] 必要套件安裝失敗。最常見原因是公司網路 Proxy / 防火牆擋住下載。
echo   解法：在本資料夾新增一個文字檔  proxy.txt ，
echo         第一行寫入公司 Proxy 位址，例如  http://proxy.company.com:8080
echo         存檔後再雙擊 install.bat 一次。Proxy 位址請洽 IT。
echo   若仍失敗，請把這個視窗的紅字錯誤截圖寄給協助您的人。
goto :fail_end

:fail_end
echo.
echo ==========================================================
echo    安裝失敗（請看上面的說明）
echo ==========================================================
echo.
pause
exit /b 1
