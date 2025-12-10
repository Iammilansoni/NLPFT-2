# ========================================
#  NLPForge Ollama Models Setup
#  PowerShell Version
# ========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NLPForge Ollama Models Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Ollama is running
Write-Host "Checking if Ollama is running..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -ErrorAction Stop
    Write-Host "[OK] Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Ollama is not running!" -ForegroundColor Red
    Write-Host "Please start Ollama first. It should auto-start on Windows." -ForegroundColor Red
    Write-Host "Or run: ollama serve" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor Cyan
Write-Host "  Pulling Embedding Models" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Cyan

# Embedding Models
Write-Host ""
Write-Host "[1/5] Pulling all-minilm (384 dim, fast)..." -ForegroundColor Yellow
ollama pull all-minilm

Write-Host ""
Write-Host "[2/5] Pulling nomic-embed-text (768 dim, recommended)..." -ForegroundColor Yellow
ollama pull nomic-embed-text

Write-Host ""
Write-Host "[3/5] Pulling mxbai-embed-large (1024 dim, precision)..." -ForegroundColor Yellow
ollama pull mxbai-embed-large

Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor Cyan
Write-Host "  Pulling LLM Models for Dataset Gen" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Cyan

Write-Host ""
Write-Host "[4/5] Pulling llama3.2:3b-instruct-q4_K_M (primary)..." -ForegroundColor Yellow
ollama pull llama3.2:3b-instruct-q4_K_M

Write-Host ""
Write-Host "[5/5] Pulling gemma2:2b-instruct-q4_K_M (fallback)..." -ForegroundColor Yellow
ollama pull gemma2:2b-instruct-q4_K_M

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Available models:" -ForegroundColor Yellow
ollama list

Write-Host ""
Read-Host "Press Enter to exit"
