# NLPForge-Tester

NLPForge-Tester is an AI-powered API testing platform that combines natural language processing, vector embeddings, and semantic search to automate API testing workflows.

## 🎯 Overview

A production-grade B2B SaaS platform where users input plain-English API requests, and the system:
- **Parses** queries using advanced NLP (spaCy + custom rules)
- **Generates** test datasets with AI (Google Gemini)
- **Embeds** data using BAAI/bge-small-en-v1.5 (384-dim vectors)
- **Stores** in dual database (PostgreSQL + Redis)
- **Searches** semantically with cosine similarity
- **Executes** tests and generates comprehensive reports

## 🏗️ Architecture

### Backend (FastAPI)
- Natural language query processing
- Vector embeddings and semantic search
- Template-based API definitions
- Dataset generation with AI
- PostgreSQL + Redis dual-database

### Frontend (Next.js 14+)
- Modern, premium UI (no "AI template" look)
- Real-time query processing
- Semantic search interface
- Template and dataset management
- Interactive dashboards and reports

## ✨ Features

### Backend Features
- 🚀 **FastAPI Framework** - High-performance async API with automatic documentation
- 🔍 **NLP Pipeline** - Advanced query parsing with intent detection and slot extraction
- 🤖 **AI Dataset Generation** - Google Gemini integration for test case generation
- 🧠 **Vector Search** - Redis-based semantic search with HNSW indexing
- 🗄️ **Dual Database** - PostgreSQL (permanent) + Redis (fast in-memory)
- 📊 **Template System** - Hot-reloadable API definitions
- 📈 **Health Monitoring** - Comprehensive health checks and metrics

### Frontend Features
- ⚡ **Next.js 14+** - App Router with Server Components
- 🎨 **Premium Design** - Human-crafted UI with tasteful animations
- 🔄 **Real-time Updates** - Live query processing with progress tracking
- 🔍 **Semantic Search** - Interactive search with filters and similarity scores
- 📝 **Template Management** - CRUD operations with hot reload
- 📊 **Dataset Operations** - Generate, upload, and manage test datasets
- 🌗 **Theme Support** - Beautiful light and dark modes
- ♿ **Accessibility** - WCAG AA compliant, keyboard navigable

<<<<<<< HEAD
## Project Structure

```
=======
>>>>>>> 4375fa89e968a4947a0bb180f74586766528b9c6
NLPForge-Tester/
├── .dockerignore                    # Docker ignore patterns
├── .git/                           # Git repository data
├── .venv/                          # Python virtual environment
├── docker-compose.yml             # Docker Compose configuration
├── Dockerfile                     # Docker container configuration
├── README.md                      # Project documentation
├── requirements.txt               # Python dependencies
├── test_storage_paths.py          # Storage path testing script
│
├── app/                           # Main application package
│   ├── __init__.py               # Package initialization
│   ├── main.py                   # FastAPI application entry point
│   │
│   ├── api/                      # API routing layer
│   │   ├── __init__.py
│   │   └── v1/                   # API version 1
│   │       ├── __init__.py
│   │       ├── convert.py        # Text conversion endpoints
│   │       ├── dictionary.py     # Dictionary management endpoints
│   │       └── health.py         # Health check and metrics endpoints (consolidated)
│   │
│   ├── core/                     # Core application components
│   │   ├── __init__.py
│   │   ├── config.py             # Configuration management
│   │   ├── database.py           # Database connectivity
│   │   ├── logger.py             # Logging configuration
│   │   └── security.py           # Security utilities
│   │
│   ├── models/                   # Data models and schemas
│   │   ├── __init__.py
│   │   └── schemas.py            # Pydantic models for API
│   │
│   └── nlp/                      # NLP processing components
│       ├── __init__.py
│       ├── assembler.py          # Final output assembly
│       ├── ranker.py             # Result ranking logic
│       ├── rule_engine.py        # Rule-based text parsing
│       └── semantic_matcher.py   # Semantic matching algorithms
│
└── storage/                      # Data storage directory
    ├── __init__.py              # Package initialization
    ├── feedback.db              # SQLite feedback database
    ├── function_dictionary.json # Browser automation functions (20 entries)
    └── faiss_index/             # Vector search index storage
        └── .gitkeep             # Placeholder for git tracking
<<<<<<< HEAD
```

## 📋 API Endpoints

### Backend API (Port 8000)

#### Query Processing
- `POST /api/v1/query` - Process natural language query
- `GET /api/v1/stats` - Get platform statistics
- `POST /api/v1/reindex/{intent}` - Reindex embeddings

#### Templates
- `GET /api/v1/templates/` - List all templates
- `GET /api/v1/templates/{intent}` - Get specific template
- `POST /api/v1/templates/` - Create template
- `PUT /api/v1/templates/{intent}` - Update template
- `DELETE /api/v1/templates/{intent}` - Delete template
- `POST /api/v1/templates/sync` - Sync from JSON
- `POST /api/v1/templates/reload` - Hot reload templates

#### Datasets
- `GET /api/v1/dataset/list` - List datasets
- `POST /api/v1/dataset/generate` - Generate with AI
- `POST /api/v1/dataset/upload` - Upload CSV
- `GET /api/v1/dataset/download` - Download dataset

#### Search
- `GET /api/v1/search/search` - Semantic search with filters

#### Health
- `GET /health` - Comprehensive health check

### Frontend Routes (Port 3000)

- `/` - Landing page
- `/dashboard` - Statistics and KPIs
- `/run/new` - Create new test run
- `/runs` - List test runs
- `/runs/:id` - Run details
- `/search` - Semantic search
- `/templates` - Template management
- `/dataset` - Dataset operations
- `/settings` - Configuration
- `/health` - Backend status

## 📚 Documentation

### Backend Documentation
- `BACKEND_COMPLETE_DOCUMENTATION.md` - Complete backend guide (100+ pages)
- `Backend/README_BACKEND.md` - Backend-specific README
- `Backend/ARCHITECTURE_POSTGRES_REDIS.md` - Database architecture
- API Docs: http://localhost:8000/docs (when running)

### Frontend Documentation
- `Frontend/README.md` - Complete frontend guide
- `Frontend/SETUP_GUIDE.md` - Step-by-step setup
- `Frontend/BACKEND_INTEGRATION_GUIDE.md` - API integration
- `Frontend/DEPLOYMENT_GUIDE.md` - Production deployment
- `Frontend/PROJECT_SUMMARY.md` - Implementation summary
- `QUICKSTART_FRONTEND.md` - 5-minute quick start

### General
- `START_HERE.md` - Project orientation
- `frontend-spec.md` - Frontend specification

## 🚀 Quick Start

### Option 1: Full Stack with Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/Iammilansoni/NLPForge-Tester.git
cd NLPForge-Tester

# Start everything with Docker Compose
docker-compose up --build
```

**Access**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Backend Only (Development)

```bash
# Navigate to backend
cd Backend

# Set up Python environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run backend
python app/main.py
```

**Access**: http://localhost:8000

### Option 3: Frontend Only (Development)

```bash
# Navigate to frontend
cd Frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env to point to your backend

# Run frontend
npm run dev
```

**Access**: http://localhost:3000

📚 **For detailed setup instructions**: See `QUICKSTART_FRONTEND.md`

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Or build and run individually**
   ```bash
   docker build -t nlpforge-tester .
   docker run -p 8000:8000 nlpforge-tester
   ```

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI 0.104.1+
- **Language**: Python 3.11+
- **NLP**: spaCy + Custom patterns
- **AI**: Google Gemini API
- **Embeddings**: BAAI/bge-small-en-v1.5 (Sentence Transformers)
- **Databases**: 
  - PostgreSQL 15 (permanent storage)
  - Redis Stack (vector search with HNSW)
- **Monitoring**: psutil, custom health checks

### Frontend
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS with CSS variables
- **UI Components**: Custom components + Radix UI
- **State Management**: TanStack Query (React Query)
- **Forms**: React Hook Form + Zod
- **Animations**: Framer Motion
- **Charts**: Recharts
- **Testing**: Jest, React Testing Library, Cypress

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Deployment**: Vercel (Frontend), Docker (Backend)
- **Documentation**: OpenAPI/Swagger, Storybook

## Development

### Code Quality
- All code follows modern Python standards
- Type hints throughout the codebase
- Pylance linting with zero errors
- Timezone-aware datetime handling

### Testing
- Health endpoints optimized for Kubernetes deployments
- Comprehensive error handling and logging
- Storage path testing utilities included

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure code quality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
=======
>>>>>>> 4375fa89e968a4947a0bb180f74586766528b9c6
