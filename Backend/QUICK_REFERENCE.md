# NLPForge Quick Reference Card

## 🚀 Query Processing Flow (1-Minute Overview)

```
User Query → FastAPI → Query Parser → Template Match → Dataset Gen (optional) → Embeddings → Vector Search → Response
```

## 📍 Key Endpoints

### 1. Main Query Endpoint (Full Pipeline)
```http
POST /api/v1/query
Content-Type: application/json

{
  "query": "Update my profile with John Pass123",
  "generate_dataset": true,
  "num_examples": 50,
  "top_k": 5
}
```

**Response:**
```json
{
  "intent": "update_profile",
  "confidence": 0.95,
  "slots": {"username": "John", "password": "Pass123"},
  "best_matches": [...],
  "search_results": [...]
}
```

### 2. Quick Search (No Parsing)
```http
GET /api/v1/search/search?query=login&top_k=5&min_similarity=0.7
```

### 3. Template Management
```http
GET  /api/v1/templates/           # List all
GET  /api/v1/templates/{intent}   # Get one
POST /api/v1/templates/           # Create
PUT  /api/v1/templates/{intent}   # Update
POST /api/v1/templates/sync       # Sync from JSON
```

## 🧠 Query Parser Components

### Hybrid Slot Extraction (4 Methods)

| Method | Speed | Accuracy | Use Case |
|--------|-------|----------|----------|
| **spaCy NER** | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | PERSON, EMAIL, PHONE entities |
| **Llama 3.2 3B** | ⚡⚡ | ⭐⭐⭐⭐⭐ | Context-aware structured extraction |
| **Regex** | ⚡⚡⚡⚡⚡ | ⭐⭐⭐⭐ | Explicit patterns (username:, email:) |
| **Contextual** | ⚡⚡⚡⚡⚡ | ⭐⭐⭐⭐ | Domain-specific ('for X and Y') |

### Priority Order (Merge)
```
Highest → Contextual Rules
        → Regex Patterns
        → Llama 3.2 3B
Lowest  → spaCy NER
```

## 📦 Core Components

### 1. Query Parser
```python
from app.nlp.query_parser import parse_query

result = parse_query("Update profile with John Pass123")
# Returns: {intent, confidence, slots, metadata}
```

### 2. Template Service
```python
from app.services.template_service import get_template_service

service = get_template_service()
template = service.get_template("login")
# Returns: {intent, endpoint, slots, keywords}
```

### 3. Embedding Manager
```python
from app.nlp.embedding_manager import get_embedding_manager

embedder = get_embedding_manager()
results = embedder.search("login", top_k=5)
# Returns: [{query, intent, similarity, ...}]
```

### 4. Dataset Generator
```python
from app.nlp.smart_dataset_generator import get_dataset_generator

generator = get_dataset_generator()
info = generator.generate_from_query(
    query="Login with admin",
    intent="login",
    slots={"username": "admin"},
    num_variations=50
)
```

## 🗄️ Data Storage

### PostgreSQL (Templates)
```sql
-- api_templates table
SELECT intent, endpoint_template, intent_keywords, slots
FROM api_templates
WHERE intent = 'login';
```

### Redis (Embeddings)
```python
# Key: nlp:embedding:{uuid}
# Value: {query, intent, slots, embedding[384], timestamp}

# Vector Index: idx:apis
# Dimension: 384
# Distance: Cosine
```

## ⚙️ Configuration (.env)

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/nlpforge

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Llama (Optional)
LLAMA_MODEL_PATH=/path/to/Llama-3.2-3B-Instruct-Q4_K_M.gguf
LLAMA_CPP_PATH=/path/to/llama-cli

# Gemini (Optional - for dataset generation)
GEMINI_API_KEY=your_key_here

# spaCy
SPACY_MODEL=en_core_web_md

# Embedding
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## 🎯 Common Tasks

### Add New API Template
```python
# 1. Add to api_template.json
{
  "name": "new_api",
  "endpoint_template": "<base_url>/api/new",
  "intent_keywords": ["new action", "create"],
  "slots": [
    {"key": "field1", "questions": ["What is field1?"]}
  ]
}

# 2. Sync to database
POST /api/v1/templates/sync
Body: {"json_path": "api_template.json"}
```

### Test Query Parsing
```python
# Backend/test_llama_extraction.py
python test_llama_extraction.py

# Or directly:
python -c "from app.nlp.query_parser import parse_query; print(parse_query('login admin pass'))"
```

### Check System Status
```http
GET /api/v1/templates/stats     # Template statistics
GET /                            # API root info
```

## 🐛 Debugging

### Enable Debug Logging
```python
# app/core/logger.py
import logging
logging.getLogger("nlpforge").setLevel(logging.DEBUG)
```

### View Logs
```bash
# Real-time logs
tail -f Backend/logs/nlpforge.log

# Or in terminal where uvicorn runs
```

### Check Individual Components
```python
# Test spaCy
from app.nlp.query_parser import get_query_parser
parser = get_query_parser()
print(parser.extract_slots_spacy("John Doe john@example.com"))

# Test Llama
from app.nlp.llama_slot_extractor import get_llama_extractor
llama = get_llama_extractor()
print(llama.enabled)  # Should be True if installed

# Test embeddings
from app.nlp.embedding_manager import get_embedding_manager
embedder = get_embedding_manager()
print(embedder.get_stats())
```

## 📊 Performance Tips

### Speed Up Queries
1. **Disable Llama** if not needed (saves ~2s per query)
   ```python
   QueryParser(use_llama=False)
   ```

2. **Use smaller spaCy model**
   ```bash
   SPACY_MODEL=en_core_web_sm  # Faster than md/lg
   ```

3. **Cache templates** in memory (already done)

4. **Enable GPU** for Llama (5-10x faster)
   ```bash
   # Build llama.cpp with CUDA
   cmake -B build -DGGML_CUDA=ON
   ```

### Improve Accuracy
1. **Add more intent_keywords** to templates
2. **Generate more dataset variations** (50-100 per intent)
3. **Use Llama** for complex queries
4. **Fine-tune Sentence Transformer** on your domain

## 🔗 Integration Examples

### Frontend (React/Next.js)
```typescript
const queryAPI = async (query: string) => {
  const res = await fetch('http://localhost:8000/api/v1/query', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({query, generate_dataset: true, top_k: 5})
  });
  const data = await res.json();
  console.log('Intent:', data.intent);
  console.log('Slots:', data.slots);
  console.log('Matches:', data.best_matches);
};
```

### Python Client
```python
import requests

response = requests.post('http://localhost:8000/api/v1/query', json={
    'query': 'Login with admin pass123',
    'generate_dataset': True,
    'top_k': 5
})

result = response.json()
print(f"Intent: {result['intent']}")
print(f"Slots: {result['slots']}")
```

### cURL
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query":"login admin pass","generate_dataset":true,"top_k":5}'
```

## 📚 Documentation Links

- **[COMPLETE_FLOW_DIAGRAM.md](./COMPLETE_FLOW_DIAGRAM.md)** - Full system flow
- **[LLAMA_SETUP.md](./LLAMA_SETUP.md)** - Setup Llama 3.2 3B
- **[LLAMA_INTEGRATION.md](./LLAMA_INTEGRATION.md)** - Technical details
- **[BACKEND_COMPLETE_DOCUMENTATION.md](./BACKEND_COMPLETE_DOCUMENTATION.md)** - Full docs

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No module named 'app'" | Run from Backend/ directory |
| "Llama not available" | Check LLAMA_MODEL_PATH in .env |
| "No templates loaded" | Run POST /api/v1/templates/sync |
| "Redis connection failed" | Start Redis: `redis-server` |
| "Intent unknown" | Add keywords to template or improve query |
| Slow queries (>5s) | Disable Llama or use GPU |

---

**Quick Start:**
```bash
cd Backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then test: http://localhost:8000/docs
