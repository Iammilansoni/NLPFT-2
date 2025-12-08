"""
Models API - Model registry endpoints
Provides access to supported embedding models and LLMs
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.postgres import get_db
from app.services.model_service import get_model_service, ModelService
from app.models.schemas import (
    ModelResponse,
    ModelListResponse,
    ModelConfigResponse
)
from app.core.logger import logger

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/", response_model=ModelListResponse)
async def list_models(
    model_type: Optional[str] = Query(None, description="Filter by type: 'embedding' or 'llm'"),
    status: Optional[str] = Query("active", description="Filter by status: 'active' or 'deprecated'"),
    cpu_friendly: Optional[bool] = Query(None, description="Filter CPU-friendly models only"),
    format: Optional[str] = Query(None, description="Response format: 'grouped' (default) or 'flat'"),
    db: AsyncSession = Depends(get_db),
    service: ModelService = Depends(get_model_service)
):
    """
    List all available models
    
    - **type**: Filter by 'embedding' or 'llm' (optional)
    - **status**: Filter by 'active' or 'deprecated' (default: active)
    - **cpu_friendly**: Filter CPU-friendly models (optional)
    - **format**: 'grouped' (default) returns embedding_models/llm_models, 'flat' returns single models array
    
    Returns embedding models, LLM models, and default model IDs
    """
    # Get all models
    all_models = await service.get_all_models(
        db=db,
        model_type=model_type,
        status=status,
        cpu_friendly=cpu_friendly
    )
    
    # Separate by type
    embedding_models = [m for m in all_models if m.type == "embedding"]
    llm_models = [m for m in all_models if m.type == "llm"]
    
    # Get defaults
    defaults = await service.get_default_models(db)
    
    # Convert to response models
    embedding_responses = [
        ModelResponse(
            model_id=m.model_id,
            type=m.type,
            name=m.name,
            dimension=m.dimension,
            context_tokens=m.context_tokens,
            cpu_friendly=bool(m.cpu_friendly),
            notes=m.notes,
            provider=m.provider,
            status=m.status
        )
        for m in embedding_models
    ]
    
    llm_responses = [
        ModelResponse(
            model_id=m.model_id,
            type=m.type,
            name=m.name,
            dimension=m.dimension,
            context_tokens=m.context_tokens,
            cpu_friendly=bool(m.cpu_friendly),
            notes=m.notes,
            provider=m.provider,
            status=m.status
        )
        for m in llm_models
    ]
    
    logger.info(f"Listed {len(all_models)} models (embedding: {len(embedding_responses)}, llm: {len(llm_responses)})")
    
    # Return flat format if requested (for frontend compatibility)
    if format == "flat":
        from fastapi.responses import JSONResponse
        return JSONResponse(content={
            "models": [
                {
                    "id": m.model_id,
                    "type": m.type,
                    "name": m.name,
                    "shortDescription": m.notes[:80] if m.notes else f"{m.type.title()} model",
                    "dimension": m.dimension,
                    "contextTokens": m.context_tokens,
                    "tokenLimit": m.context_tokens,
                    "cpuFriendly": bool(m.cpu_friendly),
                    "notes": m.notes or ""
                }
                for m in all_models
            ]
        })
    
    return ModelListResponse(
        embedding_models=embedding_responses,
        llm_models=llm_responses,
        total_count=len(all_models),
        default_embedding=defaults.get("embedding"),
        default_llm=defaults.get("llm")
    )


@router.get("/config", response_model=ModelConfigResponse)
async def get_model_config(
    db: AsyncSession = Depends(get_db),
    service: ModelService = Depends(get_model_service)
):
    """
    Get complete model configuration including compatibility matrix
    
    Returns:
    - All models (embedding + LLM)
    - Default models by type
    - Compatibility matrix from config file
    """
    # Get all active models
    all_models = await service.get_all_models(db=db, status="active")
    
    # Load config file for compatibility matrix
    config = service.load_config_file()
    
    # Get defaults
    defaults = await service.get_default_models(db)
    
    # Convert to response models
    model_responses = [
        ModelResponse(
            model_id=m.model_id,
            type=m.type,
            name=m.name,
            dimension=m.dimension,
            context_tokens=m.context_tokens,
            cpu_friendly=bool(m.cpu_friendly),
            notes=m.notes,
            provider=m.provider,
            status=m.status
        )
        for m in all_models
    ]
    
    return ModelConfigResponse(
        models=model_responses,
        default_models=defaults,
        compatibility_matrix=config.get("compatibility_matrix")
    )


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    service: ModelService = Depends(get_model_service)
):
    """
    Get detailed information about a specific model
    
    - **model_id**: Unique model identifier (e.g., 'BAAI/bge-small-en-v1.5')
    """
    from fastapi import HTTPException
    
    model = await service.get_model_by_id(db, model_id)
    
    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model not found: {model_id}"
        )
    
    return ModelResponse(
        model_id=model.model_id,
        type=model.type,
        name=model.name,
        dimension=model.dimension,
        context_tokens=model.context_tokens,
        cpu_friendly=bool(model.cpu_friendly),
        notes=model.notes,
        provider=model.provider,
        status=model.status
    )


@router.get("/compatibility/{current_model}/{new_model}")
async def check_compatibility(
    current_model: str,
    new_model: str,
    db: AsyncSession = Depends(get_db),
    service: ModelService = Depends(get_model_service)
):
    """
    Check if two models are compatible (can be swapped without re-embedding)
    
    - **current_model**: Current model ID
    - **new_model**: New model ID to migrate to
    
    Returns compatibility status and reason
    """
    result = await service.validate_model_compatibility(
        db=db,
        current_model_id=current_model,
        new_model_id=new_model
    )
    
    return result


@router.get("/embedding/active", response_model=List[ModelResponse])
async def get_active_embedding_models(
    db: AsyncSession = Depends(get_db),
    service: ModelService = Depends(get_model_service)
):
    """
    Get all active embedding models
    
    Convenience endpoint for embedding model selection
    """
    models = await service.get_embedding_models(db, status="active")
    
    return [
        ModelResponse(
            model_id=m.model_id,
            type=m.type,
            name=m.name,
            dimension=m.dimension,
            context_tokens=m.context_tokens,
            cpu_friendly=bool(m.cpu_friendly),
            notes=m.notes,
            provider=m.provider,
            status=m.status
        )
        for m in models
    ]


@router.get("/llm/active", response_model=List[ModelResponse])
async def get_active_llm_models(
    db: AsyncSession = Depends(get_db),
    service: ModelService = Depends(get_model_service)
):
    """
    Get all active LLM models
    
    Convenience endpoint for LLM model selection
    """
    models = await service.get_llm_models(db, status="active")
    
    return [
        ModelResponse(
            model_id=m.model_id,
            type=m.type,
            name=m.name,
            dimension=m.dimension,
            context_tokens=m.context_tokens,
            cpu_friendly=bool(m.cpu_friendly),
            notes=m.notes,
            provider=m.provider,
            status=m.status
        )
        for m in models
    ]


@router.post("/sync")
async def sync_models_from_config(
    db: AsyncSession = Depends(get_db),
    service: ModelService = Depends(get_model_service)
):
    """
    Sync database models with config/models.json
    
    This keeps the database in sync with the config file (single source of truth).
    
    Actions:
    - Adds new models from config
    - Updates existing models if config changed
    - Marks models as deprecated if removed from config
    
    Returns sync statistics (added, updated, deprecated, unchanged)
    
    **Note:** Run this after updating config/models.json
    """
    stats = await service.sync_models_from_config(db)
    
    logger.info(f"Model sync completed: {stats}")
    
    return {
        "success": True,
        "message": "Models synchronized from config/models.json",
        "stats": stats
    }
