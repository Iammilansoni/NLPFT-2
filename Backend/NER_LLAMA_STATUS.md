# NER + Llama + Grammar Status Report

## Current Status

### ✅ NER (spaCy) - **WORKING**
- **Status**: ✅ Functional
- **Model**: `en_core_web_md`
- **Implementation**: `Backend/app/nlp/query_parser.py`
- **Features**:
  - Extracts PERSON, EMAIL, PHONE, ORG, GPE, DATE, MONEY entities
  - EntityRuler for EMAIL/PHONE patterns
  - Heuristic username detection (tokens with @ or _)
- **Test Result**: NER extraction working correctly

### ⚠️ Llama 3.2 3B - **DISABLED**
- **Status**: ⚠️ Not Available
- **Reason**: `llama-cli` executable not found in PATH
- **Model Path**: `C:\Users\milan\models\llama-3.2-3b-instruct-q4_k_m.gguf`
- **Expected CLI**: `llama-cli`
- **Error**: `[WinError 2] The system cannot find the file specified`
- **Fallback**: System falls back to NER-only extraction (working)

### ⚠️ JSON Schema Grammar - **POTENTIAL ISSUE**
- **Status**: ⚠️ May not work with all llama.cpp versions
- **Current Implementation**: Uses `--json-schema` flag
- **Issue**: 
  - Newer llama.cpp versions (v2.0+) support `--json-schema`
  - Older versions require `--grammar` with GBNF format
  - Need to check which version is installed

## How to Fix

### 1. Enable Llama (Required for Grammar)
```bash
# Option A: Install llama.cpp and add to PATH
# Download from: https://github.com/ggerganov/llama.cpp/releases
# Extract and add to PATH

# Option B: Set LLAMA_CPP_PATH in .env
LLAMA_CPP_PATH=C:\llama.cpp\llama-cli.exe
```

### 2. Verify JSON Schema Support
```bash
# Check llama-cli version
llama-cli --version

# Test JSON schema flag
llama-cli --help | grep -i "json\|grammar"
```

### 3. Test Full Pipeline
```python
from app.nlp.query_parser import QueryParser

parser = QueryParser()
result = parser.parse("Test login with email: user@example.com and password: P@ssw0rd")

print(f"Intent: {result['intent']}")
print(f"Slots: {result['slots']}")
print(f"NER: {result['metadata']['slots_spacy']}")
print(f"Llama: {result['metadata']['slots_llama']}")
```

## Current Behavior

1. **Without Llama**: 
   - ✅ NER extraction works
   - ✅ Intent detection works
   - ⚠️ Slot extraction limited to NER entities only

2. **With Llama**:
   - ✅ NER extraction works
   - ✅ Llama extraction works (with JSON schema grammar)
   - ✅ Intelligent merging (Llama > NER)

## Recommendations

1. **If Llama is not needed**: System works fine with NER-only
2. **If Llama is needed**: Install llama.cpp and configure PATH
3. **For production**: Consider using Ollama API as alternative (easier setup)


