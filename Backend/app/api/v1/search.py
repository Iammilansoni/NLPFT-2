# app/api/v1/search.py
from fastapi import APIRouter, HTTPException, Query
from nlp.semantic_service import semantic_search

router = APIRouter()

@router.get("/search")
def search(query: str = Query(..., min_length=1), top_k: int = 5):
    try:
        return semantic_search(query, top_k=top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
