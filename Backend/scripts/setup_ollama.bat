@echo off
echo ========================================
echo  NLPForge Ollama Models Setup
echo ========================================
echo.

echo Checking if Ollama is running...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Ollama is not running!
    echo Please start Ollama first: https://ollama.ai/download
    pause
    exit /b 1
)
echo [OK] Ollama is running
echo.

echo ----------------------------------------
echo  Pulling Embedding Models
echo ----------------------------------------

echo [1/5] Pulling all-minilm (384 dim, fast)...
ollama pull all-minilm

echo [2/5] Pulling nomic-embed-text (768 dim, recommended)...
ollama pull nomic-embed-text

echo [3/5] Pulling mxbai-embed-large (1024 dim, precision)...
ollama pull mxbai-embed-large

echo.
echo ----------------------------------------
echo  Pulling LLM Models for Dataset Gen
echo ----------------------------------------

echo [4/5] Pulling llama3.2:3b-instruct-q4_K_M (primary)...
ollama pull llama3.2:3b-instruct-q4_K_M

echo [5/5] Pulling gemma2:2b-instruct-q4_K_M (fallback)...
ollama pull gemma2:2b-instruct-q4_K_M

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo Available models:
ollama list
echo.
pause
