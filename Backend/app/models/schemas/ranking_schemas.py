"""
Ranking Schemas - Two-Stage AI Ranking Engine
Stage 1: Vector Retrieval (Top-K) from Redis Vector DB
Stage 2: FlashRank Reranking with ms-marco-MiniLM-L-12-v2
"""

from typing import List, Dict, Any, Optional
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


class DetailedRankedResult(BaseModel):
    """Detailed ranked result with full metadata"""
    rank: int = Field(..., ge=1, description="Final rank after reranking")
    score: float = Field(..., description="FlashRank cross-encoder score")
    text: str = Field(..., description="Candidate text")
    query: Optional[str] = Field(None, description="Original query text from dataset")
    api: Optional[str] = Field(None, description="API name")
    endpoint: Optional[str] = Field(None, description="API endpoint")
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
