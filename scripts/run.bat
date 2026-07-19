@echo off
echo ===================================================
echo   Human Skill Digital Twin - Platform Starter
echo ===================================================

if not exist venv (
    echo [ERROR] Virtual environment not found. Please run scripts\setup.bat first.
    exit /b 1
)

echo Starting FastAPI Backend Server in a new window...
start "Digital Twin Backend (Port 8000)" cmd /k "call venv\Scripts\activate.bat && python -m backend.run"

echo Starting Vite Frontend Server in a new window...
start "Digital Twin Frontend (Port 5173)" cmd /k "cd frontend && npm run dev"

echo ===================================================
echo   Platform processes triggered!
echo   Backend running at http://localhost:8000
echo   Frontend running at http://localhost:5173
echo ===================================================
