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