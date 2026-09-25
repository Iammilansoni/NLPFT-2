"""
Embedding model API

    GET    /embeddings/settings              active model, providers, datasets grouped by model
    PUT    /embeddings/settings              choose any provider's embedding model
    DELETE /embeddings/settings              go back to the deployment default
    POST   /embeddings/datasets/{id}/embed   embed (or re-embed) one dataset on the worker
    POST   /embeddings/reembed               re-embed several datasets with the active model

Choosing a model measures its real vector width with one embedding call, so a
wrong dimension can never be stored, and reports which datasets it leaves
unsearchable until they are re-embedded.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.logger import logger
from app.core.postgres import get_db
from app.core.rate_limit import limiter
from app.core.runtime import default_embedding
from app.llm.embeddings import EmbeddingError, embed_texts
from app.llm.provider_registry import embedding_providers, get_provider
from app.models.database_models import User, UserSettings
from app.models.schemas.embedding_schemas import ErrorCode
from app.services.model_access import (
    EmbeddingSelection,
    active_embedding,
    deployment_embedder_dimension,
    resolve_credential,
)
from app.services.model_catalog_service import list_catalog
from app.services.multi_model_embedding_service import embedding_groups, queue_embedding

router = APIRouter(prefix="/embeddings", tags=["Embeddings"])


def _raise(exc: EmbeddingError, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
    raise HTTPException(status_code, {"error": exc.code, "message": exc.message})


async def _overview(db: AsyncSession, user: User) -> dict:
    active = await active_embedding(db, user.u_id)
    default = default_embedding()
    groups = await embedding_groups(db, user.u_id)
    for group in groups:
        group["matches_active"] = active.matches(group["provider"], group["model_id"], group["dimension"])

    providers = []
    for spec in embedding_providers():
        try:
            credential = await resolve_credential(db, user.u_id, spec.id)
            connected, source = True, credential.source
        except EmbeddingError:
            connected, source = False, None
        providers.append({**spec.public_dict(), "connected": connected, "credential_source": source})

    catalogue = await list_catalog(db, user.u_id, kind="embedding")
    return {
        "active": active.to_dict(),
        "deployment_default": {
            **default,
            "dimension": await deployment_embedder_dimension(),
            "provider_label": get_provider(default["provider"]).label,
        },
        "providers": providers,
        "models": catalogue,
        "groups": groups,
        "needs_reembed": [d for g in groups if not g["matches_active"] for d in g["datasets"]],
    }


@router.get("/settings")
async def get_settings(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _overview(db, current_user)


class EmbeddingChoice(BaseModel):
    provider: str = Field(..., max_length=64)
    model_id: str = Field(..., min_length=1, max_length=300)


@router.put("/settings")
@limiter.limit("20/minute")
async def choose_model(
    request: Request,
    choice: EmbeddingChoice,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    spec = get_provider(choice.provider)
    if spec is None or not spec.embeddings:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, {
            "error": ErrorCode.INVALID_MODEL,
            "message": f"{spec.label if spec else choice.provider} does not offer embedding models.",
        })
    try:
        credential = await resolve_credential(db, current_user.u_id, choice.provider)
        # One real call: proves the key and model work, and measures the width.
        [vector] = await embed_texts(
            choice.provider, choice.model_id, ["dimension probe"],
            api_key=credential.api_key, base_url=credential.base_url,
        )
    except EmbeddingError as exc:
        _raise(exc)

    settings = (await db.execute(select(UserSettings).where(UserSettings.u_id == current_user.u_id))).scalar_one_or_none()
    if settings is None:
        settings = UserSettings(u_id=current_user.u_id)
        db.add(settings)
    settings.embedding_provider = choice.provider
    settings.default_embedding_model = choice.model_id
    settings.embedding_dimension = len(vector)
    await db.commit()

    selection = EmbeddingSelection(choice.provider, choice.model_id, len(vector), False)
    logger.info(f"User {str(current_user.u_id)[:8]} now embeds with {selection.label}")
    overview = await _overview(db, current_user)
    return {**overview, "message": f"Now using {selection.label}."}


@router.delete("/settings")
async def reset_to_default(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    settings = (await db.execute(select(UserSettings).where(UserSettings.u_id == current_user.u_id))).scalar_one_or_none()
    if settings:
        settings.embedding_provider = None
        settings.default_embedding_model = None
        settings.embedding_dimension = None
        await db.commit()
    overview = await _overview(db, current_user)
    return {**overview, "message": f"Back to the deployment default, {overview['active']['label']}."}


def raise_for_embedding_error(result: dict) -> dict:
    """Turn an embedding-service error payload into the matching HTTP status.

    Another user's dataset is reported exactly like a missing one (404), so an
    ID never reveals that someone else's data exists.
    """
    error = result.get("error")
    if not error or result.get("success") is True:
        return result
    if error == ErrorCode.DATASET_NOT_FOUND:
        code = status.HTTP_404_NOT_FOUND
    elif error in (ErrorCode.MODEL_MISMATCH, ErrorCode.EMBEDDING_IN_PROGRESS):
        code = status.HTTP_409_CONFLICT
    else:
        code = status.HTTP_400_BAD_REQUEST
    raise HTTPException(code, result)


@router.post("/datasets/{dataset_id}/embed")
async def embed_dataset(
    dataset_id: uuid.UUID,
    force: bool = Query(False, description="Replace vectors made with another model"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return raise_for_embedding_error(
        await queue_embedding(db, current_user.u_id, dataset_id, force_reembed=force)
    )


class ReembedRequest(BaseModel):
    dataset_ids: Optional[List[uuid.UUID]] = Field(
        None, description="Datasets to re-embed; omitted means every dataset not on the active model"
    )


@router.post("/reembed")
async def reembed(
    body: ReembedRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.dataset_ids is None:
        overview = await _overview(db, current_user)
        ids = [uuid.UUID(d["dataset_id"]) for d in overview["needs_reembed"]]
    else:
        ids = body.dataset_ids
    results = [await queue_embedding(db, current_user.u_id, dataset_id, force_reembed=True) for dataset_id in ids]
    queued = [r for r in results if r.get("success")]
    return {
        "queued": len(queued),
        "failed": [r for r in results if not r.get("success")],
        "message": f"Re-embedding {len(queued)} dataset(s)." if queued else "Nothing needed re-embedding.",
    }
