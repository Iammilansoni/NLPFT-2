# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Frontend (Next.js)

From `/Frontend` directory:

```bash
npm run dev              # Development server (http://localhost:3000)
npm run build            # Production build
npm run start            # Start production server
npm run lint             # ESLint checks

# Testing
npm test                 # Jest unit tests
npm run test:watch       # Watch mode
npm run test:e2e         # Playwright E2E tests
npm run test:e2e:ui      # E2E tests with UI
```

### Backend (FastAPI)

From `/Backend` directory:

```bash
# Development
python -m uvicorn app.main:app --reload --port 8000

# Testing
pytest                              # Run all tests
pytest -k test_function_name        # Run specific test
pytest -m unit                      # Run unit tests only
pytest -m integration               # Run integration tests
pytest -m datasets                  # Run dataset generation tests
pytest -m embeddings                # Run embedding tests
pytest -v                           # Verbose output
pytest --cov                        # With coverage

# Database
python init_database.py             # Initialize database tables
alembic upgrade head                # Apply migrations
alembic revision --autogenerate -m "message"  # Create migration
```

### Docker

From repository root:

```bash
# Development (infrastructure only, run Frontend/Backend locally for hot reload)
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml logs -f
docker-compose -f docker-compose.dev.yml down

# Production (all services containerized)
docker-compose up -d --build
docker-compose logs -f backend
docker-compose down -v              # Full reset with volumes
```

### Ollama (LLM & Embeddings)

```bash
ollama serve                        # Start Ollama server

# Pull models (in separate terminal)
ollama pull nomic-embed-text        # Recommended embedding model
ollama pull all-minilm              # Fast embedding model
ollama pull llama3.2:3b-instruct-q4_K_M  # LLM for dataset generation
```

## Architecture & Structure

### Monorepo Layout

**NLPForge** is a monorepo with two independent deployable services:

- **Frontend** (`/Frontend`) - Next.js 14+ SPA with TypeScript
- **Backend** (`/Backend`) - FastAPI REST API with Python 3.11+

Each has its own Dockerfile, dependencies, and can be developed independently.

### Tech Stack

**Frontend:**
- Next.js 16 (React 18.3) with App Router
- TypeScript 5
- TailwindCSS + Radix UI
- React Query (TanStack) for server state
- Framer Motion for animations

**Backend:**
- FastAPI 0.123+ with async/await throughout
- SQLAlchemy 2.0 (async) + PostgreSQL 15
- Redis Stack (vector database + cache)
- FlashRank (ms-marco-MiniLM-L-12-v2 cross-encoder)
- Ollama for local embeddings

### Two-Stage Retrieval Pipeline

This is the core innovation of NLPForge. Understanding this is critical:

**Stage 1: Vector Similarity Search**
- User query → Generate embedding (via Ollama/HuggingFace models)
- Search Redis vector store using KNN search
- Returns Top-5 candidates ranked by cosine similarity
- Score: `vector_score = 1.0 - euclidean_distance`

**Stage 2: FlashRank Reranking**
- Takes Stage 1 candidates + original query
- Cross-encoder model scores query-document relevance
- Model: `ms-marco-MiniLM-L-12-v2` (neural pairwise ranking)
- Final score: 0-1 via sigmoid activation
- Returns best-ranked results

**Implementation locations:**
- Stage 1: `/Backend/app/services/redis_vector_service.py`
- Stage 2: `/Backend/app/nlp/ranking_engine.py`
- Orchestration: `/Backend/app/services/multi_model_semantic_service.py`

See `RERANKING_ARCHITECTURE.md` and `STAGE2_DETAILED_EXPLANATION.md` for mathematical details.

### Multi-Provider LLM System

Backend supports 8 LLM providers through a unified interface:

**Provider Factory Pattern:**
- Entry point: `/Backend/app/llm/provider_factory.py`
- Providers: OpenAI, Google Gemini, Anthropic, Grok (xAI), DeepSeek, Ollama, HuggingFace, Custom
- Config: `/Backend/app/core/models_config.py`
- User settings stored encrypted in PostgreSQL

**Adding a new provider:**
1. Create provider class in `/Backend/app/llm/providers/`
2. Implement `BaseLLMProvider` interface
3. Register in `provider_factory.py`
4. Add to `ProviderType` enum in schemas

### Async-First Architecture

The entire backend is built on `asyncio`:

- **Database:** `AsyncSession` with `asyncpg` driver
- **Redis:** `aioredis` client
- **HTTP clients:** `httpx.AsyncClient` for all external APIs
- **Services:** All business logic methods are `async def`

**Why this matters:**
- Never use blocking I/O operations (use `async with` for sessions)
- Database queries must use `await`
- HTTP calls to LLM providers are non-blocking
- Background tasks use FastAPI's `BackgroundTasks`

### Key Backend Directories

| Directory | Purpose |
|-----------|---------|
| `/Backend/app/api/v1/` | REST API endpoints (auth, templates, datasets, query, embeddings) |
| `/Backend/app/services/` | Business logic layer (20+ services, all async) |
| `/Backend/app/core/` | Core utilities (config, security, database session, encryption) |
| `/Backend/app/models/` | SQLAlchemy ORM models & Pydantic schemas |
| `/Backend/app/nlp/` | NLP processing (embeddings, ranking, dataset generation) |
| `/Backend/app/llm/` | LLM provider integrations (factory pattern) |
| `/Backend/alembic/` | Database migrations (Alembic) |

### Key Frontend Directories

| Directory | Purpose |
|-----------|---------|
| `/Frontend/app/` | Next.js pages (App Router, file-based routing) |
| `/Frontend/components/` | Reusable React components (UI, forms, layouts) |
| `/Frontend/lib/` | API client, types, validators, constants |
| `/Frontend/hooks/` | Custom hooks (auth, data fetching, state) |
| `/Frontend/contexts/` | React Context providers (Auth, Sidebar) |

### Component Interaction Flow

Example: User submits a query

```
User Query (Frontend)
    ↓ (Axios POST → /api/v1/query/multi-model)
API Router (/Backend/app/api/v1/query.py)
    ↓ (Validates request with Pydantic)
MultiModelSemanticService
    ↓ (Orchestrates pipeline)
    ├→ EmbeddingService (generate query embedding)
    ├→ RedisVectorService (Stage 1: KNN search)
    ├→ RankingEngine (Stage 2: FlashRank reranking)
    └→ SlotExtractionService (extract structured data)
    ↓ (Returns ranked results with scores)
API Response (JSON)
    ↓ (React Query caches & updates state)
Frontend UI (displays results)
```

### Security Patterns

**Authentication:**
- JWT tokens with `SECRET_KEY` (minimum 32 chars)
- Token storage: `HttpOnly` cookies (backend) + localStorage fallback (frontend)
- Routes: `/Backend/app/api/v1/auth/`

**API Key Encryption:**
- LLM provider API keys encrypted at rest using Fernet (`SECRET_KEY_ENCRYPTION`)
- See: `/Backend/app/core/security.py` (functions: `encrypt_api_key`, `decrypt_api_key`)

**Rate Limiting:**
- SlowAPI with Redis backend
- Default: 100 requests/minute per IP
- Config: `/Backend/app/main.py`

**CORS:**
- Configured in `/Backend/app/main.py`
- Must match `FRONTEND_URL` environment variable
- Development: Allows localhost:3000 and 127.0.0.1:3000

### Database Schema

**Key models** (`/Backend/app/models/`):
- `User` - Authentication & profile
- `Template` - API endpoint templates for test generation
- `Dataset` - Generated test datasets
- `LLMProviderConfig` - User's LLM provider settings (API keys encrypted)
- `EmbeddingModel` - Available embedding models
- `ActivityLog` - Audit trail

### Environment Configuration

**Backend** (`.env` in `/Backend`):
```bash
SECRET_KEY=<32+ chars>
SECRET_KEY_ENCRYPTION=<Fernet key>
POSTGRES_USER=nlpforge
POSTGRES_PASSWORD=<secure>
POSTGRES_DB=nlpforge
REDIS_PASSWORD=<secure>
OLLAMA_HOST=http://localhost:11434
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
GEMINI_API_KEY=<from aistudio.google.com>
```

**Frontend** (`.env.local` in `/Frontend`):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Access Points (Development)

| Service | URL | Notes |
|---------|-----|-------|
| Web App | http://localhost:3000 | Frontend |
| API Docs | http://localhost:8000/docs | Swagger UI |
| ReDoc | http://localhost:8000/redoc | Alternative API docs |
| pgAdmin | http://localhost:5050 | PostgreSQL admin (admin@example.com / admin123) |
| RedisInsight | http://localhost:8001 | Redis GUI |
| Redis Commander | http://localhost:8081 | Redis CLI (admin / admin123) |

### Important Notes

1. **Ollama models persist in Docker volume `ollama_models`** - prevents re-downloading on restart

2. **Frontend API URL resolution** - Frontend detects API URL dynamically. If running on mobile device (e.g., 10.0.0.1), it automatically uses correct host.

3. **Test database** - Backend tests use SQLite in-memory (`:memory:`), not PostgreSQL. This is configured in `/Backend/tests/conftest.py`.

4. **Alembic migrations run automatically** on backend startup via lifespan event in `/Backend/app/main.py`.

5. **Multiple embedding models** - System supports 15+ embedding models with fallback mechanism. Default: `nomic-embed-text` (768-dim).

6. **CORS troubleshooting** - If frontend can't reach backend, check:
   - Backend `CORS_ORIGINS` includes frontend URL
   - Frontend `NEXT_PUBLIC_API_URL` points to correct backend
   - Docker networking if using containers

7. **Async testing** - Backend tests require `@pytest.mark.asyncio` decorator. Use `pytest-asyncio` plugin.
