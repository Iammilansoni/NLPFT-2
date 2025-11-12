@echo off
REM Quick setup script for Llama 3.2 3B on Windows

echo ============================================================
echo Llama 3.2 3B Setup for NLPForge
echo ============================================================
echo.

REM Step 1: Download model
echo Step 1: Downloading Llama 3.2 3B model...
echo.
python scripts\download_llama_model.py
if errorlevel 1 (
    echo.
    echo ERROR: Model download failed!
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Step 2: Install llama.cpp
echo ============================================================
echo.
echo Please download llama.cpp from:
echo https://github.com/ggerganov/llama.cpp/releases
echo.
echo Download: llama-b<version>-bin-win-avx2-x64.zip
echo Extract to: C:\llama.cpp\
echo.
echo Press any key when done...
pause >nul

REM Step 3: Test setup
echo.
echo ============================================================
echo Step 3: Testing Llama setup...
echo ============================================================
echo.
python scripts\test_llama_model.py
if errorlevel 1 (
    echo.
    echo WARNING: Test failed!
    echo Please check:
    echo 1. Model path in .env file
    echo 2. llama-cli is installed and in PATH
    echo 3. See LLAMA_SETUP.md for troubleshooting
    pause
    exit /b 1
)

echo.
echo ============================================================
echo SUCCESS! Llama 3.2 3B is ready to use!
echo ============================================================
echo.
echo Your NLPForge system will now use Llama for slot extraction.
echo.
pause
