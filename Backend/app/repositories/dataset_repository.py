"""
Dataset Repository
==================

Owns every dataset query that `api/v1/datasets.py` used to inline.

Each method below replaces one or more raw `db.execute(select(...))` blocks in
that router. The route bodies become: validate input, call a method here,
serialise the result.

None of these methods filter on `u_id`. Postgres RLS does that -- see
`repositories/base.py` for why re-adding it would be actively harmful.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from sqlalchemy import func, select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.models.database_models import Dataset, Template
from app.repositories.base import BaseRepository

# Terminal + transitional states used by the embedding pipeline.
EMBEDDING_STATES = ("pending", "in_progress", "completed", "failed")


class DatasetRepository(BaseRepository[Dataset]):
    model = Dataset
    pk_name = "dataset_id"

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    async def list_for_tenant(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        embedding_status: Optional[str] = None,
        template_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Dataset], int]:
        """
        Paginated listing plus a total count for the same filters.

        Replaces the near-duplicate query bodies behind `/`, `/list` and
        `/db/list`, which had drifted apart in v1.
        """
        stmt = select(Dataset)
        count_stmt = select(func.count()).select_from(Dataset)

        def _apply(s):
            if embedding_status:
                s = s.where(Dataset.embedding_status == embedding_status)
            if template_id:
                s = s.where(Dataset.t_id == template_id)
            if search:
                s = s.where(Dataset.name.ilike(f"%{search}%"))
            return s

        stmt = _apply(stmt).order_by(Dataset.created_at.desc()).limit(limit).offset(offset)
        count_stmt = _apply(count_stmt)

        rows = list((await self.db.execute(stmt)).scalars().all())
        total = int((await self.db.execute(count_stmt)).scalar() or 0)
        return rows, total

    async def list_by_template(
        self, template_id: uuid.UUID, *, limit: int = 50
    ) -> List[Dataset]:
        stmt = (
            select(Dataset)
            .where(Dataset.t_id == template_id)
            .order_by(Dataset.created_at.desc())
            .limit(limit)
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def latest_for_template(self, template_id: uuid.UUID) -> Optional[Dataset]:
        """Most recent dataset for a template -- used by the model-compat check."""
        stmt = (
            select(Dataset)
            .where(Dataset.t_id == template_id)
            .order_by(Dataset.created_at.desc())
            .limit(1)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    # ------------------------------------------------------------------
    # Joined reads
    # ------------------------------------------------------------------

    async def get_with_template(
        self, dataset_id: uuid.UUID
    ) -> Optional[Tuple[Dataset, Optional[Template]]]:
        """
        Dataset plus its template in one round trip.

        v1 fetched these separately in several endpoints -- two queries where one
        outer join suffices, and a window in which the template could vanish
        between them.
        """
        stmt = (
            select(Dataset, Template)
            .outerjoin(Template, Dataset.t_id == Template.t_id)
            .where(Dataset.dataset_id == dataset_id)
        )
        row = (await self.db.execute(stmt)).first()
        return (row[0], row[1]) if row else None

    # ------------------------------------------------------------------
    # Embedding lifecycle
    # ------------------------------------------------------------------

    async def set_embedding_status(
        self,
        dataset_id: uuid.UUID,
        status: str,
        *,
        progress: Optional[int] = None,
        error: Optional[str] = None,
        embedded_rows: Optional[int] = None,
    ) -> bool:
        """Advance a dataset's embedding state machine."""
        if status not in EMBEDDING_STATES:
            raise ValueError(f"invalid embedding_status {status!r}; expected one of {EMBEDDING_STATES}")

        values: Dict[str, Any] = {"embedding_status": status}
        if progress is not None:
            values["embedding_progress"] = max(0, min(100, progress))
        if error is not None:
            values["embedding_error"] = error
        if embedded_rows is not None:
            values["embedded_rows"] = embedded_rows
        if status == "completed":
            values["embedding_progress"] = 100
            values["embedding_error"] = None

        result = await self.db.execute(
            sa_update(Dataset).where(Dataset.dataset_id == dataset_id).values(**values)
        )
        return bool(result.rowcount)

    async def mark_embedding_model(
        self, dataset_id: uuid.UUID, model: str, dimension: int
    ) -> bool:
        """
        Record which model embedded this dataset.

        This is the field the Stage 1 compatibility check reads before searching.
        A dataset embedded with one model and queried with another produces
        meaningless distances, so it is written in the same transaction that
        starts embedding rather than afterwards.
        """
        result = await self.db.execute(
            sa_update(Dataset)
            .where(Dataset.dataset_id == dataset_id)
            .values(embedding_model=model, embedding_dimension=dimension)
        )
        return bool(result.rowcount)

    async def find_stale_processing(self, older_than_minutes: int = 30) -> List[Dataset]:
        """
        Datasets stuck `in_progress` past a threshold -- a worker died mid-run.

        Backs the stale-task recovery service. Returns rows rather than mutating,
        so the caller decides between retry and fail.
        """
        cutoff = datetime.now(timezone.utc).timestamp() - older_than_minutes * 60
        stmt = select(Dataset).where(Dataset.embedding_status == "in_progress")
        rows = list((await self.db.execute(stmt)).scalars().all())
        stale = []
        for row in rows:
            created = row.created_at
            if created is None:
                continue
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if created.timestamp() < cutoff:
                stale.append(row)
        return stale

    # ------------------------------------------------------------------
    # Aggregates
    # ------------------------------------------------------------------

    async def stats(self) -> Dict[str, Any]:
        """Dashboard counters for the caller's tenant, in one query per axis."""
        by_status = {
            r[0]: int(r[1])
            for r in (
                await self.db.execute(
                    select(Dataset.embedding_status, func.count()).group_by(
                        Dataset.embedding_status
                    )
                )
            ).all()
        }
        totals = (
            await self.db.execute(
                select(
                    func.count(),
                    func.coalesce(func.sum(Dataset.total_rows), 0),
                    func.coalesce(func.sum(Dataset.embedded_rows), 0),
                ).select_from(Dataset)
            )
        ).first()

        return {
            "datasets": int(totals[0] or 0),
            "total_rows": int(totals[1] or 0),
            "embedded_rows": int(totals[2] or 0),
            "by_status": {s: by_status.get(s, 0) for s in EMBEDDING_STATES},
        }

    async def delete_cascade(self, dataset_id: uuid.UUID) -> Dict[str, int]:
        """
        Delete a dataset and its vectors.

        `vector_rows.dataset_id` carries no FK to datasets (vectors may outlive a
        dataset during re-embedding), so the cleanup is explicit. Both statements
        share the caller's transaction, so a failure rolls back together and
        cannot orphan vectors.
        """
        from app.services.pgvector_store import get_pgvector_store

        vectors = await get_pgvector_store().delete_by_dataset(self.db, dataset_id)
        deleted = await self.delete(dataset_id)
        logger.info(
            f"Deleted dataset {dataset_id}: {int(deleted)} row, {vectors} vectors"
        )
        return {"datasets": int(deleted), "vector_rows": vectors}
