# NLPForge Complete Backend Flow

## 🎯 Overview

This document explains the **complete end-to-end flow** of how NLPForge processes natural language queries from the Frontend, performs operations, and generates results.

---

## 📊 Architecture Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                      │
│  User Input: "Update my profile with credential as John Pass123"│
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP POST
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API LAYER (FastAPI)                          │
│              /api/v1/query OR /api/v1/search                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  QUERY PARSER (Hybrid NER + Llama)              │
│              Intent Detection + Slot Extraction                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│               TEMPLATE SERVICE (PostgreSQL)                     │
│                  API Template Matching                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│            DATASET GENERATOR (Optional - If Needed)             │
│              Generate Training Variations                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│          EMBEDDING MANAGER (Sentence Transformers)              │
│              Vectorize & Store in Redis                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│         SEMANTIC SEARCH (Redis Vector Search)                   │
│              Find Best Matching APIs                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                 RESPONSE BUILDER                                │
│     Intent + Slots + Best Matches → JSON Response              │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP 200 OK
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
│              Display Results to User                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Detailed Flow Breakdown

### **Stage 1: Frontend → API Request**

#### Frontend (React/Next.js)
```typescript
// Frontend/src/app/test-runner/page.tsx or query page

const handleSearch = async (query: string) => {
  const response = await fetch('http://localhost:8000/api/v1/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: "Update my profile with credential as John Pass123",
      generate_dataset: true,
      num_examples: 50,
      top_k: 5
    })
  });
  
  const result = await response.json();
  // result contains: intent, slots, confidence, best_matches, search_results
}
```

**What happens:**
- User types natural language query in Frontend
- Frontend sends HTTP POST to `/api/v1/query` endpoint
- Request includes query text and parameters

---

### **Stage 2: API Endpoint Receives Request**

#### Backend (FastAPI)
```python
# Backend/app/api/v1/query.py

@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, background_tasks: BackgroundTasks):
    """
    Main entry point for query processing
    
    Input:
    {
        "query": "Update my profile with credential as John Pass123",
        "generate_dataset": true,
        "num_examples": 50,
        "top_k": 5
    }
    """
    logger.info(f"📥 Received query: {request.query}")
```

**What happens:**
1. FastAPI validates request using Pydantic model
2. Extracts query parameters
3. Logs the incoming request
4. Proceeds to Step 3

---

### **Stage 3: Query Parsing (Hybrid NER + Llama)**

#### Query Parser
```python
# Backend/app/nlp/query_parser.py

from app.nlp.query_parser import parse_query

# Step 1: Parse query
parsed = parse_query(request.query)
# Returns: {
#   "intent": "update_profile",
#   "confidence": 0.95,
#   "slots": {"username": "John", "password": "Pass123"},
#   "raw_query": "Update my profile..."
# }
```

**Internal Flow of Query Parser:**

```
┌────────────────────────────────────────────────────────────┐
│  Input: "Update my profile with credential as John Pass123"│
└──────────────────┬─────────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────────┐
│  STEP 1: Intent Detection (Pattern Matching)              │
│  - Load templates from PostgreSQL via template_service    │
│  - Check intent_keywords: ["update profile", "edit profile"]│
│  - Match patterns with query                              │
│  - Result: intent = "update_profile", confidence = 0.95   │
└──────────────────┬─────────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────────┐
│  STEP 2: spaCy NER (Named Entity Recognition)             │
│  - Load spaCy model: en_core_web_md                       │
│  - Extract entities: PERSON, EMAIL, PHONE, ORG            │
│  - Result: {"name": "John"} (found PERSON entity)         │
└──────────────────┬─────────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────────┐
│  STEP 3: Llama 3.2 3B Slot Extraction (if available)      │
│  - Get template slot definitions from PostgreSQL          │
│  - Generate JSON schema for slots                         │
│  - Build Llama prompt with instructions                   │
│  - Call llama-cli with JSON schema grammar                │
│  - Parse JSON output                                      │
│  - Result: {"username": "John", "password": "Pass123"}    │
└──────────────────┬─────────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────────┐
│  STEP 4: Regex Pattern Extraction                         │
│  - Apply regex patterns for explicit markers              │
│  - username:, password:, email:, phone: patterns          │
│  - Result: {} (no explicit markers in this query)         │
└──────────────────┬─────────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────────┐
│  STEP 5: Contextual Rules                                 │
│  - Apply domain-specific patterns                         │
│  - "credential as X and Y" pattern                        │
│  - Result: {"username": "John", "password": "Pass123"}    │
└──────────────────┬─────────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────────┐
│  STEP 6: Intelligent Merging                              │
│  - Merge results with priority:                           │
│    contextual > regex > llama > spacy                     │
│  - Validate against query (anti-hallucination)            │
│  - Final: {"username": "John", "password": "Pass123"}     │
└──────────────────┬─────────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────────┐
│  OUTPUT:                                                   │
│  {                                                         │
│    "intent": "update_profile",                            │
│    "confidence": 0.95,                                    │
│    "slots": {"username": "John", "password": "Pass123"},  │
│    "metadata": {                                          │
│      "slots_spacy": {"name": "John"},                     │
│      "slots_llama": {"username": "John", ...},            │
│      "slots_regex": {},                                   │
│      "slots_contextual": {"username": "John", ...}        │
│    }                                                      │
│  }                                                        │
└────────────────────────────────────────────────────────────┘
```

---

### **Stage 4: Template Matching**

```python
# Backend/app/services/template_service.py

# Get template for detected intent
template_service = get_template_service()
template = template_service.get_template("update_profile")

# Returns:
# {
#   "intent": "update_profile",
#   "endpoint_template": "<base_url>/api/update_profile",
#   "intent_keywords": ["update profile", "edit profile"],
#   "slots": [
#     {"key": "username", "questions": ["What is the username?"]},
#     {"key": "password", "questions": ["What is the password?"]}
#   ],
#   "request_payload": {...},
#   "response_example": {...}
# }
```

**What happens:**
1. Template service queries PostgreSQL for intent template
2. Returns API endpoint structure and slot definitions
3. Used for validation and response building

---

### **Stage 5: Dataset Generation (Optional)**

**Condition:** If `generate_dataset=true` AND existing embeddings < threshold

```python
# Backend/app/nlp/smart_dataset_generator.py

generator = get_dataset_generator()

# Check existing embeddings
embedder = get_embedding_manager()
stats = embedder.get_stats()
existing_count = stats.get("intents", {}).get("update_profile", 0)

if existing_count < 10:
    # Generate dataset variations
    dataset_info = generator.generate_from_query(
        query="Update my profile with credential as John Pass123",
        intent="update_profile",
        slots={"username": "John", "password": "Pass123"},
        num_variations=50
    )
    
    # Generates 50 variations like:
    # - "Modify my profile using John and Pass123"
    # - "Edit profile with John Pass123"
    # - "Change my account details John Pass123"
    # etc.
```

**Generated Dataset Structure:**
```python
dataset_info = {
    "paths": {
        "csv": "datasets/update_profile_abc123.csv",
        "json": "datasets/update_profile_abc123.json"
    },
    "statistics": {
        "total_variations": 50,
        "intent": "update_profile",
        "unique_patterns": 35
    }
}
```

---

### **Stage 6: Embedding & Vector Storage**

```python
# Backend/app/nlp/embedding_manager.py

embedder = get_embedding_manager()

# Read generated CSV
import pandas as pd
df = pd.read_csv(dataset_info["paths"]["csv"])

# Extract data
queries = df['query'].tolist()  # 50 variations
intents = df['intent'].tolist()  # ["update_profile", ...]
slots_list = [json.loads(row['slots']) for _, row in df.iterrows()]

# Generate embeddings using Sentence Transformers
# Model: all-MiniLM-L6-v2 (384 dimensions)
redis_keys = embedder.upsert_batch(
    queries=queries,
    intents=intents,
    slots_list=slots_list
)

# Stores in Redis:
# Key: "nlp:embedding:{uuid}"
# Value: {
#   "query": "Update my profile...",
#   "intent": "update_profile",
#   "slots": {"username": "John", ...},
#   "embedding": [0.123, -0.456, ...],  # 384-dim vector
#   "timestamp": "2025-11-10T12:00:00Z"
# }
```

**What happens:**
1. Sentence Transformer model converts text to 384-dim vectors
2. Embeddings stored in Redis with metadata
3. Vector index created for fast similarity search

---

### **Stage 7: Semantic Search**

```python
# Backend/app/nlp/embedding_manager.py

# Perform vector similarity search
search_results = embedder.search(
    query="Update my profile with credential as John Pass123",
    top_k=5,
    intent_filter=None  # Allow cross-intent matches
)

# Returns:
# [
#   {
#     "query": "Update my profile with John Pass123",
#     "intent": "update_profile",
#     "slots": {"username": "John", "password": "Pass123"},
#     "similarity": 0.97,
#     "confidence": 0.95
#   },
#   {
#     "query": "Edit profile John Pass123",
#     "intent": "update_profile",
#     "slots": {...},
#     "similarity": 0.92,
#     "confidence": 0.90
#   },
#   ...
# ]
```

**Search Algorithm:**
1. Convert user query to embedding vector
2. Redis vector search (cosine similarity)
3. Find top-k most similar stored embeddings
4. Return matches with similarity scores

---

### **Stage 8: Response Building**

```python
# Backend/app/api/v1/query.py

# Build best matches from search results
best_matches = []
for result in search_results:
    best_matches.append({
        "api": result["intent"],
        "score": result["similarity"],
        "confidence": result.get("confidence", 1.0)
    })

# Deduplicate by API intent
seen_apis = set()
unique_matches = []
for match in best_matches:
    if match["api"] not in seen_apis:
        seen_apis.add(match["api"])
        unique_matches.append(match)

# Build response
response = QueryResponse(
    query=request.query,
    intent="update_profile",
    slots={"username": "John", "password": "Pass123"},
    confidence=0.95,
    best_matches=unique_matches,
    dataset_generated=True,
    dataset_info=dataset_info,
    search_results=search_results[:5]
)

return response
```

---

### **Stage 9: Response to Frontend**

#### Backend Response (JSON)
```json
{
  "query": "Update my profile with credential as John Pass123",
  "intent": "update_profile",
  "confidence": 0.95,
  "slots": {
    "username": "John",
    "password": "Pass123"
  },
  "best_matches": [
    {
      "api": "update_profile",
      "score": 0.97,
      "confidence": 0.95
    },
    {
      "api": "change_password",
      "score": 0.85,
      "confidence": 0.82
    }
  ],
  "dataset_generated": true,
  "dataset_info": {
    "paths": {
      "csv": "datasets/update_profile_abc123.csv",
      "json": "datasets/update_profile_abc123.json"
    },
    "redis_keys": 50
  },
  "search_results": [
    {
      "query": "Update my profile with John Pass123",
      "intent": "update_profile",
      "similarity": 0.97,
      "slots": {"username": "John", "password": "Pass123"}
    }
  ]
}
```

#### Frontend Displays Results
```typescript
// Frontend processes response
const result = await response.json();

// Display:
// - Intent: update_profile (95% confidence)
// - Extracted Fields:
//   • username: John
//   • password: Pass123
// - Best Matching APIs:
//   1. update_profile (97% match)
//   2. change_password (85% match)
// - Dataset Status: Generated 50 variations
```

---

## 🗂️ Data Storage Architecture

### PostgreSQL (Permanent Storage)
```
┌─────────────────────────────────────┐
│  api_templates Table                │
├─────────────────────────────────────┤
│ - id (UUID)                         │
│ - intent (VARCHAR) PRIMARY KEY      │
│ - endpoint_template (TEXT)          │
│ - intent_keywords (JSONB)           │
│ - slots (JSONB)                     │
│ - request_payload (JSONB)           │
│ - response_example (JSONB)          │
│ - created_at (TIMESTAMP)            │
│ - updated_at (TIMESTAMP)            │
└─────────────────────────────────────┘

Example Row:
{
  "intent": "update_profile",
  "endpoint_template": "<base_url>/api/update_profile",
  "intent_keywords": ["update profile", "edit profile"],
  "slots": [
    {"key": "username", "questions": ["What is username?"]},
    {"key": "password", "questions": ["What is password?"]}
  ]
}
```

### Redis (Fast Vector Search)
```
┌─────────────────────────────────────┐
│  Redis Keys Structure               │
├─────────────────────────────────────┤
│ nlp:embedding:{uuid}                │
│ {                                   │
│   "query": "...",                   │
│   "intent": "update_profile",       │
│   "slots": {...},                   │
│   "embedding": [0.1, 0.2, ...],    │
│   "timestamp": "2025-11-10..."     │
│ }                                   │
└─────────────────────────────────────┘

Vector Index: idx:apis
- Dimension: 384 (from all-MiniLM-L6-v2)
- Distance: Cosine Similarity
- Algorithm: HNSW (fast approximate search)
```

---

## 🎬 Alternative Flow: Direct Search (Skip Query Parser)

If user already knows the API and just wants to search:

```
Frontend: /api/v1/search/search?query=login&top_k=5&min_similarity=0.7
                           │
                           ▼
Backend: app/api/v1/search.py
                           │
                           ▼
Embedding Manager: Convert query to vector
                           │
                           ▼
Redis: Vector similarity search
                           │
                           ▼
Response: List of similar queries with scores
```

**Usage:**
- Autocomplete suggestions
- Similar query recommendations
- Quick API lookup without full parsing

---

## 🔄 Complete System Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERACTION                         │
│  Types: "Update my profile with credential as John Pass123"    │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
        ▼                                         ▼
┌──────────────────┐                    ┌──────────────────┐
│  Query Endpoint  │                    │ Search Endpoint  │
│  /api/v1/query   │                    │/api/v1/search    │
│ (Full Pipeline)  │                    │ (Direct Search)  │
└────────┬─────────┘                    └────────┬─────────┘
         │                                       │
         ▼                                       │
┌──────────────────────────────────────┐        │
│  Query Parser (Hybrid NER + Llama)   │        │
│  ├─ Intent Detection                 │        │
│  ├─ spaCy NER                        │        │
│  ├─ Llama 3.2 3B Extraction          │        │
│  ├─ Regex Patterns                   │        │
│  └─ Contextual Rules                 │        │
└────────┬─────────────────────────────┘        │
         │                                       │
         ▼                                       │
┌──────────────────────────────────────┐        │
│  Template Service (PostgreSQL)       │        │
│  - Load API templates                │        │
│  - Get slot definitions              │        │
│  - Validate intent                   │        │
└────────┬─────────────────────────────┘        │
         │                                       │
         ▼                                       │
┌──────────────────────────────────────┐        │
│  Dataset Generator (Optional)        │        │
│  - Check existing embeddings         │        │
│  - Generate variations if needed     │        │
│  - Save to CSV/JSON                  │        │
└────────┬─────────────────────────────┘        │
         │                                       │
         ▼                                       │
┌──────────────────────────────────────┐        │
│  Embedding Manager                   │◄───────┘
│  - Sentence Transformer              │
│  - Generate 384-dim vectors          │
│  - Store in Redis                    │
│  - Create/update vector index        │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  Redis Vector Search (idx:apis)      │
│  - Cosine similarity search          │
│  - Top-k retrieval                   │
│  - Score ranking                     │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  Response Builder                    │
│  - Merge results                     │
│  - Deduplicate intents               │
│  - Format JSON response              │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  Frontend (React/Next.js)            │
│  - Display intent & slots            │
│  - Show best matches                 │
│  - Render confidence scores          │
└──────────────────────────────────────┘
```

---

## 📝 Key Components Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Query Parser** | spaCy + Llama 3.2 3B + Regex | Extract intent & slots from natural language |
| **Template Service** | PostgreSQL | Store & retrieve API templates |
| **Dataset Generator** | Gemini API / Rule-based | Generate training variations |
| **Embedding Manager** | Sentence Transformers | Convert text to vectors |
| **Vector Store** | Redis + RediSearch | Fast similarity search |
| **API Layer** | FastAPI | REST endpoints |
| **Frontend** | Next.js + React | User interface |

---

## 🚀 Performance Characteristics

| Stage | Latency | Notes |
|-------|---------|-------|
| API Request | ~5ms | Network + FastAPI overhead |
| Intent Detection | ~10ms | Pattern matching on templates |
| spaCy NER | ~50ms | Fast entity recognition |
| Llama Extraction | ~1-2s | CPU inference (0.3s on GPU) |
| Regex/Contextual | ~5ms | Simple pattern matching |
| Template Lookup | ~10ms | PostgreSQL query |
| Dataset Generation | ~30-60s | If needed (async background) |
| Embedding | ~100ms | 50 queries batch |
| Vector Search | ~20ms | Redis HNSW index |
| Response Build | ~5ms | JSON serialization |
| **Total (without dataset)** | **~2-3s** | Including Llama |
| **Total (without Llama)** | **~100ms** | Fallback mode |

---

## 🔧 Configuration & Tuning

### Enable/Disable Components

```python
# Backend/.env

# Llama slot extraction (optional)
LLAMA_MODEL_PATH=/path/to/model.gguf
LLAMA_CPP_PATH=/path/to/llama-cli

# spaCy model
SPACY_MODEL=en_core_web_md  # or en_core_web_sm (faster)

# Dataset generation threshold
EMBEDDING_THRESHOLD=10  # Generate dataset if < 10 examples exist

# Search parameters
DEFAULT_TOP_K=5
MIN_SIMILARITY=0.7

# Sentence transformer model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

---

## 🎯 Use Cases

### 1. Query API Endpoint (Full Pipeline)
**Best for:** Complex queries requiring intent detection + slot extraction
```
POST /api/v1/query
{
  "query": "Update my profile with John Pass123",
  "generate_dataset": true
}
```

### 2. Search Endpoint (Direct)
**Best for:** Autocomplete, suggestions, known APIs
```
GET /api/v1/search/search?query=login&top_k=5
```

### 3. Template Management
**Best for:** Admin operations, adding new APIs
```
GET /api/v1/templates/          # List all
GET /api/v1/templates/login     # Get specific
POST /api/v1/templates/         # Create new
POST /api/v1/templates/sync     # Sync from JSON
```

---

## 📚 Related Documentation

- **[LLAMA_SETUP.md](./LLAMA_SETUP.md)** - Setup Llama 3.2 3B
- **[LLAMA_INTEGRATION.md](./LLAMA_INTEGRATION.md)** - Technical details
- **[BACKEND_COMPLETE_DOCUMENTATION.md](./BACKEND_COMPLETE_DOCUMENTATION.md)** - Full backend docs
- **[test_llama_extraction.py](./test_llama_extraction.py)** - Test suite

---

This is the **complete flow** of how NLPForge processes queries from Frontend to Backend and generates intelligent API responses! 🎉
