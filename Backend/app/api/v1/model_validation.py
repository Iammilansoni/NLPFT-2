# Backend\app\api\v1\model_validation.py

"""
Model Compatibility Validation API - Dashboard Mismatch Handling

Purpose:
This API endpoint handles model mismatch detection and provides clear
actions for users when their Settings model doesn't match the dataset's model.

NON-NEGOTIABLE RULES:
1. Dashboard CANNOT silently use a different model than Settings
2. Any mismatch MUST be surfaced to the user with clear actions
3. User MUST explicitly choose an action to resolve mismatch
4. No automatic fallbacks or silent model switching

Mismatch Handling Flow:
1. Dashboard query page selects a model (or uses default)
2. Before search: Check model compatibility
3. If MATCH: Proceed with vector search
4. If MISMATCH:
   - DO NOT perform search
   - Return structured error with actions
   - User chooses: "Use Settings Model" or "Re-embed with Selected Model"

Frontend UX (Required):
When mismatch detected, show modal with:
- Warning message explaining the mismatch
- "Your datasets are embedded with Model A, but you selected Model B"
- Button 1: "Use Settings Model" -> Switch selection to match Settings, proceed
- Button 2: "Re-embed with Selected Model" -> Update Settings, redirect to re-embed
"""

from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import uuid

from app.core.postgres import get_db
from app.api.v1.auth import get_current_user
from app.models.schemas import UserResponse
from app.core.embedding_model_registry import get_embedding_registry
from app.services.user_embedding_settings_service import get_user_embedding_settings_service
from app.models.database_models import Dataset
from app.core.logger import logger
from sqlalchemy import select


router = APIRouter(prefix="/model-validation", tags=["model-validation"])


# --- Schemas ---

class ModelOption(BaseModel):
    """Action option for mismatch resolution"""
    action: str = Field(..., description="Action identifier")
    label: str = Field(..., description="Button label")
    description: str = Field(..., description="Action description")
    recommended: bool = Field(default=False, description="Is this the recommended action")


class ModelMismatchResponse(BaseModel):
    """
    Model mismatch response structure.
    
    Frontend should:
    1. Show this in a modal/dialog
    2. Display the warning message prominently
    3. Show action buttons based on 'options'
    4. Block search until user resolves mismatch
    """
    compatible: bool = Field(default=False)
    error_code: str = Field(default="MODEL_MISMATCH")
    
    # Mismatch details
    settings_model: str = Field(..., description="Model from user's Settings")
    settings_model_display: str = Field(..., description="Display name of Settings model")
    settings_dimension: int = Field(..., description="Dimension of Settings model")
    
    dataset_model: str = Field(..., description="Model dataset was embedded with")
    dataset_model_display: str = Field(..., description="Display name of dataset model")
    dataset_dimension: int = Field(..., description="Dimension of dataset model")
    
    # User-facing message
    message: str = Field(..., description="Clear warning message for the user")
    detailed_message: str = Field(..., description="Technical explanation")
    
    # Actions
    options: List[ModelOption] = Field(..., description="Available resolution actions")
    
    # Dataset info
    dataset_id: Optional[str] = None
    embedded_rows: Optional[int] = None
    
    # API endpoints for actions
    switch_settings_endpoint: str = Field(
        default="/api/v1/user/settings",
        description="Endpoint to update Settings model"
    )
    reembed_endpoint: Optional[str] = Field(
        default=None,
        description="Endpoint to trigger re-embedding"
    )


class CompatibilityCheckResponse(BaseModel):
    """Response for compatibility check"""
    compatible: bool
    settings_model: str
    settings_model_display: str
    settings_dimension: int
    dataset_model: Optional[str] = None
    dataset_model_display: Optional[str] = None
    dataset_dimension: Optional[int] = None
    message: str
    mismatch_details: Optional[ModelMismatchResponse] = None


class ValidationPreflightRequest(BaseModel):
    """Request for search preflight validation"""
    selected_model: Optional[str] = Field(
        None, 
        description="Model selected in dashboard (if different from Settings)"
    )
    dataset_id: Optional[str] = Field(
        None,
        description="Dataset ID to check"
    )
    template_id: Optional[str] = Field(
        None,
        description="Template ID to check (uses latest dataset)"
    )


class ValidationPreflightResponse(BaseModel):
    """Response for search preflight validation"""
    can_proceed: bool = Field(..., description="Whether search can proceed")
    settings_model: str = Field(..., description="Model from Settings")
    effective_model: str = Field(..., description="Model that will be used")
    dataset_model: Optional[str] = Field(None, description="Model dataset was embedded with")
    warning: Optional[ModelMismatchResponse] = Field(
        None, 
        description="Mismatch warning if applicable"
    )


# --- Endpoints ---

@router.get("/available-models")
async def get_available_embedding_models(
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Get all available embedding models.
    
    Returns model list for Settings page and Dashboard dropdown.
    """
    registry = get_embedding_registry()
    models = registry.list_models()
    default_model = registry.DEFAULT_MODEL_ID
    
    return {
        "models": models,
        "default_model": default_model,
        "count": len(models)
    }


@router.get("/user-settings")
async def get_user_embedding_settings(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's current embedding settings.
    
    Returns the active embedding model from Settings (source of truth).
    """
    settings_service = get_user_embedding_settings_service()
    model_id, dimension, model_spec = await settings_service.get_active_embedding_model_async(
        db, current_user.u_id
    )
    
    return {
        "active_model": model_id,
        "active_model_display": model_spec.display_name,
        "dimension": dimension,
        "redis_index": model_spec.redis_index_name,
        "redis_namespace": model_spec.redis_namespace,
        "model_info": model_spec.to_dict()
    }


@router.get("/check-compatibility", response_model=CompatibilityCheckResponse)
async def check_model_compatibility(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    dataset_id: Optional[uuid.UUID] = Query(None, description="Dataset UUID to check"),
    template_id: Optional[uuid.UUID] = Query(None, description="Template UUID (uses latest dataset)")
):
    """
    Check if user's Settings model is compatible with a dataset's embedded model.
    
    ❗ CRITICAL: This MUST be called before any vector search.
    
    Returns:
    - If compatible: { compatible: true, ... }
    - If mismatch: { compatible: false, mismatch_details: {...} }
    
    Frontend should:
    1. Call this before every search
    2. If compatible=false, show modal with mismatch_details
    3. Block search until user resolves mismatch
    """
    registry = get_embedding_registry()
    settings_service = get_user_embedding_settings_service()
    
    # Get user's active model
    model_id, dimension, model_spec = await settings_service.get_active_embedding_model_async(
        db, current_user.u_id
    )
    
    # If no dataset specified, just return Settings info
    if not dataset_id and not template_id:
        return CompatibilityCheckResponse(
            compatible=True,
            settings_model=model_id,
            settings_model_display=model_spec.display_name,
            settings_dimension=dimension,
            message="No dataset specified. Settings model will be used."
        )
    
    # Get dataset
    if dataset_id:
        result = await db.execute(
            select(Dataset).where(
                Dataset.dataset_id == dataset_id,
                Dataset.u_id == current_user.u_id
            )
        )
        dataset = result.scalar_one_or_none()
    elif template_id:
        result = await db.execute(
            select(Dataset).where(
                Dataset.t_id == template_id,
                Dataset.u_id == current_user.u_id
            ).order_by(Dataset.created_at.desc()).limit(1)
        )
        dataset = result.scalar_one_or_none()
    else:
        dataset = None
    
    if not dataset:
        return CompatibilityCheckResponse(
            compatible=True,
            settings_model=model_id,
            settings_model_display=model_spec.display_name,
            settings_dimension=dimension,
            message="No dataset found. Settings model will be used for new embeddings."
        )
    
    # Check if dataset is embedded
    if not dataset.embedding_model:
        return CompatibilityCheckResponse(
            compatible=True,
            settings_model=model_id,
            settings_model_display=model_spec.display_name,
            settings_dimension=dimension,
            message="Dataset not yet embedded. Settings model will be used."
        )
    
    # Get dataset's model info
    try:
        dataset_model_spec = registry.get_model(dataset.embedding_model)
        dataset_model_display = dataset_model_spec.display_name
        dataset_dim = dataset_model_spec.dimension
    except ValueError:
        dataset_model_display = dataset.embedding_model
        dataset_dim = dataset.embedding_dimension or 0
    
    # Check compatibility
    if dataset.embedding_model == model_id:
        return CompatibilityCheckResponse(
            compatible=True,
            settings_model=model_id,
            settings_model_display=model_spec.display_name,
            settings_dimension=dimension,
            dataset_model=dataset.embedding_model,
            dataset_model_display=dataset_model_display,
            dataset_dimension=dataset_dim,
            message="Models match. Search will work correctly."
        )
    
    # MISMATCH DETECTED
    logger.warning(
        f"Model mismatch detected: Settings={model_id}, Dataset={dataset.embedding_model}"
    )
    
    mismatch = ModelMismatchResponse(
        compatible=False,
        error_code="MODEL_MISMATCH",
        settings_model=model_id,
        settings_model_display=model_spec.display_name,
        settings_dimension=dimension,
        dataset_model=dataset.embedding_model,
        dataset_model_display=dataset_model_display,
        dataset_dimension=dataset_dim,
        message=(
            f"Model Mismatch Detected\n\n"
            f"Your datasets are embedded with '{dataset_model_display}' ({dataset_dim}D), "
            f"but your Settings use '{model_spec.display_name}' ({dimension}D).\n\n"
            f"Vectors from different models cannot be compared."
        ),
        detailed_message=(
            f"Vector spaces are model-specific. A query embedded with '{model_spec.display_name}' "
            f"cannot be meaningfully compared to dataset vectors embedded with '{dataset_model_display}'."
        ),
        options=[
            ModelOption(
                action="use_settings_model",
                label=f"Search with {dataset_model_display}",
                description=(
                    f"Update your Settings to use '{dataset_model_display}' and proceed with search. "
                    f"No re-embedding needed."
                ),
                recommended=True
            ),
            ModelOption(
                action="reembed_dataset",
                label=f"Re-embed with {model_spec.display_name}",
                description=(
                    f"Re-embed all datasets using '{model_spec.display_name}'. "
                    f"This may take several minutes depending on dataset size."
                ),
                recommended=False
            )
        ],
        dataset_id=str(dataset.dataset_id),
        embedded_rows=dataset.embedded_rows,
        reembed_endpoint=f"/api/v1/datasets/{dataset.dataset_id}/reembed"
    )
    
    return CompatibilityCheckResponse(
        compatible=False,
        settings_model=model_id,
        settings_model_display=model_spec.display_name,
        settings_dimension=dimension,
        dataset_model=dataset.embedding_model,
        dataset_model_display=dataset_model_display,
        dataset_dimension=dataset_dim,
        message="Model mismatch detected. Search blocked.",
        mismatch_details=mismatch
    )


@router.post("/preflight-check", response_model=ValidationPreflightResponse)
async def preflight_search_validation(
    request: ValidationPreflightRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Preflight validation before search.
    
    Call this BEFORE executing any vector search to:
    1. Check if selected model matches Settings
    2. Check if Settings model matches dataset's model
    3. Return clear actions if mismatch detected
    
    ❗ If can_proceed=false, DO NOT execute search.
    Show the warning modal to user instead.
    """
    registry = get_embedding_registry()
    settings_service = get_user_embedding_settings_service()
    
    # Get user's active model
    model_id, dimension, model_spec = await settings_service.get_active_embedding_model_async(
        db, current_user.u_id
    )
    
    # Determine effective model
    selected_model = request.selected_model
    if selected_model and selected_model != model_id:
        # Dashboard selected different model than Settings
        # This should NOT silently override Settings
        # Return warning about Settings mismatch
        try:
            selected_spec = registry.get_model(selected_model)
            selected_display = selected_spec.display_name
            selected_dim = selected_spec.dimension
        except ValueError:
            selected_display = selected_model
            selected_dim = 0
        
        return ValidationPreflightResponse(
            can_proceed=False,
            settings_model=model_id,
            effective_model=model_id,  # Settings is source of truth
            warning=ModelMismatchResponse(
                compatible=False,
                error_code="DASHBOARD_SETTINGS_MISMATCH",
                settings_model=model_id,
                settings_model_display=model_spec.display_name,
                settings_dimension=dimension,
                dataset_model=selected_model,
                dataset_model_display=selected_display,
                dataset_dimension=selected_dim,
                message=(
                    f"Dashboard Selection Mismatch\n\n"
                    f"You selected '{selected_display}' in the dashboard, "
                    f"but your Settings use '{model_spec.display_name}'.\n\n"
                    f"Settings is the source of truth for embeddings."
                ),
                detailed_message=(
                    "The Settings page controls which embedding model is used. "
                    "Dashboard selections must match Settings."
                ),
                options=[
                    ModelOption(
                        action="use_settings",
                        label=f"Use {model_spec.display_name}",
                        description="Use the model from Settings (recommended)",
                        recommended=True
                    ),
                    ModelOption(
                        action="update_settings",
                        label=f"Change Settings to {selected_display}",
                        description="Update Settings to use selected model",
                        recommended=False
                    )
                ]
            )
        )
    
    # Check dataset compatibility if specified
    dataset = None
    if request.dataset_id:
        result = await db.execute(
            select(Dataset).where(
                Dataset.dataset_id == uuid.UUID(request.dataset_id),
                Dataset.u_id == current_user.u_id
            )
        )
        dataset = result.scalar_one_or_none()
    elif request.template_id:
        result = await db.execute(
            select(Dataset).where(
                Dataset.t_id == uuid.UUID(request.template_id),
                Dataset.u_id == current_user.u_id
            ).order_by(Dataset.created_at.desc()).limit(1)
        )
        dataset = result.scalar_one_or_none()
    
    if not dataset or not dataset.embedding_model:
        # No dataset or not embedded - can proceed
        return ValidationPreflightResponse(
            can_proceed=True,
            settings_model=model_id,
            effective_model=model_id,
            dataset_model=None
        )
    
    # Check dataset model compatibility
    if dataset.embedding_model == model_id:
        return ValidationPreflightResponse(
            can_proceed=True,
            settings_model=model_id,
            effective_model=model_id,
            dataset_model=dataset.embedding_model
        )
    
    # MISMATCH with dataset
    try:
        dataset_spec = registry.get_model(dataset.embedding_model)
        dataset_display = dataset_spec.display_name
        dataset_dim = dataset_spec.dimension
    except ValueError:
        dataset_display = dataset.embedding_model
        dataset_dim = dataset.embedding_dimension or 0
    
    return ValidationPreflightResponse(
        can_proceed=False,
        settings_model=model_id,
        effective_model=model_id,
        dataset_model=dataset.embedding_model,
        warning=ModelMismatchResponse(
            compatible=False,
            error_code="MODEL_MISMATCH",
            settings_model=model_id,
            settings_model_display=model_spec.display_name,
            settings_dimension=dimension,
            dataset_model=dataset.embedding_model,
            dataset_model_display=dataset_display,
            dataset_dimension=dataset_dim,
            message=(
                f"Model Mismatch\n\n"
                f"Dataset embedded with '{dataset_display}' ({dataset_dim}D), "
                f"but Settings use '{model_spec.display_name}' ({dimension}D)."
            ),
            detailed_message="Cannot search - vectors from different models are incompatible.",
            options=[
                ModelOption(
                    action="switch_to_dataset_model",
                    label=f"Use {dataset_display}",
                    description="Update Settings to match dataset",
                    recommended=True
                ),
                ModelOption(
                    action="reembed",
                    label=f"Re-embed with {model_spec.display_name}",
                    description="Re-embed dataset (may take time)",
                    recommended=False
                )
            ],
            dataset_id=str(dataset.dataset_id),
            embedded_rows=dataset.embedded_rows,
            reembed_endpoint=f"/api/v1/datasets/{dataset.dataset_id}/reembed"
        )
    )


@router.post("/switch-to-dataset-model")
async def switch_to_dataset_model(
    dataset_id: uuid.UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Switch user's Settings to use the dataset's embedding model.
    
    This is the "Use Settings Model" action from mismatch modal.
    After this, user can proceed with search.
    """
    # Get dataset
    result = await db.execute(
        select(Dataset).where(
            Dataset.dataset_id == dataset_id,
            Dataset.u_id == current_user.u_id
        )
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )
    
    if not dataset.embedding_model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset has not been embedded yet"
        )
    
    # Update Settings
    settings_service = get_user_embedding_settings_service()
    result = await settings_service.set_active_embedding_model_async(
        db, current_user.u_id, dataset.embedding_model
    )
    
    logger.info(
        f"Switched user {str(current_user.u_id)[:8]} to model {dataset.embedding_model}"
    )
    
    return {
        "success": True,
        "message": f"Settings updated to use {dataset.embedding_model}",
        "new_model": dataset.embedding_model,
        "can_proceed_with_search": True
    }