@echo off
REM NLPForge Development Startup Script
REM Starts both Backend (FastAPI) and Frontend (Next.js)

echo.
echo ============================================================
echo  NLPForge Development Environment Setup
echo ============================================================
echo.

REM Check if Backend is running
netstat -ano | findstr :8000 > nul
if %errorlevel%==0 (
    echo [✓] Backend already running on port 8000
) else (
    echo [!] Backend not running. Starting...
    start "NLPForge Backend" cmd /k "cd /d %~dp0Backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    timeout /t 3
    echo [✓] Backend started on port 8000
)

echo.

REM Check if Frontend is running
netstat -ano | findstr :3000 > nul
if %errorlevel%==0 (
    echo [✓] Frontend already running on port 3000
) else (
    echo [!] Frontend not running. Starting...
    start "NLPForge Frontend" cmd /k "cd /d %~dp0Frontend && npm run dev"
    timeout /t 3
    echo [✓] Frontend started on port 3000
)

echo.
echo ============================================================
echo  ✨ Development Environment Ready!
echo ============================================================
echo.
echo Frontend:  http://localhost:3000
echo Backend:   http://localhost:8000
echo API Docs:  http://localhost:8000/docs
echo.
echo To stop:
echo   - Close the "NLPForge Backend" window to stop backend
echo   - Close the "NLPForge Frontend" window to stop frontend
echo.
pause
