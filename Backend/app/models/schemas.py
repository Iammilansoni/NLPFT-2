"""Pydantic schemas for NLPForge API."""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Comprehensive health check response schema."""
    status: str = Field(..., description="Overall system status (healthy, warning, degraded, unhealthy)")
    version: str = Field(..., description="Application version")
    timestamp: str = Field(..., description="Health check timestamp in ISO format")
    checks: Dict[str, Any] = Field(..., description="Detailed component health statuses and metrics")


class ConvertRequest(BaseModel):
    """Request schema for text conversion."""
    text: str = Field(..., description="Text to convert", min_length=1)
    target_format: str = Field(..., description="Target format for conversion")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional conversion options")


class ConvertResponse(BaseModel):
    """Response schema for text conversion."""
    original_text: str = Field(..., description="Original input text")
    converted_text: str = Field(..., description="Converted text")
    target_format: str = Field(..., description="Target format used")
    processing_time: float = Field(..., description="Processing time in seconds")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class DictionaryEntry(BaseModel):
    """Schema for dictionary entries."""
    word: str = Field(..., description="The word or phrase")
    definition: str = Field(..., description="Definition of the word")
    category: Optional[str] = Field(None, description="Category or domain")
    examples: Optional[List[str]] = Field(default_factory=list, description="Usage examples")
    synonyms: Optional[List[str]] = Field(default_factory=list, description="Synonyms")
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


class DictionaryResponse(BaseModel):
    """Response schema for dictionary operations."""
    entries: List[DictionaryEntry] = Field(..., description="Dictionary entries")
    total_count: int = Field(..., description="Total number of entries")
    page: Optional[int] = Field(None, description="Current page number")
    page_size: Optional[int] = Field(None, description="Number of entries per page")


class MetricsResponse(BaseModel):
    """Response schema for system metrics."""
    uptime: float = Field(..., description="System uptime in seconds")
    requests_count: int = Field(..., description="Total number of requests processed")
    active_connections: int = Field(..., description="Number of active connections")
    memory_usage: Dict[str, float] = Field(..., description="Memory usage statistics")
    cpu_usage: float = Field(..., description="CPU usage percentage")
    disk_usage: Dict[str, float] = Field(..., description="Disk usage statistics")
    cache_stats: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Cache statistics")


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    request_id: Optional[str] = Field(None, description="Request ID for tracking")

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = None

class ResultItem(BaseModel):
    query: str
    api: str
    endpoint: str
    request: Dict[str, Any]
    response: Dict[str, Any]
    cosine_distance: float
    cosine_similarity: float

class SearchResponse(BaseModel):
    input_query: str
    top_k: int
    results: List[ResultItem]

class DatasetGenerateRequest(BaseModel):
    seed_query: str
    api: str
    endpoint: str
    request: Dict[str, Any]
    response: Dict[str, Any]
    examples: int = 50
    
class UploadResponse(BaseModel):
    message: str
    filename: str