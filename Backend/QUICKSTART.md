# 🚀 Quick Start Guide - NLPForge Backend

Get up and running in 5 minutes!

## Architecture

🧠 **PostgreSQL** → Main Brain (permanent storage)
- Stores: datasets, API metadata, query logs, user data
- Port: 5432

⚡ **Redis** → Fast Memory (speed & search)
- Stores: embeddings, cache, task queues
- Ports: 6379 (Redis), 8001 (RedisInsight UI)

## Prerequisites

- Python 3.9+
- Docker Desktop (optional but recommended)
- Gemini API Key (free at https://makersuite.google.com/)

## Installation (Windows)

### Option 1: Automated Setup (Recommended)

```bash
# Run the setup script
setup.bat
```

This will:
✅ Create virtual environment
✅ Install dependencies
✅ Download spaCy model
✅ Create .env file

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download spaCy model
python -m spacy download en_core_web_md

# 4. Setup environment
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

## Configuration

Edit `.env` file and add your Gemini API key:

```env
GEMINI_API_KEY=your_actual_api_key_here
```

Get your free API key: https://makersuite.google.com/

## Start Services

### Option A: Docker Compose (Easiest)

```bash
docker-compose up -d
```

This starts:
- Backend API (http://localhost:8000)
- PostgreSQL (localhost:5432) 🧠 Main Brain
- Redis (localhost:6379) ⚡ Fast Memory
- RedisInsight UI (http://localhost:8001)

### Option B: Manual

```bash
# Start PostgreSQL
docker run -d -p 5432:5432 ^
  -e POSTGRES_USER=nlpforge ^
  -e POSTGRES_PASSWORD=nlpforge_password ^
  -e POSTGRES_DB=nlpforge ^
  postgres:15-alpine

# Start Redis
docker run -d -p 6379:6379 -p 8001:8001 redis/redis-stack:latest

# Initialize database
python init_database.py

# Start API
python -m app.main
```

## Test the API

### 1. Check API is running

Open browser: http://localhost:8000

You should see:
```json
{
  "name": "NLPForge API",
  "version": "0.1.0",
  "status": "running"
}
```

### 2. Run the demo

```bash
python examples\complete_workflow_test.py
```

This will test multiple scenarios and show you the complete pipeline in action!

### 3. Try your own query

```bash
curl -X POST http://localhost:8000/api/v1/query ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"Authenticate my credentials for Milan and MS3ESD\", \"generate_dataset\": true, \"num_examples\": 50}"
```

Expected response:
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
    {"api": "login", "score": 0.97}
  ],
  "dataset_generated": true
}
```

## API Documentation

Interactive docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Test Different Scenarios

### Login
```bash
curl -X POST http://localhost:8000/api/v1/query ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"Login with john_doe and password123\"}"
```

### Signup
```bash
curl -X POST http://localhost:8000/api/v1/query ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"Create account for john with email john@test.com\"}"
```

### Update Profile
```bash
curl -X POST http://localhost:8000/api/v1/query ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"Update my profile for user milan\"}"
```

### Password Reset
```bash
curl -X POST http://localhost:8000/api/v1/query ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"I forgot my password for milan@example.com\"}"
```

## View Statistics

```bash
curl http://localhost:8000/api/v1/stats
```

## View Generated Datasets

Datasets are saved in:
- **PostgreSQL**: Permanent storage with metadata
- **CSV/JSON**: `Backend/datasets/` directory
- **Redis**: Fast vector embeddings for search

## Database Management

### PostgreSQL (Main Brain 🧠)
```bash
# Connect to PostgreSQL
docker exec -it <postgres-container-id> psql -U nlpforge -d nlpforge

# View tables
\dt

# View datasets
SELECT intent, total_examples, created_at FROM datasets;

# View query logs
SELECT query, intent, confidence, created_at FROM query_logs ORDER BY created_at DESC LIMIT 10;
```

### Redis (Fast Memory ⚡)

Access RedisInsight UI: http://localhost:8001

Or use Redis CLI:
```bash
docker exec -it <redis-container-id> redis-cli

# View all keys
KEYS api:*

# Count documents
DBSIZE

# View a specific document
HGETALL api:<hash>
```

## Troubleshooting

### Redis Connection Error
```bash
# Check if Redis is running
docker ps | findstr redis

# Start Redis if not running
docker run -d -p 6379:6379 redis/redis-stack:latest
```

### PostgreSQL Connection Error
```bash
# Check if PostgreSQL is running
docker ps | findstr postgres

# Start PostgreSQL if not running
docker run -d -p 5432:5432 -e POSTGRES_USER=nlpforge -e POSTGRES_PASSWORD=nlpforge_password -e POSTGRES_DB=nlpforge postgres:15-alpine

# Initialize database
python init_database.py
```

### spaCy Model Error
```bash
python -m spacy download en_core_web_md
```

### Gemini API Error
- Check your API key in `.env`
- Verify quota at https://makersuite.google.com/

### Port Already in Use
```bash
# Change port in .env
PORT=8001

# Or kill the process using port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

## Next Steps

1. ✅ Read full documentation: `README_BACKEND.md`
2. ✅ Explore API endpoints: http://localhost:8000/docs
3. ✅ Integrate with your frontend
4. ✅ Customize API templates in `app/nlp/smart_dataset_generator.py`
5. ✅ Add authentication for production

## Support

- Documentation: `README_BACKEND.md`
- API Docs: http://localhost:8000/docs
- Pipeline Spec: `pipeline_spec.md`

---

🎉 You're all set! Start making intelligent API test queries!
