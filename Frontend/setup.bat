@echo off
echo ================================================
echo NLPForge Frontend - Quick Setup Script
echo ================================================
echo.

echo [1/5] Checking Node.js installation...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed!
    echo Please download and install Node.js from https://nodejs.org/
    pause
    exit /b 1
)
node --version
echo.

echo [2/5] Checking npm installation...
npm --version
echo.

echo [3/5] Installing dependencies (this may take 2-3 minutes)...
call npm install
if %errorlevel% neq 0 (
    echo ERROR: npm install failed!
    pause
    exit /b 1
)
echo.

echo [4/5] Setting up environment variables...
if not exist .env.local (
    copy .env.example .env.local
    echo Created .env.local from .env.example
) else (
    echo .env.local already exists, skipping...
)
echo.

echo [5/5] Initializing Git hooks (Husky)...
call npm run prepare
echo.

echo ================================================
echo Setup Complete!
echo ================================================
echo.
echo Next steps:
echo   1. Edit .env.local if needed
echo   2. Run: npm run dev
echo   3. Open: http://localhost:3000
echo.
echo Additional commands:
echo   - npm run storybook  (Component development)
echo   - npm run test       (Run tests)
echo   - npm run build      (Production build)
echo.
pause
