# Backend/app/services/multi_model_embedding_service.py

"""
Dataset Embedding Service
=========================

Turns a generated or uploaded dataset into routable vectors.

Every row's utterance (`query` column) is embedded with the user's active
embedding model (Settings -> Embedding model, else the deployment default) and
written to PostgreSQL `vector_rows` through `PgVectorStore`, inside a
tenant-bound transaction. Search reads with the same selection, so a freshly
embedded dataset is immediately queryable.

Rules:
  1. A dataset is tagged with the (provider, model, dimension) that embedded
     it. Embedding over a different model needs an explicit re-embed; routing
     never compares vectors across models (MODEL_MISMATCH instead).
  2. Embedding is idempotent: the dataset's previous vectors are deleted first,
     so re-running never duplicates rows.
  3. Only the utterance is embedded -- the same text the benchmark and the demo
     seed index -- so retrieval quality measured in evals/ applies here.
  4. Long jobs run on the Celery worker (`queue_embedding`); the dataset row
     carries progress and a plain-English error for the UI to poll.
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.core.tenancy import tenant_session
from app.llm.embeddings import EmbeddingError
from app.llm.provider_registry import provider_label
from app.models.database_models import CSVData, Dataset, Template, UserSettings
from app.models.schemas.embedding_schemas import EmbeddingStatus, ErrorCode
from app.services.model_access import EmbeddingSelection, active_embedding, embedder_for
from app.services.pgvector_store import get_pgvector_store

PROGRESS_CHUNK = 64  # rows per progress update


def _clean(value: Any, default: str = "") -> str:
    """pandas yields NaN for empty cells; never embed or store the string 'nan'."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    return str(value).strip()


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def dataset_embedding(dataset: Dataset) -> Optional[Dict[str, Any]]:
    """The model a dataset's vectors came from, or None if it was never embedded."""
    if not dataset.embedding_model:
        return None
    provider = dataset.embedding_provider or "ollama"
    return {
        "provider": provider,
        "provider_label": provider_label(provider),
        "model_id": dataset.embedding_model,
        "dimension": dataset.embedding_dimension,
        "label": f"{provider_label(provider)} · {dataset.embedding_model} · {dataset.embedding_dimension}-dim",
    }


def mismatch_options(dataset: Dataset, active: EmbeddingSelection) -> List[Dict[str, Any]]:
    """The two ways out of a model mismatch, described for the UI."""
    embedded = dataset_embedding(dataset)
    return [
        {
            "action": "switch_model",
            "label": f"Search with {embedded['model_id']}",
            "description": f"Switch your embedding model back to {embedded['label']}. No re-embedding needed.",
            "provider": embedded["provider"],
            "model_id": embedded["model_id"],
            "dimension": embedded["dimension"],
        },
        {
            "action": "reembed",
            "label": f"Re-embed with {active.model_id}",
            "description": f"Replace this dataset's vectors using {active.label}.",
            "dataset_id": str(dataset.dataset_id),
        },
    ]


class MultiModelDatasetEmbeddingService:
    """Embeds datasets into pgvector with the user's embedding model."""

    def __init__(self):
        self.store = get_pgvector_store()

    async def _dataset(self, db: AsyncSession, user_id: uuid.UUID, dataset_id: uuid.UUID) -> Optional[Dataset]:
        return (await db.execute(
            select(Dataset).where(Dataset.dataset_id == dataset_id, Dataset.u_id == user_id)
        )).scalar_one_or_none()

    async def check_before_embedding(
        self, db: AsyncSession, user_id: uuid.UUID, dataset_id: uuid.UUID, force_reembed: bool
    ) -> Optional[Dict[str, Any]]:
        """An error dict if embedding should not start, else None."""
        dataset = await self._dataset(db, user_id, dataset_id)
        if not dataset:
            return {"success": False, "error": ErrorCode.DATASET_NOT_FOUND, "message": f"Dataset {dataset_id} not found"}
        if dataset.embedding_status == EmbeddingStatus.IN_PROGRESS and not force_reembed:
            return {
                "success": False, "error": ErrorCode.EMBEDDING_IN_PROGRESS,
                "message": f"This dataset is already being embedded ({dataset.embedding_progress or 0}% done).",
            }
        active = await active_embedding(db, user_id)
        if dataset.embedding_model and not force_reembed and not active.matches(
            dataset.embedding_provider or "ollama", dataset.embedding_model, dataset.embedding_dimension
        ):
            embedded = dataset_embedding(dataset)
            return {
                "success": False,
                "error": ErrorCode.MODEL_MISMATCH,
                "message": (
                    f"This dataset was embedded with {embedded['label']}, but your embedding model is "
                    f"{active.label}. Re-embed it, or switch your model back."
                ),
                "dataset_id": str(dataset_id),
                "dataset_model": embedded,
                "active_model": active.to_dict(),
                "options": mismatch_options(dataset, active),
            }
        return None

    async def mark_queued(self, db: AsyncSession, user_id: uuid.UUID, dataset_id: uuid.UUID) -> None:
        """Show the dataset as in progress the moment the job is queued, so the UI starts polling."""
        dataset = await self._dataset(db, user_id, dataset_id)
        if dataset:
            dataset.embedding_status = EmbeddingStatus.IN_PROGRESS
            dataset.embedding_progress = 0
            dataset.embedding_error = None
            await db.commit()

    async def embed_dataset(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        dataset_id: uuid.UUID,
        force_reembed: bool = False,
        selection: Optional[EmbeddingSelection] = None,
    ) -> Dict[str, Any]:
        """
        Embed every utterance of a dataset and index it for routing.

        Returns a status dict. Failures are reported and also recorded on the
        dataset row, so the UI's status polling shows them.
        """
        task_id = str(uuid.uuid4())
        if not force_reembed:
            blocked = await self.check_before_embedding(db, user_id, dataset_id, force_reembed=False)
            if blocked:
                return blocked
        dataset = await self._dataset(db, user_id, dataset_id)
        if not dataset:
            return {"success": False, "error": ErrorCode.DATASET_NOT_FOUND, "message": f"Dataset {dataset_id} not found"}
        selection = selection or await active_embedding(db, user_id)

        async def _fail(error: str, message: str) -> Dict[str, Any]:
            dataset.embedding_status = EmbeddingStatus.FAILED
            dataset.embedding_error = message
            await db.commit()
            logger.warning(f"Embedding dataset {str(dataset_id)[:8]} failed: {message}")
            return {"success": False, "error": error, "message": message, "task_id": task_id}

        try:
            embedder = await embedder_for(db, user_id, selection)
        except EmbeddingError as exc:
            return await _fail(exc.code, exc.message)

        try:
            csv_path = dataset.csv_path
            if not csv_path or not Path(csv_path).exists():
                return await _fail("CSV_NOT_FOUND", "The dataset's CSV file is missing on the server. Generate or upload it again.")

            df = pd.read_csv(csv_path)
            if "query" not in df.columns:
                return await _fail("INVALID_DATASET", "The dataset has no 'query' column, so there is nothing to embed.")

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
            dataset.embedding_provider = selection.provider
            dataset.embedding_model = selection.model_id
            dataset.embedding_dimension = selection.dimension
            dataset.total_rows = total_rows
            dataset.embedded_rows = 0
            dataset.embedding_error = None
            dataset.embedding_started_at = _now()
            await db.commit()

            await self.store.ensure_index(db, selection.dimension)

            # Idempotent: drop this dataset's previous vectors first.
            async with tenant_session(user_id) as tdb:
                deleted = await self.store.delete_by_dataset(tdb, dataset.dataset_id)
            if deleted:
                logger.info(f"Removed {deleted} previous vectors for dataset {str(dataset_id)[:8]}")

            unroutable = sum(1 for r in rows if not r["t_id"])
            embedded = 0
            for start in range(0, total_rows, PROGRESS_CHUNK):
                batch = rows[start : start + PROGRESS_CHUNK]
                vectors = await embedder.embed([r["query"] for r in batch])
                if embedder.dimension != selection.dimension:
                    # The model's real width differs from what was recorded
                    # (e.g. the provider changed it). Index under the real one
                    # and correct the user's setting so search matches.
                    selection = await self._correct_dimension(db, user_id, selection, embedder.dimension)
                    dataset.embedding_dimension = selection.dimension
                    await self.store.ensure_index(db, selection.dimension)
                async with tenant_session(user_id) as tdb:
                    embedded += await self.store.upsert_rows(
                        tdb, batch, vectors,
                        embedding_model=selection.model_id,
                        dimension=selection.dimension,
                        embedding_provider=selection.provider,
                    )
                dataset.embedded_rows = embedded
                dataset.embedding_progress = int(embedded * 100 / max(total_rows, 1))
                await db.commit()

            dataset.embedding_status = EmbeddingStatus.COMPLETED
            dataset.embedding_progress = 100
            dataset.embedding_completed_at = _now()
            if unroutable:
                dataset.embedding_error = f"{unroutable} rows have no template and cannot be routed to"
            await db.execute(
                update(CSVData)
                .where(CSVData.dataset_id == dataset_id, CSVData.u_id == user_id)
                .values(is_embedded=1)
            )
            await db.commit()

            logger.info(
                f"Embedded dataset {str(dataset_id)[:8]}: {embedded}/{total_rows} rows with {selection.label}"
            )
            return {
                "success": True,
                "task_id": task_id,
                "dataset_id": str(dataset_id),
                "provider": selection.provider,
                "model_id": selection.model_id,
                "dimension": selection.dimension,
                "vector_store": "pgvector",
                "total_rows": total_rows,
                "embedded_count": embedded,
                "failed_count": total_rows - embedded,
                "unroutable_rows": unroutable,
                "status": EmbeddingStatus.COMPLETED,
            }

        except EmbeddingError as exc:
            await db.rollback()
            return await _fail(exc.code, exc.message)
        except Exception as e:  # noqa: BLE001 - recorded on the dataset and returned
            logger.error(f"Embedding failed for dataset {dataset_id}: {e}", exc_info=True)
            await db.rollback()
            return await _fail("EMBEDDING_FAILED", f"Embedding stopped unexpectedly: {e}")

    async def _correct_dimension(
        self, db: AsyncSession, user_id: uuid.UUID, selection: EmbeddingSelection, measured: int
    ) -> EmbeddingSelection:
        logger.warning(f"{selection.label} now produces {measured}-dim vectors; recording the measured width")
        if not selection.is_default:
            settings = (await db.execute(select(UserSettings).where(UserSettings.u_id == user_id))).scalar_one_or_none()
            if settings:
                settings.embedding_dimension = measured
        return EmbeddingSelection(selection.provider, selection.model_id, measured, selection.is_default)

    async def _template_ids_by_name(self, db: AsyncSession, user_id: uuid.UUID) -> Dict[str, uuid.UUID]:
        result = await db.execute(select(Template.api_name, Template.t_id).where(Template.u_id == user_id))
        return {name: t_id for name, t_id in result.all() if name}

    async def get_embedding_status(self, db: AsyncSession, user_id: uuid.UUID, dataset_id: uuid.UUID) -> Dict[str, Any]:
        dataset = await self._dataset(db, user_id, dataset_id)
        if not dataset:
            return {"error": ErrorCode.DATASET_NOT_FOUND, "message": f"Dataset {dataset_id} not found"}
        active = await active_embedding(db, user_id)
        embedded = dataset_embedding(dataset)
        return {
            "dataset_id": str(dataset.dataset_id),
            "status": dataset.embedding_status,
            "progress": dataset.embedding_progress,
            "embedding": embedded,
            "embedding_provider": dataset.embedding_provider,
            "embedding_model": dataset.embedding_model,
            "embedding_dimension": dataset.embedding_dimension,
            "matches_active_model": bool(embedded) and active.matches(
                embedded["provider"], embedded["model_id"], embedded["dimension"]
            ),
            "total_rows": dataset.total_rows,
            "embedded_rows": dataset.embedded_rows,
            "error": dataset.embedding_error,
            "started_at": dataset.embedding_started_at.isoformat() if dataset.embedding_started_at else None,
            "completed_at": dataset.embedding_completed_at.isoformat() if dataset.embedding_completed_at else None,
        }


async def embedding_groups(db: AsyncSession, user_id: uuid.UUID) -> List[Dict[str, Any]]:
    """The user's embedded datasets, grouped by the model that produced their vectors."""
    datasets = (await db.execute(
        select(Dataset).where(
            Dataset.u_id == user_id,
            Dataset.embedding_status == EmbeddingStatus.COMPLETED,
            Dataset.embedding_model.isnot(None),
        ).order_by(Dataset.created_at.desc())
    )).scalars().all()
    groups: Dict[tuple, Dict[str, Any]] = {}
    for dataset in datasets:
        embedded = dataset_embedding(dataset)
        key = (embedded["provider"], embedded["model_id"], embedded["dimension"])
        group = groups.setdefault(key, {**embedded, "datasets": []})
        group["datasets"].append({
            "dataset_id": str(dataset.dataset_id),
            "name": dataset.name or "Untitled dataset",
            "rows": dataset.embedded_rows or 0,
        })
    return list(groups.values())


async def queue_embedding(db: AsyncSession, user_id: uuid.UUID, dataset_id: uuid.UUID, force_reembed: bool) -> Dict[str, Any]:
    """
    Start embedding a dataset on the Celery worker.

    Checks run here, synchronously, so a model mismatch or a missing dataset is
    answered immediately instead of failing later in the background.
    """
    service = get_multi_model_embedding_service()
    blocked = await service.check_before_embedding(db, user_id, dataset_id, force_reembed)
    if blocked:
        return blocked
    active = await active_embedding(db, user_id)
    await service.mark_queued(db, user_id, dataset_id)
    try:
        from app.worker.tasks import embed_dataset_task

        embed_dataset_task.delay(str(user_id), str(dataset_id))
    except Exception as exc:  # noqa: BLE001 - no broker: embed in this request instead
        logger.warning(f"Could not queue embedding ({exc}); embedding inline")
        return await service.embed_dataset(db, user_id, dataset_id, force_reembed=True)
    return {
        "success": True,
        "queued": True,
        "dataset_id": str(dataset_id),
        "status": EmbeddingStatus.IN_PROGRESS,
        "provider": active.provider,
        "model_id": active.model_id,
        "dimension": active.dimension,
        "message": f"Embedding with {active.label}. Progress updates as it runs.",
    }


# --- Singleton Accessor ---

_service_instance: Optional[MultiModelDatasetEmbeddingService] = None


def get_multi_model_embedding_service() -> MultiModelDatasetEmbeddingService:
    """Get the singleton dataset embedding service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = MultiModelDatasetEmbeddingService()
    return _service_instance
