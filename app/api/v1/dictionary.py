"""Dictionary management endpoints for NLPForge API."""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.models.schemas import DictionaryEntry, DictionaryResponse
from app.core.logger import logger

router = APIRouter(prefix="/dictionary", tags=["dictionary"])


@router.get("/", response_model=DictionaryResponse)
async def get_dictionary_entries(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of entries per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in words and definitions")
) -> DictionaryResponse:
    """
    Get dictionary entries with pagination and filtering.
    """
    # TODO: Implement actual dictionary loading and search
    logger.info(f"📚 Dictionary request: page={page}, size={page_size}, category={category}, search={search}")
    
    # Placeholder response
    return DictionaryResponse(
        entries=[],
        total_count=0,
        page=page,
        page_size=page_size
    )


@router.post("/", response_model=DictionaryEntry)
async def add_dictionary_entry(entry: DictionaryEntry) -> DictionaryEntry:
    """
    Add a new dictionary entry.
    """
    # TODO: Implement actual dictionary entry addition
    logger.info(f"📚 Adding dictionary entry: {entry.word}")
    
    # Placeholder response
    return entry


@router.get("/{word}", response_model=DictionaryEntry)
async def get_dictionary_entry(word: str) -> DictionaryEntry:
    """
    Get a specific dictionary entry by word.
    """
    # TODO: Implement actual dictionary lookup
    logger.info(f"📚 Looking up word: {word}")
    
    # Placeholder - return 404 for now
    raise HTTPException(status_code=404, detail=f"Word '{word}' not found in dictionary")


@router.delete("/{word}")
async def delete_dictionary_entry(word: str) -> dict:
    """
    Delete a dictionary entry.
    """
    # TODO: Implement actual dictionary entry deletion
    logger.info(f"📚 Deleting word: {word}")
    
    # Placeholder response
    return {"message": f"Word '{word}' deleted successfully"}