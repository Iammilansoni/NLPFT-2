"""
Search Schemas - Semantic search functionality
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Search request"""
    query: str = Field(..., min_length=1, description="Search query")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results")
    confidence_threshold: Optional[float] = Field(default=0.7, ge=0.0, le=1.0)


class SearchResponse(BaseModel):
    """Search response"""
    query: str
    results: List[Dict[str, Any]]
    total: int
    confidence_threshold: Optional[float] = None
