# NLPForge-Tester

NLPForge-Tester is an AI-powered UI testing framework that leverages JSON, NLP, and Python to automate and validate user interface interactions intelligently.

## Overview

A modular FastAPI-based NLP project that provides comprehensive natural language processing capabilities for automated testing and validation. The application converts natural language instructions into structured test steps using advanced NLP pipeline components.

## Features

- 🚀 **FastAPI Framework** - High-performance async API with automatic documentation
- 🔍 **NLP Pipeline** - Rule engine, semantic matching, ranking, and assembly components
- 📊 **Health Monitoring** - Comprehensive health checks for production deployment
- 🐳 **Docker Support** - Production-ready containerization with health checks
- 📁 **Function Dictionary** - 20+ predefined browser automation functions
- 🗄️ **Database Integration** - MongoDB support with async operations
- 📈 **Metrics & Monitoring** - System resource monitoring and request tracking

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

## API Endpoints

### Health & Monitoring
- `GET /health/` - Simple health check
- `GET /health/ready` - Readiness probe for Kubernetes
- `GET /health/live` - Liveness probe for Kubernetes
- `GET /health/simple` - Basic health status for load balancers
- `GET /health/metrics` - Prometheus-compatible metrics (consolidated endpoint)

### Text Processing
- `POST /convert/` - Convert natural language to structured test steps
- `GET /dictionary/` - Retrieve function dictionary entries
- `POST /dictionary/` - Add new dictionary entries

### Monitoring
All monitoring functionality is consolidated in the health endpoints:
- `GET /health/` - Comprehensive JSON health status and metrics
- `GET /health/metrics` - Prometheus-compatible metrics format

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/Iammilansoni/NLPForge-Tester.git
   cd NLPForge-Tester
   ```

2. **Set up Python virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health/
   - Convert Endpoint: http://localhost:8000/convert/

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

## Technology Stack

- **Framework**: FastAPI 0.104.1
- **Language**: Python 3.11+
- **Database**: MongoDB (with motor async driver)
- **NLP**: Custom rule engine and semantic matching
- **Monitoring**: psutil for system metrics
- **Containerization**: Docker & Docker Compose
- **Documentation**: Automatic OpenAPI/Swagger generation

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
