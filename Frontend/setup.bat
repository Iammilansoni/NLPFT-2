A.
@echo off
echo ========================================
echo NLPForge Frontend - Setup Script
echo ========================================
echo.

echo Checking Node.js installation...
node --version
if errorlevel 1 (
    echo ERROR: Node.js is not installed!
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)
echo.

echo Checking npm installation...
npm --version
if errorlevel 1 (
    echo ERROR: npm is not installed!
    pause
    exit /b 1
)
echo.

echo ========================================
echo Step 1: Installing Dependencies
echo ========================================
echo This may take 2-5 minutes...
echo.
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)
echo.

echo ========================================
echo Step 2: Creating Environment File
echo ========================================
if not exist .env (
    copy .env.example .env
    echo .env file created successfully!
) else (
    echo .env file already exists, skipping...
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Review .env file and update if needed
echo 2. Start backend API (if not running)
echo 3. Run: npm run dev
echo 4. Open: http://localhost:3000
echo.
echo Press any key to exit...
pause > nul
