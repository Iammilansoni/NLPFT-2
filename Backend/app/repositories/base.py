"""
Repository Base
===============

Thin data-access layer between routers and the ORM.

WHAT PROBLEM THIS SOLVES
------------------------
`datasets.py` is 2,103 lines with 30 route decorators and 48 raw `db.execute` /
`select(...)` calls -- business logic and SQL living in the HTTP layer despite a
populated `services/` package. `template_builder.py` is another 1,908 lines of
the same. Consequences:

  * Query logic cannot be unit tested without spinning up FastAPI.
  * The same lookup is re-implemented slightly differently in several endpoints.
  * Tenancy was 32 hand-written `u_id ==` filters, each an opportunity to forget.

Repositories own the SQL. Routers own HTTP: parse, delegate, serialise.

TENANCY IS NOT THIS LAYER'S JOB ANYMORE
---------------------------------------
Under Phase 3, repositories receive a session already bound to a tenant by
`app.core.tenancy`, and Postgres RLS filters every statement. Repository methods
therefore contain NO `u_id` predicate.

That absence is deliberate and load-bearing. Re-adding "just to be safe" would
mask an RLS misconfiguration behind an application-level filter -- the failure
would then only surface in Celery workers or scripts that bypass the router.
`verify_rls_enforced()` at startup is the safety net; a redundant WHERE clause is
not.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Generic, List, Optional, Sequence, Type, TypeVar

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    """
    CRUD shared by every repository.

    Subclasses set `model` and `pk_name`, then add domain queries. Anything used
    by more than one endpoint belongs here rather than in a route body.
    """

    model: Type[ModelT]
    pk_name: str

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # -- helpers -----------------------------------------------------------

    @property
    def _pk(self):
        return getattr(self.model, self.pk_name)

    @staticmethod
    def _as_uuid(value: Any) -> uuid.UUID:
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))

    # -- read --------------------------------------------------------------

    async def get(self, pk: Any) -> Optional[ModelT]:
        """Fetch one row by primary key, or None. RLS scopes it to the tenant."""
        result = await self.db.execute(select(self.model).where(self._pk == self._as_uuid(pk)))
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[Any] = None,
        **filters: Any,
    ) -> List[ModelT]:
        stmt = select(self.model)
        for field, value in filters.items():
            if value is not None:
                stmt = stmt.where(getattr(self.model, field) == value)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        stmt = stmt.limit(limit).offset(offset)
        return list((await self.db.execute(stmt)).scalars().all())

    async def count(self, **filters: Any) -> int:
        stmt = select(func.count()).select_from(self.model)
        for field, value in filters.items():
            if value is not None:
                stmt = stmt.where(getattr(self.model, field) == value)
        return int((await self.db.execute(stmt)).scalar() or 0)

    async def exists(self, pk: Any) -> bool:
        stmt = select(func.count()).select_from(self.model).where(
            self._pk == self._as_uuid(pk)
        )
        return bool((await self.db.execute(stmt)).scalar())

    # -- write -------------------------------------------------------------

    async def create(self, **values: Any) -> ModelT:
        """
        Insert one row.

        `u_id` is intentionally not defaulted here: the caller supplies it, and
        the RLS WITH CHECK clause rejects any value other than the session's
        tenant. Writing to another tenant fails at the database, not on trust.
        """
        obj = self.model(**values)
        self.db.add(obj)
        await self.db.flush()
        return obj

    async def update(self, pk: Any, **values: Any) -> Optional[ModelT]:
        clean = {k: v for k, v in values.items() if v is not None}
        if not clean:
            return await self.get(pk)
        await self.db.execute(
            sa_update(self.model).where(self._pk == self._as_uuid(pk)).values(**clean)
        )
        await self.db.flush()
        return await self.get(pk)

    async def delete(self, pk: Any) -> bool:
        result = await self.db.execute(
            sa_delete(self.model).where(self._pk == self._as_uuid(pk))
        )
        deleted = bool(result.rowcount)
        if not deleted:
            # Under RLS an out-of-tenant pk is indistinguishable from a missing
            # one -- both delete zero rows. That is the correct behaviour: it
            # leaks no information about other tenants' data.
            logger.debug(f"{self.model.__name__} {pk}: nothing deleted (absent or out of tenant)")
        return deleted

    async def bulk_create(self, items: Sequence[Dict[str, Any]]) -> int:
        if not items:
            return 0
        self.db.add_all([self.model(**item) for item in items])
        await self.db.flush()
        return len(items)
