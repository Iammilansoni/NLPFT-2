"""
Pydantic Schemas for PostgreSQL Models
All request/response validation schemas organized by domain
"""

# Auth schemas
from .auth_schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    Token,
    TokenData,
    UserBase,
    UserCreate,
    UserLogin,
    UserResponse,
    VerifyEmailRequest,
)

# Common schemas
from .common_schemas import (
    ErrorResponse,
    HealthResponse,
    MessageResponse,
)

# CSV Data schemas
from .csv_data_schemas import (
    CSVDataBulkCreate,
    CSVDataCreate,
    CSVDataResponse,
    CSVDataUpdate,
)

# Dataset schemas
from .dataset_schemas import (
    DatasetGenerateRequest,
    UploadResponse,
)

# Embedding schemas
from .embedding_schemas import (
    DatasetEmbeddingStatus,
    # Dataset models
    DatasetInfo,
    # Basic CRUD
    EmbeddingCreate,
    EmbeddingError,
    EmbeddingResponse,
    # Enums
    EmbeddingStatus,
    # Internal models
    EmbeddingTask,
    EmbedProgressResponse,
    ErrorCode,
    # Error responses
    ModelMismatchError,
    # Request models
    ReembedDatasetRequest,
    # Response models
    ReembedDatasetResponse,
    SearchDatasetRequest,
    SearchDatasetResponse,
    SearchResult,
    VectorSearchRequest,
    VectorSearchResult,
)

# Model schemas
from .model_schemas import (
    ModelConfigResponse,
    ModelFilterRequest,
    ModelListResponse,
    ModelResponse,
)

# Ranking schemas (Two-Stage AI Ranking Engine)
from .ranking_schemas import (
    AlternativeAPI,
    DetailedRankedResult,
    DetailedRankingResponse,
    RankedResult,
    RankingRequest,
    RankingResponse,
    RerankerInfoResponse,
    SemanticRetrievalMetadata,
    # Semantic Retrieval Pipeline
    SemanticRetrievalRequest,
    SemanticRetrievalResponse,
    Stage1Result,
)

# Search schemas
from .search_schemas import (
    SearchRequest,
    SearchResponse,
)

# Template schemas
from .template_schemas import (
    ExpectedResponseCreate,
    ExpectedResponseResponse,
    MetadataCreate,
    MetadataResponse,
    ParameterCreate,
    ParameterResponse,
    TemplateCreate,
    TemplateResponse,
    TemplateUpdate,
)

__all__ = [
    # Auth
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",
    "TokenData",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "ChangePasswordRequest",
    "VerifyEmailRequest",
    # Templates
    "TemplateCreate",
    "TemplateUpdate",
    "TemplateResponse",
    "ParameterCreate",
    "ParameterResponse",
    "ExpectedResponseCreate",
    "ExpectedResponseResponse",
    "MetadataCreate",
    "MetadataResponse",
    # CSV Data
    "CSVDataCreate",
    "CSVDataUpdate",
    "CSVDataResponse",
    "CSVDataBulkCreate",
    # Embeddings
    "EmbeddingCreate",
    "EmbeddingResponse",
    "VectorSearchRequest",
    "VectorSearchResult",
    "EmbeddingStatus",
    "ErrorCode",
    "ModelMismatchError",
    "EmbeddingError",
    "DatasetInfo",
    "DatasetEmbeddingStatus",
    "ReembedDatasetRequest",
    "SearchDatasetRequest",
    "ReembedDatasetResponse",
    "SearchResult",
    "SearchDatasetResponse",
    "EmbedProgressResponse",
    "EmbeddingTask",
    # Search
    "SearchRequest",
    "SearchResponse",
    # Query
    "QueryRequest",
    "QueryResponse",
    # Dataset
    "DatasetGenerateRequest",
    "UploadResponse",
    # Common
    "ErrorResponse",
    "MessageResponse",
    "HealthResponse",
    # Models
    "ModelResponse",
    "ModelListResponse",
    "ModelConfigResponse",
    "ModelFilterRequest",
    # Ranking (Two-Stage AI Ranking Engine)
    "RankingRequest",
    "RankedResult",
    "RankingResponse",
    "Stage1Result",
    "DetailedRankedResult",
    "DetailedRankingResponse",
    "RerankerInfoResponse",
    # Semantic Retrieval Pipeline
    "SemanticRetrievalRequest",
    "SemanticRetrievalResponse",
    "SemanticRetrievalMetadata",
    "AlternativeAPI",
]
