# NLPForge Backend

FastAPI-based backend service for converting natural language test descriptions into structured automation steps.

## Features

- **Enhanced Rule Engine**: Advanced NLP processing with 87.8% success rate
- **REST API**: Three main endpoints for health, conversion, and dictionary management
- **MongoDB Integration**: Function dictionary storage with CRUD operations
- **Prometheus Metrics**: Built-in monitoring and observability
- **Hot Reload**: Real-time updates for dictionary changes

## API Endpoints

### Health Monitoring
- `GET /api/v1/health` - System health status
- `GET /api/v1/health/ready` - Readiness probe
- `GET /api/v1/health/live` - Liveness probe

### NLP Conversion
- `POST /api/v1/convert` - Convert natural language to test steps

### Dictionary Management
- `GET /api/v1/dictionary` - List all functions
- `POST /api/v1/dictionary` - Create new function
- `PUT /api/v1/dictionary/{function_id}` - Update function
- `DELETE /api/v1/dictionary/{function_id}` - Delete function

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the server:
```bash
python -m app.main
```

3. Access API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Architecture

- **FastAPI**: Modern Python web framework
- **MongoDB**: Function dictionary storage
- **Enhanced Rule Engine**: NLP processing core
- **Assembler**: Test step generation
- **Hot Reload**: Dynamic dictionary updates

## Test Suite

Run the comprehensive test suite:
```bash
python test_enhanced_convert.py
```

**Current Performance**: 65/74 test cases passing (87.8% success rate)