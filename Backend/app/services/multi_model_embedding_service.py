# Backend\app\services\multi_model_embedding_service.py

"""
Multi-Model Dataset Embedding Service - Safe Dataset Embedding Pipeline

Purpose:
This service handles dataset embedding with strict model governance.
It ensures that datasets are embedded using the model from Settings
and properly tracked for compatibility checks.

Non-Negotiable Rules:
1. Dataset embedding uses ONLY the model from user's Settings
2. Each dataset records which model was used
3. Re-embedding clears previous vectors before creating new ones
4. Embedding status is tracked for progress reporting
5. No mixing of vectors from different models

Embedding Flow:
1. Fetch user's active embedding model from Settings
2. Validate model is available in Ollama
3. Ensure model-specific Redis index exists
4. Delete any existing vectors for this dataset (if re-embedding)
5. Generate embeddings in batches using Ollama
6. Store vectors in model-specific Redis namespace
7. Update dataset metadata with embedding info
"""

import uuid
import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.logger import logger
from app.core.embedding_model_registry import get_embedding_registry
from app.models.database_models import Dataset, Template, Metadata, UserSettings
from app.services.user_embedding_settings_service import get_user_embedding_settings_service
from app.services.multi_model_redis_service import get_multi_model_redis_service
from app.services.ollama_embedding_service import get_ollama_service
from app.models.schemas.embedding_schemas import (
    EmbeddingStatus,
    ErrorCode,
)


class MultiModelDatasetEmbeddingService:
    """
    Dataset embedding service with multi-model support.
    
    This service:
    - Fetches embedding model from user's Settings (source of truth)
    - Generates embeddings using Ollama
    - Stores vectors in model-specific Redis namespace/index
    - Tracks embedding status and metadata
    - Enforces one-model-per-dataset rule
    
    CRITICAL: Never embed a dataset with a model different from Settings
    without explicit re-embedding action.
    """
    
    def __init__(self):
        self.registry = get_embedding_registry()
        self.settings_service = get_user_embedding_settings_service()
        self.redis_service = get_multi_model_redis_service()
        self.ollama_service = get_ollama_service()
    
    # --- Main Embedding Methods ---
    
    async def embed_dataset(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        dataset_id: uuid.UUID,
        batch_size: int = 32,
        force_reembed: bool = False
    ) -> Dict[str, Any]:
        """
        Embed a dataset using the user's active embedding model.
        
        Critical Flow:
        1. Get user's active model from Settings (SOURCE OF TRUTH)
        2. Check if dataset already embedded with different model
        3. If different model and not force_reembed: return error
        4. If force_reembed: delete existing vectors first
        5. Generate embeddings using Ollama
        6. Store in model-specific Redis index
        7. Update dataset metadata
        
        Args:
            db: AsyncSession
            user_id: User UUID
            dataset_id: Dataset UUID
            batch_size: Batch size for embedding
            force_reembed: If True, re-embed even if already embedded
            
        Returns:
            Embedding result with status and metadata
        """
        task_id = str(uuid.uuid4())
        
        try:
            logger.info(
                f" Starting dataset embedding (dataset={str(dataset_id)[:8]}, "
                f"user={str(user_id)[:8]}, force={force_reembed})"
            )
            
            # 1. Get dataset
            result = await db.execute(
                select(Dataset).where(
                    Dataset.dataset_id == dataset_id,
                    Dataset.u_id == user_id
                )
            )
            dataset = result.scalar_one_or_none()
            
            if not dataset:
                return {
                    "success": False,
                    "error": ErrorCode.DATASET_NOT_FOUND,
                    "message": f"Dataset {dataset_id} not found"
                }
            
            # 2. Get user's active embedding model from Settings
            model_id, dimension, model_spec = await self.settings_service.get_active_embedding_model_async(
                db, user_id
            )
            
            logger.info(f"User's active model: {model_id} (dim={dimension})")
            
            # 3. Check for existing embedding with different model
            if dataset.embedding_model and dataset.embedding_model != model_id:
                if not force_reembed:
                    logger.warning(
                        f" Dataset already embedded with {dataset.embedding_model}, "
                        f"but user wants {model_id}"
                    )
                    return {
                        "success": False,
                        "error": ErrorCode.MODEL_MISMATCH,
                        "message": (
                            f"Dataset was previously embedded with '{dataset.embedding_model}'. "
                            f"Set force_reembed=True to re-embed with '{model_id}'."
                        ),
                        "dataset_id": str(dataset_id),
                        "existing_model": dataset.embedding_model,
                        "requested_model": model_id,
                        "options": [
                            {
                                "action": "force_reembed",
                                "label": f"Re-embed with {model_id}",
                                "description": "This will delete existing vectors and create new ones"
                            },
                            {
                                "action": "use_existing",
                                "label": f"Keep using {dataset.embedding_model}",
                                "description": "Change your Settings to use the existing model"
                            }
                        ]
                    }
                else:
                    # Force re-embed: delete existing vectors
                    logger.info(f" Deleting existing vectors (model={dataset.embedding_model})")
                    deleted = self.redis_service.delete_dataset_vectors(
                        model_id=dataset.embedding_model,
                        user_id=user_id,
                        dataset_id=dataset_id
                    )
                    logger.info(f" Deleted {deleted} existing vectors")
            
            # 4. Check Ollama availability
            if not await self.ollama_service.check_ollama_available():
                return {
                    "success": False,
                    "error": "OLLAMA_UNAVAILABLE",
                    "message": "Ollama service not available at http://localhost:11434"
                }
            
            # 5. Update dataset status to in_progress
            dataset.embedding_status = EmbeddingStatus.IN_PROGRESS
            dataset.embedding_progress = 0
            dataset.embedding_model = model_id
            dataset.embedding_dimension = dimension
            dataset.embedding_started_at = datetime.utcnow()
            dataset.embedding_error = None
            await db.commit()
            
            # 6. Ensure Redis index exists
            self.redis_service.ensure_model_index_exists(model_id)
            
            # 7. Read CSV and prepare for embedding
            csv_path = dataset.csv_path
            if not Path(csv_path).exists():
                dataset.embedding_status = EmbeddingStatus.FAILED
                dataset.embedding_error = f"CSV file not found: {csv_path}"
                await db.commit()
                return {
                    "success": False,
                    "error": "CSV_NOT_FOUND",
                    "message": f"CSV file not found: {csv_path}"
                }
            
            df = pd.read_csv(csv_path)
            total_rows = len(df)
            
            if total_rows == 0:
                dataset.embedding_status = EmbeddingStatus.COMPLETED
                dataset.embedding_progress = 100
                dataset.total_rows = 0
                dataset.embedded_rows = 0
                await db.commit()
                return {
                    "success": True,
                    "message": "Dataset is empty",
                    "embedded_count": 0
                }
            
            dataset.total_rows = total_rows
            await db.commit()
            
            logger.info(f" Embedding {total_rows} rows")
            
            # 8. Process in batches
            embedded_count = 0
            failed_count = 0
            template_id = dataset.t_id
            
            for batch_start in range(0, total_rows, batch_size):
                batch_end = min(batch_start + batch_size, total_rows)
                batch = df.iloc[batch_start:batch_end]
                
                # Prepare texts for embedding
                texts = []
                row_metadata = []
                
                for idx, row in batch.iterrows():
                    # Combine fields for rich context
                    query = row.get('query', '')
                    api = row.get('api', row.get('api_name', ''))
                    notes = row.get('notes', '')
                    endpoint = row.get('endpoint', '')
                    method = row.get('method', 'POST')
                    
                    text = f"{query} {api} {endpoint} {notes}".strip()
                    if not text:
                        text = f"API test case row {idx}"
                    
                    texts.append(text)
                    row_metadata.append({
                        "row_id": int(idx),
                        "query": str(query),
                        "api_name": str(api),
                        "endpoint": str(endpoint),
                        "method": str(method),
                        "scenario_type": str(row.get('scenario_type', 'valid')),
                        "test_category": str(row.get('test_category', 'valid_flow')),
                        "notes": str(notes),
                    })
                
                # Generate embeddings using Ollama
                try:
                    embeddings = await self.ollama_service.generate_embeddings_batch(
                        model_name=model_id,
                        texts=texts,
                        batch_size=batch_size
                    )
                except Exception as e:
                    logger.error(f"Batch embedding failed: {e}")
                    failed_count += len(texts)
                    continue
                
                # Prepare vectors for batch storage
                vectors_data = []
                for i, (embedding, metadata) in enumerate(zip(embeddings, row_metadata)):
                    if embedding is None:
                        failed_count += 1
                        continue
                    
                    vectors_data.append({
                        "row_id": metadata["row_id"],
                        "vector": np.array(embedding, dtype=np.float32),
                        "metadata": metadata
                    })
                
                # Store in Redis
                if vectors_data:
                    success, failures = self.redis_service.store_vectors_batch(
                        model_id=model_id,
                        user_id=user_id,
                        dataset_id=dataset_id,
                        template_id=template_id,
                        vectors_data=vectors_data
                    )
                    embedded_count += success
                    failed_count += failures
                
                # Update progress
                progress = int((batch_end / total_rows) * 100)
                dataset.embedding_progress = progress
                dataset.embedded_rows = embedded_count
                await db.commit()
                
                logger.info(
                    f" Progress: {progress}% ({embedded_count}/{total_rows})"
                )
            
            # 9. Finalize
            dataset.embedding_status = EmbeddingStatus.COMPLETED
            dataset.embedding_progress = 100
            dataset.embedded_rows = embedded_count
            dataset.embedding_completed_at = datetime.utcnow()
            
            if failed_count > 0:
                dataset.embedding_error = f"{failed_count} rows failed to embed"
            
            await db.commit()
            
            logger.info(
                f" Embedding completed: {embedded_count}/{total_rows} rows "
                f"(model={model_id}, failed={failed_count})"
            )
            
            return {
                "success": True,
                "task_id": task_id,
                "dataset_id": str(dataset_id),
                "model_id": model_id,
                "dimension": dimension,
                "redis_index": model_spec.redis_index_name,
                "redis_namespace": model_spec.redis_namespace,
                "total_rows": total_rows,
                "embedded_count": embedded_count,
                "failed_count": failed_count,
                "status": EmbeddingStatus.COMPLETED
            }
            
        except Exception as e:
            logger.error(f" Embedding failed: {e}", exc_info=True)
            
            # Update dataset with error
            try:
                result = await db.execute(
                    select(Dataset).where(Dataset.dataset_id == dataset_id)
                )
                dataset = result.scalar_one_or_none()
                if dataset:
                    dataset.embedding_status = EmbeddingStatus.FAILED
                    dataset.embedding_error = str(e)
                    await db.commit()
            except Exception:
                pass
            
            return {
                "success": False,
                "error": "EMBEDDING_FAILED",
                "message": str(e),
                "task_id": task_id
            }
    
    async def reembed_dataset(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        dataset_id: uuid.UUID,
        new_model_id: Optional[str] = None,
        batch_size: int = 32
    ) -> Dict[str, Any]:
        """
        Re-embed a dataset with a new model (or current settings model).
        
        This is called when user explicitly wants to change the embedding model.
        It will:
        1. Update user's Settings if new_model_id provided
        2. Delete all existing vectors
        3. Re-embed with new model
        
        Args:
            db: AsyncSession
            user_id: User UUID
            dataset_id: Dataset UUID
            new_model_id: Optional new model to use (updates Settings)
            batch_size: Batch size for embedding
            
        Returns:
            Re-embedding result
        """
        # If new model specified, update Settings first
        if new_model_id:
            await self.settings_service.set_active_embedding_model_async(
                db, user_id, new_model_id
            )
            logger.info(f" Updated Settings to use model: {new_model_id}")
        
        # Now embed with force_reembed=True
        return await self.embed_dataset(
            db=db,
            user_id=user_id,
            dataset_id=dataset_id,
            batch_size=batch_size,
            force_reembed=True
        )
    
    # --- Status Methods ---
    
    async def get_embedding_status(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        dataset_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Get embedding status for a dataset.
        
        Args:
            db: AsyncSession
            user_id: User UUID
            dataset_id: Dataset UUID
            
        Returns:
            Embedding status info
        """
        result = await db.execute(
            select(Dataset).where(
                Dataset.dataset_id == dataset_id,
                Dataset.u_id == user_id
            )
        )
        dataset = result.scalar_one_or_none()
        
        if not dataset:
            return {
                "error": ErrorCode.DATASET_NOT_FOUND,
                "message": f"Dataset {dataset_id} not found"
            }
        
        return {
            "dataset_id": str(dataset.dataset_id),
            "status": dataset.embedding_status,
            "progress": dataset.embedding_progress,
            "embedding_model": dataset.embedding_model,
            "embedding_dimension": dataset.embedding_dimension,
            "total_rows": dataset.total_rows,
            "embedded_rows": dataset.embedded_rows,
            "error": dataset.embedding_error,
            "started_at": dataset.embedding_started_at.isoformat() if dataset.embedding_started_at else None,
            "completed_at": dataset.embedding_completed_at.isoformat() if dataset.embedding_completed_at else None,
        }
    
    async def check_model_compatibility(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        dataset_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Check if user's current model is compatible with dataset's embedded model.
        
        This should be called before any vector search.
        
        Args:
            db: AsyncSession
            user_id: User UUID
            dataset_id: Dataset UUID
            
        Returns:
            Compatibility info with actions if mismatched
        """
        # Get dataset
        result = await db.execute(
            select(Dataset).where(
                Dataset.dataset_id == dataset_id,
                Dataset.u_id == user_id
            )
        )
        dataset = result.scalar_one_or_none()
        
        if not dataset:
            return {
                "error": ErrorCode.DATASET_NOT_FOUND,
                "message": f"Dataset {dataset_id} not found"
            }
        
        # Check if dataset is embedded
        if not dataset.embedding_model:
            return {
                "compatible": False,
                "error": ErrorCode.NOT_EMBEDDED,
                "message": "Dataset has not been embedded yet",
                "action_required": "embed_dataset",
                "endpoint": f"/api/v1/datasets/{dataset_id}/embed"
            }
        
        if dataset.embedding_status == EmbeddingStatus.IN_PROGRESS:
            return {
                "compatible": False,
                "error": ErrorCode.EMBEDDING_IN_PROGRESS,
                "message": f"Embedding in progress ({dataset.embedding_progress}%)",
                "progress": dataset.embedding_progress
            }
        
        # Get user's active model
        user_model_id, _, _ = await self.settings_service.get_active_embedding_model_async(
            db, user_id
        )
        
        # Check compatibility
        return self.settings_service.validate_model_for_search(
            user_model_id=user_model_id,
            dataset_model_id=dataset.embedding_model
        )


# --- Singleton Accessor ---

_service_instance: Optional[MultiModelDatasetEmbeddingService] = None


def get_multi_model_embedding_service() -> MultiModelDatasetEmbeddingService:
    """Get the singleton multi-model dataset embedding service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = MultiModelDatasetEmbeddingService()
    return _service_instance