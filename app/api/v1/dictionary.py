"""Dictionary management endpoints for NLPForge API."""

import json
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import DictionaryEntry, DictionaryResponse
from app.core.logger import logger
from app.core.config import settings

router = APIRouter(prefix="/dictionary", tags=["dictionary"])


@router.get("/", response_model=DictionaryResponse)
async def get_dictionary_entries(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of entries per page")
) -> DictionaryResponse:
    """
    Get dictionary entries with pagination.
    """
    try:
        # Load the function dictionary
        dictionary_path = settings.function_dictionary_path
        if not dictionary_path.exists():
            logger.warning(f"Function dictionary not found at {dictionary_path}")
            return DictionaryResponse(
                entries=[],
                total_count=0,
                page=page,
                page_size=page_size
            )
        
        with open(dictionary_path, 'r', encoding='utf-8') as file:
            functions = json.load(file)
        
        # Convert to DictionaryEntry format
        entries: list[DictionaryEntry] = []
        for func in functions:
            entry = DictionaryEntry(
                word=func.get("name", ""),
                definition=func.get("description", ""),
                category=func.get("category", "automation"),
                examples=func.get("templates", []),
                synonyms=func.get("aliases", [])
            )
            entries.append(entry)
        
        # Apply pagination
        total_count = len(entries)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_entries: list[DictionaryEntry] = entries[start_idx:end_idx]
        
        logger.info(f"Retrieved {len(paginated_entries)} dictionary entries (page {page})")
        
        return DictionaryResponse(
            entries=paginated_entries,  # type: ignore
            total_count=total_count,
            page=page,
            page_size=page_size
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in function dictionary: {e}")
        raise HTTPException(status_code=500, detail="Invalid dictionary format")
    except Exception as e:
        logger.error(f"Error retrieving dictionary entries: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dictionary entries")


@router.get("/{word}")
async def get_dictionary_entry(word: str) -> Dict[str, Any]:
    """
    Get a specific dictionary entry by word/function name.
    """
    try:
        dictionary_path = settings.function_dictionary_path
        if not dictionary_path.exists():
            raise HTTPException(status_code=404, detail="Dictionary not found")
        
        with open(dictionary_path, 'r', encoding='utf-8') as file:
            functions = json.load(file)
        
        # Find the function by name
        for func in functions:
            if func.get("name", "").lower() == word.lower():
                return func
        
        raise HTTPException(status_code=404, detail=f"Word '{word}' not found in dictionary")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving dictionary entry for '{word}': {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dictionary entry")


@router.post("/")
async def add_dictionary_entry(entry: DictionaryEntry) -> Dict[str, str]:
    """
    Add a new dictionary entry.
    """
    # This would typically save to database
    # For now, return a success message
    logger.info(f"Added dictionary entry: {entry.word}")
    return {"message": f"Word '{entry.word}' added successfully"}


@router.delete("/{word}")
async def delete_dictionary_entry(word: str) -> Dict[str, str]:
    """
    Delete a dictionary entry.
    """
    # This would typically delete from database
    # For now, return a success message
    logger.info(f"Deleted dictionary entry: {word}")
    return {"message": f"Word '{word}' deleted successfully"}
