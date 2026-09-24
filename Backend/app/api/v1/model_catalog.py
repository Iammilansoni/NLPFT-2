"""
Model catalogue API

    GET  /model-catalog           models visible to the caller, plus per-provider sync health
    POST /model-catalog/sync      re-list the caller's providers now
    POST /model-catalog/discover  list a provider's models with a key that is not saved yet
                                  (the "add connection" form needs a model list before saving)
"""

from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.encryption import decrypt_api_key
from app.core.postgres import get_db
from app.core.rate_limit import limiter
from app.llm.embeddings import EmbeddingError
from app.llm.model_discovery import SUPPORTED_PROVIDERS, DiscoveryError, discover_models
from app.llm.provider_registry import provider_label
from app.models.database_models import LLMProviderConfig, User
from app.services import model_catalog_service as catalog
from app.services.model_access import resolve_credential

router = APIRouter(prefix="/model-catalog", tags=["Model Catalogue"])


@router.get("")
async def get_catalog(
    kind: Optional[Literal["llm", "embedding"]] = Query(None),
    provider: Optional[str] = Query(None),
    include_retired: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    models = await catalog.list_catalog(
        db, current_user.u_id, kind=kind, provider=provider, include_retired=include_retired
    )
    return {
        "models": models,
        "sources": await catalog.list_sources(db, current_user.u_id),
        "counts": {
            "llm": sum(m["kind"] == "llm" for m in models),
            "embedding": sum(m["kind"] == "embedding" for m in models),
        },
        "policy": catalog.policy(),
    }


@router.post("/sync")
@limiter.limit("6/minute")
async def sync_now(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    results = await catalog.sync_catalog(db, user_id=current_user.u_id)
    return {"results": [r.to_dict() for r in results]}


class DiscoverRequest(BaseModel):
    provider: str
    api_key: Optional[str] = Field(None, max_length=500)
    base_url: Optional[str] = Field(None, max_length=500)
    # Editing a saved connection: use its stored key unless a new one is typed.
    config_id: Optional[UUID] = None


@router.post("/discover")
@limiter.limit("20/minute")
async def discover(
    request: Request,
    body: DiscoverRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Listing models is not supported for '{body.provider}'.")
    api_key, base_url = body.api_key or None, body.base_url or None
    if body.config_id and not api_key:
        config = await db.get(LLMProviderConfig, body.config_id)
        if not config or config.u_id != current_user.u_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Configuration not found")
        if config.api_key_encrypted:
            try:
                api_key = decrypt_api_key(config.api_key_encrypted)
            except Exception:  # noqa: BLE001
                return {"ok": False, "error": "The saved API key can't be decrypted. Enter it again.", "error_code": "AUTH", "models": []}
        base_url = base_url or config.base_url
    elif not api_key:
        # No key typed: list with whatever this user can already use for the
        # provider (their saved connection, or a deployment-wide key).
        try:
            credential = await resolve_credential(db, current_user.u_id, body.provider)
            api_key, base_url = credential.api_key, base_url or credential.base_url
        except EmbeddingError:
            pass  # public listings work without one; others report NO_KEY below
    try:
        models = await discover_models(body.provider, api_key, base_url)
    except DiscoveryError as exc:
        return {"ok": False, "error": exc.message, "error_code": exc.code, "models": []}
    return {
        "ok": True,
        "provider_label": provider_label(body.provider),
        "models": [
            {
                "provider": body.provider,
                "model_id": m.model_id,
                "kind": m.kind,
                "display_name": m.display_name,
                "description": m.description,
                "context_tokens": m.context_tokens,
                "dimension": m.dimension,
                "is_local": m.is_local,
                "is_free": m.is_free,
                "shutdown_date": m.shutdown_date.isoformat() if m.shutdown_date else None,
                "status": "active",
            }
            for m in sorted(models, key=lambda m: m.model_id)
        ],
    }
