# Llama 3.2 3B Setup Guide

This guide will help you download and set up Llama 3.2 3B Instruct for intelligent slot extraction in NLPForge.

## Why Llama 3.2 3B?

- **Lightweight**: Only ~2GB (Q4_K_M quantized)
- **Fast**: Runs on CPU efficiently
- **Accurate**: Better slot extraction than regex/NER
- **Structured**: Supports JSON schema for reliable output
- **Local**: No API calls, complete privacy

---

## Step 1: Download the Model

### Option A: Using the Download Script (Recommended)

```bash
cd Backend
python scripts/download_llama_model.py
```

This will:
- Download Llama 3.2 3B Instruct (Q4_K_M, ~2GB)
- Save to `~/models/llama-3.2-3b-instruct-q4_k_m.gguf`
- Show setup instructions

### Option B: Manual Download

1. Go to: https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF
2. Download: `Llama-3.2-3B-Instruct-Q4_K_M.gguf` (~2GB)
3. Save to: `C:\Users\milan\models\llama-3.2-3b-instruct-q4_k_m.gguf`

### Option C: Using Hugging Face CLI

```bash
pip install huggingface-hub
huggingface-cli download bartowski/Llama-3.2-3B-Instruct-GGUF Llama-3.2-3B-Instruct-Q4_K_M.gguf --local-dir ~/models
```

---

## Step 2: Install llama.cpp

### Windows

1. **Download Pre-built Binary:**
   - Go to: https://github.com/ggerganov/llama.cpp/releases
   - Download: `llama-b<version>-bin-win-avx2-x64.zip`
   - Extract to: `C:\llama.cpp\`
   - Add to PATH or note the path to `llama-cli.exe`

2. **Or Build from Source:**
   ```bash
   git clone https://github.com/ggerganov/llama.cpp
   cd llama.cpp
   mkdir build
   cd build
   cmake ..
   cmake --build . --config Release
   ```

### Linux/Mac

```bash
# Clone and build
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make

# Install to system
sudo cp llama-cli /usr/local/bin/
```

---

## Step 3: Configure Environment Variables

Add to your `Backend/.env` file:

```bash
# Llama 3.2 3B Configuration
LLAMA_MODEL_PATH=C:\Users\milan\models\llama-3.2-3b-instruct-q4_k_m.gguf
LLAMA_CPP_PATH=C:\llama.cpp\llama-cli.exe

# Or if llama-cli is in PATH:
# LLAMA_CPP_PATH=llama-cli
```

**For Linux/Mac:**
```bash
LLAMA_MODEL_PATH=/home/milan/models/llama-3.2-3b-instruct-q4_k_m.gguf
LLAMA_CPP_PATH=llama-cli
```

---

## Step 4: Test the Setup

```bash
cd Backend
python scripts/test_llama_model.py
```

Expected output:
```
✅ Llama model loaded: /path/to/model.gguf

Test 1: login
Query: "login with username john_doe and password SecureP@ss123"
Expected slots: ['username', 'password']
Extracted: {'username': 'john_doe', 'password': 'SecureP@ss123'}
✅ All required slots extracted
```

---

## Step 5: Verify Integration

The Llama extractor is already integrated into your `query_parser.py`. Test it:

```python
from app.nlp.query_parser import parse_query

result = parse_query("login with john and pass123")
print(result)
# Output:
# {
#   'intent': 'login',
#   'slots': {'username': 'john', 'password': 'pass123'},
#   'confidence': 0.95,
#   'metadata': {
#     'slots_llama': {'username': 'john', 'password': 'pass123'},
#     ...
#   }
# }
```

---

## Troubleshooting

### Model Not Found
```
⚠️ Llama 3.2 3B model not found. Slot extraction will use fallback methods.
```

**Solution:**
- Check `LLAMA_MODEL_PATH` in `.env`
- Verify file exists: `ls ~/models/llama-3.2-3b-instruct-q4_k_m.gguf`
- Use absolute path in `.env`

### llama-cli Not Available
```
llama-cli not available: llama-cli
```

**Solution:**
- Install llama.cpp (see Step 2)
- Add to PATH or use absolute path in `.env`
- Test: `llama-cli --version`

### Inference Timeout
```
Llama inference timed out
```

**Solution:**
- Increase timeout in `llama_slot_extractor.py` (line 280)
- Use faster quantization (Q4_0 instead of Q4_K_M)
- Enable GPU inference (set `-ngl` parameter)

### GPU Acceleration (Optional)

For faster inference with NVIDIA GPU:

1. Build llama.cpp with CUDA:
   ```bash
   cmake -B build -DLLAMA_CUDA=ON
   cmake --build build --config Release
   ```

2. Update `llama_slot_extractor.py`:
   ```python
   "-ngl", "33",  # Offload 33 layers to GPU
   ```

---

## Performance Benchmarks

| Hardware | Inference Time | Tokens/sec |
|----------|---------------|------------|
| CPU (Intel i7) | ~2-3 seconds | 15-20 |
| CPU (AMD Ryzen) | ~1-2 seconds | 25-30 |
| GPU (RTX 3060) | ~0.5 seconds | 80-100 |
| GPU (RTX 4090) | ~0.2 seconds | 200+ |

---

## Model Variants

If you need different performance/quality tradeoffs:

| Model | Size | Quality | Speed | Use Case |
|-------|------|---------|-------|----------|
| Q4_0 | 1.8GB | Good | Fast | Production (CPU) |
| Q4_K_M | 2.0GB | Better | Medium | **Recommended** |
| Q5_K_M | 2.4GB | Best | Slower | High accuracy |
| Q8_0 | 3.5GB | Excellent | Slow | Maximum quality |

Download from: https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF

---

## Alternative: Use Ollama (Easier Setup)

If you prefer a simpler setup:

1. Install Ollama: https://ollama.ai/download
2. Pull model: `ollama pull llama3.2:3b-instruct`
3. Update `llama_slot_extractor.py` to use Ollama API

---

## Next Steps

Once Llama is working:

1. ✅ Slot extraction will be more accurate
2. ✅ Handles complex queries better
3. ✅ Extracts context-aware information
4. ✅ Works with any API template

Your NLPForge system will automatically use Llama when available, falling back to regex/NER if not.

---

## Support

- Llama.cpp: https://github.com/ggerganov/llama.cpp
- Model: https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF
- Issues: Check Backend logs for detailed error messages
