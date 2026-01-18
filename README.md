<div align="center">

# 🧠 NLPForge

### **AI-Powered NLP Dataset Generator & Semantic Search Platform**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.123+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

*Transform natural language queries into executable API test cases using LLM-powered semantic understanding*

[🚀 Quick Start](#-quick-start) • [📖 Documentation](#-features) • [🐳 Docker](#-docker-deployment) • [🤝 Contributing](#-contributing)

---

</div>

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Environment Setup](#-environment-setup)
- [Docker Deployment](#-docker-deployment)
- [API Documentation](#-api-documentation)
- [Embedding Models](#-embedding-models)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

**NLPForge** is an enterprise-grade platform that bridges the gap between natural language and API testing. Simply describe what you want to test in plain English, and NLPForge will intelligently process your request.

### How It Works

```
┌─────────────────────────────────────────────────────────────────────────┐
│  📝 Input: "Authenticate with email milansoni@nlpforge.com              │
│            and password secure123"                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  🧠 NLPForge Processing Pipeline                                         │
│  ├── 1️⃣  Semantic Understanding (Embedding Generation)                   │
│  ├── 2️⃣  Template Matching (Vector Similarity Search)                    │
│  ├── 3️⃣  Re-ranking (FlashRank Cross-Encoder)                            │
│  └── 4️⃣  Slot Extraction (LLM-Powered Value Extraction)                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ✅ Output:                                                              │
│  {                                                                       │
│    "api_name": "User_Login",                                            │
│    "base_url": "https://api.nlpforge.com",                              │
│    "endpoint": "/auth/login",                                           │
│    "method": "POST",                                                    │
│    "extracted_request_body": {                                          │
│      "email": "milansoni@nlpforge.com",                                 │
│      "password": "secure123"                                            │
│    }                                                                    │
│  }                                                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🔍 **Semantic Search**
- Natural language query processing
- Multi-model embedding support
- Two-stage retrieval with re-ranking
- Real-time similarity scoring

</td>
<td width="50%">

### 📊 **Dataset Generation**
- AI-powered synthetic data creation
- Gemini LLM integration
- Customizable templates
- Export to CSV/JSON formats

</td>
</tr>
<tr>
<td width="50%">

### 🎨 **Template Management**
- Visual template builder
- Slot/parameter definition
- Version control & history
- Import/Export capabilities

</td>
<td width="50%">

### 🔐 **Enterprise Security**
- JWT-based authentication
- Multi-tenant data isolation
- Audit logging & telemetry
- Role-based access control

</td>
</tr>
<tr>
<td width="50%">

### 📈 **Analytics Dashboard**
- Real-time metrics & charts
- Query performance tracking
- Model accuracy monitoring
- Usage statistics

</td>
<td width="50%">

### ⚡ **High Performance**
- Redis vector caching
- Async/await architecture
- Background job processing
- Horizontal scalability

</td>
</tr>
</table>

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          🌐 Frontend (Next.js 16)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │Dashboard │ │Templates │ │ Datasets │ │  Query   │ │ Settings │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │ REST API / WebSocket
┌────────────────────────────────▼─────────────────────────────────────────┐
│                         🚀 Backend (FastAPI)                              │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                         API Layer (v1)                               │ │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │ │
│  │  │  Auth  │ │Template│ │Dataset │ │Embedding│ │ Query  │ │Telemetry│ │ │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                       Service Layer                                  │ │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐        │ │
│  │  │ Embedding  │ │  Ranking   │ │    Slot    │ │  Gemini    │        │ │
│  │  │  Service   │ │  Service   │ │ Extraction │ │ Integration│        │ │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘        │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└─────────────┬─────────────────────┬─────────────────────┬────────────────┘
              │                     │                     │
     ┌────────▼────────┐   ┌───────▼───────┐    ┌───────▼───────┐
     │   🐘 PostgreSQL  │   │  🔴 Redis     │    │   🦙 Ollama    │
     │   (Metadata)     │   │  (Vectors)    │    │   (LLM/Embed)  │
     │   Port: 5432     │   │  Port: 6379   │    │   Port: 11434  │
     └─────────────────┘   └───────────────┘    └───────────────┘
```

---

## 🛠️ Tech Stack

<table>
<tr>
<th>Layer</th>
<th>Technology</th>
<th>Purpose</th>
</tr>
<tr>
<td><strong>Frontend</strong></td>
<td>
  <img src="https://img.shields.io/badge/Next.js-16-black?logo=nextdotjs" alt="Next.js"/>
  <img src="https://img.shields.io/badge/TypeScript-5.0-3178C6?logo=typescript" alt="TypeScript"/>
  <img src="https://img.shields.io/badge/Tailwind-3.4-06B6D4?logo=tailwindcss" alt="Tailwind"/>
</td>
<td>Modern React framework with server components</td>
</tr>
<tr>
<td><strong>Backend</strong></td>
<td>
  <img src="https://img.shields.io/badge/FastAPI-0.123-009688?logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0-red" alt="SQLAlchemy"/>
</td>
<td>High-performance async API server</td>
</tr>
<tr>
<td><strong>Database</strong></td>
<td>
  <img src="https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Redis_Stack-7.2-DC382D?logo=redis" alt="Redis"/>
</td>
<td>Relational + Vector storage</td>
</tr>
<tr>
<td><strong>AI/ML</strong></td>
<td>
  <img src="https://img.shields.io/badge/Ollama-Local-white" alt="Ollama"/>
  <img src="https://img.shields.io/badge/Gemini-API-8E75B2?logo=google" alt="Gemini"/>
  <img src="https://img.shields.io/badge/FlashRank-Reranking-orange" alt="FlashRank"/>
</td>
<td>Embeddings, LLM inference, Re-ranking</td>
</tr>
<tr>
<td><strong>DevOps</strong></td>
<td>
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker" alt="Docker"/>
</td>
<td>Containerized deployment</td>
</tr>
</table>

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **Docker & Docker Compose** | v2.0+ | Latest |
| **RAM** | 8GB | 16GB+ |
| **Disk Space** | 10GB | 20GB+ |
| **Git** | v2.0+ | Latest |

### Step 1: Clone the Repository

```bash
git clone https://github.com/Iammilansoni/NLPFT-2.git
cd NLPFT-2
```

### Step 2: Configure Environment

```bash
# Copy environment templates
cp Backend/.env.example Backend/.env
cp Frontend/.env.example Frontend/.env.local
```

### Step 3: Set Required Variables

Edit `Backend/.env`:

```env
# Generate a secure key (run this command and paste the output)
# python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your_generated_secret_key_here

# Get from: https://aistudio.google.com/apikey
GEMINI_API_KEY=your_gemini_api_key

# Database passwords
POSTGRES_PASSWORD=your_secure_postgres_password
REDIS_PASSWORD=your_secure_redis_password

# Email configuration (for registration/password reset)
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password  # Use Gmail App Password
```

### Step 4: Launch Services

```bash
# Start all services (first run may take 10-15 minutes to download models)
docker compose up -d --build

# Monitor startup progress
docker compose logs -f
```

### Step 5: Access the Platform

| Service | URL | Credentials |
|---------|-----|-------------|
| 🌐 **Web App** | http://localhost:3000 | Create new account |
| 📚 **API Docs** | http://localhost:8000/docs | - |
| 🔍 **RedisInsight** | http://localhost:8001 | - |
| 🗄️ **pgAdmin** | http://localhost:5050 | admin@example.com / admin123 |
| 📊 **Redis Commander** | http://localhost:8081 | admin / admin123 |

### Step 6: Getting Started

1. **Register** → Create your account at `/auth/register`
2. **Create Template** → Define your first API template
3. **Generate Dataset** → Use AI to create training data
4. **Query** → Search with natural language!

---

## ⚙️ Environment Setup

### Backend Environment Variables

<details>
<summary><strong>📄 Backend/.env Configuration</strong></summary>

| Variable | Required | Description |
|:---------|:--------:|:------------|
| `SECRET_KEY` | ✅ | JWT signing key (min 32 chars) |
| `GEMINI_API_KEY` | ✅ | Google Gemini API key for dataset generation |
| `POSTGRES_USER` | ✅ | PostgreSQL username |
| `POSTGRES_PASSWORD` | ✅ | PostgreSQL password |
| `POSTGRES_DB` | ✅ | PostgreSQL database name |
| `REDIS_PASSWORD` | ✅ | Redis password |
| `SMTP_HOST` | ✅ | SMTP server host |
| `SMTP_PORT` | ✅ | SMTP server port |
| `SMTP_USER` | ✅ | SMTP username/email |
| `SMTP_PASSWORD` | ✅ | SMTP password (use App Password for Gmail) |
| `OLLAMA_BASE_URL` | ⚪ | Ollama server URL (default: http://localhost:11434) |
| `PGADMIN_PASSWORD` | ⚪ | pgAdmin password (default: admin123) |
| `REDIS_COMMANDER_PASSWORD` | ⚪ | Redis Commander password (default: admin123) |

</details>

### Frontend Environment Variables

<details>
<summary><strong>📄 Frontend/.env.local Configuration</strong></summary>

| Variable | Required | Description |
|:---------|:--------:|:------------|
| `NEXT_PUBLIC_API_URL` | ✅ | Backend API URL (default: http://localhost:8000) |

</details>

> ⚠️ **Security Warning**: Never commit `.env` files with real credentials to version control!

---

## 🐳 Docker Deployment

### 🏭 Production Mode

All services run in Docker containers:

```bash
# Start all services
docker compose up -d --build

# View logs
docker compose logs -f

# Check service status
docker compose ps

# Stop services
docker compose down

# Full reset (⚠️ removes all data)
docker compose down -v && docker compose up -d --build
```

### 🔧 Development Mode

Infrastructure in Docker, applications run locally with hot reload:

```bash
# Start infrastructure only
docker compose -f docker-compose.dev.yml up -d

# Start Ollama locally (faster model loading)
ollama serve

# Pull required models
ollama pull nomic-embed-text
ollama pull all-minilm  
ollama pull mxbai-embed-large
ollama pull llama3.1:8b-instruct-q4_K_M
```

**Terminal 1 - Backend:**
```bash
cd Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd Frontend
npm install
npm run dev
```

### 📦 Service Ports Reference

| Service | Port | Description |
|---------|------|-------------|
| `frontend` | 3000 | Next.js web application |
| `backend` | 8000 | FastAPI server |
| `postgres` | 5432 | PostgreSQL database |
| `redis` | 6379 | Redis vector database |
| `redis-insight` | 8001 | Redis web UI |
| `redis-commander` | 8081 | Redis management |
| `pgadmin` | 5050 | PostgreSQL admin |
| `ollama` | 11434 | LLM inference server |

---

## 📚 API Documentation

### Interactive API Docs

Once the backend is running, access the full API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Core API Endpoints

<details>
<summary><strong>🔐 Authentication</strong></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register new user |
| `POST` | `/api/v1/auth/login` | User login |
| `POST` | `/api/v1/auth/logout` | User logout |
| `POST` | `/api/v1/auth/refresh` | Refresh access token |
| `POST` | `/api/v1/auth/forgot-password` | Request password reset |

</details>

<details>
<summary><strong>📋 Templates</strong></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/template-builder/templates` | List all templates |
| `POST` | `/api/v1/template-builder/templates` | Create new template |
| `GET` | `/api/v1/template-builder/templates/{id}` | Get template by ID |
| `PUT` | `/api/v1/template-builder/templates/{id}` | Update template |
| `DELETE` | `/api/v1/template-builder/templates/{id}` | Delete template |

</details>

<details>
<summary><strong>📊 Datasets</strong></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/datasets` | List all datasets |
| `POST` | `/api/v1/datasets/generate` | Generate new dataset |
| `GET` | `/api/v1/datasets/{id}` | Get dataset details |
| `DELETE` | `/api/v1/datasets/{id}` | Delete dataset |
| `GET` | `/api/v1/datasets/{id}/download` | Download dataset |

</details>

<details>
<summary><strong>🔍 Query & Search</strong></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/multi-model-query` | Multi-model semantic search |
| `POST` | `/api/v1/embeddings/search` | Vector similarity search |
| `POST` | `/api/v1/ranking/rerank` | Re-rank search results |

</details>

---

## 🧬 Embedding Models

NLPForge supports multiple embedding models via Ollama for different use cases:

| Model | Dimensions | Speed | Memory | Best For |
|:------|:----------:|:-----:|:------:|:---------|
| `nomic-embed-text` | 768 | ⚡ Fast | ~500MB | **Recommended** - General use, balanced performance |
| `all-minilm` | 384 | ⚡⚡ Fastest | ~250MB | Prototyping, low-resource environments |
| `mxbai-embed-large` | 1024 | 🐢 Moderate | ~1.3GB | Maximum accuracy, enterprise applications |

### Changing Embedding Model

1. Navigate to **Settings** → **Embedding Model**
2. Select your preferred model
3. Re-embed existing templates if needed

> 💡 **Tip**: Start with `nomic-embed-text` for most use cases. Switch to `mxbai-embed-large` if you need higher accuracy for complex queries.

---

## 🔧 Troubleshooting

<details>
<summary><strong>🐳 Docker Issues</strong></summary>

### Services fail to start
```bash
# Check logs for specific service
docker compose logs backend
docker compose logs postgres

# Restart everything
docker compose down && docker compose up -d --build
```

### Port already in use
```bash
# Find process using port (Linux/Mac)
lsof -i :8000

# Find process using port (Windows)
netstat -ano | findstr :8000

# Kill the process or change ports in docker-compose.yml
```

### Out of disk space
```bash
# Clean Docker resources
docker system prune -a --volumes
```

</details>

<details>
<summary><strong>🔐 Authentication Issues</strong></summary>

### "SECRET_KEY must be at least 32 characters"
```bash
# Generate a secure key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to Backend/.env
SECRET_KEY=<paste_generated_key>
```

### "GEMINI_API_KEY not set"
1. Visit https://aistudio.google.com/apikey
2. Create a new API key
3. Add to `Backend/.env`: `GEMINI_API_KEY=your_key`

</details>

<details>
<summary><strong>🦙 Ollama Issues</strong></summary>

### Connection refused
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If using Docker, check container
docker compose logs ollama

# Start Ollama manually
ollama serve
```

### Model not found
```bash
# Pull required models
ollama pull nomic-embed-text
ollama pull llama3.1:8b-instruct-q4_K_M
```

</details>

<details>
<summary><strong>🗄️ Database Issues</strong></summary>

### PostgreSQL connection fails
```bash
# Check PostgreSQL status
docker compose ps postgres
docker compose logs postgres

# Reset database
docker compose down -v
docker compose up -d postgres
```

### Redis connection fails
```bash
# Check Redis status
docker compose logs redis

# Test Redis connection
docker compose exec redis redis-cli -a <password> ping
```

</details>

<details>
<summary><strong>🌐 Frontend Issues</strong></summary>

### "Failed to fetch" or API errors
1. Check backend is running: http://localhost:8000/docs
2. Verify `NEXT_PUBLIC_API_URL` in `Frontend/.env.local`
3. Check browser console for CORS errors

### Build fails
```bash
# Clear cache and rebuild
docker compose build --no-cache frontend
```

</details>

### 🧹 Cleanup Commands

```bash
# Stop all services
docker compose down

# Remove all data (⚠️ destructive)
docker compose down -v

# Remove NLPForge images
docker rmi $(docker images | grep nlpforge | awk '{print $3}')

# Full Docker cleanup
docker system prune -a
```

---

## 📁 Project Structure

```
NLPFT-2/
├── 📂 Backend/
│   ├── 📂 app/
│   │   ├── 📂 api/v1/           # REST API endpoints
│   │   │   ├── auth.py          # Authentication routes
│   │   │   ├── datasets.py      # Dataset management
│   │   │   ├── embeddings.py    # Embedding operations
│   │   │   ├── ranking.py       # Re-ranking service
│   │   │   ├── template_builder.py  # Template CRUD
│   │   │   └── telemetry.py     # Metrics & logging
│   │   ├── 📂 core/             # Configuration & utilities
│   │   │   ├── config.py        # App settings
│   │   │   ├── security.py      # JWT & auth
│   │   │   └── logger.py        # Logging setup
│   │   ├── 📂 models/           # Database & Pydantic models
│   │   ├── 📂 services/         # Business logic layer
│   │   └── 📂 nlp/              # NLP processing
│   ├── 📂 alembic/              # Database migrations
│   ├── 📂 datasets/             # Generated datasets
│   ├── 📄 requirements.txt
│   └── 📄 Dockerfile
│
├── 📂 Frontend/
│   ├── 📂 app/                  # Next.js App Router pages
│   │   ├── 📂 auth/             # Login, Register, Forgot Password
│   │   ├── 📂 dashboard/        # Main dashboard
│   │   ├── 📂 templates/        # Template management
│   │   ├── 📂 datasets/         # Dataset management
│   │   ├── 📂 query/            # Search interface
│   │   └── 📂 settings/         # User settings
│   ├── 📂 components/           # Reusable React components
│   ├── 📂 lib/                  # Utilities & API client
│   ├── 📂 contexts/             # React context providers
│   ├── 📄 package.json
│   └── 📄 Dockerfile
│
├── 📄 docker-compose.yml        # Production deployment
├── 📄 docker-compose.dev.yml    # Development setup
└── 📄 README.md
```

---

## 🔒 Security Best Practices

| Practice | Description |
|:---------|:------------|
| 🔑 **Unique Secret Keys** | Generate unique `SECRET_KEY` for each environment |
| 📧 **App Passwords** | Use Gmail App Passwords instead of regular passwords |
| 🔐 **Change Defaults** | Update default passwords for pgAdmin & Redis Commander |
| 🚫 **Never Commit Secrets** | Only commit `.env.example` files, never `.env` |
| 👥 **Multi-Tenant** | All user data is isolated per-user automatically |

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Setup

1. **Fork & Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/NLPFT-2.git
   cd NLPFT-2
   ```

2. **Setup Environment**
   ```bash
   cp Backend/.env.example Backend/.env
   cp Frontend/.env.example Frontend/.env.local
   ```

3. **Start Dev Services**
   ```bash
   docker compose -f docker-compose.dev.yml up -d
   ```

4. **Create Feature Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

5. **Make Changes & Test**
   ```bash
   # Run backend tests
   cd Backend && pytest
   
   # Run frontend tests
   cd Frontend && npm test
   ```

6. **Submit PR**
   ```bash
   git commit -m "feat: add amazing feature"
   git push origin feature/amazing-feature
   # Open Pull Request on GitHub
   ```

### Commit Convention

| Prefix | Description |
|:-------|:------------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation |
| `style:` | Formatting |
| `refactor:` | Code restructuring |
| `test:` | Adding tests |
| `chore:` | Maintenance |

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 👥 Contributors

<table>
<tr>
<td align="center">
<a href="https://github.com/Iammilansoni">
<img src="https://github.com/Iammilansoni.png" width="80px;" alt="Milan Soni"/><br />
<sub><b>Milan Soni</b></sub>
</a>
</td>
<td align="center">
<a href="https://github.com/Avadhi-Singhal">
<img src="https://github.com/Avadhi-Singhal.png" width="80px;" alt="Avadhi Singhal"/><br />
<sub><b>Avadhi Singhal</b></sub>
</a>
</td>
<td align="center">
<a href="https://github.com/AbhilashJoshi09">
<img src="https://github.com/AbhilashJoshi09.png" width="80px;" alt="Abhilash Joshi"/><br />
<sub><b>Abhilash Joshi</b></sub>
</a>
</td>
</tr>
</table>

---

<div align="center">

**⭐ Star this repository if you find it helpful!**

Made with ❤️ by the NLPForge Team

[Report Bug](https://github.com/Iammilansoni/NLPFT-2/issues) • [Request Feature](https://github.com/Iammilansoni/NLPFT-2/issues)

</div>
