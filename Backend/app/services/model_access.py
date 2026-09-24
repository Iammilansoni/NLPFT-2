"""
Model access: whose key, which embedding model
==============================================

Two questions every model call has to answer, answered in one place.

1. Which credential? For a provider, the user's own saved connection comes
   first (their default one, else the most recently updated). If they have
   none, the deployment's key for that provider (an environment variable) is
   used when the admin set one. Providers that need no key (Ollama, built-in
   ONNX, custom servers) work without either.

2. Which embedding model? The one the user picked in Settings -> Embedding
   model, else the deployment default (`app.core.runtime`). Vectors are only
   comparable within one (provider, model, dimension), so this triple is what
   datasets are tagged with and what search filters on.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_api_key
from app.core.logger import logger
from app.core.runtime import ProviderEmbedder, default_embedding
from app.llm.embeddings import EmbeddingError
from app.llm.provider_registry import get_provider, provider_label
from app.models.database_models import LLMProviderConfig, UserSettings


@dataclass(frozen=True)
class ResolvedCredential:
    provider: str
    api_key: Optional[str]
    base_url: Optional[str]
    source: str  # "connection" | "deployment" | "none-needed"
    config_id: Optional[str] = None
    config_name: Optional[str] = None


async def resolve_credential(db: AsyncSession, user_id: uuid.UUID, provider: str) -> ResolvedCredential:
    """
    The key to use for `provider` on behalf of this user.

    Raises EmbeddingError(code="NO_KEY") when the provider needs a key and
    neither the user nor the deployment has one; the message says how to fix it.
    """
    spec = get_provider(provider)
    if spec is None:
        raise EmbeddingError(f"Unknown provider '{provider}'.", "UNSUPPORTED")

    configs = (await db.execute(
        select(LLMProviderConfig)
        .where(
            LLMProviderConfig.u_id == user_id,
            LLMProviderConfig.provider == provider,
            LLMProviderConfig.is_active == 1,
        )
        .order_by(LLMProviderConfig.is_default.desc(), LLMProviderConfig.updated_at.desc().nullslast())
    )).scalars().all()
    for config in configs:
        api_key = None
        if config.api_key_encrypted:
            try:
                api_key = decrypt_api_key(config.api_key_encrypted)
            except Exception:  # noqa: BLE001 -- try the next connection
                logger.warning(f"Cannot decrypt the key of connection {config.config_id}")
                continue
        if api_key or not spec.requires_key:
            return ResolvedCredential(
                provider, api_key, config.base_url, "connection", str(config.config_id), config.name
            )

    env_key = os.getenv(spec.env_key) if spec.env_key else None
    if env_key:
        return ResolvedCredential(provider, env_key, None, "deployment")
    if not spec.requires_key:
        return ResolvedCredential(provider, None, None, "none-needed")
    raise EmbeddingError(
        f"Using {spec.label} needs an API key. Add yours in Settings → AI Providers.",
        "NO_KEY",
    )


async def has_credential(db: AsyncSession, user_id: uuid.UUID, provider: str) -> bool:
    try:
        await resolve_credential(db, user_id, provider)
        return True
    except EmbeddingError:
        return False


@dataclass(frozen=True)
class EmbeddingSelection:
    provider: str
    model_id: str
    dimension: int
    is_default: bool  # the deployment default, not an explicit user choice

    @property
    def label(self) -> str:
        return f"{provider_label(self.provider)} · {self.model_id} · {self.dimension}-dim"

    def to_dict(self) -> Dict[str, Any]:
        return {**asdict(self), "provider_label": provider_label(self.provider), "label": self.label}

    def matches(self, provider: Optional[str], model_id: Optional[str], dimension: Optional[int]) -> bool:
        return (provider, model_id, dimension) == (self.provider, self.model_id, self.dimension)


async def active_embedding(db: AsyncSession, user_id: uuid.UUID) -> EmbeddingSelection:
    """The embedding model this user searches and embeds with."""
    settings = (await db.execute(select(UserSettings).where(UserSettings.u_id == user_id))).scalar_one_or_none()
    if settings and settings.embedding_provider and settings.default_embedding_model and settings.embedding_dimension:
        return EmbeddingSelection(
            settings.embedding_provider, settings.default_embedding_model, settings.embedding_dimension, False
        )
    default = default_embedding()
    embedder = await deployment_embedder_dimension()
    return EmbeddingSelection(default["provider"], default["model_id"], embedder, True)


async def deployment_embedder_dimension() -> int:
    """The default model's real width, measured once (the configured value is only a hint)."""
    from app.core.runtime import get_embedder

    embedder = get_embedder()
    if not getattr(embedder, "_measured", False):
        try:
            await embedder.embed_one("dimension probe")
            embedder._measured = True  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001 -- fall back to the hint; search reports the outage itself
            logger.warning(f"Could not measure the default embedder's dimension: {exc}")
    return embedder.dimension


async def embedder_for(db: AsyncSession, user_id: uuid.UUID, selection: EmbeddingSelection) -> ProviderEmbedder:
    """An embedder for `selection`, authenticated as this user. Raises EmbeddingError(NO_KEY)."""
    credential = await resolve_credential(db, user_id, selection.provider)
    return ProviderEmbedder(
        selection.provider, selection.model_id, selection.dimension,
        api_key=credential.api_key, base_url=credential.base_url,
    )
