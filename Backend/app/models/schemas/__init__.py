"""
Pydantic Schemas for PostgreSQL Models
All request/response validation schemas organized by domain
"""

# Auth schemas
from .auth_schemas import (
    UserBase,
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    TokenData,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    VerifyEmailRequest,
)

# Template schemas
from .template_schemas import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    ParameterCreate,
    ParameterResponse,
    ExpectedResponseCreate,
    ExpectedResponseResponse,
    MetadataCreate,
    MetadataResponse,
)

# CSV Data schemas
from .csv_data_schemas import (
    CSVDataCreate,
    CSVDataUpdate,
    CSVDataResponse,
    CSVDataBulkCreate,
)

# Embedding schemas
from .embedding_schemas import (
    EmbeddingCreate,
    EmbeddingResponse,
    VectorSearchRequest,
    VectorSearchResult,
)

# Common schemas
from .common_schemas import (
    ErrorResponse,
    MessageResponse,
    HealthResponse,
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
    # Common
    "ErrorResponse",
    "MessageResponse",
    "HealthResponse",
]
