# app/api/v1/search.py
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from semantic_search import semantic_search  # import your semantic search function

router = APIRouter()

@router.get("/search")
async def search_api(
    q: str = Query(..., description="Query text for semantic search"),
    top_k: Optional[int] = Query(5, description="Number of results to return")
):
    """
    Perform semantic search on the ingested API dataset using embeddings stored in Redis.
    """
    try:
        results = semantic_search(q, top_k)
        return {"status": "success", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
