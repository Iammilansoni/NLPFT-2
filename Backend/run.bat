@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM NLPForge Backend - All-in-One Setup & Run Script
REM ============================================================

REM Color codes for better visibility
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "BLUE=[94m"
set "CYAN=[96m"
set "RESET=[0m"

:MENU
cls
echo.
echo %CYAN%============================================================%RESET%
echo %CYAN%           NLPForge Backend - Main Menu%RESET%
echo %CYAN%============================================================%RESET%
echo.
echo  %GREEN%1.%RESET% Full Setup (First Time Installation)
echo  %GREEN%2.%RESET% Quick Start (Already Setup)
echo  %GREEN%3.%RESET% Setup Llama Model
echo  %GREEN%4.%RESET% Start Services (Docker)
echo  %GREEN%5.%RESET% Initialize Database
echo  %GREEN%6.%RESET% Run API Server
echo  %GREEN%7.%RESET% Run Tests
echo  %RED%8.%RESET% Exit
echo.
echo %CYAN%============================================================%RESET%
echo.
set /p choice="Select option (1-8): "

if "%choice%"=="1" goto FULL_SETUP
if "%choice%"=="2" goto QUICK_START
if "%choice%"=="3" goto SETUP_LLAMA
if "%choice%"=="4" goto START_SERVICES
if "%choice%"=="5" goto INIT_DB
if "%choice%"=="6" goto RUN_API
if "%choice%"=="7" goto RUN_TESTS
if "%choice%"=="8" goto EXIT
goto MENU

REM ============================================================
:FULL_SETUP
REM ============================================================
cls
echo ============================================================
echo Full Setup - First Time Installation
echo ============================================================
echo.

echo [1/9] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    goto MENU
)
echo OK - Python found
echo.

echo [2/9] Checking Docker installation...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Docker is not installed
    echo Install Docker Desktop from https://www.docker.com/
    set DOCKER_AVAILABLE=0
) else (
    echo OK - Docker found
    set DOCKER_AVAILABLE=1
)
echo.

echo [3/9] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    echo OK - Virtual environment created
)
echo.

echo [4/9] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    goto MENU
)
echo OK - Virtual environment activated
echo.

echo [5/9] Upgrading pip...
python -m pip install --upgrade pip
echo OK - pip upgraded
echo.

echo [6/9] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    goto MENU
)
echo OK - Dependencies installed
echo.

echo [7/9] Downloading spaCy model (en_core_web_md)...
python -m spacy download en_core_web_md
if %errorlevel% neq 0 (
    echo WARNING: Failed to download spaCy model
    echo You can download it manually later
) else (
    echo OK - spaCy model downloaded
)
echo.

echo [8/9] Setting up .env file...
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

echo [9/9] Starting Docker services...
if %DOCKER_AVAILABLE%==1 (
    docker-compose up -d
    if %errorlevel% neq 0 (
        echo WARNING: Failed to start Docker services
        echo You can start them manually later
    ) else (
        echo OK - Docker services started
        timeout /t 5 /nobreak >nul
    )
) else (
    echo Skipping Docker services (Docker not available)
)
echo.

echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
echo Next steps:
echo   1. Edit .env file and add your API keys
echo   2. Run option 5 to initialize database
echo   3. Run option 6 to start API server
echo.
pause
goto MENU

REM ============================================================
:QUICK_START
REM ============================================================
cls
echo ============================================================
echo Quick Start - Starting All Services
echo ============================================================
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

echo Starting Docker services...
docker-compose up -d
if %errorlevel% neq 0 (
    echo ERROR: Failed to start Docker services
    echo Please check Docker Desktop is running
    pause
    goto MENU
)
echo OK - Services started
echo.

timeout /t 3 /nobreak >nul

echo Starting API server...
echo API will be available at: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
goto MENU

REM ============================================================
:SETUP_LLAMA
REM ============================================================
cls
echo ============================================================
echo Llama 3.2 3B Setup
echo ============================================================
echo.

call venv\Scripts\activate.bat

echo Step 1: Downloading Llama 3.2 3B model...
python scripts\download_llama_model.py
if %errorlevel% neq 0 (
    echo ERROR: Model download failed!
    pause
    goto MENU
)
echo.

echo Step 2: Install llama.cpp
echo Please download from: https://github.com/ggerganov/llama.cpp/releases
echo Download: llama-b<version>-bin-win-avx2-x64.zip
echo Extract to: C:\llama.cpp\
echo.
pause
echo.

echo Step 3: Testing Llama setup...
python scripts\test_llama_model.py
if %errorlevel% neq 0 (
    echo WARNING: Test failed! Check LLAMA_SETUP.md
    pause
    goto MENU
)
echo.

echo ============================================================
echo SUCCESS! Llama 3.2 3B is ready!
echo ============================================================
pause
goto MENU

REM ============================================================
:START_SERVICES
REM ============================================================
cls
echo ============================================================
echo Starting Docker Services
echo ============================================================
echo.

docker-compose up -d
if %errorlevel% neq 0 (
    echo ERROR: Failed to start services
    echo Make sure Docker Desktop is running
    pause
    goto MENU
)

echo.
echo Services started:
echo   - PostgreSQL: localhost:5432
echo   - Redis: localhost:6379
echo   - Redis Insight: http://localhost:8001
echo.
pause
goto MENU

REM ============================================================
:INIT_DB
REM ============================================================
cls
echo ============================================================
echo Initializing Database
echo ============================================================
echo.

call venv\Scripts\activate.bat

echo Creating database schema and tables...
python init_database.py
if %errorlevel% neq 0 (
    echo ERROR: Database initialization failed
    pause
    goto MENU
)

echo.
echo ============================================================
echo Database initialized successfully!
echo ============================================================
pause
goto MENU

REM ============================================================
:RUN_API
REM ============================================================
cls
echo ============================================================
echo Starting API Server
echo ============================================================
echo.

call venv\Scripts\activate.bat

echo API Server starting...
echo   - API: http://localhost:8000
echo   - Docs: http://localhost:8000/docs
echo   - ReDoc: http://localhost:8000/redoc
echo.
echo Press Ctrl+C to stop
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
goto MENU

REM ============================================================
:RUN_TESTS
REM ============================================================
cls
echo ============================================================
echo Running Tests
echo ============================================================
echo.

call venv\Scripts\activate.bat

echo Select test to run:
echo 1. Complete Workflow Test
echo 2. Llama Extraction Test
echo 3. Autoscaling System Test
echo 4. Back to Menu
echo.
set /p test_choice="Select (1-4): "

if "%test_choice%"=="1" (
    python examples\complete_workflow_test.py
) else if "%test_choice%"=="2" (
    python test_llama_extraction.py
) else if "%test_choice%"=="3" (
    python test_autoscaling_system.py
) else (
    goto MENU
)

echo.
pause
goto MENU

REM ============================================================
:EXIT
REM ============================================================
cls
echo ============================================================
echo Shutting Down
echo ============================================================
echo.

set /p shutdown="Stop Docker services? (y/n): "
if /i "%shutdown%"=="y" (
    echo Stopping Docker services...
    docker-compose down
    echo Services stopped
)

echo.
echo Goodbye!
timeout /t 2 /nobreak >nul
exit /b 0
