# NLPForge API Testing Platform - Complete Project Documentation

## 🎯 Project Overview

**NLPForge** is an AI-powered API testing platform that uses Natural Language Processing to understand user queries, generate test datasets, and perform semantic search on API endpoints.

**Tech Stack:**
- **Backend:** FastAPI (Python), PostgreSQL, Redis
- **Frontend:** Next.js 14, React, TypeScript, Tailwind CSS
- **AI/ML:** Sentence Transformers, Vector Embeddings, Gemini API
- **Architecture:** Multi-tenant SaaS with user isolation

---

## 📊 Database Architecture

### PostgreSQL Tables (7 Total)

#### 1. **users** - User Authentication
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    user_name TEXT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,  -- Bcrypt hashed
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 2. **templates** - API Templates
```sql
CREATE TABLE templates (
    t_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    api_name TEXT,
    description TEXT,
    base_url TEXT,
    method TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_templates_user ON templates(user_id);
```

#### 3. **parameters** - API Parameters
```sql
CREATE TABLE parameters (
    parameter_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    t_id UUID REFERENCES templates(t_id) ON DELETE CASCADE,
    name TEXT,
    type TEXT,
    description TEXT
);
CREATE INDEX idx_params_template ON parameters(t_id);
```

#### 4. **expected_responses** - Expected API Responses
```sql
CREATE TABLE expected_responses (
    response_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    t_id UUID REFERENCES templates(t_id) ON DELETE CASCADE,
    status INT,
    fields JSONB
);
CREATE INDEX idx_exp_template ON expected_responses(t_id);
```

#### 5. **metadata** - Template Metadata
```sql
CREATE TABLE metadata (
    metadata_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    t_id UUID REFERENCES templates(t_id) ON DELETE CASCADE,
    confidence NUMERIC,
    remarks TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_metadata_template ON metadata(t_id);
```

#### 6. **csv_data** - Test Data (Millions of Rows)
```sql
CREATE TABLE csv_data (
    csv_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    t_id UUID REFERENCES templates(t_id) ON DELETE CASCADE,
    query TEXT,
    api_name TEXT,
    endpoint TEXT,
    request JSONB,
    response JSONB,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_csv_user_template ON csv_data(user_id, t_id);
CREATE INDEX idx_csv_template ON csv_data(t_id);
```

#### 7. **embeddings** - Vector Metadata
```sql
CREATE TABLE embeddings (
    emb_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    t_id UUID REFERENCES templates(t_id),
    csv_id UUID REFERENCES csv_data(csv_id),
    redis_key TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_embeddings_template ON embeddings(t_id);
CREATE INDEX idx_embeddings_user ON embeddings(user_id);
```

### Redis Vector Storage
**Format:** `embedding:{user_id}:{template_id}:{csv_id}`
- Stores actual vector embeddings (1536 dimensions)
- HNSW index for fast similarity search
- Cosine distance metric

---

## 🗂️ Backend Structure

### File Organization

```
Backend/app/
├── api/v1/
│   ├── auth.py              # Authentication endpoints
│   ├── user_data.py         # User's templates & CSV data (multi-tenant)
│   ├── embeddings.py        # Vector embeddings & search
│   ├── dataset.py           # Dataset generation & upload
│   ├── query.py             # Natural language query processing
│   ├── search.py            # Semantic search
│   └── templates.py         # Template management (runtime CRUD)
│
├── models/
│   ├── __init__.py          # Exports all models
│   ├── database_models.py   # 7 SQLAlchemy ORM models
│   └── schemas/             # Pydantic validation schemas
│       ├── __init__.py
│       ├── auth_schemas.py
│       ├── template_schemas.py
│       ├── csv_data_schemas.py
│       ├── embedding_schemas.py
│       ├── query_schemas.py
│       ├── search_schemas.py
│       ├── dataset_schemas.py
│       └── common_schemas.py
│
├── services/
│   ├── auth_service.py      # JWT, password hashing, user CRUD
│   ├── enterprise_service.py # Multi-tenant data operations
│   ├── template_service.py  # Template management
│   └── email_service.py     # Email notifications
│
├── core/
│   ├── postgres.py          # PostgreSQL connection & session
│   ├── security.py          # JWT tokens, OAuth2
│   ├── config.py            # Environment configuration
│   └── logger.py            # Logging setup
│
├── nlp/
│   ├── query_parser.py      # Parse natural language queries
│   ├── dataset_generator.py # Generate test datasets with Gemini
│   ├── embedding_manager.py # Vector embeddings with Redis
│   └── semantic_search_service.py # Semantic search
│
└── main.py                  # FastAPI application entry point
```

---

## 🔌 API Endpoints

### Authentication (`/api/v1/auth`)

#### POST `/auth/register`
**Description:** Register new user  
**Request:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123",
  "confirm_password": "SecurePass123",
  "full_name": "John Doe"
}
```
**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "user_id": "uuid",
    "email": "user@example.com",
    "username": "johndoe",
    "created_at": "2024-01-01T00:00:00"
  }
}
```

#### POST `/auth/login/json`
**Description:** Login with JSON payload  
**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```
**Response:** Same as register

#### GET `/auth/me`
**Description:** Get current user info  
**Headers:** `Authorization: Bearer <token>`  
**Response:**
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "username": "johndoe",
  "created_at": "2024-01-01T00:00:00"
}
```

---

### User Data Management (`/api/v1/user-data`)

#### POST `/user-data/templates`
**Description:** Create API template  
**Auth:** Required  
**Request:**
```json
{
  "api_name": "user_login",
  "description": "User authentication API",
  "base_url": "https://api.example.com",
  "method": "POST"
}
```

#### GET `/user-data/templates`
**Description:** Get all user's templates  
**Auth:** Required  
**Query Params:** `skip=0&limit=100`

#### GET `/user-data/templates/{template_id}`
**Description:** Get specific template  
**Auth:** Required

#### POST `/user-data/csv-data`
**Description:** Create CSV test data entry  
**Auth:** Required  
**Request:**
```json
{
  "template_id": "uuid",
  "query": "login with username john",
  "api_name": "user_login",
  "endpoint": "/auth/login",
  "request": {"username": "john", "password": "pass123"},
  "response": {"token": "abc123", "status": "success"}
}
```

#### GET `/user-data/csv-data/template/{template_id}`
**Description:** Get CSV data for template (paginated)  
**Auth:** Required  
**Query Params:** `skip=0&limit=1000`

#### GET `/user-data/csv-data/template/{template_id}/count`
**Description:** Count CSV entries for template  
**Auth:** Required

#### GET `/user-data/statistics`
**Description:** Get user statistics  
**Auth:** Required  
**Response:**
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "statistics": {
    "templates": 5,
    "csv_data": 1000,
    "embeddings": 1000
  }
}
```

---

### Query Processing (`/api/v1/query`)

#### POST `/query`
**Description:** Process natural language query through complete pipeline  
**Request:**
```json
{
  "query": "authenticate user with username john and password pass123",
  "generate_dataset": true,
  "num_examples": 50,
  "top_k": 5
}
```
**Response:**
```json
{
  "query": "authenticate user...",
  "intent": "user_login",
  "slots": {"username": "john", "password": "pass123"},
  "confidence": 0.95,
  "best_matches": [
    {"api": "user_login", "score": 0.95, "confidence": 1.0}
  ],
  "dataset_generated": true,
  "dataset_info": {
    "rows": 50,
    "paths": {"csv": "path/to/file.csv"}
  },
  "search_results": [...],
  "dataset_download_url": "/api/v1/dataset/download-file/filename.csv"
}
```

**Pipeline Steps:**
1. Parse query → extract intent & slots
2. Check if dataset exists
3. Generate dataset if needed (using Gemini AI)
4. Embed dataset to Redis
5. Perform vector search
6. Return best matches

#### GET `/stats`
**Description:** Get vector database statistics

#### POST `/reindex/{intent}`
**Description:** Reindex specific intent (regenerate embeddings)

---

### Dataset Management (`/api/v1/dataset`)

#### POST `/dataset/generate`
**Description:** Generate test dataset using Gemini AI  
**Request:**
```json
{
  "api_name": "user_login",
  "description": "User authentication",
  "base_url": "https://api.example.com",
  "method": "POST",
  "parameters": {},
  "num_samples": 50
}
```

#### POST `/dataset/upload`
**Description:** Upload CSV file  
**Content-Type:** `multipart/form-data`

#### GET `/dataset/download-file/{filename}`
**Description:** Download generated CSV file

---

### Embeddings & Search (`/api/v1/embeddings`)

#### POST `/embeddings/create`
**Description:** Create embedding for text  
**Auth:** Required  
**Request:**
```json
{
  "text": "login with username",
  "metadata": {"api": "user_login"}
}
```

#### POST `/embeddings/search`
**Description:** Vector similarity search  
**Auth:** Required  
**Request:**
```json
{
  "query": "authenticate user",
  "top_k": 5,
  "user_id": "uuid",
  "template_id": "uuid"
}
```

#### GET `/embeddings/user`
**Description:** Get user's embeddings  
**Auth:** Required

---

### Template Management (`/api/v1/templates`)

#### GET `/templates/`
**Description:** List all templates

#### GET `/templates/stats`
**Description:** Get template statistics

#### POST `/templates/sync`
**Description:** Sync templates from JSON to database

#### POST `/templates/reload`
**Description:** Hot reload all services (no restart needed)

#### GET `/templates/{intent}`
**Description:** Get specific template by intent

#### POST `/templates/`
**Description:** Create new template

#### PUT `/templates/{intent}`
**Description:** Update template

#### DELETE `/templates/{intent}`
**Description:** Delete template

---

### Search (`/api/v1/search`)

#### POST `/search`
**Description:** Semantic search across all data  
**Request:**
```json
{
  "query": "find login API",
  "top_k": 5,
  "confidence_threshold": 0.7
}
```

---

## 📦 Pydantic Schemas

### Auth Schemas (`auth_schemas.py`)
- `UserCreate` - User registration
- `UserLogin` - User login
- `UserResponse` - User data response
- `Token` - JWT token response
- `ForgotPasswordRequest` - Password reset request
- `ResetPasswordRequest` - Password reset with token
- `ChangePasswordRequest` - Change password
- `VerifyEmailRequest` - Email verification

### Template Schemas (`template_schemas.py`)
- `TemplateCreate/Update/Response` - API templates
- `ParameterCreate/Response` - API parameters
- `ExpectedResponseCreate/Response` - Expected responses
- `MetadataCreate/Response` - Template metadata

### CSV Data Schemas (`csv_data_schemas.py`)
- `CSVDataCreate` - Create test data
- `CSVDataUpdate` - Update test data
- `CSVDataResponse` - Test data response
- `CSVDataBulkCreate` - Bulk insert

### Embedding Schemas (`embedding_schemas.py`)
- `EmbeddingCreate` - Create embedding
- `EmbeddingResponse` - Embedding data
- `VectorSearchRequest` - Search request
- `VectorSearchResult` - Search result

### Query Schemas (`query_schemas.py`)
- `QueryRequest` - Natural language query
- `QueryResponse` - Query processing result

### Search Schemas (`search_schemas.py`)
- `SearchRequest` - Search request
- `SearchResponse` - Search results

### Dataset Schemas (`dataset_schemas.py`)
- `DatasetGenerateRequest` - Generate dataset
- `UploadResponse` - File upload response

### Common Schemas (`common_schemas.py`)
- `ErrorResponse` - Standard error
- `MessageResponse` - Success message
- `HealthResponse` - Health check

---

## 🎨 Frontend Structure

```
Frontend/src/
├── app/
│   ├── auth/
│   │   ├── signup/page.tsx       # Signup page with validation
│   │   ├── signin/page.tsx       # Signin page
│   │   └── forgot-password/page.tsx # Password reset
│   ├── dashboard/                # Dashboard (existing)
│   ├── datasets/                 # Dataset management
│   ├── search/                   # Search interface
│   └── layout.tsx                # Root layout with AuthProvider
│
├── components/
│   ├── ui/                       # Shadcn UI components
│   │   ├── alert.tsx
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   └── ...
│   └── ...
│
├── contexts/
│   ├── auth-context.tsx          # Authentication state management
│   └── sidebar-context.tsx
│
├── hooks/
│   └── ...
│
└── lib/
    ├── api-client.ts             # Axios instance
    └── ...
```

### Auth Context (`auth-context.tsx`)

**Provides:**
- `user` - Current user object
- `token` - JWT token
- `isLoading` - Loading state
- `isAuthenticated` - Auth status
- `login(email, password)` - Login function
- `signup(email, username, password, confirmPassword, fullName)` - Signup function
- `logout()` - Logout function
- `refreshUser()` - Refresh user data

**Usage:**
```tsx
import { useAuth } from '@/contexts/auth-context';

function MyComponent() {
  const { user, isAuthenticated, login, logout } = useAuth();
  
  if (!isAuthenticated) {
    return <LoginForm onLogin={login} />;
  }
  
  return <div>Welcome {user.username}</div>;
}
```

---

## 🔐 Authentication Flow

### Registration Flow
1. User fills signup form (email, username, password, confirm_password)
2. Frontend validates password strength (uppercase, lowercase, digit)
3. POST `/api/v1/auth/register`
4. Backend creates user with bcrypt hashed password
5. Backend generates JWT token
6. Frontend stores token in localStorage
7. Frontend redirects to dashboard

### Login Flow
1. User enters email & password
2. POST `/api/v1/auth/login/json`
3. Backend verifies credentials
4. Backend generates JWT token
5. Frontend stores token & user data
6. Redirect to dashboard

### Protected Routes
1. Frontend checks `isAuthenticated` from auth context
2. If not authenticated, redirect to `/auth/signin`
3. All API calls include `Authorization: Bearer <token>` header
4. Backend validates JWT on protected endpoints

---

## 🧠 NLP Pipeline

### Query Processing Flow

1. **Parse Query** (`query_parser.py`)
   - Extract intent (API name)
   - Extract slots (parameters)
   - Calculate confidence score

2. **Check Dataset** (`dataset_generator.py`)
   - Query Redis for existing embeddings
   - If < 10 embeddings, generate new dataset

3. **Generate Dataset** (if needed)
   - Use Gemini AI to generate test cases
   - Create CSV with format: `query,api,endpoint,request,response`
   - Save to `Backend/datasets/`

4. **Embed Dataset** (`embedding_manager.py`)
   - Generate vector embeddings using Sentence Transformers
   - Store in Redis with key: `embedding:{user_id}:{template_id}:{csv_id}`
   - Create metadata entry in PostgreSQL

5. **Vector Search**
   - Convert query to embedding
   - Perform cosine similarity search in Redis
   - Return top K matches

6. **Return Results**
   - Best matching APIs
   - Confidence scores
   - Dataset download URL

---

## 🔧 Services

### AuthService (`auth_service.py`)
- `hash_password(password)` - Bcrypt hashing
- `verify_password(plain, hashed)` - Verify password
- `create_access_token(data, expires_delta)` - Generate JWT
- `decode_token(token)` - Decode JWT
- `create_user(db, email, password, user_name)` - Create user
- `get_user_by_email(db, email)` - Get user
- `get_user_by_id(db, user_id)` - Get user by ID
- `authenticate_user(db, email, password)` - Authenticate

### EnterpriseService (`enterprise_service.py`)
**Multi-tenant CRUD operations with user isolation**

- `create_template(db, user_id, ...)` - Create template
- `get_user_templates(db, user_id, skip, limit)` - Get templates
- `get_template_by_id(db, t_id, user_id)` - Get template
- `create_csv_data(db, user_id, t_id, ...)` - Create CSV data
- `get_csv_data_by_template(db, user_id, t_id, skip, limit)` - Get CSV data
- `count_csv_data_by_template(db, user_id, t_id)` - Count entries
- `create_embedding_metadata(db, user_id, redis_key, ...)` - Create embedding
- `get_embeddings_by_user(db, user_id, skip, limit)` - Get embeddings
- `delete_embedding_by_redis_key(db, redis_key, user_id)` - Delete embedding
- `get_user_statistics(db, user_id)` - Get stats

---

## 🚀 What's Implemented

### ✅ Backend
- [x] 7 PostgreSQL tables with proper relationships
- [x] Multi-tenant architecture (user isolation)
- [x] JWT authentication with bcrypt password hashing
- [x] User registration & login endpoints
- [x] Protected endpoints with OAuth2
- [x] Template CRUD operations
- [x] CSV data management (optimized for millions of rows)
- [x] Vector embeddings with Redis
- [x] Natural language query processing
- [x] Dataset generation with Gemini AI
- [x] Semantic search with vector similarity
- [x] Hot reload for templates (no restart needed)
- [x] Comprehensive error handling
- [x] Logging system
- [x] Database migrations with Alembic

### ✅ Frontend
- [x] Beautiful signup page with password strength indicator
- [x] Signin page with "Remember me" option
- [x] Forgot password page UI
- [x] Auth context for state management
- [x] Protected routes
- [x] JWT token storage in localStorage
- [x] Responsive design with Tailwind CSS
- [x] Dark mode support
- [x] Form validation
- [x] Error handling with alerts

### ✅ Architecture
- [x] Clean separation of concerns
- [x] Centralized schema organization
- [x] Proper file naming (database_models.py, user_data.py)
- [x] All imports fixed and working
- [x] No duplicate files
- [x] All diagnostics passing

---

## 🔨 What Needs to Be Done

### Backend

#### High Priority
- [ ] **Password Reset Flow**
  - Implement forgot password endpoint
  - Generate reset tokens
  - Send reset emails
  - Implement reset password endpoint

- [ ] **Email Verification**
  - Send verification email on signup
  - Implement email verification endpoint
  - Add `is_verified` check on protected routes

- [ ] **Email Service**
  - Configure SMTP settings
  - Implement email templates
  - Send welcome emails
  - Send password reset emails

- [ ] **API Rate Limiting**
  - Add rate limiting middleware
  - Prevent brute force attacks
  - Limit API calls per user

- [ ] **Input Validation**
  - Add more comprehensive validation
  - Sanitize user inputs
  - Prevent SQL injection

- [ ] **Error Handling**
  - Standardize error responses
  - Add more specific error messages
  - Log errors properly

#### Medium Priority
- [ ] **User Profile Management**
  - Update profile endpoint
  - Change password endpoint
  - Delete account endpoint
  - Upload profile picture

- [ ] **Template Versioning**
  - Track template changes
  - Version history
  - Rollback capability

- [ ] **Bulk Operations**
  - Bulk CSV data upload
  - Bulk template creation
  - Bulk delete operations

- [ ] **Search Improvements**
  - Filter by date range
  - Filter by confidence score
  - Advanced search options

- [ ] **Analytics**
  - Track API usage
  - User activity logs
  - Popular queries
  - Performance metrics

- [ ] **Caching**
  - Cache frequently accessed data
  - Redis caching layer
  - Cache invalidation strategy

#### Low Priority
- [ ] **OAuth Integration**
  - Google OAuth
  - GitHub OAuth
  - Microsoft OAuth

- [ ] **Webhooks**
  - Notify on dataset generation
  - Notify on search results
  - Custom webhook endpoints

- [ ] **Export Features**
  - Export templates as JSON
  - Export CSV data
  - Export search results

- [ ] **API Documentation**
  - Auto-generated OpenAPI docs
  - Interactive API explorer
  - Code examples

---

### Frontend

#### High Priority
- [ ] **Dashboard**
  - Display user statistics
  - Recent queries
  - Quick actions
  - Activity feed

- [ ] **Template Management UI**
  - List templates
  - Create template form
  - Edit template
  - Delete template
  - Template details view

- [ ] **CSV Data Management UI**
  - Upload CSV files
  - View CSV data in table
  - Edit CSV entries
  - Delete CSV entries
  - Pagination

- [ ] **Query Interface**
  - Natural language input
  - Real-time suggestions
  - Display results
  - Download generated datasets

- [ ] **Search Interface**
  - Search bar with filters
  - Display search results
  - Similarity scores
  - Result details

- [ ] **User Profile Page**
  - View profile
  - Edit profile
  - Change password
  - Account settings

#### Medium Priority
- [ ] **Notifications**
  - Toast notifications
  - Email notifications
  - In-app notifications

- [ ] **Data Visualization**
  - Charts for statistics
  - Query trends
  - API usage graphs

- [ ] **Dark Mode Toggle**
  - Theme switcher
  - Persist theme preference

- [ ] **Responsive Design**
  - Mobile optimization
  - Tablet optimization
  - Touch-friendly UI

- [ ] **Loading States**
  - Skeleton loaders
  - Progress indicators
  - Optimistic updates

#### Low Priority
- [ ] **Onboarding**
  - Welcome tour
  - Tutorial videos
  - Help documentation

- [ ] **Keyboard Shortcuts**
  - Quick navigation
  - Command palette

- [ ] **Accessibility**
  - ARIA labels
  - Keyboard navigation
  - Screen reader support

---

## 🐛 Known Issues

### Backend
1. **Email Service Not Configured**
   - Email sending is not implemented
   - Need SMTP configuration

2. **Password Reset Not Implemented**
   - Forgot password endpoint exists but not functional
   - Need to implement token generation and email sending

3. **No Rate Limiting**
   - API endpoints are not rate limited
   - Vulnerable to abuse

4. **Missing Tests**
   - No unit tests
   - No integration tests
   - No end-to-end tests

### Frontend
1. **OAuth Not Implemented**
   - Google/GitHub buttons are placeholders
   - Need to implement OAuth flow

2. **Remember Me Not Functional**
   - Checkbox exists but doesn't persist login
   - Need to implement refresh tokens

3. **No Error Boundaries**
   - App crashes on unhandled errors
   - Need React error boundaries

4. **No Loading States**
   - Forms don't show loading during submission
   - Need loading indicators

---

## 🔄 What Needs to Change

### Architecture Changes

1. **Separate Auth Service**
   - Move auth logic to dedicated microservice
   - Use separate database for auth
   - Implement refresh tokens

2. **Add Redis Caching**
   - Cache user sessions
   - Cache frequently accessed templates
   - Cache search results

3. **Implement Message Queue**
   - Use Celery for background tasks
   - Queue dataset generation
   - Queue email sending

4. **Add API Gateway**
   - Centralized API management
   - Rate limiting
   - Request/response transformation

### Database Changes

1. **Add Indexes**
   - Add more indexes for performance
   - Analyze slow queries
   - Optimize query plans

2. **Add Audit Logs**
   - Track all user actions
   - Store in separate table
   - Implement log rotation

3. **Add Soft Deletes**
   - Don't hard delete data
   - Add `deleted_at` column
   - Implement restore functionality

### Security Changes

1. **Add CORS Configuration**
   - Restrict allowed origins
   - Configure CORS headers properly

2. **Add HTTPS**
   - Force HTTPS in production
   - Configure SSL certificates

3. **Add Input Sanitization**
   - Sanitize all user inputs
   - Prevent XSS attacks
   - Prevent SQL injection

4. **Add Security Headers**
   - Content-Security-Policy
   - X-Frame-Options
   - X-Content-Type-Options

---

## 📝 Environment Variables

### Backend (`.env`)
```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=nlpforge
POSTGRES_PASSWORD=your_password
POSTGRES_DB=nlpforge
DATABASE_URL=postgresql+asyncpg://nlpforge:password@localhost:5432/nlpforge

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
INDEX_NAME=idx:api

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key

# Email (Not Configured)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# App
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
```

### Frontend (`.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 7+

### Backend Setup
```bash
cd Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
alembic upgrade head
python -m uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd Frontend
npm install
cp .env.example .env.local
# Edit .env.local
npm run dev
```

### Access
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 📚 Key Concepts

### Multi-Tenancy
Every table has `user_id` to isolate data between users. All queries filter by `user_id` to ensure users only see their own data.

### Vector Embeddings
Text is converted to 1536-dimensional vectors using Sentence Transformers. Vectors are stored in Redis for fast similarity search.

### Natural Language Processing
User queries are parsed to extract intent (API name) and slots (parameters). The system uses pattern matching and semantic similarity.

### Dataset Generation
Gemini AI generates realistic test cases based on API descriptions. Generated data is stored in CSV format and embedded for search.

### Semantic Search
Vector similarity search finds the most relevant APIs based on query meaning, not just keywords.

---

## 🎯 Success Metrics

### Performance
- API response time < 200ms
- Vector search < 50ms
- Support 1M+ CSV rows per user
- Handle 1000+ concurrent users

### Quality
- 95%+ query intent accuracy
- 90%+ search relevance
- Zero data leakage between users
- 99.9% uptime

---

## 📞 Support & Contact

For questions or issues, refer to:
- API Documentation: `/docs`
- GitHub Issues: (Add your repo URL)
- Email: (Add support email)

---

**Last Updated:** 2024-01-15  
**Version:** 1.0.0  
**Status:** In Development 🚧
