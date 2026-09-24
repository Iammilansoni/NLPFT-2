"""
Model catalogue
===============

Keeps `model_catalog` in step with what providers actually serve.

Sync, per (scope, provider) group:

1. List models with every credential in the group (`model_discovery`).
2. Record the outcome on `model_catalog_sources`, so the UI can say why a
   provider's list is short or stale.
3. Upsert every model seen. A model that comes back is active again.
4. Lifecycle, only when EVERY credential in the group listed successfully:
     - no longer listed               -> deprecated (still usable)
     - still missing after the grace  -> retired (hidden from pickers)
     - provider's shutdown date passed -> retired
     - retired, unused, past retention -> deleted
   A failed, partial or empty listing changes nothing: an outage or a revoked
   key must never retire a whole provider's models.

Credentials come from two places:
  - the deployment: Ollama, keys in the environment, public listings -> scope "global"
  - each user's saved LLM connections                                -> scope = that user's id
"""

from __future__ import annotations

import asyncio
import importlib.util
import os
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_api_key
from app.core.logger import logger
from app.llm import provider_registry as registry
from app.llm.model_discovery import (
    SUPPORTED_PROVIDERS,
    DiscoveredModel,
    DiscoveryError,
    discover_models,
    probe_dimension,
)
from app.llm.provider_registry import provider_label
from app.models.database_models import (
    Dataset,
    LLMProviderConfig,
    ModelCatalogEntry,
    ModelCatalogSource,
    UserSettings,
    utc_now,
)

GLOBAL_SCOPE = "global"

# How long a model may be missing from a successful listing before it is retired.
RETIRE_GRACE = timedelta(hours=float(os.getenv("MODEL_RETIRE_GRACE_HOURS", "72")))
# How long a retired, unused model stays visible (as retired) before it is deleted.
RETIRED_RETENTION = timedelta(days=float(os.getenv("MODEL_RETIRED_RETENTION_DAYS", "7")))
# How long a newly listed model carries the "new" badge.
NEW_BADGE_WINDOW = timedelta(days=float(os.getenv("MODEL_NEW_BADGE_DAYS", "7")))
# Read by the Celery beat schedule too; surfaced here so the UI can state the policy.
SYNC_INTERVAL_MINUTES = float(os.getenv("MODEL_CATALOG_SYNC_MINUTES", "360"))
# Embedding dimensions measured per sync (each costs one tiny embed call).
MAX_DIMENSION_PROBES = int(os.getenv("MODEL_MAX_DIMENSION_PROBES", "10"))

# Providers whose model listing needs no key, synced for everyone.
PUBLIC_LISTINGS = tuple(
    p.strip() for p in os.getenv("MODEL_CATALOG_PUBLIC_PROVIDERS", "openrouter").split(",") if p.strip()
)


@dataclass(frozen=True)
class Credential:
    scope: str
    provider: str
    api_key: Optional[str]
    base_url: Optional[str]


@dataclass
class GroupResult:
    scope: str
    provider: str
    ok: bool
    model_count: int = 0
    added: int = 0
    deprecated: int = 0
    retired: int = 0
    deleted: int = 0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "provider_label": provider_label(self.provider),
            "scope": "shared" if self.scope == GLOBAL_SCOPE else "yours",
            "ok": self.ok,
            "model_count": self.model_count,
            "added": self.added,
            "deprecated": self.deprecated,
            "retired": self.retired,
            "deleted": self.deleted,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------

def deployment_credentials() -> List[Credential]:
    creds: List[Credential] = []
    if os.getenv("EXECUTION_MODE", "local").lower() == "local" or os.getenv("OLLAMA_HOST"):
        creds.append(Credential(GLOBAL_SCOPE, "ollama", None, os.getenv("OLLAMA_HOST")))
    if importlib.util.find_spec("fastembed") is not None:
        creds.append(Credential(GLOBAL_SCOPE, "builtin", None, None))
    for spec in registry.PROVIDERS:
        if spec.env_key and os.getenv(spec.env_key):
            creds.append(Credential(GLOBAL_SCOPE, spec.id, os.getenv(spec.env_key), None))
    keyed = {c.provider for c in creds}
    creds += [Credential(GLOBAL_SCOPE, p, None, None) for p in PUBLIC_LISTINGS if p not in keyed]
    return creds


async def user_credentials(
    db: AsyncSession, user_id: Optional[uuid.UUID] = None, provider: Optional[str] = None
) -> List[Credential]:
    query = select(LLMProviderConfig).where(LLMProviderConfig.is_active == 1)
    if user_id:
        query = query.where(LLMProviderConfig.u_id == user_id)
    if provider:
        query = query.where(LLMProviderConfig.provider == provider)
    creds: List[Credential] = []
    for config in (await db.execute(query)).scalars():
        if config.provider not in SUPPORTED_PROVIDERS:
            continue
        api_key = None
        if config.api_key_encrypted:
            try:
                api_key = decrypt_api_key(config.api_key_encrypted)
            except Exception:  # noqa: BLE001 -- a bad key must not stop other users' syncs
                logger.warning(f"Model catalogue: cannot decrypt the key of LLM config {config.config_id}")
                continue
        creds.append(Credential(str(config.u_id), config.provider, api_key, config.base_url))
    return creds


def _signature(cred: Credential) -> tuple:
    base_url = (cred.base_url or "").rstrip("/")
    if cred.provider == "ollama":
        base_url = base_url or (os.getenv("OLLAMA_HOST") or "").rstrip("/")
    return cred.provider, cred.api_key, base_url


def _group(creds: Iterable[Credential]) -> Dict[tuple, List[Credential]]:
    groups: Dict[tuple, List[Credential]] = {}
    for cred in dict.fromkeys(creds):  # de-duplicate identical credentials, keep order
        groups.setdefault((cred.scope, cred.provider), []).append(cred)
    return groups


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

async def sync_catalog(
    db: AsyncSession,
    *,
    user_id: Optional[uuid.UUID] = None,
    provider: Optional[str] = None,
    include_global: bool = True,
) -> List[GroupResult]:
    """
    Sync the catalogue. With no arguments: every deployment and user credential
    (the scheduled job). With `user_id`: that user's connections, plus the
    shared providers unless `include_global` is False.
    """
    shared = [c for c in deployment_credentials() if provider in (None, c.provider)]
    # A user connection that reaches exactly what the deployment already lists
    # (typically the bundled Ollama) would only duplicate the shared models.
    shared_signatures = {_signature(c) for c in shared}
    personal = [c for c in await user_credentials(db, user_id=user_id, provider=provider) if _signature(c) not in shared_signatures]
    groups = _group((shared if include_global else []) + personal)

    results = [await _sync_group(db, scope, prov, group) for (scope, prov), group in groups.items()]

    # A group can only be declared credential-less by a sync that saw every
    # credential that could serve it: the full sync for everything, or a
    # user's all-provider sync for that user's own scope.
    if provider is None and user_id is None and include_global:
        results += await _retire_orphaned_groups(db, set(groups))
    elif provider is None and user_id is not None:
        results += await _retire_orphaned_groups(db, set(groups), only_scope=str(user_id))
    await db.commit()
    return results


async def _sync_group(db: AsyncSession, scope: str, provider: str, creds: Sequence[Credential]) -> GroupResult:
    now = utc_now()
    outcomes = await asyncio.gather(
        *(discover_models(c.provider, c.api_key, c.base_url) for c in creds), return_exceptions=True
    )
    listings = [o for o in outcomes if isinstance(o, list)]
    errors = [o for o in outcomes if isinstance(o, BaseException)]
    for err in errors:
        if not isinstance(err, DiscoveryError):
            logger.exception(f"Model catalogue: unexpected error listing {provider}", exc_info=err)

    source = await db.get(ModelCatalogSource, (scope, provider))
    if source is None:
        source = ModelCatalogSource(scope=scope, provider=provider, model_count=0)
        db.add(source)
    source.last_attempt_at = now

    if not listings:
        first = errors[0] if errors else None
        source.last_error = first.message if isinstance(first, DiscoveryError) else f"Listing {provider_label(provider)} models failed unexpectedly."
        source.last_error_code = first.code if isinstance(first, DiscoveryError) else "UNEXPECTED"
        return GroupResult(scope, provider, ok=False, error=source.last_error)

    seen: Dict[str, DiscoveredModel] = {}
    for listing in listings:
        for model in listing:
            seen.setdefault(model.model_id, model)

    existing = {
        row.model_id: row
        for row in (await db.execute(
            select(ModelCatalogEntry).where(ModelCatalogEntry.scope == scope, ModelCatalogEntry.provider == provider)
        )).scalars()
    }
    result = GroupResult(scope, provider, ok=True, model_count=len(seen))

    for model_id, model in seen.items():
        row = existing.get(model_id)
        if row is None:
            row = ModelCatalogEntry(
                id=uuid.uuid4(), scope=scope, provider=provider, model_id=model_id, first_seen_at=now,
            )
            db.add(row)
            result.added += 1
        row.kind = model.kind
        row.display_name = model.display_name
        row.description = model.description or None
        row.context_tokens = model.context_tokens
        row.dimension = model.dimension or row.dimension
        row.is_local = model.is_local
        row.is_free = model.is_free
        row.shutdown_date = model.shutdown_date
        row.extra = model.metadata or None
        row.last_seen_at = now
        row.missing_since = None
        if model.shutdown_date and model.shutdown_date <= date.today():
            _retire(row, now, f"{provider_label(provider)} announced this model shuts down on {model.shutdown_date:%d %b %Y}.")
        else:
            row.status, row.status_reason, row.retired_at = "active", None, None

    if not errors:
        for model_id, row in existing.items():
            if model_id in seen:
                continue
            if row.status == "active":
                row.status = "deprecated"
                row.missing_since = now
                row.status_reason = (
                    f"{provider_label(provider)} stopped listing this model on {now:%d %b %Y}. "
                    f"It will be retired if it doesn't come back within {_describe(RETIRE_GRACE)}."
                )
                result.deprecated += 1
            elif row.status == "deprecated" and row.missing_since and now - row.missing_since >= RETIRE_GRACE:
                _retire(row, now, f"{provider_label(provider)} has not listed this model since {row.missing_since:%d %b %Y}.")
                result.retired += 1
        result.deleted = await _delete_unused_retired(db, scope, provider)
    else:
        logger.info(
            f"Model catalogue: {provider} ({scope}) listed with {len(errors)} of {len(creds)} credentials failing; "
            "skipping deprecation this round"
        )

    await _probe_missing_dimensions(db, scope, provider, creds)

    if source.first_success_at is None:
        source.first_success_at = now
    source.last_success_at = now
    source.model_count = len(seen)
    source.last_error = errors[0].message if errors and isinstance(errors[0], DiscoveryError) else None
    source.last_error_code = errors[0].code if errors and isinstance(errors[0], DiscoveryError) else None
    await db.flush()
    return result


def _retire(row: ModelCatalogEntry, now: datetime, reason: str) -> None:
    if row.status != "retired":
        row.retired_at = now
    row.status = "retired"
    row.status_reason = reason


def _describe(delta: timedelta) -> str:
    hours = delta.total_seconds() / 3600
    return f"{hours / 24:g} days" if hours >= 24 and hours % 24 == 0 else f"{hours:g} hours"


async def _retire_orphaned_groups(
    db: AsyncSession, live_groups: set, only_scope: Optional[str] = None
) -> List[GroupResult]:
    """Models whose only credential was removed (e.g. a deleted connection) can no longer be used."""
    now = utc_now()
    query = select(ModelCatalogEntry)
    if only_scope:
        query = query.where(ModelCatalogEntry.scope == only_scope)
    rows = (await db.execute(query)).scalars().all()
    results: Dict[tuple, GroupResult] = {}
    for row in rows:
        key = (row.scope, row.provider)
        if key in live_groups:
            continue
        group = results.setdefault(key, GroupResult(row.scope, row.provider, ok=True))
        if row.status != "retired":
            _retire(row, now, f"No saved {provider_label(row.provider)} connection can reach this model any more.")
            group.retired += 1
    for scope, provider in results:
        results[(scope, provider)].deleted = await _delete_unused_retired(db, scope, provider)
    await db.flush()

    # A sync record for a group with no credential and no remaining models is just noise in the UI.
    remaining = {
        (scope, provider)
        for scope, provider in (await db.execute(
            select(ModelCatalogEntry.scope, ModelCatalogEntry.provider).distinct()
        )).all()
    }
    sources = select(ModelCatalogSource)
    if only_scope:
        sources = sources.where(ModelCatalogSource.scope == only_scope)
    for source in (await db.execute(sources)).scalars().all():
        key = (source.scope, source.provider)
        if key not in live_groups and key not in remaining:
            await db.delete(source)
    return list(results.values())


async def _delete_unused_retired(db: AsyncSession, scope: str, provider: str) -> int:
    retired = (await db.execute(
        select(ModelCatalogEntry).where(
            ModelCatalogEntry.scope == scope,
            ModelCatalogEntry.provider == provider,
            ModelCatalogEntry.status == "retired",
            ModelCatalogEntry.retired_at <= utc_now() - RETIRED_RETENTION,
        )
    )).scalars().all()
    deleted = 0
    for row in retired:
        if await count_dependents(db, row) == 0:
            await db.delete(row)
            deleted += 1
    return deleted


async def count_dependents(db: AsyncSession, row: ModelCatalogEntry) -> int:
    """How many saved connections, datasets and settings still reference this model."""
    scoped_user = None if row.scope == GLOBAL_SCOPE else uuid.UUID(row.scope)
    if row.kind == "llm":
        query = select(func.count()).select_from(LLMProviderConfig).where(
            LLMProviderConfig.provider == row.provider, LLMProviderConfig.model_name == row.model_id
        )
        if scoped_user:
            query = query.where(LLMProviderConfig.u_id == scoped_user)
        return int((await db.execute(query)).scalar() or 0)

    names = {row.model_id, f"{row.model_id}:latest"}
    datasets = select(func.count()).select_from(Dataset).where(Dataset.embedding_model.in_(names))
    settings = select(func.count()).select_from(UserSettings).where(UserSettings.default_embedding_model.in_(names))
    if scoped_user:
        datasets = datasets.where(Dataset.u_id == scoped_user)
        settings = settings.where(UserSettings.u_id == scoped_user)
    return int((await db.execute(datasets)).scalar() or 0) + int((await db.execute(settings)).scalar() or 0)


async def _probe_missing_dimensions(db: AsyncSession, scope: str, provider: str, creds: Sequence[Credential]) -> None:
    keyed = next((c for c in creds if c.api_key or provider == "ollama"), None)
    if keyed is None:
        return
    unmeasured = (await db.execute(
        select(ModelCatalogEntry).where(
            ModelCatalogEntry.scope == scope,
            ModelCatalogEntry.provider == provider,
            ModelCatalogEntry.kind == "embedding",
            ModelCatalogEntry.dimension.is_(None),
            ModelCatalogEntry.status != "retired",
        ).limit(MAX_DIMENSION_PROBES)
    )).scalars().all()
    for row in unmeasured:
        row.dimension = await probe_dimension(provider, row.model_id, keyed.api_key, keyed.base_url)


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------

async def list_catalog(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    kind: Optional[str] = None,
    provider: Optional[str] = None,
    include_retired: bool = False,
) -> List[Dict[str, Any]]:
    """Models visible to `user_id`: shared ones plus those found with their own keys."""
    query = select(ModelCatalogEntry).where(
        or_(ModelCatalogEntry.scope == GLOBAL_SCOPE, ModelCatalogEntry.scope == str(user_id))
    )
    if kind:
        query = query.where(ModelCatalogEntry.kind == kind)
    if provider:
        query = query.where(ModelCatalogEntry.provider == provider)
    if not include_retired:
        query = query.where(ModelCatalogEntry.status != "retired")
    rows = (await db.execute(query.order_by(ModelCatalogEntry.provider, ModelCatalogEntry.model_id))).scalars().all()

    sources = {
        (s.scope, s.provider): s
        for s in (await db.execute(select(ModelCatalogSource))).scalars()
    }
    # The same model can be listed both globally and with the user's own key; show it once.
    unique: Dict[tuple, ModelCatalogEntry] = {}
    for row in rows:
        key = (row.provider, row.model_id)
        if key not in unique or row.scope == GLOBAL_SCOPE:
            unique[key] = row
    return [serialize_entry(row, sources.get((row.scope, row.provider))) for row in unique.values()]


def serialize_entry(row: ModelCatalogEntry, source: Optional[ModelCatalogSource] = None) -> Dict[str, Any]:
    now = utc_now()
    # Everything is "new" on a provider's first sync; only later arrivals earn the badge.
    bootstrap = source.first_success_at if source and source.first_success_at else row.first_seen_at
    is_new = row.first_seen_at > bootstrap + timedelta(minutes=5) and now - row.first_seen_at < NEW_BADGE_WINDOW
    return {
        "provider": row.provider,
        "provider_label": provider_label(row.provider),
        "model_id": row.model_id,
        "kind": row.kind,
        "display_name": row.display_name,
        "description": row.description,
        "context_tokens": row.context_tokens,
        "dimension": row.dimension,
        "is_local": row.is_local,
        "is_free": row.is_free,
        "is_new": is_new,
        "status": row.status,
        "status_reason": row.status_reason,
        "shutdown_date": row.shutdown_date.isoformat() if row.shutdown_date else None,
        "first_seen_at": row.first_seen_at.isoformat() + "Z",
        "last_seen_at": row.last_seen_at.isoformat() + "Z",
        "shared": row.scope == GLOBAL_SCOPE,
    }


async def list_sources(db: AsyncSession, user_id: uuid.UUID) -> List[Dict[str, Any]]:
    rows = (await db.execute(
        select(ModelCatalogSource).where(
            or_(ModelCatalogSource.scope == GLOBAL_SCOPE, ModelCatalogSource.scope == str(user_id))
        ).order_by(ModelCatalogSource.provider)
    )).scalars().all()
    return [
        {
            "provider": s.provider,
            "provider_label": provider_label(s.provider),
            "scope": "shared" if s.scope == GLOBAL_SCOPE else "yours",
            "model_count": s.model_count,
            "last_success_at": s.last_success_at.isoformat() + "Z" if s.last_success_at else None,
            "last_attempt_at": s.last_attempt_at.isoformat() + "Z" if s.last_attempt_at else None,
            "last_error": s.last_error,
            "last_error_code": s.last_error_code,
        }
        for s in rows
    ]


async def lookup_status(db: AsyncSession, user_id: uuid.UUID, provider: str, model_id: str) -> Optional[Dict[str, Any]]:
    """Catalogue status of one model for this user, or None when the catalogue has never seen it."""
    rows = (await db.execute(
        select(ModelCatalogEntry).where(
            ModelCatalogEntry.provider == provider,
            ModelCatalogEntry.model_id == model_id,
            or_(ModelCatalogEntry.scope == GLOBAL_SCOPE, ModelCatalogEntry.scope == str(user_id)),
        )
    )).scalars().all()
    if not rows:
        return None
    best = min(rows, key=lambda r: {"active": 0, "deprecated": 1, "retired": 2}.get(r.status, 3))
    return {"status": best.status, "status_reason": best.status_reason}


def policy() -> Dict[str, float]:
    """The lifecycle rules in force, for the UI to explain rather than hard-code."""
    return {
        "sync_interval_minutes": SYNC_INTERVAL_MINUTES,
        "retire_grace_hours": RETIRE_GRACE.total_seconds() / 3600,
        "retired_retention_days": RETIRED_RETENTION.total_seconds() / 86400,
        "new_badge_days": NEW_BADGE_WINDOW.total_seconds() / 86400,
    }
