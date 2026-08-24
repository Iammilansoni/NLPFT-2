"""
Query Schemas - Natural language query processing
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for query endpoint"""
    query: str = Field(..., description="Natural language query", min_length=1)
    generate_dataset: bool = Field(True, description="Whether to generate dataset if needed")
    num_examples: int = Field(50, description="Number of examples to generate", ge=10, le=200)
    top_k: int = Field(5, description="Number of similar results to return", ge=1, le=20)


class QueryResponse(BaseModel):
    """Response model for query endpoint"""
    query: str
    intent: str
    slots: Dict
    confidence: float
    best_matches: List[Dict]
    dataset_generated: bool
    dataset_info: Optional[Dict] = None
    search_results: List[Dict]
    dataset_download_url: Optional[str] = None
