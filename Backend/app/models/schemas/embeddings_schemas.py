"""
Embedding Schemas - Vector embeddings metadata (vectors stored in Redis)
Matches: embeddings table + Redis vector storage
Redis Key Format: embedding:{user_id}:{template_id}:{csv_id}
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


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


class VectorSearchRequest(BaseModel):
    """Vector search request"""
    query: str = Field(..., min_length=1, description="Search query")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results")
    user_id: Optional[str] = Field(None, description="Filter by user")
    template_id: Optional[str] = Field(None, description="Filter by template")
    
    class Config:
        populate_by_name = True


class VectorSearchResult(BaseModel):
    """Single vector search result"""
    csv_id: str
    score: float = Field(..., description="Similarity score (0-1)")
    query: Optional[str] = None
    api_name: Optional[str] = None
    endpoint: Optional[str] = None
    request: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None