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
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-environment-setup">Environment Setup</a> •
  <a href="#-docker-deployment">Docker</a> •
  <a href="#-development">Development</a> •
  <a href="#-troubleshooting">Troubleshooting</a>
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
Query: "Authenticate with email milansoni@nlpforge.com and password secure123"

↓ NLPForge Processing ↓

{
  "api_name": "User_Login",
  "base_url": "https://api.nlpforge.com",
  "endpoint": "/auth/login",
  "method": "POST",
  "extracted_request_body": {
    "email": "milansoni@nlpforge.com",
    "password": "secure123"
  }
}
```

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

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui |
| **Backend** | FastAPI, Python 3.11+, SQLAlchemy, Pydantic |
| **Database** | PostgreSQL 15 (metadata), Redis Stack (vectors) |
| **AI/ML** | Ollama (embeddings + LLM), FlashRank (re-ranking), Gemini (dataset generation) |
| **DevOps** | Docker, Docker Compose |

---

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (v2.0+)
- **16GB RAM** recommended (for LLM inference)
- **20GB disk space** (for models)
- **Git**

### Step 1: Clone the Repository

```bash
git clone https://github.com/Iammilansoni/NLPForge-Tester.git
cd NLPForge-Tester
```

### Step 2: Set Up Environment Variables

```bash
# Copy example environment files
cp Backend/.env.example Backend/.env
cp Frontend/.env.example Frontend/.env.local
```

**Edit `Backend/.env`** with your actual credentials:

```bash
# REQUIRED: Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy the output and set SECRET_KEY in Backend/.env

# REQUIRED for dataset generation: Get Gemini API key
# Visit: https://aistudio.google.com/apikey

# REQUIRED: Configure SMTP for email (registration, password reset)
# For Gmail, use App Passwords (not your regular password)
# Create at: Google Account → Security → 2-Step Verification → App Passwords
```

### Step 3: Start All Services

```bash
# Start everything (first run downloads models automatically - may take 10-15 minutes)
docker compose up -d --build

# View logs to monitor startup progress
docker compose logs -f
```

### Step 4: Access the Application

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| **Frontend** | http://localhost:3000 | Register new account |
| **API Docs** | http://localhost:8000/docs | - |
| **RedisInsight** | http://localhost:8001 | - |
| **Redis Commander** | http://localhost:8081 | admin / admin123 |
| **pgAdmin** | http://localhost:5050 | admin@example.com / admin123 |

### Step 5: First Steps

1. **Register** an account at http://localhost:3000/auth/register
2. **Create a Template** in the Templates page
3. **Generate Dataset** to create training data  
4. **Search** using natural language on the Dashboard

---

## ⚙️ Environment Setup

### Backend Environment (`Backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ Yes | JWT signing key (min 32 chars). Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key for dataset generation. Get from [AI Studio](https://aistudio.google.com/apikey) |
| `POSTGRES_PASSWORD` | ✅ Yes | PostgreSQL database password |
| `REDIS_PASSWORD` | ✅ Yes | Redis database password |
| `SMTP_USER` | ✅ Yes | Email address for sending emails (registration, password reset) |
| `SMTP_PASSWORD` | ✅ Yes | Email password (for Gmail, use [App Password](https://myaccount.google.com/apppasswords)) |
| `PGADMIN_PASSWORD` | Optional | pgAdmin admin password (default: admin123) |
| `REDIS_COMMANDER_PASSWORD` | Optional | Redis Commander password (default: admin123) |

### Frontend Environment (`Frontend/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | ✅ Yes | Backend API URL (default: http://localhost:8000) |

> **⚠️ Security Note**: Never commit `.env` files with real credentials. Only `.env.example` files should be in version control.

---

## 🐳 Docker Deployment

### Production Mode (Full Docker)

All services run in Docker containers:

```bash
# Start all services
docker compose up -d --build

# View logs
docker compose logs -f

# Stop all services
docker compose down

# Full reset (removes all data)
docker compose down -v
docker compose up -d --build
```

### Development Mode (Hybrid)

Infrastructure in Docker, frontend/backend run locally for hot reload:

```bash
# Start infrastructure only
docker compose -f docker-compose.dev.yml up -d

# Run Ollama locally (faster model loading)
ollama serve

# Pull required models
ollama pull nomic-embed-text
ollama pull all-minilm  
ollama pull mxbai-embed-large
ollama pull llama3.1:8b-instruct-q4_K_M

# Terminal 1: Start Backend
cd Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Terminal 2: Start Frontend
cd Frontend
npm install
npm run dev
```

### Docker Services

| Service | Port(s) | Purpose |
|---------|---------|---------|
| `postgres` | 5432 | Primary database (users, templates, audit logs) |
| `redis` | 6379, 8001 | Vector database + RedisInsight UI |
| `redis-commander` | 8081 | Redis web management UI |
| `pgadmin` | 5050 | PostgreSQL admin UI |
| `ollama` | 11434 | Local LLM & embedding server |
| `backend` | 8000 | FastAPI application |
| `frontend` | 3000 | Next.js web application |

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

## 🔧 Troubleshooting

### Docker Issues

**Problem: Services fail to start**
```bash
# Check logs for specific service
docker compose logs backend
docker compose logs postgres

# Restart everything
docker compose down
docker compose up -d --build
```

**Problem: "Port already in use"**
```bash
# Find what's using the port (Windows)
netstat -ano | findstr :8000

# Find what's using the port (Linux/Mac)
lsof -i :8000

# Change ports in docker-compose.yml if needed
```

**Problem: Database connection fails**
```bash
# Ensure PostgreSQL is healthy
docker compose ps
docker compose logs postgres

# Reset database
docker compose down -v
docker compose up -d --build
```

### Backend Issues

**Problem: "SECRET_KEY must be at least 32 characters"**
```bash
# Generate a secure key
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Add the output to Backend/.env as SECRET_KEY=<generated_key>
```

**Problem: "GEMINI_API_KEY not set"**
1. Visit https://aistudio.google.com/apikey
2. Create a new API key
3. Add to `Backend/.env`: `GEMINI_API_KEY=your_key_here`

**Problem: Ollama connection refused**
```bash
# Check if Ollama is running
docker compose logs ollama

# Or if running locally
curl http://localhost:11434/api/tags
```

### Frontend Issues

**Problem: "Failed to fetch" or API errors**
1. Ensure backend is running: http://localhost:8000/docs
2. Check `Frontend/.env.local` has correct `NEXT_PUBLIC_API_URL`
3. Check browser console for CORS errors

**Problem: Build fails in Docker**
```bash
# Clear Docker cache and rebuild
docker compose build --no-cache frontend
```

### Cleanup Commands

```bash
# Stop all containers
docker compose down

# Remove all containers and volumes (DELETES ALL DATA)
docker compose down -v

# Remove all NLPForge images
docker rmi $(docker images | grep nlpforge | awk '{print $3}')

# Clear Docker system (careful - affects all Docker projects)
docker system prune -a
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
│   ├── .env.example         # Environment template
│   └── requirements.txt
├── Frontend/
│   ├── app/                 # Next.js pages
│   ├── components/          # React components
│   ├── lib/                 # Utilities & API client
│   ├── .env.example         # Environment template
│   └── package.json
├── docker-compose.yml       # Production setup
├── docker-compose.dev.yml   # Development setup
└── README.md
```

---

## 🔒 Security Notes

- **Never commit** `.env` files with real credentials
- **Generate unique** `SECRET_KEY` for production
- **Use App Passwords** for Gmail SMTP (not your regular password)
- **Change default passwords** for pgAdmin and Redis Commander in production
- All data is isolated per user (multi-tenant)

---

## 🤝 Contributing

1. Fork the repository
2. Create environment files from examples
3. Start with `docker compose -f docker-compose.dev.yml up -d`
4. Create a feature branch (`git checkout -b feature/amazing-feature`)
5. Test your changes thoroughly
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Made with ❤️ by 
  <a href="https://github.com/Iammilansoni">Milan Soni</a>, 
  <a href="https://github.com/Avadhi-Singhal">Avadhi Singhal</a>, 
  <a href="https://github.com/AbhilashJoshi09">Abhilash Joshi</a>
</p>
