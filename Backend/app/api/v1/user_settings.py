"""
User Settings API - Manage user preferences for embedding models

Endpoints:
- GET /api/v1/user/settings - Get current user settings
- POST /api/v1/user/settings - Update user settings

Note: LLM model is fixed to Llama 3.2 Instruct via Ollama (local CPU) and not user-configurable
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.postgres import get_db
from app.api.v1.auth import get_current_user
from app.models.database_models import UserSettings
from app.models.schemas import UserResponse
from app.services.model_service import get_model_service, ModelService
from app.services.audit_service import get_audit_service
from app.core.logger import logger

router = APIRouter(prefix="/user", tags=["user-settings"])


# ============= SCHEMAS =============

class UserSettingsResponse(BaseModel):
    """User settings response"""
    user_id: str
    default_embedding_model: Optional[str] = None
    embedding_dimension: Optional[int] = None
    
    model_config = {"from_attributes": True}


class UserSettingsUpdate(BaseModel):
    """User settings update request"""
    default_embedding_model: Optional[str] = Field(None, description="Default embedding model ID (Ollama model name)")
    embedding_dimension: Optional[int] = Field(None, description="Embedding dimension (auto-detected if not provided)")


class UserSettingsSaveResponse(BaseModel):
    """User settings save response"""
    status: str
    message: str
    settings: UserSettingsResponse


# ============= ENDPOINTS =============

@router.get("/settings", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's settings
    
    Returns:
    - user_id: User ID
    - default_embedding_model: Selected default embedding model
    """
    # Query user settings
    query = select(UserSettings).where(UserSettings.u_id == current_user.u_id)
    result = await db.execute(query)
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create default settings if not exists
        settings = UserSettings(
            u_id=current_user.u_id,
            default_embedding_model="nomic-embed-text",
            embedding_dimension=768
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
        logger.info(f"Created default settings for user: {current_user.u_id}")
    
    return UserSettingsResponse(
        user_id=str(settings.u_id),
        default_embedding_model=settings.default_embedding_model,
        embedding_dimension=settings.embedding_dimension
    )


@router.post("/settings", response_model=UserSettingsSaveResponse)
async def update_user_settings(
    update_data: UserSettingsUpdate,
    http_request: Request,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    service: ModelService = Depends(get_model_service),
    audit_service = Depends(get_audit_service)
):
    """
    Update user's settings (default embedding model only)
    
    Validates:
    - default_embedding_model must be a valid embedding model ID
    
    Returns:
    - 200 with updated settings on success
    - 400 if payload invalid
    - 422 if model ID not supported
    """
    # Validate embedding model if provided
    # Always validate the model name, even if dimension is provided
    model_dimension = None
    
    if update_data.default_embedding_model:
        from app.core.embedding_model_registry import get_embedding_registry
        
        registry = get_embedding_registry()
        
        # Always validate that the model name is valid
        if registry.is_valid_model(update_data.default_embedding_model):
            spec = registry.get_model(update_data.default_embedding_model)
            # Use provided dimension if valid, otherwise use spec dimension
            model_dimension = update_data.embedding_dimension if update_data.embedding_dimension is not None else spec.dimension
        else:
            # Try to get from static config as fallback
            try:
                from app.core.models_config import get_embedding_model_info
                model_info = get_embedding_model_info(update_data.default_embedding_model)
                # Use provided dimension if valid, otherwise use model_info dimension
                model_dimension = update_data.embedding_dimension if update_data.embedding_dimension is not None else model_info.dimension
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid embedding model: {update_data.default_embedding_model}. Model is not registered. Please activate the model first."
                )
    
    # Get or create user settings
    query = select(UserSettings).where(UserSettings.u_id == current_user.u_id)
    result = await db.execute(query)
    settings = result.scalar_one_or_none()
    
    # Track changes for audit log
    changes = {}
    
    # Track whether dimension was explicitly resolved (from provided value or lookup)
    # Only model_dimension being set means we have a resolved dimension
    dimension_resolved = model_dimension is not None
    
    if not settings:
        # Create new settings - apply 768 default only when building new settings
        dimension_for_new = model_dimension if dimension_resolved else 768
        settings = UserSettings(
            u_id=current_user.u_id,
            default_embedding_model=update_data.default_embedding_model,
            embedding_dimension=dimension_for_new
        )
        db.add(settings)
        logger.info(f"Creating new settings for user: {current_user.u_id}")
        
        # Track new settings
        changes = {
            "default_embedding_model": {
                "before": None,
                "after": update_data.default_embedding_model
            },
            "embedding_dimension": {
                "before": None,
                "after": dimension_for_new
            }
        }
    else:
        # Update existing settings and track changes
        if update_data.default_embedding_model is not None:
            old_model = settings.default_embedding_model
            old_dim = settings.embedding_dimension
            settings.default_embedding_model = update_data.default_embedding_model
            # Only overwrite dimension if we explicitly resolved one
            if dimension_resolved:
                settings.embedding_dimension = model_dimension
            changes["default_embedding_model"] = {
                "before": old_model,
                "after": update_data.default_embedding_model
            }
            if dimension_resolved:
                changes["embedding_dimension"] = {
                    "before": old_dim,
                    "after": settings.embedding_dimension
                }
        logger.info(f"Updating settings for user: {current_user.u_id}")
    
    await db.commit()
    await db.refresh(settings)
    
    
    await audit_service.log_settings_updated(
        db=db,
        user_id=current_user.u_id,
        request=http_request,
        changes=changes
    )
    
    logger.info(f"Settings saved successfully for user {current_user.u_id}")
    
    return UserSettingsSaveResponse(
        status="ok",
        message="Settings saved successfully",
        settings=UserSettingsResponse(
            user_id=str(settings.u_id),
            default_embedding_model=settings.default_embedding_model,
            embedding_dimension=settings.embedding_dimension
        )
    )
