@echo off
cd /d "%~dp0"

echo ========================================
echo  AI Trading CLI Client
echo ========================================
echo.
echo Make sure backend is running first!
echo (Use start_backend.bat in another window)
echo.
echo ========================================
echo.

python cli_client.py

pause
