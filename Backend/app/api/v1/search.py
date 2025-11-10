# app/api/v1/search.py

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.nlp.semantic_search_service import semantic_search
from app.models.schemas import SearchResponse

router = APIRouter()

@router.get("/search", response_model=SearchResponse)
async def search_api(
    query: str = Query(..., description="Search query text"),
    top_k: Optional[int] = Query(5, description="Number of results to return"),
    min_similarity: Optional[float] = Query(0.0, description="Minimum similarity threshold")
):
    """
    Perform semantic search on the ingested API dataset using embeddings stored in Redis.
    """
    try:
        res = semantic_search(query, top_k=top_k)
        return SearchResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))