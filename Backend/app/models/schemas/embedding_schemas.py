"""
Embedding Schemas - Pydantic models for embedding-related API requests and responses

🎯 Key Design Principle: ONE EMBEDDING MODEL PER DATASET
- Once a dataset is embedded with a model, ALL rows use that model
- Re-embedding requires explicit user action and wipes previous embeddings
- MODEL_MISMATCH error returned when search model != dataset model

Redis Key Format: embedding:{user_id}:{template_id}:{csv_id}
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ============= ENUMS =============

class EmbeddingStatus(str, Enum):
    """Embedding job status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ErrorCode(str, Enum):
    """Standardized error codes"""
    MODEL_MISMATCH = "MODEL_MISMATCH"
    DATASET_NOT_FOUND = "DATASET_NOT_FOUND"
    NOT_EMBEDDED = "NOT_EMBEDDED"
    EMBEDDING_IN_PROGRESS = "EMBEDDING_IN_PROGRESS"
    EMBEDDING_FAILED = "EMBEDDING_FAILED"
    INVALID_MODEL = "INVALID_MODEL"


# ============= ERROR RESPONSES =============

class ModelMismatchError(BaseModel):
    """
    MODEL_MISMATCH error response structure
    
    Returned when user tries to search a dataset with a different model
    than what was used to embed it.
    
    Frontend should:
    1. Display this in a modal
    2. Offer "Use Previous Model" (switch user's model setting)
    3. Offer "Re-Embed Dataset" (trigger re-embedding job)
    """
    error: str = Field(default="MODEL_MISMATCH", description="Error code")
    message: str = Field(..., description="Human-readable error message")
    dataset_id: str = Field(..., description="Dataset UUID")
    embedded_with_model: str = Field(..., description="Model used to embed the dataset")
    embedded_with_dimension: int = Field(..., description="Dimension of the embedding model")
    current_model: str = Field(..., description="User's current/requested model")
    current_dimension: int = Field(..., description="Dimension of user's current model")
    embedded_rows: int = Field(..., description="Number of rows embedded")
    actions: Dict[str, str] = Field(
        default_factory=lambda: {
            "use_previous": "Switch your model settings to match the dataset's model",
            "reembed": "Re-embed the entire dataset with your current model (may take time)"
        },
        description="Available actions for the user"
    )
    reembed_endpoint: str = Field(..., description="API endpoint to trigger re-embedding")


class EmbeddingError(BaseModel):
    """Generic embedding error response"""
    error: str = Field(..., description="Error code from ErrorCode enum")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")


# ============= BASIC EMBEDDING CRUD =============

class EmbeddingCreate(BaseModel):
    """Create embedding metadata"""
    template_id: Optional[str] = Field(None, alias="t_id")
    csv_id: Optional[str] = Field(None, description="CSV data ID")
    redis_key: str = Field(..., description="Redis key for vector storage")
    
    class Config:
        populate_by_name = True


class EmbeddingResponse(BaseModel):
    """Embedding response"""
    emb_id: str
    user_id: str
    template_id: Optional[str] = Field(None, alias="t_id")
    csv_id: Optional[str] = None
    redis_key: str
    created_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True


# ============= DATASET MODELS =============

class DatasetInfo(BaseModel):
    """Dataset information with embedding status"""
    dataset_id: str
    name: Optional[str] = None
    template_id: str
    user_id: str
    
    # CSV info
    csv_path: str
    total_rows: int
    
    # Embedding info
    embedding_model: Optional[str] = None
    embedding_dimension: Optional[int] = None
    embedding_status: EmbeddingStatus
    embedding_progress: int = Field(ge=0, le=100, description="Progress 0-100%")
    embedded_rows: int
    
    # Timestamps
    created_at: datetime
    embedding_started_at: Optional[datetime] = None
    embedding_completed_at: Optional[datetime] = None
    
    # Generation info
    generated_with_llm: Optional[str] = None
    scenario_distribution: Optional[Dict[str, float]] = None
    
    class Config:
        from_attributes = True


class DatasetEmbeddingStatus(BaseModel):
    """Detailed embedding status for a dataset"""
    dataset_id: str
    status: EmbeddingStatus
    progress: int = Field(ge=0, le=100)
    
    # Counts
    total_rows: int
    embedded_rows: int
    failed_rows: int = 0
    
    # Model info
    embedding_model: Optional[str] = None
    embedding_dimension: Optional[int] = None
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    
    # Error info
    error_message: Optional[str] = None
    failed_row_ids: Optional[List[str]] = None
    
    # Background task info
    task_id: Optional[str] = None


# ============= REQUEST MODELS =============

class ReembedDatasetRequest(BaseModel):
    """
    Request to re-embed a dataset with a new model
    
    🚨 WARNING: This will:
    1. Delete ALL existing embeddings for the dataset
    2. Start a new embedding job with the specified model
    3. Update dataset's embedding_model field
    """
    model: Optional[str] = Field(
        default=None,
        description="New embedding model to use. If None, uses user's default model."
    )
    force: bool = Field(
        default=False,
        description="Force re-embed even if already embedded with the same model"
    )
    chunk_size: int = Field(
        default=100,
        ge=10,
        le=500,
        description="Number of rows to embed per batch"
    )


class SearchDatasetRequest(BaseModel):
    """
    Request to search dataset vectors
    
    🔒 REQUIRES: dataset_id to enforce model governance
    """
    dataset_id: str = Field(..., description="Dataset UUID (REQUIRED)")
    query: str = Field(..., description="Search query text")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results")
    
    # Optional filtering
    filter_scenario_type: Optional[str] = Field(
        default=None,
        description="Filter by scenario_type: valid, edge_case, extreme_scenario"
    )
    filter_test_category: Optional[str] = Field(
        default=None,
        description="Filter by test_category"
    )


class VectorSearchRequest(BaseModel):
    """Vector search request (simple)"""
    query: str = Field(..., min_length=1, description="Search query")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results")
    user_id: Optional[str] = Field(None, description="Filter by user")
    template_id: Optional[str] = Field(None, description="Filter by template")
    
    class Config:
        populate_by_name = True


# ============= RESPONSE MODELS =============

class ReembedDatasetResponse(BaseModel):
    """Response for re-embed request"""
    success: bool
    message: str
    dataset_id: str
    new_model: str
    new_dimension: int
    task_id: str
    estimated_time_seconds: Optional[int] = None
    total_rows: int
    
    # Warnings if applicable
    warnings: Optional[List[str]] = None


class SearchResult(BaseModel):
    """Individual search result"""
    csv_row_id: str
    query: str
    api: str
    endpoint: Optional[str] = None
    method: Optional[str] = None
    scenario_type: str
    test_category: str
    notes: Optional[str] = None
    similarity_score: float = Field(ge=0, le=1, description="Cosine similarity 0-1")
    
    # Full row data
    request: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None


class VectorSearchResult(BaseModel):
    """Single vector search result (simple)"""
    csv_id: str
    score: float = Field(..., description="Similarity score (0-1)")
    query: Optional[str] = None
    api_name: Optional[str] = None
    endpoint: Optional[str] = None
    request: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchDatasetResponse(BaseModel):
    """Response for search request"""
    success: bool
    query: str
    dataset_id: str
    template_id: str
    
    # Model info
    embedding_model: str
    embedding_dimension: int
    
    # Results
    total_results: int
    results: List[SearchResult]
    
    # Search metadata
    search_time_ms: Optional[int] = None


class EmbedProgressResponse(BaseModel):
    """
    Real-time embedding progress update
    
    Used for WebSocket/polling progress updates
    """
    dataset_id: str
    status: EmbeddingStatus
    progress: int = Field(ge=0, le=100)
    
    # Detailed progress
    current_chunk: int
    total_chunks: int
    rows_processed: int
    rows_total: int
    
    # Timing
    elapsed_seconds: float
    estimated_remaining_seconds: Optional[float] = None
    
    # Current operation
    current_operation: str = Field(
        default="embedding",
        description="Current operation: 'embedding', 'indexing', 'validating'"
    )
    
    # Error tracking
    errors_count: int = 0
    last_error: Optional[str] = None


# ============= INTERNAL MODELS =============

class EmbeddingTask(BaseModel):
    """Internal model for background task tracking"""
    task_id: str
    dataset_id: str
    user_id: str
    template_id: str
    
    # Task config
    model: str
    dimension: int
    chunk_size: int
    
    # Progress
    total_rows: int
    chunk_start: int
    chunk_end: int
    
    # Retry info
    retry_count: int = 0
    max_retries: int = 3
    
    # State
    created_at: datetime
    started_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
