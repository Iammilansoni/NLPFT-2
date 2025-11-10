# 🚀 NLPForge Backend - Complete Documentation

> **AI-Powered API Testing Platform**  
> Transform natural language into intelligent API test cases using NLP, Vector Embeddings, and Semantic Search

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Database Design](#database-design)
5. [File Structure](#file-structure)
6. [Core Components](#core-components)
7. [API Endpoints](#api-endpoints)
8. [Configuration](#configuration)
9. [Installation & Setup](#installation--setup)
10. [Docker Deployment](#docker-deployment)
11. [Data Flow](#data-flow)
12. [Performance](#performance)
13. [Security](#security)
14. [Monitoring](#monitoring)
15. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

NLPForge Backend is a production-grade SaaS system that converts natural language queries into executable API test cases. It combines advanced NLP, machine learning, and vector search to provide intelligent API testing automation.

### Key Capabilities

✅ **Natural Language Processing**
- Parse queries like *"Authenticate user Milan with password MS3ESD"*
- Automatically detect API intent (login, signup, update, delete, etc.)
- Extract parameters using hybrid NLP (spaCy NER + Pattern Matching + Context Analysis)

✅ **Smart Dataset Generation**
- Auto-generate 50-200 test case variations using Google Gemini AI
- Include positive tests, edge cases, boundary conditions, and negative tests
- Incremental dataset enrichment without duplication

✅ **Semantic Search**
- Vector embeddings using BAAI/bge-small-en-v1.5 (384-dimensional)
- Redis-based vector search with HNSW indexing
- Sub-50ms search latency for top-K results
- Cosine similarity scoring

✅ **Dual-Database Architecture**
- **PostgreSQL**: Permanent storage (datasets, logs, metadata, templates)
- **Redis Stack**: Fast in-memory operations (vector embeddings, search, cache)

✅ **Template System**
- Customizable API definitions
- Hot-reload without server restart
- JSON-based configuration
- Version control support

---

## 🏗️ Architecture

### System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                        │
│  • Dashboard • Query Input • Search • Templates • Datasets   │
└──────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST API
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                  NLPForge Backend (FastAPI)                   │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐     │
│  │  Query API  │  │  Search API  │  │  Dataset API   │     │
│  └─────────────┘  └──────────────┘  └────────────────┘     │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Core Services Layer                     │    │
│  │  • Query Parser  • Embedding Manager                │    │
│  │  • Dataset Generator  • Template Service            │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
                    │                      │
        ┌───────────┴──────────┐  ┌───────┴────────────┐
        │                      │  │                     │
        ▼                      ▼  ▼                     ▼
┌──────────────────┐    ┌──────────────────┐   ┌──────────────┐
│  PostgreSQL 🧠   │    │   Redis Stack ⚡  │   │  Gemini AI   │
│  Main Brain      │    │   Fast Memory    │   │  Generator   │
├──────────────────┤    ├──────────────────┤   └──────────────┘
│ • Datasets       │    │ • Embeddings     │
│ • Query Logs     │    │ • Vector Index   │
│ • Templates      │    │ • Search Cache   │
│ • Metadata       │    │ • Session Data   │
└──────────────────┘    └──────────────────┘
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
│ • Templates    │         │ • HNSW Index     │
│ • Metadata     │         │ • Cache Layer    │
│ • Examples     │         │ • Pub/Sub        │
└────────────────┘         └──────────────────┘
  Permanent Storage          Ultra-Fast Ops
  ACID Compliance           < 50ms Latency
```

---

## 💻 Technology Stack

### Backend Framework
- **FastAPI** `0.104.1` - High-performance async Python web framework
- **Uvicorn** `0.24.0` - Lightning-fast ASGI server
- **Pydantic** `2.5.0` - Data validation using Python type annotations

### Databases
- **PostgreSQL** `15+` - Primary ACID-compliant relational database
- **asyncpg** `0.29.0` - Async PostgreSQL driver for Python
- **SQLAlchemy** `2.0.23` - SQL toolkit and ORM
- **Alembic** `1.13.0` - Database migration tool

- **Redis Stack** `latest` - In-memory data store with vector search
- **redis-py** `5.0.1` - Official Python Redis client
- **RediSearch** - Vector search module (included in Redis Stack)

### NLP & Machine Learning
- **spaCy** `3.7.2` - Industrial-strength NLP library
  - Model: `en_core_web_md` (English medium model)
  - Used for: Named Entity Recognition (NER), POS tagging
  
- **Sentence Transformers** `2.2.2` - State-of-the-art sentence embeddings
  - Model: `BAAI/bge-small-en-v1.5` (384-dimensional embeddings)
  - Used for: Semantic similarity, vector search
  
- **Google Gemini** `0.3.0` - Generative AI for dataset creation
  - API: `google-generativeai`
  - Used for: Test case generation, variations

- **PyTorch** `2.1.1` - Deep learning framework (backend for transformers)
- **Transformers** `4.35.2` - HuggingFace transformers library
- **NumPy** `1.24.3` - Numerical computing
- **Pandas** `2.0.3` - Data manipulation and analysis
- **scikit-learn** `1.3.2` - Machine learning utilities

### Utilities
- **python-dotenv** `1.0.0` - Environment variable management
- **python-multipart** `0.0.6` - Multipart form data parser (file uploads)
- **aiofiles** `23.2.1` - Async file operations
- **tqdm** `4.66.1` - Progress bars
- **rapidfuzz** `3.5.2` - Fast fuzzy string matching
- **psutil** `5.9.6` - System monitoring

### Development Tools
- **pytest** `7.4.3` - Testing framework
- **pytest-asyncio** `0.21.1` - Async test support
- **httpx** `0.25.2` - HTTP client for testing

### Containerization
- **Docker** - Container platform
- **Docker Compose** - Multi-container orchestration

---

## 🗄️ Database Design

### PostgreSQL Schema

#### 1. **datasets** Table
```sql
CREATE TABLE datasets (
    id SERIAL PRIMARY KEY,
    intent VARCHAR(50) NOT NULL,
    api_name VARCHAR(100) NOT NULL,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    total_examples INTEGER DEFAULT 0,
    csv_path VARCHAR(500),
    json_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB,
    
    INDEX idx_intent (intent),
    INDEX idx_created_at (created_at),
    INDEX idx_active (is_active)
);
```

**Purpose**: Track all generated datasets with metadata
**Example Row**:
```json
{
  "id": 1,
  "intent": "login",
  "api_name": "User Authentication",
  "endpoint": "/api/v1/auth/login",
  "method": "POST",
  "total_examples": 127,
  "csv_path": "datasets/login_dataset.csv",
  "json_path": "datasets/login_dataset_20250109.json",
  "version": 3,
  "is_active": true
}
```

#### 2. **query_logs** Table
```sql
CREATE TABLE query_logs (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    intent VARCHAR(50),
    slots JSONB,
    confidence FLOAT,
    best_match_api VARCHAR(100),
    best_match_score FLOAT,
    dataset_generated BOOLEAN DEFAULT FALSE,
    processing_time_ms FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    user_id VARCHAR(100),
    session_id VARCHAR(100),
    metadata JSONB,
    
    INDEX idx_intent (intent),
    INDEX idx_created_at (created_at),
    INDEX idx_user (user_id),
    INDEX idx_session (session_id)
);
```

**Purpose**: Complete audit trail of all query processing
**Example Row**:
```json
{
  "id": 1,
  "query": "Authenticate user Milan with password MS3ESD",
  "intent": "login",
  "slots": {"username": "Milan", "password": "MS3ESD"},
  "confidence": 0.97,
  "best_match_api": "login",
  "best_match_score": 0.97,
  "dataset_generated": true,
  "processing_time_ms": 245.3,
  "user_id": "user_123",
  "session_id": "sess_abc"
}
```

#### 3. **api_templates** Table
```sql
CREATE TABLE api_templates (
    id SERIAL PRIMARY KEY,
    intent VARCHAR(50) UNIQUE NOT NULL,
    api_name VARCHAR(100) NOT NULL,
    description TEXT,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    fields JSONB NOT NULL,
    example_queries JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_system BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    
    INDEX idx_intent (intent),
    INDEX idx_system (is_system)
);
```

**Purpose**: Define customizable API templates
**Example Row**:
```json
{
  "id": 1,
  "intent": "login",
  "api_name": "User Login",
  "description": "Authenticate user credentials",
  "endpoint": "/api/v1/auth/login",
  "method": "POST",
  "fields": {
    "username": {"type": "string", "required": true},
    "password": {"type": "string", "required": true}
  },
  "example_queries": [
    "Login with username and password",
    "Authenticate user credentials"
  ],
  "is_system": true
}
```

#### 4. **embedding_metadata** Table
```sql
CREATE TABLE embedding_metadata (
    id SERIAL PRIMARY KEY,
    redis_key VARCHAR(100) UNIQUE NOT NULL,
    hash_id VARCHAR(64) UNIQUE NOT NULL,
    query TEXT NOT NULL,
    intent VARCHAR(50) NOT NULL,
    dataset_id INTEGER REFERENCES datasets(id),
    created_at TIMESTAMP DEFAULT NOW(),
    last_accessed TIMESTAMP DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    metadata JSONB,
    
    INDEX idx_redis_key (redis_key),
    INDEX idx_hash_id (hash_id),
    INDEX idx_intent (intent)
);
```

**Purpose**: Link PostgreSQL records to Redis embeddings
**Example Row**:
```json
{
  "id": 1,
  "redis_key": "api:a3b5c7d9e1f2",
  "hash_id": "a3b5c7d9e1f23456789abcdef0123456",
  "query": "Login with milan and password123",
  "intent": "login",
  "dataset_id": 1,
  "access_count": 15
}
```

#### 5. **dataset_examples** Table
```sql
CREATE TABLE dataset_examples (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER NOT NULL REFERENCES datasets(id),
    query TEXT NOT NULL,
    intent VARCHAR(50) NOT NULL,
    slots JSONB,
    api_name VARCHAR(100),
    endpoint VARCHAR(255),
    method VARCHAR(10),
    hash_id VARCHAR(64) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    is_embedded BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    
    INDEX idx_dataset (dataset_id),
    INDEX idx_intent (intent),
    INDEX idx_hash (hash_id),
    INDEX idx_embedded (is_embedded)
);
```

**Purpose**: Store individual test case examples (Redis backup)

### Redis Data Structures

#### 1. Vector Embeddings (Hash)
```
Key: api:<hash_id>
Type: HASH
Fields:
  embedding: bytes        # 384-dim float32 vector (1536 bytes)
  intent: string         # "login", "signup", etc.
  slots_json: string     # JSON: {"username": "milan", ...}
  query: string          # Original query text
  hash_id: string        # SHA256 hash
  api_name: string       # Template name
  endpoint: string       # API endpoint URL
  template_version: int  # Template version
  created_at: string     # ISO timestamp
  confidence: float      # Extraction confidence
```

**Example**:
```redis
HGETALL api:a3b5c7d9e1f2
1) "embedding"
2) <binary data: 1536 bytes>
3) "intent"
4) "login"
5) "slots_json"
6) "{\"username\":\"milan\",\"password\":\"test123\"}"
7) "query"
8) "Login with milan and test123"
9) "hash_id"
10) "a3b5c7d9e1f23456789abcdef0123456"
```

#### 2. Vector Index (HNSW)
```
Index Name: idx:api
Type: HNSW (Hierarchical Navigable Small World)
Algorithm: Cosine Similarity
Dimension: 384
Distance Metric: COSINE
M: 16              # Max edges per node
EF_Construction: 200  # Construction time accuracy
EF_Runtime: 10     # Query time accuracy
```

**Search Query**:
```redis
FT.SEARCH idx:api "*=>[KNN 5 @embedding $vec AS score]" 
  PARAMS 2 vec <query_embedding_bytes>
  RETURN 3 query intent score
  SORTBY score ASC
  DIALECT 2
```

---

## 📁 File Structure

```
Backend/
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI application entry
│   ├── redis_config.py                  # Redis configuration
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── query.py                 # Query processing endpoints
│   │       ├── dataset.py               # Dataset management endpoints
│   │       ├── search.py                # Semantic search endpoints
│   │       └── templates.py             # Template CRUD endpoints
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                    # Configuration management
│   │   ├── logger.py                    # Logging configuration
│   │   └── postgres.py                  # PostgreSQL connection & models
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py                   # Pydantic models (request/response)
│   │
│   ├── nlp/
│   │   ├── __init__.py
│   │   ├── query_parser.py              # Intent & slot extraction
│   │   ├── embedding_manager.py         # Vector embeddings & Redis
│   │   ├── embedding_model.py           # Sentence transformer wrapper
│   │   ├── semantic_search_service.py   # Search service
│   │   └── smart_dataset_generator.py   # AI dataset generation
│   │
│   └── services/
│       ├── __init__.py
│       ├── dataset_service.py           # Dataset operations
│       ├── embedding_service.py         # Embedding operations
│       ├── template_loader.py           # Template loading
│       └── template_service.py          # Template management
│
├── datasets/                            # Generated CSV datasets
│   ├── login_dataset.csv
│   ├── signup_dataset.csv
│   └── ...
│
├── storage/                             # Persistent storage
│   └── embeddings/
│
├── examples/
│   ├── complete_workflow.py             # Usage examples
│   └── complete_workflow_test.py        # Full pipeline test
│
├── tests/                               # Unit tests
│   ├── test_query_parser.py
│   ├── test_embeddings.py
│   └── ...
│
├── .env                                 # Environment variables (not in git)
├── .env.example                         # Example environment config
├── .gitignore
├── requirements.txt                     # Python dependencies
├── Dockerfile                           # Docker image definition
├── docker-compose.yml                   # Multi-container setup
├── init_database.py                     # Database initialization script
├── api_template.json                    # API template definitions
├── README_BACKEND.md                    # Backend documentation
├── ARCHITECTURE_POSTGRES_REDIS.md       # Architecture documentation
└── QUICKSTART.md                        # Quick start guide
```

---

## 🧩 Core Components

### 1. Query Parser (`app/nlp/query_parser.py`)

**Purpose**: Extract intent and parameters from natural language queries

**Approach**: Hybrid NLP combining:
- **Pattern Matching**: Regex patterns for intent detection
- **spaCy NER**: Named Entity Recognition for parameter extraction
- **Contextual Analysis**: Token-based context analysis

**Example**:
```python
from app.nlp.query_parser import QueryParser

parser = QueryParser()
result = parser.parse("Authenticate user Milan with password MS3ESD")

# Output:
{
    "intent": "login",
    "slots": {
        "username": "Milan",
        "password": "MS3ESD"
    },
    "confidence": 0.97
}
```

**Intent Patterns**:
```python
INTENT_PATTERNS = {
    "login": [
        r"\b(login|authenticate|signin|sign in|auth)\b",
        r"\b(credentials|password|username)\b"
    ],
    "signup": [
        r"\b(signup|register|create account|join|sign up)\b"
    ],
    "update": [
        r"\b(update|edit|modify|change)\b.*\b(profile|user|account|info)\b"
    ],
    "delete": [
        r"\b(delete|remove|deactivate)\b.*\b(account|user|profile)\b"
    ],
    # ... more patterns
}
```

### 2. Embedding Manager (`app/nlp/embedding_manager.py`)

**Purpose**: Generate and manage vector embeddings in Redis

**Model**: BAAI/bge-small-en-v1.5 (384-dimensional)

**Key Operations**:
```python
from app.nlp.embedding_manager import EmbeddingManager

embedder = EmbeddingManager()

# Generate embedding
embedding = await embedder.get_embedding("Login with test user")
# Returns: np.array([0.123, -0.456, ..., 0.789])  # 384 floats

# Store in Redis
await embedder.upsert_embedding(
    query="Login with test user",
    intent="login",
    slots={"username": "test"}
)

# Search similar queries
results = await embedder.search(
    query="Authenticate test user",
    top_k=5
)
# Returns top 5 most similar queries with scores
```

**Performance**:
- Embedding generation: ~10-20ms per query
- Batch embedding: ~100 queries/second
- Vector search: <50ms for top-5 results

### 3. Smart Dataset Generator (`app/nlp/smart_dataset_generator.py`)

**Purpose**: Generate diverse test datasets using Google Gemini AI

**Features**:
- Generates 10-200 test case variations
- Includes positive tests, edge cases, boundary tests, negative tests
- Uses SHA256 hashing for deduplication
- Incremental dataset enrichment
- CSV and JSON export

**Example**:
```python
from app.nlp.smart_dataset_generator import SmartDatasetGenerator

generator = SmartDatasetGenerator()

# Generate 50 test cases
dataset = await generator.generate_dataset(
    intent="login",
    seed_prompt="Generate login test cases",
    num_examples=50,
    api_name="User Login",
    endpoint="/api/v1/auth/login"
)

# Output:
{
    "intent": "login",
    "total_examples": 50,
    "paths": {
        "csv": "datasets/login_dataset.csv",
        "json": "datasets/login_20250109_143022.json"
    },
    "embedded_count": 50
}
```

**Generated Test Case Types**:
1. **Positive Tests** (40%): Valid inputs, happy path scenarios
2. **Boundary Tests** (20%): Edge cases, min/max values
3. **Negative Tests** (20%): Invalid inputs, missing fields
4. **Security Tests** (10%): SQL injection, XSS, special characters
5. **Performance Tests** (10%): Large payloads, stress scenarios

### 4. Template Service (`app/services/template_service.py`)

**Purpose**: Manage API template definitions

**Features**:
- Load templates from JSON or database
- Hot-reload without server restart
- CRUD operations via API
- Template versioning
- Sync with external sources

**Example Template**:
```json
{
  "intent": "login",
  "api_name": "User Login",
  "description": "Authenticate user credentials",
  "endpoint": "/api/v1/auth/login",
  "method": "POST",
  "intent_keywords": ["login", "authenticate", "signin", "auth"],
  "parameters": [
    {
      "name": "username",
      "type": "string",
      "required": true,
      "description": "Username or email"
    },
    {
      "name": "password",
      "type": "string",
      "required": true,
      "description": "User password"
    }
  ],
  "example_queries": [
    "Login with {username} and {password}",
    "Authenticate user {username}",
    "Sign in as {username}"
  ],
  "response_format": {
    "token": "string",
    "user_id": "string",
    "expires_at": "timestamp"
  }
}
```

---

## 🌐 API Endpoints

### Query Processing (`/api/v1/query`)

#### 1. **POST /api/v1/query** - Process Natural Language Query
Main endpoint for query processing pipeline.

**Request**:
```json
{
  "query": "Authenticate user Milan with password MS3ESD",
  "generate_dataset": true,
  "num_examples": 50,
  "top_k": 5
}
```

**Response**:
```json
{
  "query": "Authenticate user Milan with password MS3ESD",
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
    "num_variations": 10,
    "total_examples": 127,
    "paths": {
      "csv": "datasets/login_dataset.csv",
      "json": "datasets/login_dataset_20250109.json"
    },
    "redis_keys": 127
  },
  "search_results": [
    {
      "query": "Login with milan and MS3ESD",
      "intent": "login",
      "slots": {"username": "milan", "password": "MS3ESD"},
      "similarity": 0.97,
      "api_name": "User Login",
      "endpoint": "/api/v1/auth/login",
      "confidence": 0.99
    }
  ]
}
```

#### 2. **GET /api/v1/stats** - Get Database Statistics

**Response**:
```json
{
  "total_vectors": 1247,
  "intents": {
    "login": 234,
    "signup": 189,
    "update": 156,
    "delete": 98,
    "get_user": 203
  },
  "datasets_count": 8,
  "query_logs_count": 3421,
  "templates_count": 12
}
```

#### 3. **POST /api/v1/reindex/{intent}** - Reindex Intent Embeddings

Regenerate and re-embed all examples for a specific intent.

**Response**:
```json
{
  "message": "Reindexed login intent",
  "deleted": 234,
  "generated": 250,
  "embedded": 250
}
```

### Template Management (`/api/v1/templates`)

#### 4. **GET /api/v1/templates/** - List All Templates

**Response**:
```json
[
  {
    "api_name": "login",
    "description": "User authentication",
    "endpoint": "/api/v1/auth/login",
    "method": "POST",
    "intent_keywords": ["login", "authenticate", "signin"],
    "parameters": [...],
    "example_queries": [...]
  },
  // ... more templates
]
```

#### 5. **GET /api/v1/templates/{intent}** - Get Specific Template

**Response**: Single template object

#### 6. **POST /api/v1/templates/** - Create New Template

**Request**: Template object (see Template Service section)
**Response**: Created template with ID

#### 7. **PUT /api/v1/templates/{intent}** - Update Template

**Request**: Partial or full template object
**Response**: Updated template

#### 8. **DELETE /api/v1/templates/{intent}** - Delete Template

**Response**:
```json
{
  "message": "Template deleted successfully",
  "intent": "custom_api"
}
```

#### 9. **POST /api/v1/templates/sync** - Sync from JSON File

Sync templates from `api_template.json` file.

**Response**:
```json
{
  "success": true,
  "message": "Synced templates",
  "added": 3,
  "updated": 2,
  "total": 12
}
```

#### 10. **POST /api/v1/templates/reload** - Hot Reload

Reload all templates without server restart.

**Response**:
```json
{
  "success": true,
  "message": "Services reloaded",
  "services_reloaded": ["TemplateService", "QueryParser"],
  "templates_count": 12
}
```

#### 11. **GET /api/v1/templates/stats** - Template Statistics

**Response**:
```json
{
  "total_templates": 12,
  "template_names": ["login", "signup", "update", ...],
  "cache_stats": {
    "intents": 12,
    "examples": 847
  }
}
```

### Dataset Management (`/api/v1/dataset`)

#### 12. **POST /api/v1/dataset/upload** - Upload CSV Dataset

**Request**: Multipart form data with CSV file
**Response**:
```json
{
  "message": "Dataset uploaded successfully",
  "file": "custom_dataset.csv",
  "rows": 150,
  "embedded": true
}
```

#### 13. **POST /api/v1/dataset/generate** - Generate Dataset

**Request**:
```json
{
  "seed_prompt": "Generate login test cases with edge cases",
  "examples": 50,
  "api_name": "login",
  "endpoint": "/api/v1/auth/login"
}
```

**Response**:
```json
{
  "message": "Dataset generated",
  "csv_path": "datasets/login_dataset.csv",
  "ingestion": {
    "success": true,
    "count": 50
  }
}
```

#### 14. **GET /api/v1/dataset/list** - List All Datasets

**Response**:
```json
{
  "datasets": [
    "login_dataset.csv",
    "signup_dataset.csv",
    "update_profile_dataset.csv"
  ]
}
```

#### 15. **GET /api/v1/dataset/download?filename={name}** - Download Dataset

**Response**: File download (CSV format)

### Semantic Search (`/api/v1/search`)

#### 16. **GET /api/v1/search/search?query={query}&top_k={k}** - Vector Search

**Parameters**:
- `query`: Search query string
- `top_k`: Number of results (default: 5, max: 20)

**Response**:
```json
{
  "input_query": "Authenticate user",
  "top_k": 5,
  "results": [
    {
      "query": "Login with username and password",
      "api": "login",
      "endpoint": "/api/v1/auth/login",
      "request": {
        "username": "test",
        "password": "pass123"
      },
      "response": {
        "token": "abc123",
        "user_id": "user_456"
      },
      "cosine_distance": 0.03,
      "cosine_similarity": 0.97
    },
    // ... 4 more results
  ]
}
```

---

## ⚙️ Configuration

### Environment Variables (`.env`)

```env
# ============================================
# APPLICATION SETTINGS
# ============================================
APP_NAME=NLPForge Backend API
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=True
HOST=0.0.0.0
PORT=8000
WORKERS=4
LOG_LEVEL=INFO

# ============================================
# POSTGRESQL CONFIGURATION (Main Brain 🧠)
# ============================================
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=nlpforge
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=nlpforge
DATABASE_URL=postgresql+asyncpg://nlpforge:your_secure_password_here@localhost:5432/nlpforge

# Connection Pool
POSTGRES_POOL_SIZE=10
POSTGRES_MAX_OVERFLOW=20

# ============================================
# REDIS CONFIGURATION (Fast Memory ⚡)
# ============================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
INDEX_NAME=idx:api

# Redis Connection Pool
REDIS_POOL_SIZE=10
REDIS_MAX_CONNECTIONS=50

# ============================================
# NLP MODELS
# ============================================
# Sentence Transformer Model
MODEL_NAME=BAAI/bge-small-en-v1.5
EMBEDDING_DIM=384

# spaCy Model
SPACY_MODEL=en_core_web_md

# ============================================
# GEMINI AI (Dataset Generation)
# ============================================
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-pro
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=2048

# ============================================
# API SETTINGS
# ============================================
TOP_K=5                      # Default search results
BATCH_SIZE=32                # Embedding batch size
CONFIDENCE_THRESHOLD=0.7     # Minimum confidence for intent
MAX_EXAMPLES=200             # Max dataset examples
MIN_EXAMPLES=10              # Min dataset examples

# ============================================
# SECURITY
# ============================================
SECRET_KEY=your_secret_key_change_in_production
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# ============================================
# STORAGE
# ============================================
STORAGE_PATH=./storage
DATASETS_PATH=./datasets
UPLOAD_MAX_SIZE=10485760     # 10MB in bytes

# ============================================
# MONITORING
# ============================================
ENABLE_METRICS=True
METRICS_PORT=9090
```

---

## 🚀 Installation & Setup

### Prerequisites

- **Python**: 3.9+ (recommended: 3.11)
- **PostgreSQL**: 15+ 
- **Redis Stack**: Latest (includes RediSearch)
- **Docker & Docker Compose**: Latest (optional but recommended)
- **Git**: For version control

### Method 1: Docker Compose (Recommended)

**Step 1**: Clone repository
```bash
cd Backend
```

**Step 2**: Create `.env` file
```bash
cp .env.example .env
# Edit .env with your configuration
```

**Step 3**: Start all services
```bash
docker-compose up -d
```

This will start:
- **nlpforge-api**: FastAPI backend (port 8000)
- **postgres**: PostgreSQL database (port 5432)
- **redis**: Redis Stack (port 6379, RedisInsight UI on 8001)

**Step 4**: Check status
```bash
docker-compose ps
docker-compose logs -f nlpforge-api
```

**Step 5**: Access services
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- RedisInsight: http://localhost:8001

### Method 2: Manual Installation

**Step 1**: Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

**Step 2**: Install dependencies
```bash
pip install -r requirements.txt
```

**Step 3**: Download spaCy model
```bash
python -m spacy download en_core_web_md
```

**Step 4**: Start PostgreSQL
```bash
docker run -d \
  -p 5432:5432 \
  -e POSTGRES_USER=nlpforge \
  -e POSTGRES_PASSWORD=your_secure_password \
  -e POSTGRES_DB=nlpforge \
  --name nlpforge-postgres \
  postgres:15-alpine
```

**Step 5**: Start Redis Stack
```bash
docker run -d \
  -p 6379:6379 \
  -p 8001:8001 \
  --name nlpforge-redis \
  redis/redis-stack:latest
```

**Step 6**: Initialize database
```bash
python init_database.py
```

**Step 7**: Start API
```bash
# Development (with hot reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production (multiple workers)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🐳 Docker Deployment

### Docker Compose Configuration

```yaml
version: '3.8'

services:
  nlpforge-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - POSTGRES_HOST=postgres
      - REDIS_HOST=redis
      # ... more env vars
    volumes:
      - ./storage:/app/storage
      - ./datasets:/app/datasets
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=nlpforge
      - POSTGRES_PASSWORD=nlpforge_password
      - POSTGRES_DB=nlpforge
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U nlpforge"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis/redis-stack:latest
    ports:
      - "6379:6379"
      - "8001:8001"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU-only
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_md

# Copy application
COPY app/ ./app/

# Create directories
RUN mkdir -p /app/storage /app/datasets

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Commands

```bash
# Build image
docker build -t nlpforge-backend:latest .

# Run single container
docker run -d \
  -p 8000:8000 \
  -e POSTGRES_HOST=host.docker.internal \
  -e REDIS_HOST=host.docker.internal \
  --name nlpforge-api \
  nlpforge-backend:latest

# View logs
docker logs -f nlpforge-api

# Execute commands in container
docker exec -it nlpforge-api python -c "print('Hello')"

# Stop and remove
docker stop nlpforge-api
docker rm nlpforge-api

# Docker Compose commands
docker-compose up -d              # Start all services
docker-compose down               # Stop all services
docker-compose logs -f api        # Follow API logs
docker-compose ps                 # List services
docker-compose restart api        # Restart API service
docker-compose build --no-cache   # Rebuild images
```

---

## 🔄 Data Flow

### Complete Query Processing Flow

```
1. USER QUERY
   ↓
   "Authenticate user Milan with password MS3ESD"
   
2. QUERY PARSER (NLP)
   ↓
   • Pattern matching: Detect "authenticate" → login intent
   • spaCy NER: Extract "Milan" (PERSON) → username
   • Context analysis: Extract "MS3ESD" after "password" → password
   ↓
   {intent: "login", slots: {username: "Milan", password: "MS3ESD"}}
   
3. TEMPLATE LOOKUP
   ↓
   • Query template_service for "login" intent
   • Get API definition (endpoint, method, fields)
   ↓
   Template: {endpoint: "/api/v1/auth/login", method: "POST"}
   
4. DATASET CHECK (PostgreSQL)
   ↓
   • Query datasets table: SELECT * WHERE intent='login'
   • Check if dataset exists and is recent
   ↓
   Dataset exists: login_dataset.csv (127 examples)
   
5. EMBEDDING COUNT (Redis)
   ↓
   • Count embeddings: FT.SEARCH idx:api "@intent:login"
   • If count < 10: Generate new dataset
   • If count >= 10: Skip generation (reuse existing)
   ↓
   Count: 127 embeddings → Skip generation
   
6. VECTOR EMBEDDING
   ↓
   • Generate embedding for query using BAAI/bge-small-en-v1.5
   • 384-dimensional float32 vector
   ↓
   Embedding: [0.123, -0.456, ..., 0.789] (384 dims)
   
7. VECTOR SEARCH (Redis HNSW)
   ↓
   • KNN search with cosine similarity
   • Return top-K most similar queries
   • Query time: ~25ms
   ↓
   Top 5 results with similarity scores
   
8. LOG TO POSTGRESQL
   ↓
   • INSERT INTO query_logs (query, intent, slots, confidence, ...)
   • Track for analytics and improvements
   ↓
   Log ID: 3422
   
9. RESPONSE
   ↓
   Return complete results to user
```

### Dataset Generation Flow (when needed)

```
1. TRIGGER: New intent or low embedding count
   
2. GEMINI AI PROMPT
   ↓
   Generate 50 diverse test cases for login API:
   - Positive tests (happy path)
   - Edge cases (empty, special chars)
   - Negative tests (invalid inputs)
   - Security tests (SQL injection, XSS)
   
3. AI GENERATION
   ↓
   Gemini generates 50 variations in JSON format
   
4. DEDUPLICATION
   ↓
   • SHA256 hash each query
   • Remove duplicates
   • Keep unique examples only
   
5. SAVE TO POSTGRESQL
   ↓
   • INSERT INTO datasets (intent, total_examples, paths, ...)
   • INSERT INTO dataset_examples (query, intent, slots, ...)
   
6. SAVE TO FILES
   ↓
   • CSV: datasets/login_dataset.csv
   • JSON: datasets/login_dataset_20250109_143022.json
   
7. GENERATE EMBEDDINGS
   ↓
   • Batch encode all queries
   • 384-dim vectors for each
   
8. STORE IN REDIS
   ↓
   • HSET api:<hash_id> embedding <bytes> intent login ...
   • Add to vector index for search
   
9. UPDATE METADATA
   ↓
   • INSERT INTO embedding_metadata (redis_key, hash_id, ...)
   • Link PostgreSQL ↔ Redis
```

---

## ⚡ Performance

### Benchmarks

| Operation | Latency | Throughput | Notes |
|-----------|---------|------------|-------|
| **Query Parsing** | 5-10ms | 100-200 req/s | spaCy NER + patterns |
| **Single Embedding** | 10-20ms | 50-100 req/s | BAAI/bge-small-en-v1.5 |
| **Batch Embedding (32)** | 200-300ms | ~100 queries/s | GPU: 500+ queries/s |
| **Vector Search (top-5)** | 10-50ms | 200-500 req/s | Redis HNSW index |
| **PostgreSQL Insert** | 2-5ms | 200-500 req/s | Single row |
| **PostgreSQL Query** | 5-15ms | 100-200 req/s | With indexes |
| **Dataset Generation** | 30-60s | - | 50 examples via Gemini |
| **Complete Pipeline** | 200-500ms | 20-50 req/s | Full query processing |

### Scaling Strategies

#### Vertical Scaling
```
Single Server:
- CPU: 8+ cores for parallel processing
- RAM: 16GB+ (spaCy models, embeddings cache)
- GPU: Optional (10x faster embeddings)
- SSD: For faster database I/O
```

#### Horizontal Scaling
```
Load Balancer
    ↓
┌────────┬────────┬────────┐
│ API 1  │ API 2  │ API 3  │  (Stateless FastAPI instances)
└────────┴────────┴────────┘
    ↓           ↓
PostgreSQL   Redis Cluster
(Primary)    (Sharded)
    ↓
Read Replicas
```

#### Caching Strategy
```python
# 1. In-memory cache (FastAPI app.state)
template_cache = app.state.template_service.cache  # < 1ms

# 2. Redis cache
redis.get("query:result:hash")  # 1-5ms

# 3. PostgreSQL (if not cached)
db.query(...)  # 5-15ms
```

### Optimization Tips

1. **Batch Embeddings**: Process multiple queries together
   ```python
   embeddings = model.encode(queries, batch_size=32)
   ```

2. **Connection Pooling**: Reuse database connections
   ```python
   # PostgreSQL
   pool_size=10, max_overflow=20
   
   # Redis
   connection_pool=redis.ConnectionPool(max_connections=50)
   ```

3. **Async Operations**: Use async/await for I/O
   ```python
   async def process_query(query):
       result = await db.execute(...)
       embeddings = await generate_embeddings(...)
   ```

4. **Index Optimization**: Proper database indexes
   ```sql
   CREATE INDEX idx_intent ON datasets(intent);
   CREATE INDEX idx_created ON query_logs(created_at);
   ```

5. **Redis Persistence**: Balance speed vs durability
   ```redis
   # Fast: No persistence
   CONFIG SET save ""
   
   # Balanced: RDB snapshots
   SAVE 900 1
   
   # Safe: AOF always
   CONFIG SET appendonly yes
   ```

---

## 🔐 Security

### Authentication & Authorization

```python
# JWT-based authentication (to be implemented)
from fastapi.security import HTTPBearer
from jose import jwt

security = HTTPBearer()

@app.post("/api/v1/query")
async def process_query(
    request: QueryRequest,
    token: str = Depends(security)
):
    payload = jwt.decode(token, SECRET_KEY)
    user_id = payload.get("sub")
    # Process with user context
```

### Input Validation

```python
from pydantic import BaseModel, validator, Field

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    generate_dataset: bool = False
    num_examples: int = Field(default=50, ge=10, le=200)
    top_k: int = Field(default=5, ge=1, le=20)
    
    @validator('query')
    def sanitize_query(cls, v):
        # Remove SQL injection attempts
        if any(word in v.lower() for word in ['drop', 'delete', 'truncate']):
            raise ValueError("Malicious query detected")
        return v
```

### Environment Security

```bash
# Never commit .env file
echo ".env" >> .gitignore

# Use strong passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -hex 32)

# Restrict CORS in production
CORS_ORIGINS='["https://yourdomain.com"]'
```

### API Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/query")
@limiter.limit("100/minute")
async def process_query(...):
    # Max 100 requests per minute per IP
    pass
```

### Database Security

```sql
-- PostgreSQL: Create read-only user for analytics
CREATE USER analytics WITH PASSWORD 'secure_password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics;

-- Redis: Enable password authentication
CONFIG SET requirepass "your_redis_password"
```

---

## 📊 Monitoring

### Health Checks

```python
@app.get("/health")
async def health_check():
    # Check PostgreSQL
    try:
        await db_manager.execute("SELECT 1")
        pg_status = "healthy"
    except:
        pg_status = "unhealthy"
    
    # Check Redis
    try:
        redis_client.ping()
        redis_status = "healthy"
    except:
        redis_status = "unhealthy"
    
    return {
        "status": "healthy" if all([pg_status, redis_status]) else "degraded",
        "postgres": pg_status,
        "redis": redis_status,
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Metrics Collection

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

query_counter = Counter('queries_total', 'Total queries processed')
query_duration = Histogram('query_duration_seconds', 'Query processing time')
active_connections = Gauge('active_connections', 'Active database connections')

@app.post("/api/v1/query")
async def process_query(...):
    query_counter.inc()
    with query_duration.time():
        result = await process(...)
    return result
```

### Logging

```python
import logging
from app.core.logger import logger

# Structured logging
logger.info("Query processed", extra={
    "query_id": query_id,
    "intent": intent,
    "confidence": confidence,
    "processing_time_ms": duration,
    "user_id": user_id
})

# Error logging with context
try:
    result = await process_query(...)
except Exception as e:
    logger.error("Query processing failed", extra={
        "query": query,
        "error": str(e),
        "traceback": traceback.format_exc()
    })
```

### Dashboard Metrics

Key metrics to monitor:

1. **Request Metrics**
   - Total requests
   - Requests per second
   - Success rate
   - Error rate
   - P50/P95/P99 latency

2. **Database Metrics**
   - Connection pool usage
   - Active connections
   - Query latency
   - Slow queries
   - Database size

3. **Redis Metrics**
   - Memory usage
   - Key count
   - Hit rate
   - Evictions
   - Search latency

4. **Business Metrics**
   - Queries processed
   - Datasets generated
   - Embeddings created
   - Unique intents
   - User activity

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Redis Connection Error
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solution**:
```bash
# Check Redis is running
docker ps | grep redis

# Test connection
redis-cli ping
# Should return: PONG

# Check port availability
netstat -an | findstr 6379

# Restart Redis
docker restart nlpforge-redis
```

#### 2. PostgreSQL Connection Error
```
asyncpg.exceptions.CannotConnectNowError: Cannot connect to database
```

**Solution**:
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
docker exec nlpforge-postgres pg_isready -U nlpforge

# Check logs
docker logs nlpforge-postgres

# Verify credentials
psql -h localhost -U nlpforge -d nlpforge
```

#### 3. spaCy Model Not Found
```
OSError: [E050] Can't find model 'en_core_web_md'
```

**Solution**:
```bash
# Download model
python -m spacy download en_core_web_md

# Verify installation
python -c "import spacy; nlp = spacy.load('en_core_web_md'); print('OK')"

# In Docker
docker exec nlpforge-api python -m spacy download en_core_web_md
```

#### 4. Gemini API Error
```
google.api_core.exceptions.PermissionDenied: API key not valid
```

**Solution**:
```bash
# Check API key in .env
cat .env | grep GEMINI_API_KEY

# Get new API key at: https://makersuite.google.com/

# Update .env and restart
docker-compose restart nlpforge-api
```

#### 5. Out of Memory (OOM)
```
MemoryError: Unable to allocate array
```

**Solution**:
```bash
# Check memory usage
docker stats

# Increase Docker memory limit
# Docker Desktop → Settings → Resources → Memory: 8GB+

# Reduce batch size in .env
BATCH_SIZE=16

# Use CPU-only PyTorch
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

#### 6. Slow Query Performance
```
Query taking > 1 second
```

**Solution**:
```sql
-- Check for missing indexes
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public';

-- Analyze query plan
EXPLAIN ANALYZE SELECT * FROM query_logs WHERE intent='login';

-- Create index if needed
CREATE INDEX idx_intent ON query_logs(intent);

-- Vacuum database
VACUUM ANALYZE;
```

#### 7. Redis Memory Full
```
OOM command not allowed when used memory > 'maxmemory'
```

**Solution**:
```redis
# Check memory usage
INFO memory

# Increase maxmemory
CONFIG SET maxmemory 2gb

# Set eviction policy
CONFIG SET maxmemory-policy allkeys-lru

# Or persist to disk
docker-compose down
# Edit docker-compose.yml to add volume
docker-compose up -d
```

### Debug Mode

Enable detailed logging:

```bash
# In .env
DEBUG=True
LOG_LEVEL=DEBUG

# Restart application
docker-compose restart nlpforge-api

# View logs
docker-compose logs -f nlpforge-api
```

### Testing Components

```bash
# Test query parser
python -c "
from app.nlp.query_parser import QueryParser
parser = QueryParser()
result = parser.parse('Login with milan')
print(result)
"

# Test embeddings
python -c "
from app.nlp.embedding_manager import EmbeddingManager
embedder = EmbeddingManager()
embedding = embedder.get_embedding('test query')
print(f'Embedding shape: {embedding.shape}')
"

# Test database connection
python -c "
import asyncio
from app.core.postgres import db_manager
async def test():
    await db_manager.connect()
    result = await db_manager.execute('SELECT 1')
    print(f'Database: OK')
asyncio.run(test())
"
```

---

## 📚 Additional Resources

### Documentation
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- **RedisInsight UI**: http://localhost:8001

### External Links
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [spaCy Documentation](https://spacy.io/)
- [Sentence Transformers](https://www.sbert.net/)
- [Redis Stack](https://redis.io/docs/stack/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Google Gemini](https://ai.google.dev/)

### Related Files
- `README_BACKEND.md` - Quick start guide
- `ARCHITECTURE_POSTGRES_REDIS.md` - Architecture details
- `QUICKSTART.md` - Installation guide
- `api_template.json` - Template definitions

---

## 📄 License

Proprietary software for Bangalore-based company.

---

## 🙏 Acknowledgments

- **spaCy** - Industrial-strength NLP
- **Sentence Transformers** - State-of-the-art embeddings
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Reliable ACID database
- **Redis Stack** - Fast in-memory data store
- **Google Gemini** - AI-powered generation

---

## 📧 Support

For issues, questions, or contributions:
- **Email**: support@nlpforge.com
- **GitHub Issues**: [Repository Issues]
- **Documentation**: [Full Docs]

---

**Built with ❤️ for intelligent API testing automation**

*Last Updated: November 9, 2025*
