@echo off
REM ============================================================
REM  CAI DAT 1 LAN tren Windows (nhay doi vao file nay de chay).
REM  Tao moi truong Python rieng tai C:\ebm-venv va cai thu vien.
REM ============================================================
chcp 65001 >nul
cd /d "%~dp0.."
echo === Dang tao moi truong Python tai C:\ebm-venv ...
python -m venv C:\ebm-venv
if errorlevel 1 (
  echo [LOI] Chua cai Python. Hay cai Python tu https://www.python.org/downloads/
  echo        Nho TICH "Add Python to PATH" khi cai, roi chay lai file nay.
  pause
  exit /b 1
)
echo === Dang cai thu vien (vai phut) ...
C:\ebm-venv\Scripts\python.exe -m pip install --upgrade pip
C:\ebm-venv\Scripts\pip install -r requirements.txt
echo.
echo === Thu chay nhanh (khong goi mang) ...
C:\ebm-venv\Scripts\python.exe run.py alert
echo.
echo ====== CAI DAT XONG ======
echo Tiep theo: dung Task Scheduler cho chay file run_ebm_windows.bat luc 18:05 hang ngay.
pause
