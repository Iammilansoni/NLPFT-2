"""Pydantic schemas for NLPForge API."""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Error response schema for exception handling."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class SearchRequest(BaseModel):
    """Request schema for semantic search endpoint."""
    query: str = Field(..., description="Search query text")
    top_k: Optional[int] = Field(None, description="Number of results to return")


class ResultItem(BaseModel):
    """Individual search result item."""
    query: str = Field(..., description="Original query")
    api: str = Field(..., description="API name")
    endpoint: str = Field(..., description="API endpoint")
    request: Dict[str, Any] = Field(..., description="Request payload")
    response: Dict[str, Any] = Field(..., description="Response payload")
    cosine_distance: float = Field(..., description="Cosine distance score")
    cosine_similarity: float = Field(..., description="Cosine similarity score")


class SearchResponse(BaseModel):
    """Response schema for semantic search endpoint."""
    input_query: str = Field(..., description="Original input query")
    top_k: int = Field(..., description="Number of results returned")
    results: List[ResultItem] = Field(..., description="List of search results")

class DatasetGenerateRequest(BaseModel):
    """Request schema for dataset generation from plain English query"""
    api_count: Optional[int] = Field(10, description="Number of APIs to generate")
    nl_variations_per_api: Optional[int] = Field(20, description="Number of natural language variations per API")
    use_llm: Optional[bool] = Field(True, description="Use LLM-based paraphrasing")
    embedding_model: Optional[str] = Field("sentence-transformers/all-MiniLM-L6-v2", description="Embedding model to use")
    llm_model: Optional[str] = Field("microsoft/Phi-3-mini-4k-instruct", description="LLM model for generation")
    redis_host: Optional[str] = Field("redis", description="Redis host")
    redis_port: Optional[int] = Field(6379, description="Redis port")
    api_context: Optional[str] = Field("", description="Context for domain-specific APIs")
    # Legacy fields for backward compatibility
    seed_query: Optional[str] = None
    api: Optional[str] = None
    endpoint: Optional[str] = None
    request: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None
    examples: Optional[int] = None

class UploadResponse(BaseModel):
    message: str
    filename: Optional[str] = None
    task_id: Optional[str] = None
    dataset_id: Optional[str] = None