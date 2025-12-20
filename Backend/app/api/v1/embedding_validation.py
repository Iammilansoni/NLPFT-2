"""
Embedding Model Validation API - Check for model mismatches

Endpoints:
- GET /api/v1/embeddings/validate/{template_id} - Check if dataset embeddings match user's current model
"""

from typing import Annotated, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from uuid import UUID

from app.core.postgres import get_db
from app.api.v1.auth import get_current_user
from app.models.database_models import UserSettings, Metadata, User
from app.services.embedding_service import get_enhanced_embedding_service
from app.core.logger import logger

router = APIRouter(prefix="/embeddings", tags=["embedding-validation"])


# ============= SCHEMAS =============

class EmbeddingValidationResponse(BaseModel):
    """Embedding validation response"""
    is_valid: bool
    user_model: str
    user_dimension: int
    dataset_model: str | None
    dataset_dimension: int | None
    mismatch_type: str | None  # "model", "dimension", "not_embedded", "valid"
    recommendation: str
    requires_reembedding: bool


class ReembedRequest(BaseModel):
    """Request to re-embed dataset with current user model"""
    template_id: str


# ============= ENDPOINTS =============

@router.get("/validate/{template_id}", response_model=EmbeddingValidationResponse)
async def validate_embedding_model(
    template_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Validate if dataset embeddings match user's current embedding model
    
    Returns:
    - is_valid: True if dataset can be searched with current model
    - mismatch_type: Type of mismatch (model, dimension, not_embedded, valid)
    - recommendation: What user should do
    - requires_reembedding: Whether dataset needs to be re-embedded
    """
    try:
        # Get user's current settings
        query = select(UserSettings).where(UserSettings.u_id == current_user.u_id)
        result = await db.execute(query)
        settings = result.scalar_one_or_none()
        
        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User settings not found. Please configure your embedding model in Settings."
            )
        
        user_model = settings.default_embedding_model
        user_dimension = settings.embedding_dimension
        
        # Get dataset metadata
        metadata_query = select(Metadata).where(Metadata.t_id == UUID(template_id))
        metadata_result = await db.execute(metadata_query)
        metadata = metadata_result.scalar_one_or_none()
        
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template {template_id} not found"
            )
        
        # Check if dataset has embedding info
        if not metadata.remarks or not isinstance(metadata.remarks, dict):
            return EmbeddingValidationResponse(
                is_valid=False,
                user_model=user_model,
                user_dimension=user_dimension,
                dataset_model=None,
                dataset_dimension=None,
                mismatch_type="not_embedded",
                recommendation="This dataset has not been embedded yet. Generate embeddings to enable search.",
                requires_reembedding=True
            )
        
        embedding_info = metadata.remarks.get('embedding_info', {})
        
        if not embedding_info:
            return EmbeddingValidationResponse(
                is_valid=False,
                user_model=user_model,
                user_dimension=user_dimension,
                dataset_model=None,
                dataset_dimension=None,
                mismatch_type="not_embedded",
                recommendation="This dataset has not been embedded yet. Generate embeddings to enable search.",
                requires_reembedding=True
            )
        
        dataset_model = embedding_info.get('embedded_with_model')
        dataset_dimension = embedding_info.get('embedding_dim')
        
        # Check for mismatches
        if user_model != dataset_model:
            return EmbeddingValidationResponse(
                is_valid=False,
                user_model=user_model,
                user_dimension=user_dimension,
                dataset_model=dataset_model,
                dataset_dimension=dataset_dimension,
                mismatch_type="model",
                recommendation=f"Dataset was embedded with '{dataset_model}' but you're using '{user_model}'. Search results will be inaccurate. Please re-embed the dataset or switch your model to '{dataset_model}' in Settings.",
                requires_reembedding=True
            )
        
        if user_dimension != dataset_dimension:
            return EmbeddingValidationResponse(
                is_valid=False,
                user_model=user_model,
                user_dimension=user_dimension,
                dataset_model=dataset_model,
                dataset_dimension=dataset_dimension,
                mismatch_type="dimension",
                recommendation=f"Dimension mismatch: dataset has {dataset_dimension}D embeddings but your model uses {user_dimension}D. Please re-embed the dataset.",
                requires_reembedding=True
            )
        
        # Everything matches
        return EmbeddingValidationResponse(
            is_valid=True,
            user_model=user_model,
            user_dimension=user_dimension,
            dataset_model=dataset_model,
            dataset_dimension=dataset_dimension,
            mismatch_type="valid",
            recommendation="Dataset embeddings match your current model. Search is ready to use.",
            requires_reembedding=False
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating embeddings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating embeddings: {str(e)}"
        )


@router.post("/reembed")
async def reembed_dataset(
    request: ReembedRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Re-embed a dataset with user's current embedding model
    
    This will:
    1. Delete old embeddings from Redis
    2. Generate new embeddings using user's current model
    3. Update metadata
    """
    try:
        # Get metadata to find CSV path
        metadata_query = select(Metadata).where(Metadata.t_id == UUID(request.template_id))
        metadata_result = await db.execute(metadata_query)
        metadata = metadata_result.scalar_one_or_none()
        
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template {request.template_id} not found"
            )
        
        # Get CSV path from metadata
        embedding_info = metadata.remarks.get('embedding_info', {}) if metadata.remarks else {}
        csv_path = embedding_info.get('csv_path')
        
        if not csv_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No CSV path found in metadata. Cannot re-embed."
            )
        
        # Delete old embeddings
        embedding_service = get_enhanced_embedding_service()
        redis_namespace = f"embedding:{current_user.u_id}:{request.template_id}"
        pattern = f"{redis_namespace}:*"
        
        keys = list(embedding_service.redis_service.redis_client.scan_iter(match=pattern, count=1000))
        if keys:
            embedding_service.redis_service.redis_client.delete(*keys)
            logger.info(f"Deleted {len(keys)} old embeddings")
        
        # Re-embed with current model
        logger.info(f"Re-embedding dataset with user's current model")
        task_id = await embedding_service.auto_embed_generated_dataset(
            user_id=current_user.u_id,
            template_id=UUID(request.template_id),
            csv_path=csv_path,
            db=db
        )
        
        return {
            "success": True,
            "message": "Dataset re-embedding started",
            "task_id": task_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error re-embedding dataset: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error re-embedding dataset: {str(e)}"
        )
