# app/api/v1/search.py

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.nlp.semantic_search_service import semantic_search
from app.models.schemas import SearchRequest, SearchResponse

router = APIRouter()

@router.get("/search", response_model=SearchResponse)
async def search_api(req: SearchRequest):
    """
    Perform semantic search on the ingested API dataset using embeddings stored in Redis.
    """
    try:
        top_k = req.top_k or 5
        res = semantic_search(req.query, top_k=top_k)
        return SearchResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))