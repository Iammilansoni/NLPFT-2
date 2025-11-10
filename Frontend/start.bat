@echo off
echo ========================================
echo Starting NLPForge Frontend
echo ========================================
echo.

if not exist node_modules (
    echo ERROR: Dependencies not installed!
    echo Please run setup.bat first
    pause
    exit /b 1
)

if not exist .env (
    echo WARNING: .env file not found!
    echo Creating from .env.example...
    copy .env.example .env
)

echo Starting development server...
echo Open http://localhost:3000 in your browser
echo.
echo Press Ctrl+C to stop the server
echo.

npm run dev
