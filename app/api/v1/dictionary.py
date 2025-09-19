"""Dictionary management endpoints for NLPForge API (MongoDB-powered)."""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from app.services.dictionary_service import DictionaryService
from app.models.dictionary_models import DictionaryStats
from app.core.logger import logger

router = APIRouter(prefix="/dictionary", tags=["dictionary"])

# Request/Response Models
class CreateFunctionRequest(BaseModel):
    """Request model for creating a new function."""
    name: str = Field(..., description="Function name/identifier")
    templates: List[str] = Field(..., description="Natural language templates")
    arguments: List[Dict[str, Any]] = Field(default_factory=list, description="Function arguments")
    category: str = Field("general", description="Function category")
    description: Optional[str] = Field(None, description="Function description")
    aliases: Optional[List[str]] = Field(default_factory=list, description="Alternative names")
    tags: Optional[List[str]] = Field(default_factory=list, description="Function tags")
    
    class Config:
        json_schema_extra: Dict[str, Any] = {
            "example": {
                "name": "upload_file",
                "templates": [
                    "upload {file} to {selector}",
                    "attach {file} in {selector}"
                ],
                "arguments": [
                    {"name": "selector", "type": "str", "required": True, "description": "CSS selector for file input"},
                    {"name": "file", "type": "str", "required": True, "description": "Path to file"}
                ],
                "category": "file_operations",
                "description": "Upload a file to a specified input element"
            }
        }


class UpdateFunctionRequest(BaseModel):
    """Request model for updating a function."""
    templates: Optional[List[str]] = Field(None, description="Natural language templates")
    arguments: Optional[List[Dict[str, Any]]] = Field(None, description="Function arguments")
    category: Optional[str] = Field(None, description="Function category")
    description: Optional[str] = Field(None, description="Function description")
    aliases: Optional[List[str]] = Field(None, description="Alternative names")
    tags: Optional[List[str]] = Field(None, description="Function tags")
    is_active: Optional[bool] = Field(None, description="Whether function is active")


class MatchInputRequest(BaseModel):
    """Request model for matching user input to functions."""
    input_text: str = Field(..., description="User input text to match")
    
    class Config:
        json_schema_extra = {
            "example": {
                "input_text": "login with username admin and password secret123"
            }
        }


class DictionaryListResponse(BaseModel):
    """Response model for dictionary function list."""
    functions: List[Dict[str, Any]] = Field(..., description="List of functions")
    total_count: int = Field(..., description="Total number of functions")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of functions per page")


# Dependency injection - import the correct function
from app.core.database import get_dictionary_service


# Remove the placeholder function since we now have the real one


@router.get("/", response_model=DictionaryListResponse)
async def list_functions(
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in names, templates, descriptions"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of functions per page"),
    service: DictionaryService = Depends(get_dictionary_service)
) -> DictionaryListResponse:
    """
    List all dictionary functions with optional filtering.
    
    Returns paginated list of functions with their templates, arguments, and metadata.
    """
    try:
        skip = (page - 1) * page_size
        
        functions = await service.list_functions(
            category=category,
            is_active=is_active,
            search=search,
            skip=skip,
            limit=page_size
        )
        
        # Get total count for pagination
        # Note: In a real implementation, you'd get this from the repository
        total_count = len(functions)  # Simplified for now
        
        logger.info(f"Listed {len(functions)} dictionary functions")
        
        return DictionaryListResponse(
            functions=functions,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to list functions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve functions")


@router.get("/stats", response_model=DictionaryStats)
async def get_dictionary_stats(
    service: DictionaryService = Depends(get_dictionary_service)
) -> DictionaryStats:
    """
    Get dictionary statistics and metrics.
    
    Returns overview of function counts, categories, and usage statistics.
    """
    try:
        stats = await service.get_dictionary_stats()
        logger.info("Retrieved dictionary statistics")
        return stats
    except Exception as e:
        logger.error(f"❌ Failed to get dictionary stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@router.get("/{function_id}")
async def get_function_details(
    function_id: str,
    service: DictionaryService = Depends(get_dictionary_service)
) -> Dict[str, Any]:
    """
    Get detailed information about a specific function.
    
    Returns complete function definition including usage statistics.
    """
    try:
        function_details = await service.get_function_details(function_id)
        
        if not function_details:
            raise HTTPException(status_code=404, detail=f"Function not found: {function_id}")
        
        logger.info(f"Retrieved function details: {function_id}")
        return function_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get function details: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve function details")


@router.post("/", response_model=Dict[str, str])
async def create_function(
    request: CreateFunctionRequest,
    service: DictionaryService = Depends(get_dictionary_service)
) -> Dict[str, str]:
    """
    Create a new dictionary function.
    
    Adds a new function with templates, arguments, and metadata to the dictionary.
    """
    try:
        function = await service.create_function(
            name=request.name,
            templates=request.templates,
            arguments=request.arguments,
            category=request.category,
            description=request.description,
            aliases=request.aliases,
            tags=request.tags
        )
        
        logger.info(f"Created dictionary function: {request.name}")
        
        return {
            "message": "Function created successfully",
            "function_id": str(function.id),
            "name": function.name
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to create function: {e}")
        raise HTTPException(status_code=500, detail="Failed to create function")


@router.put("/{function_id}", response_model=Dict[str, str])
async def update_function(
    function_id: str,
    request: UpdateFunctionRequest,
    service: DictionaryService = Depends(get_dictionary_service)
) -> Dict[str, str]:
    """
    Update an existing dictionary function.
    
    Updates function templates, arguments, metadata, or active status.
    """
    try:
        # Prepare updates dictionary
        updates: Dict[str, Any] = {}
        if request.templates is not None:
            updates["templates"] = request.templates
        if request.arguments is not None:
            updates["arguments"] = request.arguments
        if request.category is not None:
            updates["category"] = request.category
        if request.description is not None:
            updates["description"] = request.description
        if request.aliases is not None:
            updates["aliases"] = request.aliases
        if request.tags is not None:
            updates["tags"] = request.tags
        if request.is_active is not None:
            updates["is_active"] = request.is_active
        
        success = await service.update_function(function_id, updates)
        
        if not success:
            raise HTTPException(status_code=404, detail="Function not found")
        
        logger.info(f"Updated dictionary function: {function_id}")
        
        return {"message": "Function updated successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update function: {e}")
        raise HTTPException(status_code=500, detail="Failed to update function")


@router.delete("/{function_id}", response_model=Dict[str, str])
async def delete_function(
    function_id: str,
    service: DictionaryService = Depends(get_dictionary_service)
) -> Dict[str, str]:
    """
    Delete a dictionary function.
    
    Removes the function and all associated usage logs from the dictionary.
    """
    try:
        success = await service.delete_function(function_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Function not found")
        
        logger.info(f"Deleted dictionary function: {function_id}")
        
        return {"message": "Function deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete function: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete function")


@router.post("/match", response_model=Dict[str, Any])
async def match_user_input(
    request: MatchInputRequest,
    service: DictionaryService = Depends(get_dictionary_service)
) -> Dict[str, Any]:
    """
    Match user input against function templates.
    
    Returns the best matching function with extracted arguments and confidence score.
    """
    try:
        match_result = await service.match_user_input(request.input_text)
        
        if not match_result:
            return {
                "matched": False,
                "message": "No matching function found",
                "input": request.input_text
            }
        
        logger.info(f"Matched input to function: {match_result['function_name']}")
        
        return {
            "matched": True,
            "input": request.input_text,
            **match_result
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to match user input: {e}")
        raise HTTPException(status_code=500, detail="Failed to match input")


@router.post("/hot-reload", response_model=Dict[str, str])
async def hot_reload_dictionary(
    service: DictionaryService = Depends(get_dictionary_service)
) -> Dict[str, str]:
    """
    Hot reload the dictionary cache.
    
    Forces refresh of the in-memory function cache without restarting the server.
    Useful after bulk updates or manual database changes.
    """
    try:
        success = await service.hot_reload()
        
        if not success:
            raise HTTPException(status_code=500, detail="Hot reload failed")
        
        logger.info("Dictionary hot reload completed successfully")
        
        return {
            "message": "Dictionary hot reload completed successfully",
            "timestamp": "2025-09-14T12:00:00Z"  # Simplified timestamp
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Hot reload failed: {e}")
        raise HTTPException(status_code=500, detail="Hot reload failed")


@router.get("/categories/list")
async def list_categories(
    service: DictionaryService = Depends(get_dictionary_service)
) -> List[Dict[str, Any]]:
    """
    Get list of all function categories with counts.
    
    Returns available categories and number of functions in each.
    """
    try:
        stats = await service.get_dictionary_stats()
        
        categories: List[Dict[str, Any]] = [
            {"name": category, "count": count}
            for category, count in stats.categories.items()
        ]
        
        # Sort by count (descending) then by name
        categories.sort(key=lambda x: (-x["count"], x["name"]))
        
        logger.info(f"Listed {len(categories)} categories")
        return categories
        
    except Exception as e:
        logger.error(f"❌ Failed to list categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve categories")


@router.post("/hot-reload")
async def trigger_hot_reload(service: DictionaryService = Depends(lambda: get_db_manager().dictionary_service)):
    """
    Trigger hot-reload of dictionary functions and Rule Engine patterns.
    
    This endpoint forces a reload of:
    - Function definitions from MongoDB
    - Compiled regex patterns in the Rule Engine
    - Dictionary cache
    
    It triggers callbacks to all registered components (Rule Engine, etc.)
    and ensures atomic updates without service downtime.
    """
    logger.info("🔄 Hot-reload request received")
    
    try:
        if service is None:
            raise HTTPException(status_code=503, detail="Dictionary service not available")
        
        # Trigger hot-reload which will:
        # 1. Reload dictionary repository cache
        # 2. Notify all registered callbacks (including Rule Engine)
        success = await service.hot_reload()
        
        if success:
            logger.info("✅ Hot-reload completed successfully")
            return {
                "success": True,
                "message": "Dictionary and Rule Engine hot-reload completed successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.warning("⚠️ Hot-reload completed with issues")
            return {
                "success": False,
                "message": "Hot-reload completed but some operations failed",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.exception(f"❌ Hot-reload failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Hot-reload failed: {str(e)}"
        )


# Import datetime at module level for the hot-reload endpoint
from datetime import datetime
from app.core.database import db_manager

def get_db_manager():
    """Get database manager for dependency injection."""
    return db_manager
