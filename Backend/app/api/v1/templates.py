"""
Template Management API - REST endpoints for runtime template management
Enables CRUD operations on API templates without code changes
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from app.services.template_service import get_template_service
from app.core.logger import logger
from app.nlp.query_parser import get_query_parser
from app.nlp.smart_dataset_generator import SmartDatasetGenerator

router = APIRouter(prefix="/templates", tags=["templates"])


# Pydantic models for request/response
class ParameterModel(BaseModel):
    """API parameter model"""
    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type (string, integer, etc.)")
    required: bool = Field(default=True, description="Whether parameter is required")
    description: Optional[str] = Field(None, description="Parameter description")


class TemplateCreateModel(BaseModel):
    """Template creation model"""
    api_name: str = Field(..., description="Unique API identifier")
    description: str = Field(..., description="API description")
    endpoint: str = Field(..., description="API endpoint path")
    method: str = Field(..., description="HTTP method (GET, POST, PUT, DELETE)")
    intent_keywords: List[str] = Field(..., description="Keywords for intent detection")
    parameters: List[ParameterModel] = Field(..., description="API parameters")
    example_queries: Optional[List[str]] = Field(None, description="Example queries")
    response_format: Optional[Dict] = Field(None, description="Expected response structure")


class TemplateUpdateModel(BaseModel):
    """Template update model (all fields optional)"""
    description: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    intent_keywords: Optional[List[str]] = None
    parameters: Optional[List[ParameterModel]] = None
    example_queries: Optional[List[str]] = None
    response_format: Optional[Dict] = None


class TemplateResponse(BaseModel):
    """Template response model"""
    api_name: str
    description: str
    endpoint: str
    method: str
    intent_keywords: List[str]
    parameters: List[Dict]
    example_queries: List[str]
    response_format: Optional[Dict] = None


class SyncResponse(BaseModel):
    """Sync operation response"""
    success: bool
    message: str
    added: int
    updated: int
    total: int


class ReloadResponse(BaseModel):
    """Reload operation response"""
    success: bool
    message: str
    services_reloaded: List[str]
    templates_count: int


class StatsResponse(BaseModel):
    """Statistics response"""
    total_templates: int
    template_names: List[str]
    cache_stats: Dict


@router.get("/", response_model=List[TemplateResponse])
async def list_templates():
    """
    List all API templates
    
    Returns:
        List of all templates with full details
    """
    try:
        template_service = get_template_service()
        templates = template_service.get_all_templates()
        
        logger.info(f"Retrieved {len(templates)} templates")
        
        return [
            TemplateResponse(
                api_name=name,
                description=template.get("description", ""),
                endpoint=template.get("endpoint", ""),
                method=template.get("method", "POST"),
                intent_keywords=template.get("intent_keywords", []),
                parameters=template.get("parameters", []),
                example_queries=template.get("example_queries", []),
                response_format=template.get("response_format")
            )
            for name, template in templates.items()
        ]
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list templates: {str(e)}"
        )


@router.get("/{intent}", response_model=TemplateResponse)
async def get_template(intent: str):
    """
    Get a specific API template by intent
    
    Args:
        intent: API intent name
        
    Returns:
        Template details
    """
    try:
        template_service = get_template_service()
        template = template_service.get_template(intent)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template not found: {intent}"
            )
        
        logger.info(f"Retrieved template: {intent}")
        
        return TemplateResponse(
            api_name=intent,
            description=template.get("description", ""),
            endpoint=template.get("endpoint", ""),
            method=template.get("method", "POST"),
            intent_keywords=template.get("intent_keywords", []),
            parameters=template.get("parameters", []),
            example_queries=template.get("example_queries", []),
            response_format=template.get("response_format")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template {intent}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template: {str(e)}"
        )


@router.post("/", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(template: TemplateCreateModel):
    """
    Create a new API template
    
    Args:
        template: Template data
        
    Returns:
        Created template
    """
    try:
        template_service = get_template_service()
        
        # Check if template already exists
        existing = template_service.get_template(template.api_name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Template already exists: {template.api_name}"
            )
        
        # Convert Pydantic model to dict
        template_dict = {
            "api_name": template.api_name,
            "description": template.description,
            "endpoint": template.endpoint,
            "method": template.method,
            "intent_keywords": template.intent_keywords,
            "parameters": [p.dict() for p in template.parameters],
            "example_queries": template.example_queries or [],
            "response_format": template.response_format
        }
        
        # Create template
        created = template_service.create_template(template_dict)
        
        if not created:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create template"
            )
        
        logger.info(f"✅ Created new template: {template.api_name}")
        
        # Trigger hot reload
        await reload_services()
        
        return TemplateResponse(
            api_name=template.api_name,
            description=template.description,
            endpoint=template.endpoint,
            method=template.method,
            intent_keywords=template.intent_keywords,
            parameters=[p.dict() for p in template.parameters],
            example_queries=template.example_queries or [],
            response_format=template.response_format
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}"
        )


@router.put("/{intent}", response_model=TemplateResponse)
async def update_template(intent: str, updates: TemplateUpdateModel):
    """
    Update an existing API template
    
    Args:
        intent: API intent name
        updates: Fields to update
        
    Returns:
        Updated template
    """
    try:
        template_service = get_template_service()
        
        # Check if template exists
        existing = template_service.get_template(intent)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template not found: {intent}"
            )
        
        # Build updates dict (only include non-None fields)
        updates_dict = {}
        if updates.description is not None:
            updates_dict["description"] = updates.description
        if updates.endpoint is not None:
            updates_dict["endpoint"] = updates.endpoint
        if updates.method is not None:
            updates_dict["method"] = updates.method
        if updates.intent_keywords is not None:
            updates_dict["intent_keywords"] = updates.intent_keywords
        if updates.parameters is not None:
            updates_dict["parameters"] = [p.dict() for p in updates.parameters]
        if updates.example_queries is not None:
            updates_dict["example_queries"] = updates.example_queries
        if updates.response_format is not None:
            updates_dict["response_format"] = updates.response_format
        
        # Update template
        updated = template_service.update_template(intent, updates_dict)
        
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update template"
            )
        
        logger.info(f"✅ Updated template: {intent}")
        
        # Trigger hot reload
        await reload_services()
        
        # Get updated template
        template = template_service.get_template(intent)
        
        return TemplateResponse(
            api_name=intent,
            description=template.get("description", ""),
            endpoint=template.get("endpoint", ""),
            method=template.get("method", "POST"),
            intent_keywords=template.get("intent_keywords", []),
            parameters=template.get("parameters", []),
            example_queries=template.get("example_queries", []),
            response_format=template.get("response_format")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template {intent}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update template: {str(e)}"
        )


@router.delete("/{intent}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(intent: str):
    """
    Delete an API template
    
    Args:
        intent: API intent name
    """
    try:
        template_service = get_template_service()
        
        # Check if template exists
        existing = template_service.get_template(intent)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template not found: {intent}"
            )
        
        # Delete template
        deleted = template_service.delete_template(intent)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete template"
            )
        
        logger.info(f"✅ Deleted template: {intent}")
        
        # Trigger hot reload
        await reload_services()
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template {intent}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete template: {str(e)}"
        )


@router.post("/sync", response_model=SyncResponse)
async def sync_from_json():
    """
    Sync templates from api_template.json to database
    
    Returns:
        Sync statistics
    """
    try:
        template_service = get_template_service()
        
        # Sync from JSON
        stats = template_service.sync_from_json()
        
        logger.info(f"✅ Synced templates from JSON: {stats}")
        
        # Trigger hot reload
        await reload_services()
        
        return SyncResponse(
            success=True,
            message="Templates synced successfully from JSON",
            added=stats.get("added", 0),
            updated=stats.get("updated", 0),
            total=stats.get("total", 0)
        )
    except Exception as e:
        logger.error(f"Error syncing templates from JSON: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync templates: {str(e)}"
        )


@router.post("/reload", response_model=ReloadResponse)
async def reload_services():
    """
    Hot reload all services (query parser, dataset generator)
    No server restart required
    
    Returns:
        Reload status
    """
    try:
        template_service = get_template_service()
        
        # Reload template service from database
        template_service.reload_templates()
        templates = template_service.get_all_templates()
        
        # Reload query parser
        query_parser = get_query_parser()
        query_parser.reload_patterns()
        
        # Reload dataset generator
        # Note: We create a new instance to reload templates
        # In production, you'd want a global instance with reload method
        dataset_generator = SmartDatasetGenerator()
        dataset_generator.reload_templates()
        
        logger.info(f"✅ Hot reload complete: {len(templates)} templates loaded")
        
        return ReloadResponse(
            success=True,
            message=f"Successfully reloaded {len(templates)} templates",
            services_reloaded=["template_service", "query_parser", "dataset_generator"],
            templates_count=len(templates)
        )
    except Exception as e:
        logger.error(f"Error reloading services: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload services: {str(e)}"
        )


@router.get("/stats", response_model=StatsResponse)
async def get_statistics():
    """
    Get template statistics
    
    Returns:
        Statistics about templates and cache
    """
    try:
        template_service = get_template_service()
        templates = template_service.get_all_templates()
        
        cache_stats = {
            "template_count": len(templates),
            "cache_enabled": True,
            "source": "database"
        }
        
        return StatsResponse(
            total_templates=len(templates),
            template_names=list(templates.keys()),
            cache_stats=cache_stats
        )
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )
