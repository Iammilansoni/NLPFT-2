# Backend/app/services/multi_model_embedding_service.py

"""
Dataset Embedding Service
=========================

Turns a generated or uploaded dataset into routable vectors.

Every row's utterance (`query` column) is embedded with the deployment's runtime
embedder (`app.core.runtime.get_embedder`) and written to PostgreSQL
`vector_rows` through `PgVectorStore`, inside a tenant-bound transaction. That is
exactly the store and the embedder Stage 1 of the routing pipeline reads with,
so a freshly embedded dataset is immediately queryable.

Rules:
  1. One embedder per deployment. The dataset records the model and dimension
     it was embedded with; routing refuses to search a dataset embedded by a
     different model (MODEL_MISMATCH) instead of comparing incompatible vectors.
  2. Embedding is idempotent: the dataset's previous vectors are deleted first,
     so re-running never duplicates rows.
  3. Only the utterance is embedded -- the same text the benchmark and the demo
     seed index -- so retrieval quality measured in evals/ applies here.
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.core.runtime import get_embedder
from app.core.tenancy import tenant_session
from app.models.database_models import CSVData, Dataset, Template
from app.models.schemas.embedding_schemas import EmbeddingStatus, ErrorCode
from app.services.pgvector_store import get_pgvector_store


def _clean(value: Any, default: str = "") -> str:
    """pandas yields NaN for empty cells; never embed or store the string 'nan'."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    return str(value).strip()


class MultiModelDatasetEmbeddingService:
    """Embeds datasets into pgvector with the runtime embedder."""

    def __init__(self):
        self.embedder = get_embedder()
        self.store = get_pgvector_store()

    async def embed_dataset(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        dataset_id: uuid.UUID,
        batch_size: int = 64,
        force_reembed: bool = False,
    ) -> Dict[str, Any]:
        """
        Embed every utterance of a dataset and index it for routing.

        Returns a status dict. Failures are reported and also recorded on the
        dataset row, so the UI's status polling shows them.
        """
        task_id = str(uuid.uuid4())
        model_id = self.embedder.model_id
        dimension = self.embedder.dimension

        dataset = (
            await db.execute(
                select(Dataset).where(Dataset.dataset_id == dataset_id, Dataset.u_id == user_id)
            )
        ).scalar_one_or_none()
        if not dataset:
            return {
                "success": False,
                "error": ErrorCode.DATASET_NOT_FOUND,
                "message": f"Dataset {dataset_id} not found",
            }

        if dataset.embedding_model and dataset.embedding_model != model_id and not force_reembed:
            return {
                "success": False,
                "error": ErrorCode.MODEL_MISMATCH,
                "message": (
                    f"Dataset was embedded with '{dataset.embedding_model}', but this "
                    f"deployment embeds with '{model_id}'. Re-embed to replace its vectors."
                ),
                "dataset_id": str(dataset_id),
                "existing_model": dataset.embedding_model,
                "requested_model": model_id,
                "options": [
                    {
                        "action": "force_reembed",
                        "label": f"Re-embed with {model_id}",
                        "description": "Deletes the existing vectors and creates new ones",
                    }
                ],
            }

        async def _fail(error: str, message: str) -> Dict[str, Any]:
            dataset.embedding_status = EmbeddingStatus.FAILED
            dataset.embedding_error = message
            await db.commit()
            return {"success": False, "error": error, "message": message, "task_id": task_id}

        try:
            csv_path = dataset.csv_path
            if not csv_path or not Path(csv_path).exists():
                return await _fail("CSV_NOT_FOUND", f"CSV file not found: {csv_path}")

            df = pd.read_csv(csv_path)
            if "query" not in df.columns:
                return await _fail("INVALID_DATASET", "Dataset has no 'query' column to embed")

            # Rows need a template id to be routable. Generated datasets carry
            # one on the dataset; uploaded CSVs may instead name the API per row.
            template_ids = await self._template_ids_by_name(db, user_id)

            rows: List[Dict[str, Any]] = []
            for _, row in df.iterrows():
                utterance = _clean(row.get("query"))
                if not utterance:
                    continue
                api_name = _clean(row.get("api_name", row.get("api")))
                t_id = dataset.t_id or template_ids.get(api_name)
                rows.append(
                    {
                        "t_id": t_id,
                        "dataset_id": dataset.dataset_id,
                        "query": utterance,
                        "api_name": api_name or None,
                        "endpoint": _clean(row.get("endpoint")) or None,
                        "method": _clean(row.get("method"), "POST"),
                        "scenario_type": _clean(row.get("scenario_type"), "valid"),
                        "test_category": _clean(row.get("test_category")) or None,
                        "intent_type": _clean(row.get("intent_type")) or None,
                        "notes": _clean(row.get("notes")) or None,
                    }
                )

            total_rows = len(rows)
            dataset.embedding_status = EmbeddingStatus.IN_PROGRESS
            dataset.embedding_progress = 0
            dataset.embedding_model = model_id
            dataset.embedding_dimension = dimension
            dataset.total_rows = total_rows
            dataset.embedded_rows = 0
            dataset.embedding_error = None
            dataset.embedding_started_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await db.commit()

            # Idempotent: drop this dataset's previous vectors first.
            async with tenant_session(user_id) as tdb:
                deleted = await self.store.delete_by_dataset(tdb, dataset.dataset_id)
            if deleted:
                logger.info(f"Removed {deleted} previous vectors for dataset {str(dataset_id)[:8]}")

            unroutable = sum(1 for r in rows if not r["t_id"])
            embedded = 0
            for start in range(0, total_rows, batch_size):
                batch = rows[start : start + batch_size]
                vectors = await self.embedder.embed([r["query"] for r in batch])
                if len(vectors) != len(batch):
                    raise RuntimeError(
                        f"embedder returned {len(vectors)} vectors for {len(batch)} texts"
                    )
                async with tenant_session(user_id) as tdb:
                    embedded += await self.store.upsert_rows(
                        tdb, batch, vectors, embedding_model=model_id, dimension=dimension
                    )
                dataset.embedded_rows = embedded
                dataset.embedding_progress = int(embedded * 100 / max(total_rows, 1))
                await db.commit()

            dataset.embedding_status = EmbeddingStatus.COMPLETED
            dataset.embedding_progress = 100
            dataset.embedding_completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            if unroutable:
                dataset.embedding_error = (
                    f"{unroutable} rows have no template and cannot be routed to"
                )
            await db.execute(
                update(CSVData)
                .where(CSVData.dataset_id == dataset_id, CSVData.u_id == user_id)
                .values(is_embedded=1)
            )
            await db.commit()

            logger.info(
                f"Embedded dataset {str(dataset_id)[:8]}: {embedded}/{total_rows} rows "
                f"(model={model_id}, dim={dimension})"
            )
            return {
                "success": True,
                "task_id": task_id,
                "dataset_id": str(dataset_id),
                "model_id": model_id,
                "dimension": dimension,
                "vector_store": "pgvector",
                "total_rows": total_rows,
                "embedded_count": embedded,
                "failed_count": total_rows - embedded,
                "unroutable_rows": unroutable,
                "status": EmbeddingStatus.COMPLETED,
            }

        except Exception as e:  # noqa: BLE001 - recorded on the dataset and returned
            logger.error(f"Embedding failed for dataset {dataset_id}: {e}", exc_info=True)
            await db.rollback()
            return await _fail("EMBEDDING_FAILED", str(e))

    async def _template_ids_by_name(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> Dict[str, uuid.UUID]:
        result = await db.execute(
            select(Template.api_name, Template.t_id).where(Template.u_id == user_id)
        )
        return {name: t_id for name, t_id in result.all() if name}

    async def reembed_dataset(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        dataset_id: uuid.UUID,
        new_model_id: Optional[str] = None,
        batch_size: int = 64,
    ) -> Dict[str, Any]:
        """
        Re-embed a dataset with the runtime embedder, replacing its vectors.

        `new_model_id` is accepted for API compatibility. The embedding model is a
        deployment setting (EXECUTION_MODE), so a request for a different model
        is reported rather than silently ignored.
        """
        if new_model_id and new_model_id != self.embedder.model_id:
            return {
                "success": False,
                "error": ErrorCode.MODEL_MISMATCH,
                "message": (
                    f"This deployment embeds with '{self.embedder.model_id}'. The "
                    f"embedding model is set per deployment (EXECUTION_MODE), not per request."
                ),
            }
        return await self.embed_dataset(
            db=db, user_id=user_id, dataset_id=dataset_id,
            batch_size=batch_size, force_reembed=True,
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
                "endpoint": f"/api/v1/datasets/db/{dataset_id}/embed"
            }
        
        if dataset.embedding_status == EmbeddingStatus.IN_PROGRESS:
            return {
                "compatible": False,
                "error": ErrorCode.EMBEDDING_IN_PROGRESS,
                "message": f"Embedding in progress ({dataset.embedding_progress}%)",
                "progress": dataset.embedding_progress
            }
        
        runtime_model = self.embedder.model_id
        if dataset.embedding_model == runtime_model:
            return {"compatible": True, "model": runtime_model}
        return {
            "compatible": False,
            "error": ErrorCode.MODEL_MISMATCH,
            "message": (
                f"Dataset embedded with '{dataset.embedding_model}', deployment "
                f"embeds with '{runtime_model}'. Re-embed the dataset."
            ),
            "dataset_model": dataset.embedding_model,
            "runtime_model": runtime_model,
        }


# --- Singleton Accessor ---

_service_instance: Optional[MultiModelDatasetEmbeddingService] = None


def get_multi_model_embedding_service() -> MultiModelDatasetEmbeddingService:
    """Get the singleton multi-model dataset embedding service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = MultiModelDatasetEmbeddingService()
    return _service_instance