# Schemas Structure

## Location
`Backend/app/models/schemas/`

## Files Overview

All Pydantic schemas match the PostgreSQL database structure (7 main tables).

### 1. **auth_schemas.py** → `users` table
- `UserCreate` - User registration
- `UserLogin` - User authentication  
- `UserResponse` - User data response
- `Token` - JWT token response
- Password reset and verification schemas

### 2. **template_schemas.py** → `templates`, `parameters`, `expected_responses`, `metadata` tables
- `TemplateCreate/Update/Response` - API templates
- `ParameterCreate/Response` - API parameters
- `ExpectedResponseCreate/Response` - Expected API responses
- `MetadataCreate/Response` - Template metadata & confidence scores

### 3. **csv_data_schemas.py** → `csv_data` table
- `CSVDataCreate` - Create test data entry
- `CSVDataUpdate` - Update test data
- `CSVDataResponse` - Test data response
- `CSVDataBulkCreate` - Bulk insert (for millions of rows)

### 4. **embedding_schemas.py** → `embeddings` table + Redis vectors
- `EmbeddingCreate` - Create embedding metadata
- `EmbeddingResponse` - Embedding data
- `VectorSearchRequest` - Search vectors in Redis
- `VectorSearchResult` - Search results

**Redis Key Format:** `embedding:{user_id}:{template_id}:{csv_id}`

### 5. **common_schemas.py** - Shared schemas
- `ErrorResponse` - Standard error format
- `MessageResponse` - Success messages
- `HealthResponse` - Health check format

### 6. **__init__.py** - Central exports
Exports all schemas for easy importing:
```python
from app.models.schemas import UserCreate, TemplateResponse, CSVDataCreate
```

## Database Mapping

| Schema File | PostgreSQL Tables | Purpose |
|------------|------------------|---------|
| `auth_schemas.py` | `users` | Authentication & user management |
| `template_schemas.py` | `templates`, `parameters`, `expected_responses`, `metadata` | API template configuration |
| `csv_data_schemas.py` | `csv_data` | Test data storage (millions of rows) |
| `embedding_schemas.py` | `embeddings` + Redis | Vector embeddings metadata |
| `common_schemas.py` | N/A | Shared response formats |

## Usage Examples

### Import schemas
```python
from app.models.schemas import (
    UserCreate,
    TemplateCreate,
    CSVDataCreate,
    VectorSearchRequest
)
```

### Create user
```python
user_data = UserCreate(
    email="user@example.com",
    username="johndoe",
    password="SecurePass123",
    confirm_password="SecurePass123"
)
```

### Create template
```python
template = TemplateCreate(
    api_name="user_api",
    description="User management API",
    base_url="https://api.example.com",
    method="POST"
)
```

### Search vectors
```python
search = VectorSearchRequest(
    query="find user by email",
    top_k=5,
    template_id="abc-123"
)
```

## Key Features

✅ **Clean separation** - One file per domain  
✅ **Database aligned** - Matches PostgreSQL schema exactly  
✅ **Type safe** - Full Pydantic validation  
✅ **Scalable** - Handles millions of CSV rows  
✅ **Redis integrated** - Vector embeddings support  
✅ **Multi-tenant** - User isolation built-in
