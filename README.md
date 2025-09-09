# NLPForge-Tester

NLPForge-Tester is an AI-powered UI testing framework that leverages JSON, NLP, and Python to automate and validate user interface interactions intelligently.

## Overview

A modular NLP project that provides comprehensive natural language processing capabilities for automated testing and validation.

## Structure

The project is organized with the following structure:

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
│   │       ├── health.py         # Health check endpoints
│   │       └── metrics.py        # Metrics and monitoring endpoints
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
