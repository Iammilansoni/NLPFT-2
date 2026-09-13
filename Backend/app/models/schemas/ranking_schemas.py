"""
Ranking Schemas - Two-Stage AI Ranking Engine
Stage 1: Vector Retrieval (Top-K) from Redis Vector DB
Stage 2: FlashRank Reranking with ms-marco-MiniLM-L-12-v2
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RankingRequest(BaseModel):
    """Request for two-stage ranking"""
    query: str = Field(..., min_length=1, description="Search query text")
    top_k: int = Field(
        default=5, 
        ge=1, 
        le=50, 
        description="Number of candidates to retrieve in Stage 1 (default: 5)"
    )
    include_details: bool = Field(
        default=False,
        description="Include detailed results with Stage 1 and full metadata"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "login with username admin and password secret123",
                "top_k": 5,
                "include_details": False
            }
        }


class RankedResult(BaseModel):
    """Single ranked result from the reranking pipeline"""
    rank: int = Field(..., ge=1, description="Final rank after reranking (1 = best)")
    score: float = Field(..., description="FlashRank cross-encoder relevance score")
    text: str = Field(..., description="Original candidate text (unmodified)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rank": 1,
                "score": 0.9523,
                "text": "Validate login with username test and password 123"
            }
        }


class RankingResponse(BaseModel):
    """Response from two-stage ranking engine"""
    query: str = Field(..., description="Original user query")
    ranked_results: List[RankedResult] = Field(
        ..., 
        description="Final ranked results ordered by FlashRank score (highest first)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "login with username admin and password secret123",
                "ranked_results": [
                    {"rank": 1, "score": 0.9523, "text": "Validate login with username test and password 123"},
                    {"rank": 2, "score": 0.8912, "text": "Login to system with credentials admin/admin123"},
                    {"rank": 3, "score": 0.7845, "text": "Authenticate user with username and password"},
                    {"rank": 4, "score": 0.6723, "text": "Sign in using email and password"},
                    {"rank": 5, "score": 0.5634, "text": "User authentication endpoint"}
                ]
            }
        }


class Stage1Result(BaseModel):
    """Stage 1 vector retrieval result"""
    rank: int = Field(..., ge=1, description="Rank from vector similarity search")
    vector_score: float = Field(..., description="Vector cosine similarity score")
    text: str = Field(..., description="Candidate text")
    api: Optional[str] = Field(None, description="API name")
    endpoint: Optional[str] = Field(None, description="API endpoint")
    method: Optional[str] = Field(None, description="HTTP method (GET, POST, etc.)")


class DetailedRankedResult(BaseModel):
    """Detailed ranked result with full metadata"""
    rank: int = Field(..., ge=1, description="Final rank after reranking")
    score: float = Field(..., description="FlashRank cross-encoder score")
    text: str = Field(..., description="Candidate text")
    query: Optional[str] = Field(None, description="Original query text from dataset")
    api: Optional[str] = Field(None, description="API name")
    endpoint: Optional[str] = Field(None, description="API endpoint")
    method: Optional[str] = Field(None, description="HTTP method (GET, POST, etc.)")
    request: Optional[Dict[str, Any]] = Field(None, description="Request payload")
    response: Optional[Dict[str, Any]] = Field(None, description="Expected response")
    vector_score: Optional[float] = Field(None, description="Original vector similarity score")


class DetailedRankingResponse(BaseModel):
    """Detailed response with Stage 1 and Stage 2 results"""
    query: str = Field(..., description="Original user query")
    stage1_results: List[Stage1Result] = Field(
        ...,
        description="Stage 1 vector retrieval candidates (ordered by vector similarity)"
    )
    ranked_results: List[DetailedRankedResult] = Field(
        ...,
        description="Stage 2 reranked results (ordered by FlashRank score)"
    )
    reranker_model: str = Field(
        default="ms-marco-MiniLM-L-12-v2",
        description="Cross-encoder model used for reranking"
    )
    top_k: int = Field(..., description="Number of candidates retrieved in Stage 1")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "login with admin credentials",
                "stage1_results": [
                    {"rank": 1, "vector_score": 0.92, "text": "Login with admin", "api": "login", "endpoint": "/api/login"}
                ],
                "ranked_results": [
                    {"rank": 1, "score": 0.95, "text": "Login with admin", "api": "login", "endpoint": "/api/login", "vector_score": 0.92}
                ],
                "reranker_model": "ms-marco-MiniLM-L-12-v2",
                "top_k": 5
            }
        }


class RerankerInfoResponse(BaseModel):
    """Information about the reranker model"""
    model_name: str = Field(..., description="Name of the reranker model")
    type: str = Field(..., description="Model type (cross-encoder)")
    framework: str = Field(..., description="Framework used (FlashRank)")
    description: str = Field(..., description="Model description")


# ============================================================================
# Semantic API Retrieval Schemas
# ============================================================================

class SemanticRetrievalRequest(BaseModel):
    """Request for semantic API retrieval pipeline"""
    query: str = Field(..., min_length=1, description="Natural language query to find matching API")
    top_k: int = Field(
        default=5, 
        ge=1, 
        le=50, 
        description="Number of candidates to retrieve from vector search (default: 5)"
    )
    intent_type: Optional[str] = Field(
        None,
        description="Optional query intent hint (create, read, update, delete, query)"
    )
    include_alternatives: bool = Field(
        default=False,
        description="Include alternative API suggestions in response"
    )
    model_name: Optional[str] = Field(
        None,
        description="Optional embedding model name to use for search"
    )
    include_slot_extraction: bool = Field(
        default=True,
        description="Extract values from query and populate the API request schema"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Create a new order for customer 12345 with COD payment",
                "top_k": 10,
                "intent_type": "create",
                "include_alternatives": True,
                "include_slot_extraction": True
            }
        }


class SemanticRetrievalMetadata(BaseModel):
    """Metadata about the semantic retrieval decision"""
    # Query context
    query: Optional[str] = Field(None, description="Original user query")
    top_k: Optional[int] = Field(None, description="Number of candidates requested")
    total_candidates: Optional[int] = Field(None, description="Total candidates retrieved from vector search")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    
    # Template match info - Optional for error responses, populated for successful responses
    t_id: Optional[str] = Field(None, description="Template ID (UUID) from PostgreSQL")
    match_count: Optional[int] = Field(None, description="Number of dataset rows matched to this template")
    avg_similarity: Optional[float] = Field(None, description="Average vector similarity score")
    avg_confidence: Optional[float] = Field(None, description="Average confidence score from dataset")
    intent_alignment: Optional[float] = Field(None, description="Intent alignment bonus (0.0-1.0)")
    dominant_intent: Optional[str] = Field(None, description="Most common intent type among matches")
    domain_tags: List[str] = Field(default=[], description="Domain tags from template")
    matched_queries: List[str] = Field(default=[], description="Preview of matched dataset queries")


class AlternativeAPI(BaseModel):
    """Alternative API suggestion"""
    t_id: str = Field(..., description="Template ID")
    api_name: Optional[str] = Field(None, description="API name")
    endpoint: Optional[str] = Field(None, description="API endpoint")
    method: Optional[str] = Field(None, description="HTTP method")
    avg_similarity: float = Field(..., description="Average similarity score")
    match_count: int = Field(..., description="Number of matches")


class Stage1VectorResult(BaseModel):
    """Stage 1 vector search result"""
    query: str = Field(..., description="Matched query from dataset")
    similarity_score: float = Field(..., description="Vector similarity score (0.0-1.0)")
    t_id: str = Field(..., description="Template ID")


class Stage2RerankResult(BaseModel):
    """Stage 2 re-ranking result"""
    t_id: str = Field(..., description="Template ID")
    avg_similarity: float = Field(..., description="Average similarity across matches")
    avg_confidence_score: float = Field(..., description="Average confidence score")
    final_score: float = Field(..., description="Final weighted score")
    rank: int = Field(..., description="Rank position (1 = best)")
    match_count: int = Field(..., description="Number of dataset matches")


class SemanticRetrievalResponse(BaseModel):
    """Response from semantic API retrieval pipeline"""
    success: bool = Field(..., description="Whether retrieval was successful")
    
    # Stage-by-stage data for dashboard visualization
    stage1_vector_search: Optional[List[Stage1VectorResult]] = Field(
        None,
        description="Stage 1: Vector search results from Redis"
    )
    stage2_reranking: Optional[List[Stage2RerankResult]] = Field(
        None,
        description="Stage 2: Re-ranking results by template"
    )
    final_output: Optional[Dict[str, Any]] = Field(
        None,
        description="Final selected API output"
    )
    
    # Legacy fields for backward compatibility
    api_name: Optional[str] = Field(None, description="Resolved API name from PostgreSQL")
    endpoint: Optional[str] = Field(None, description="API endpoint from PostgreSQL")
    method: Optional[str] = Field(None, description="HTTP method (GET, POST, PUT, DELETE)")
    base_url: Optional[str] = Field(None, description="Base URL for the API")
    request_schema: Optional[Dict[str, Any]] = Field(
        None, 
        description="JSON schema for request body (from PostgreSQL)"
    )
    response_schema: Optional[Dict[str, Any]] = Field(
        None, 
        description="Expected response schema (from PostgreSQL)"
    )
    auth_config: Optional[Dict[str, Any]] = Field(
        None, 
        description="Authentication configuration"
    )
    headers: Optional[Dict[str, Any]] = Field(None, description="Required headers")
    confidence: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0, 
        description="Overall confidence score (0.0-1.0)"
    )
    extracted_request_body: Optional[Dict[str, Any]] = Field(
        None,
        description="Extracted values from query, populated into the API request schema"
    )
    metadata: Optional[SemanticRetrievalMetadata] = Field(
        None, 
        description="Retrieval metadata and statistics"
    )
    alternatives: Optional[List[AlternativeAPI]] = Field(
        None, 
        description="Alternative API suggestions (if requested)"
    )
    error: Optional[str] = Field(None, description="Error message if retrieval failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "api_name": "Create_Customer_Order",
                "endpoint": "/v1/orders",
                "method": "POST",
                "base_url": "https://api.example.com",
                "request_schema": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string"},
                        "items": {"type": "array"}
                    }
                },
                "confidence": 0.8765,
                "metadata": {
                    "t_id": "abc-123-uuid",
                    "match_count": 5,
                    "avg_similarity": 0.92,
                    "avg_confidence": 0.85,
                    "intent_alignment": 0.8,
                    "dominant_intent": "create",
                    "domain_tags": ["ecommerce", "orders"],
                    "matched_queries": ["Create order for customer 12345"]
                },
                "alternatives": [
                    {
                        "t_id": "def-456-uuid",
                        "api_name": "Update_Order",
                        "endpoint": "/v1/orders/{id}",
                        "method": "PUT",
                        "avg_similarity": 0.75,
                        "match_count": 2
                    }
                ]
            }
        }
