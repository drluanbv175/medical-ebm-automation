@echo off
REM ============================================================
REM  CHAY HANG NGAY tren Windows (Task Scheduler goi file nay).
REM  Quet nguon that -> phat hien cai moi -> tu gui email.
REM  %~dp0 = thu muc chua file nay, nen khong phu thuoc duong dan OneDrive.
REM ============================================================
chcp 65001 >nul
cd /d "%~dp0.."
echo ===== %date% %time% : BAT DAU cap nhat >> "data\archive\windows_daily.log"
C:\ebm-venv\Scripts\python.exe run.py live-update >> "data\archive\windows_daily.log" 2>&1
echo ===== %date% %time% : KET THUC (ma thoat %errorlevel%) >> "data\archive\windows_daily.log"
