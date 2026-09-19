@echo off
echo ==========================================
echo Starting VoiceStock Inventory System
echo ==========================================

REM Start Backend
start "VoiceStock Backend (FastAPI)" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

REM Start Frontend
start "VoiceStock Frontend (Vite)" cmd /k "cd /d %~dp0frontend && npm run dev -- --host 0.0.0.0 --port 5173"

echo.
echo Both servers are starting up:
echo - Frontend: http://localhost:5173
echo - Backend:  http://localhost:8000/docs
echo ==========================================
