@echo off
echo ========================================
echo  Starting AI Trading Backend Server
echo ========================================
echo.

cd /d "%~dp0backend"

echo Starting FastAPI server on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
echo ========================================
echo.

python -m uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 --reload
