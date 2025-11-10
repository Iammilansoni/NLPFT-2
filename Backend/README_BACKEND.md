# NLPForge Backend - Intelligent API Testing SaaS Pipeline

## 🚀 Overview

A production-grade SaaS system that converts natural language queries into API test cases using advanced NLP, embeddings, and vector search. The system automatically detects API intents, extracts parameters, generates smart datasets, and performs semantic search using a **dual-database architecture**:

- **PostgreSQL** 🧠: Main brain for permanent storage (datasets, logs, metadata)
- **Redis** ⚡: Fast memory for vector embeddings and semantic search

## 🎯 Key Features

- **Natural Language Understanding**: Parse queries like "Authenticate my credentials for Milan and MS3ESD" → detect Login API
- **Hybrid NLP Approach**: Combines spaCy NER + Pattern Matching + Contextual Analysis
- **Smart Dataset Generation**: Automatically generates test datasets using Gemini API with edge cases
- **Vector Search**: Redis-based semantic search with BAAI/bge-small-en-v1.5 embeddings
- **Intelligent Deduplication**: SHA256 hashing prevents duplicate test cases
- **Incremental Dataset Growth**: Automatically enriches existing datasets without overwriting
- **Multi-API Support**: Handles Login, Signup, Update, Delete, Get, Reset Password APIs

## 🏗️ Architecture

```
Backend/
├── app/
│   ├── main.py                    # FastAPI application
│   ├── api/
│   │   └── v1/
│   │       ├── query.py          # Main query processing endpoint
│   │       ├── dataset.py        # Dataset management
│   │       └── search.py         # Search endpoints
│   ├── nlp/
│   │   ├── query_parser.py       # Intent & slot extraction
│   │   ├── embedding_manager.py  # Vector embeddings & Redis
│   │   └── smart_dataset_generator.py  # Dataset generation with Gemini
│   ├── core/
│   │   ├── config.py             # Configuration
│   │   ├── postgres.py           # PostgreSQL models & connection
│   │   └── logger.py             # Logging
│   ├── services/
│   │   └── postgres_service.py   # Database operations
│   └── models/
│       └── schemas.py            # Pydantic models
├── datasets/                      # Generated CSV datasets
├── storage/                       # Persistent storage
├── examples/
│   └── complete_workflow_test.py # Full pipeline demo
├── init_database.py              # Database initialization
├── docker-compose.yml            # Docker setup
└── requirements.txt              # Python dependencies
```

### Database Architecture

```
┌─────────────────────────────────────────┐
│         NLPForge Backend API             │
└─────────────────────────────────────────┘
                    │
    ┌───────────────┴────────────────┐
    │                                │
    ▼                                ▼
┌────────────────┐         ┌──────────────────┐
│ PostgreSQL 🧠  │         │    Redis ⚡      │
│  Main Brain    │         │  Fast Memory     │
├────────────────┤         ├──────────────────┤
│ • Datasets     │         │ • Embeddings     │
│ • Query Logs   │         │ • Vector Search  │
│ • Templates    │         │ • Cache          │
│ • Metadata     │         │ • Task Queues    │
└────────────────┘         └──────────────────┘
```

## 📋 Prerequisites

- Python 3.9+
- PostgreSQL 15+ (Main database)
- Redis Stack (Vector search support)
- Docker & Docker Compose (recommended)
- Gemini API Key (for dataset generation)

## 🔧 Installation

### 1. Clone the Repository

```bash
cd Backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Download spaCy Model

```bash
python -m spacy download en_core_web_md
```

### 5. Configure Environment

Create `.env` file:

```env
# PostgreSQL Configuration (Main Brain)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=nlpforge
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=nlpforge
DATABASE_URL=postgresql+asyncpg://nlpforge:your_secure_password@localhost:5432/nlpforge

# Redis Configuration (Fast Memory)
REDIS_HOST=localhost
REDIS_PORT=6379
INDEX_NAME=idx:api

# Embedding Model
MODEL_NAME=BAAI/bge-small-en-v1.5
SPACY_MODEL=en_core_web_md

# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# API Settings
TOP_K=5
BATCH_SIZE=32
CONFIDENCE_THRESHOLD=0.7
```

### 6. Start Services

#### Option A: Using Docker Compose (Recommended)

```bash
docker-compose up -d
```

This starts:
- FastAPI backend (port 8000)
- Redis Stack (port 6379, RedisInsight UI on 8001)
- PostgreSQL (port 5432)

#### Option B: Manual Setup

Start PostgreSQL:
```bash
docker run -d -p 5432:5432 -e POSTGRES_USER=nlpforge -e POSTGRES_PASSWORD=your_secure_password -e POSTGRES_DB=nlpforge postgres:15
```

Start Redis:
```bash
docker run -d -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
```

Initialize Database:
```bash
python init_database.py
```

Start API:
```bash
python -m app.main
```

## 🎮 Usage

### API Endpoint: `/api/v1/query`

The main endpoint that handles the complete pipeline.

#### Request

```json
POST /api/v1/query
{
  "query": "Authenticate my credentials for Milan and MS3ESD",
  "generate_dataset": true,
  "num_examples": 50,
  "top_k": 5
}
```

#### Response

```json
{
  "query": "Authenticate my credentials for Milan and MS3ESD",
  "intent": "login",
  "slots": {
    "username": "Milan",
    "password": "MS3ESD"
  },
  "confidence": 0.97,
  "best_matches": [
    {"api": "login", "score": 0.97, "confidence": 1.0},
    {"api": "signup", "score": 0.34, "confidence": 0.8}
  ],
  "dataset_generated": true,
  "dataset_info": {
    "intent": "login",
    "total_examples": 50,
    "base_examples": 10,
    "generated_examples": 40,
    "paths": {
      "csv": "datasets/login_dataset.csv",
      "json": "datasets/login_dataset_20250108_143022.json"
    },
    "redis_keys": 50
  },
  "search_results": [
    {
      "intent": "login",
      "slots": {"username": "milan", "password": "MS3ESD"},
      "query": "Login with milan and MS3ESD",
      "similarity": 0.97
    }
  ]
}
```

### Example: Python Client

```python
import requests

url = "http://localhost:8000/api/v1/query"
payload = {
    "query": "Create account for john with email john@test.com",
    "generate_dataset": True,
    "num_examples": 50
}

response = requests.post(url, json=payload)
result = response.json()

print(f"Intent: {result['intent']}")
print(f"Slots: {result['slots']}")
print(f"Confidence: {result['confidence']:.2%}")
```

### Run Complete Workflow Demo

```bash
python examples/complete_workflow_test.py
```

This will test multiple scenarios:
- Login authentication
- User signup
- Profile update
- Account deletion
- User retrieval
- Password reset

## 📊 API Endpoints

### Query Processing

- `POST /api/v1/query` - Process natural language query (main endpoint)
- `GET /api/v1/stats` - Get database statistics
- `POST /api/v1/reindex/{intent}` - Reindex specific API intent

### Dataset Management

- `POST /api/v1/dataset/upload` - Upload CSV dataset
- `POST /api/v1/dataset/generate` - Generate dataset from prompt
- `GET /api/v1/dataset/list` - List all datasets
- `GET /api/v1/dataset/download` - Download dataset

### Search

- `GET /api/v1/search/search` - Perform semantic search

### Health & Docs

- `GET /` - API information
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

## 🔍 How It Works

### 1. Query Parsing

The system uses a **hybrid approach** to extract intent and slots:

```python
# query_parser.py

# Pattern Matching
INTENT_PATTERNS = {
    "login": [r"\b(login|authenticate|signin)\b"],
    "signup": [r"\b(signup|register|create account)\b"]
}

# spaCy NER
doc = nlp("Authenticate Milan with password MS3ESD")
for ent in doc.ents:
    if ent.label_ == "PERSON":
        slots["username"] = ent.text

# Contextual Analysis
pattern = r"for\s+([a-zA-Z0-9_-]+)\s+and\s+([a-zA-Z0-9@#$%^&*!_-]+)"
```

### 2. Smart Dataset Generation

Generates diverse test cases using Gemini API:

```python
# smart_dataset_generator.py

# Base examples
base_examples = [
    "Login with {username} and {password}",
    "Authenticate credentials for {username} and {password}"
]

# Expand with Gemini
prompt = f"""
Generate 50 varied queries for {intent} API.
Include edge cases, negative tests, different phrasings.
"""
expanded = gemini.generate(prompt)
```

### 3. Vector Embeddings

Uses BAAI/bge-small-en-v1.5 for high-quality embeddings:

```python
# embedding_manager.py

# Generate embedding
model = SentenceTransformer("BAAI/bge-small-en-v1.5")
embedding = model.encode(query)

# Store in Redis with metadata
redis_client.hset(f"api:{hash_id}", mapping={
    "embedding": embedding.tobytes(),
    "intent": "login",
    "slots_json": json.dumps(slots),
    "hash_id": hash_id,
    "created_at": datetime.utcnow().isoformat()
})
```

### 4. Vector Search

Performs cosine similarity search in Redis:

```python
# embedding_manager.py

# KNN search with HNSW index
query = f"*=>[KNN {top_k} @embedding $vec AS score]"
results = redis_client.ft(index_name).search(query, {
    "vec": query_embedding.tobytes()
})

# Results are sorted by similarity
for doc in results.docs:
    similarity = 1 - float(doc.score)  # Convert distance to similarity
```

## 🎨 Dataset Reuse Policy

The system intelligently manages datasets:

### ✅ When to Reuse

- **Same API, Multiple Users**: If 5 users ask about Login API, reuse the same dataset
- **Existing Embeddings**: If Redis has >10 embeddings for an intent, skip generation
- **Incremental Growth**: Add new variations to existing datasets

### 🔄 When to Generate

- **New API**: First time an intent is encountered
- **Low Coverage**: Less than 10 embeddings exist
- **Explicit Request**: User requests dataset generation

### 📈 Smart Enrichment

```python
# Load existing
existing_df = pd.read_csv("login_dataset.csv")

# Generate new
new_examples = generate_dataset(intent="login", num=20)

# Merge (deduplicate by query)
merged_df = pd.concat([existing_df, new_df])
merged_df = merged_df.drop_duplicates(subset=['query'])

# Save
merged_df.to_csv("login_dataset.csv")
```

## 🧪 Testing

### Run Unit Tests

```bash
pytest tests/
```

### Test Individual Components

```python
# Test query parser
from app.nlp.query_parser import parse_query

result = parse_query("Login with milan and password123")
print(result)
# Output: {'intent': 'login', 'slots': {'username': 'milan', 'password': 'password123'}}

# Test embeddings
from app.nlp.embedding_manager import get_embedding_manager

embedder = get_embedding_manager()
embedder.upsert_embedding(
    query="Login with test user",
    intent="login",
    slots={"username": "test"}
)

# Test search
results = embedder.search("Authenticate test user", top_k=5)
print(results)
```

## 📦 Docker Deployment

Build and deploy with Docker:

```bash
# Build image
docker build -t nlpforge-backend .

# Run container
docker run -d -p 8000:8000 \
  -e REDIS_HOST=redis \
  -e POSTGRES_HOST=postgres \
  -e POSTGRES_USER=nlpforge \
  -e POSTGRES_PASSWORD=your_secure_password \
  -e POSTGRES_DB=nlpforge \
  --name nlpforge-api \
  nlpforge-backend

# Or use docker-compose (recommended)
docker-compose up -d
```

## 🔐 Security

- API keys stored in `.env` (never commit)
- Redis password authentication
- Input validation with Pydantic
- Rate limiting (configure in production)

## 📈 Performance

- **Embedding Speed**: ~100 queries/second (batch mode)
- **Search Latency**: <50ms for top-5 results
- **Redis HNSW Index**: O(log N) search complexity
- **Dataset Generation**: ~30 seconds for 50 examples (with Gemini)

## 🐛 Troubleshooting

### Redis Connection Error

```bash
# Check Redis is running
redis-cli ping
# Should return: PONG

# Check port
netstat -an | findstr 6379
```

### spaCy Model Not Found

```bash
python -m spacy download en_core_web_md
```

### Gemini API Error

- Check API key in `.env`
- Verify quota at https://makersuite.google.com/

### Docker Issues

```bash
# Check logs
docker-compose logs -f nlpforge-api

# Restart services
docker-compose restart

# Rebuild
docker-compose up -d --build
```

## 🚀 Production Deployment

### Environment Variables

```env
ENVIRONMENT=production
DEBUG=False
WORKERS=4

# PostgreSQL (with connection pooling)
POSTGRES_POOL_SIZE=10
POSTGRES_MAX_OVERFLOW=20

# Redis
REDIS_PASSWORD=your_redis_password
```

### Scale with Docker

```bash
docker-compose up -d --scale nlpforge-api=3
```

### Database Backups

```bash
# PostgreSQL backup
docker exec nlpforge-postgres pg_dump -U nlpforge nlpforge > backup.sql

# Restore
docker exec -i nlpforge-postgres psql -U nlpforge nlpforge < backup.sql
```

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **RedisInsight**: http://localhost:8001

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is proprietary software for Bangalore-based company.

## 🙏 Acknowledgments

- **spaCy**: NLP library for entity recognition
- **Sentence Transformers**: Embedding models
- **PostgreSQL**: Reliable ACID-compliant database
- **Redis Stack**: Vector database and caching
- **Google Gemini**: Dataset generation
- **FastAPI**: High-performance API framework

---

Built with ❤️ for intelligent API testing
