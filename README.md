<p align="center">
  <h1 align="center">🧠 NLPForge</h1>
  <p align="center">
    <strong>AI-Powered API Test Case Generation & Semantic Search Platform</strong>
  </p>
  <p align="center">
    Transform natural language queries into executable API test cases using LLM-powered semantic understanding
  </p>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#api-documentation">API Docs</a> •
  <a href="#configuration">Configuration</a>
</p>

---

## 🎯 Overview

NLPForge is an enterprise-grade platform that bridges the gap between natural language and API testing. Simply describe what you want to test in plain English, and NLPForge will:

1. **Understand** your intent using semantic search
2. **Match** to the most relevant API template
3. **Extract** values from your query to populate request parameters
4. **Generate** complete, executable API test cases

### Example

```
Query: "Authenticate with email milansoni@example.com and password secure123"

↓ NLPForge Processing ↓

{
  "api_name": "User_Login",
  "base_url": "https://api.example.com",
  "endpoint": "/auth/login",
  "method": "POST",
  "extracted_request_body": {
    "email": "milansoni@example.com",
    "password": "secure123"
  }
}
```

---

## ✨ Features

### 🔍 Semantic Search Pipeline
- **Two-Stage Retrieval**: Vector similarity search + FlashRank re-ranking
- **Multi-Model Support**: Choose from 3 embedding models based on your needs
- **Multi-Tenant Security**: Complete user data isolation

### 🤖 LLM-Powered Slot Extraction
- Extracts values from natural language queries
- Populates API request schemas automatically
- Supports complex nested JSON structures

### 📋 Enterprise Template Builder
- Create and manage API templates with JSON schemas
- Approval workflow (Draft → Review → Approved)
- Version control and audit logging

### 📊 Synthetic Dataset Generation
- Generate diverse test data using Ollama LLMs
- Embed datasets for semantic search
- CSV export for integration

### 🔐 Security & Compliance
- JWT authentication with refresh tokens
- Complete audit trail for all actions
- Multi-tenant data isolation

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│  Dashboard │ Templates │ Datasets │ Settings │ Search           │
└─────────────────────────────┬───────────────────────────────────┘
                              │ REST API
┌─────────────────────────────▼───────────────────────────────────┐
│                     Backend (FastAPI)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Auth Service │  │ Template API │  │ Search API   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Embedding    │  │ Slot Extract │  │ Telemetry    │           │
│  │ Service      │  │ Service      │  │ Service      │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────┬─────────────┬─────────────────┬───────────────────┘
              │             │                 │
     ┌────────▼───┐   ┌─────▼─────┐   ┌──────▼──────┐
     │ PostgreSQL │   │   Redis   │   │   Ollama    │
     │ (Metadata) │   │ (Vectors) │   │ (LLM/Embed) │
     └────────────┘   └───────────┘   └─────────────┘
```

### Technology Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui |
| **Backend** | FastAPI, Python 3.11+, SQLAlchemy, Pydantic |
| **Database** | PostgreSQL 15 (metadata), Redis Stack (vectors) |
| **AI/ML** | Ollama (embeddings + LLM), FlashRank (re-ranking) |
| **DevOps** | Docker, Docker Compose |

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- 16GB RAM recommended (for LLM inference)
- 20GB disk space (for models)

### One-Command Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/NLPForge-Tester.git
cd NLPForge-Tester

# Start all services (first run downloads models automatically)
docker-compose up -d

# View logs
docker-compose logs -f
```

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Register new account |
| **API Docs** | http://localhost:8000/docs | - |
| **RedisInsight** | http://localhost:8001 | - |
| **pgAdmin** | http://localhost:5050 | admin@nlpforge.local / admin123 |

### First Steps

1. **Register** an account at http://localhost:3000/auth/register
2. **Create a Template** in the Templates page
3. **Generate Dataset** to create training data
4. **Search** using natural language on the Dashboard

---

## 🔧 Development Setup

For local development with hot reload:

```bash
# Start infrastructure services only
docker-compose -f docker-compose.dev.yml up -d

# Run Ollama locally (separate terminal)
ollama serve

# Pull required models
ollama pull nomic-embed-text
ollama pull all-minilm
ollama pull mxbai-embed-large
ollama pull llama3.1:8b-instruct-q4_K_M

# Start Backend (separate terminal)
cd Backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Start Frontend (separate terminal)
cd Frontend
npm install
npm run dev
```

---

## 📊 Embedding Models

NLPForge supports 3 embedding models via Ollama:

| Model | Dimension | Speed | Best For |
|-------|-----------|-------|----------|
| `nomic-embed-text` | 768 | ⚡ Fast | General use, **recommended default** |
| `all-minilm` | 384 | ⚡⚡ Fastest | Prototyping, low-resource environments |
| `mxbai-embed-large` | 1024 | 🐢 Moderate | Maximum accuracy, enterprise search |

Change your embedding model in **Settings** → **Embedding Model**.

---

## 📖 API Documentation

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register new user |
| `POST` | `/api/v1/auth/login` | Login and get tokens |
| `GET` | `/api/v1/templates` | List user's templates |
| `POST` | `/api/v1/templates` | Create new template |
| `POST` | `/api/v1/ranking/semantic-retrieve` | Semantic search |
| `GET` | `/api/v1/stats` | Dashboard statistics |

Full API documentation available at: **http://localhost:8000/docs**

### Semantic Search Request

```bash
curl -X POST "http://localhost:8000/api/v1/ranking/semantic-retrieve" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Login with email test@example.com and password secret123",
    "top_k": 5,
    "include_slot_extraction": true
  }'
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# PostgreSQL
POSTGRES_USER=nlpforge
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=nlpforge

# Redis
REDIS_PASSWORD=your_redis_password

# Application
SECRET_KEY=your-super-secret-key-change-in-production
ENVIRONMENT=production
LOG_LEVEL=INFO

# Optional
HUGGINGFACE_TOKEN=your_token
```

### Docker Compose Services

| Service | Port | Purpose |
|---------|------|---------|
| `postgres` | 5432 | Primary database |
| `redis` | 6379, 8001 | Vector DB + RedisInsight |
| `redis-commander` | 8081 | Redis web UI |
| `pgadmin` | 5050 | PostgreSQL admin |
| `ollama` | 11434 | LLM & embeddings |
| `backend` | 8000 | FastAPI server |
| `frontend` | 3000 | Next.js app |

---

## 🔒 Security

### Multi-Tenant Isolation

- All database queries filter by `user_id`
- Redis vectors are namespaced per user
- API endpoints require authentication
- Complete audit logging

### Authentication Flow

```
Register → Email Verification → Login → JWT Access Token → API Access
                                          ↓
                                   Refresh Token (7 days)
```

---

## 📁 Project Structure

```
NLPForge-Tester/
├── Backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── core/            # Config, security, logging
│   │   ├── models/          # Database & Pydantic models
│   │   ├── services/        # Business logic
│   │   └── nlp/             # Embedding & ranking
│   ├── alembic/             # Database migrations
│   └── requirements.txt
├── Frontend/
│   ├── app/                 # Next.js pages
│   ├── components/          # React components
│   ├── lib/                 # Utilities & API client
│   └── package.json
├── docker-compose.yml       # Production setup
├── docker-compose.dev.yml   # Development setup
└── README.md
```

---

## 🧪 Testing

```bash
# Backend tests
cd Backend
pytest tests/ -v

# Frontend tests
cd Frontend
npm run test
```

---

## 📈 Performance Telemetry

NLPForge tracks real-time performance metrics:

- **Search Latency**: Redis vector search time
- **Embedding Latency**: Ollama embedding generation
- **Reranker Latency**: FlashRank re-ranking time

View metrics on the Dashboard performance chart.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) - Local LLM inference
- [Redis Stack](https://redis.io/docs/stack/) - Vector database
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [Next.js](https://nextjs.org/) - Frontend framework
- [FlashRank](https://github.com/PrithivirajDamodaran/FlashRank) - Re-ranking

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/Iammilansoni">Milan Soni</a>
</p>
