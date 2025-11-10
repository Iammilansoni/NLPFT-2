@echo off
REM NLPForge Backend Setup Script for Windows
REM This script automates the complete setup process

echo ============================================================
echo NLPForge Backend - Automated Setup
echo ============================================================
echo.

REM Check Python installation
echo [1/8] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)
echo OK - Python found

REM Check Docker installation
echo.
echo [2/8] Checking Docker installation...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Docker is not installed
    echo You can continue but won't be able to use docker-compose
    echo Install Docker Desktop from https://www.docker.com/
) else (
    echo OK - Docker found
)

REM Create virtual environment
echo.
echo [3/8] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    echo OK - Virtual environment created
)

REM Activate virtual environment
echo.
echo [4/8] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo OK - Virtual environment activated

REM Upgrade pip
echo.
echo [5/8] Upgrading pip...
python -m pip install --upgrade pip
echo OK - pip upgraded

REM Install dependencies
echo.
echo [6/8] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo OK - Dependencies installed

REM Download spaCy model
echo.
echo [7/8] Downloading spaCy model (en_core_web_md)...
python -m spacy download en_core_web_md
if %errorlevel% neq 0 (
    echo WARNING: Failed to download spaCy model
    echo You can download it manually later with: python -m spacy download en_core_web_md
) else (
    echo OK - spaCy model downloaded
)

REM Setup .env file
echo.
echo [8/8] Setting up .env file...
if exist .env (
    echo .env file already exists, skipping...
) else (
    copy .env.example .env
    echo OK - .env file created from .env.example
    echo.
    echo IMPORTANT: Please edit .env file and add:
    echo   - Your Gemini API key (GEMINI_API_KEY)
    echo   - Redis password if needed (REDIS_PASSWORD)
    echo.
)

echo.
echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
echo Next steps:
echo   1. Edit .env file and add your API keys
echo   2. Start PostgreSQL: docker run -d -p 5432:5432 -e POSTGRES_USER=nlpforge -e POSTGRES_PASSWORD=nlpforge_password -e POSTGRES_DB=nlpforge postgres:15-alpine
echo   3. Start Redis: docker run -d -p 6379:6379 redis/redis-stack
echo   4. Or use docker-compose: docker-compose up -d
echo   5. Initialize database: python init_database.py
echo   6. Run the API: python -m app.main
echo   7. Test: python examples\complete_workflow_test.py
echo.
echo Database Architecture:
echo   PostgreSQL (Main Brain): Permanent storage
echo   Redis (Fast Memory): Embeddings and search
echo.
echo Documentation:
echo   - API: http://localhost:8000/docs
echo   - Quick Start: QUICKSTART.md
echo   - Architecture: ARCHITECTURE_POSTGRES_REDIS.md
echo.
pause
