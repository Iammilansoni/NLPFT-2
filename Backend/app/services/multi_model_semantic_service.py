# Backend/app/services/multi_model_semantic_service.py

"""
Semantic Routing Pipeline
=========================

Resolves one natural-language request to one API template, then extracts a
schema-valid request body for it.

    Stage 1  RECALL      runtime embedder -> pgvector KNN over the tenant's rows
    Stage 2  RANKING     max-pool row scores per template (cross-encoder optional)
    Stage 3  EXTRACTION  schema-constrained LLM decode -> pydantic -> repair retry

Model governance
----------------
One embedder per deployment (`EXECUTION_MODE`): Ollama nomic-embed-text (768d)
locally, in-process ONNX bge-small (384d) in cloud mode. Every vector row records
the model and dimension that produced it and Stage 1 filters on both, so rows
embedded by a different model are never compared against this query. A dataset
embedded with another model is reported as MODEL_MISMATCH instead of searched.

Tenancy
-------
Stage 1 runs inside `tenant_session()`, which binds `app.tenant_id` for the
transaction. `PgVectorStore.search` filters on that tenant explicitly and
PostgreSQL RLS enforces the same predicate a second time when the application
role is not a superuser.

Failure is reported, never swallowed
------------------------------------
`ranking.degraded` is true only when an enabled component could not run.
`extraction.ok` distinguishes "the request carried no values" from "the LLM was
unreachable" from "a required field was not mentioned".
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, Optional

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.core.runtime import get_embedder
from app.core.tenancy import tenant_session
from app.models.database_models import Dataset, Template
from app.models.schemas.embedding_schemas import ErrorCode
from app.nlp.cross_encoder_reranker import (
    RERANKER_ENABLED,
    STAGE1_TOP_K,
    STAGE2_TOP_K,
    get_reranker,
)
from app.nlp.url_extraction import extract_url_from_query
from app.services.pgvector_store import get_pgvector_store
from app.services.structured_extraction_service import get_structured_extraction_service


class MultiModelSemanticRetrievalService:
    """The only service that performs routing. All query endpoints use it."""

    def __init__(self):
        # Process-wide singletons, resolved once.
        self.embedder = get_embedder()
        self.pgvector_store = get_pgvector_store()
        self.reranker = get_reranker()
        self.extractor = get_structured_extraction_service()

    async def semantic_search(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        user_query: str,
        top_k: int = STAGE1_TOP_K,
        dataset_id: Optional[uuid.UUID] = None,
        template_id: Optional[uuid.UUID] = None,
        include_alternatives: bool = False,
        skip_compatibility_check: bool = False,
        include_slot_extraction: bool = True,
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        embedder = self.embedder
        effective_model = embedder.model_id
        dimension = embedder.dimension

        logger.info(
            f"[route] query='{user_query[:50]}' user={str(user_id)[:8]} "
            f"embedder={effective_model} dim={dimension} k={top_k}"
        )

        # -- Model compatibility (only when scoped to a dataset/template) --------
        if not skip_compatibility_check and (dataset_id or template_id):
            stmt = select(Dataset).where(Dataset.u_id == user_id)
            if dataset_id:
                stmt = stmt.where(Dataset.dataset_id == dataset_id)
            else:
                stmt = stmt.where(Dataset.t_id == template_id).order_by(
                    Dataset.created_at.desc()
                ).limit(1)
            dataset = (await db.execute(stmt)).scalar_one_or_none()

            if dataset and dataset.embedding_model and dataset.embedding_model != effective_model:
                logger.warning(
                    f"Model mismatch: runtime={effective_model} dataset={dataset.embedding_model}"
                )
                return {
                    "success": False,
                    "error": ErrorCode.MODEL_MISMATCH,
                    "message": (
                        f"Model mismatch: this deployment embeds with "
                        f"'{effective_model}', but the dataset was embedded with "
                        f"'{dataset.embedding_model}'. Re-embed the dataset."
                    ),
                    "metadata": {
                        "embedding_model": effective_model,
                        "dataset_model": dataset.embedding_model,
                        "dataset_id": str(dataset.dataset_id),
                    },
                }

        # -- Stage 1: embed + recall ---------------------------------------------
        embed_t0 = time.perf_counter()
        try:
            query_embedding = await embedder.embed_one(user_query)
        except Exception as e:  # noqa: BLE001 - reported to the caller
            logger.error(f"Embedding generation failed: {e}")
            return {"success": False, "error": "EMBEDDING_FAILED", "message": str(e)}
        embed_ms = (time.perf_counter() - embed_t0) * 1000

        if not query_embedding:
            return {
                "success": False,
                "error": "EMBEDDING_FAILED",
                "message": f"The embedding model '{effective_model}' returned no vector.",
            }

        query_vector = np.asarray(query_embedding, dtype=np.float32)
        if query_vector.shape[0] != dimension:
            return {
                "success": False,
                "error": "DIMENSION_MISMATCH",
                "message": (
                    f"Embedder returned {query_vector.shape[0]} dimensions, "
                    f"expected {dimension}."
                ),
            }

        async with tenant_session(user_id) as tdb:
            vector_result = await self.pgvector_store.search(
                tdb,
                query_vector,
                embedding_model=effective_model,
                dimension=dimension,
                top_k=top_k,
                dataset_id=dataset_id,
                template_id=template_id,
            )
        search_results = vector_result.rows

        stage1_results = [
            {
                "query": r.get("query", ""),
                "similarity_score": round(r.get("similarity", 0.0), 4),
                "t_id": r.get("t_id") or "",
                "api_name": r.get("api_name", ""),
                "row_id": r.get("row_uid", ""),
            }
            for r in search_results
        ]

        if not search_results:
            return {
                "success": False,
                "error": "NO_RESULTS",
                "message": (
                    "No indexed utterances match this query. Embed a dataset for "
                    "your templates first (Datasets -> Embed)."
                ),
                "stage1_vector_search": [],
                "metadata": {
                    "query": user_query,
                    "embedding_model": effective_model,
                    "stage1_top_k": top_k,
                },
            }

        # -- Stage 2: rank templates ---------------------------------------------
        rerank_outcome = await self.reranker.run(
            query=user_query, stage1_rows=search_results, top_k=STAGE2_TOP_K
        )
        if rerank_outcome.degraded:
            logger.warning(f"Stage 2 degraded: {rerank_outcome.degraded_reason}")

        stage2_results = [t.to_dict() for t in rerank_outcome.templates]
        best = rerank_outcome.best
        if best is None:
            return {
                "success": False,
                "error": "RANKING_FAILED",
                "message": "Ranking produced no template candidate.",
                "stage1_vector_search": stage1_results,
                "stage2_reranking": stage2_results,
            }

        # -- Resolve the winning template ----------------------------------------
        template = await self._resolve_template(db, uuid.UUID(best.t_id), user_id)
        if not template:
            return {
                "success": False,
                "error": "TEMPLATE_NOT_FOUND",
                "message": f"Template {best.t_id} not found",
                "stage1_vector_search": stage1_results,
                "stage2_reranking": stage2_results,
            }

        # -- Stage 3: structured extraction --------------------------------------
        extraction: Optional[Dict[str, Any]] = None
        if include_slot_extraction:
            result = await self.extractor.extract(
                query=user_query,
                request_schema=template.get("json_schema"),
                api_name=template["api_name"],
                endpoint=template["endpoint"],
            )
            extraction = result.to_dict()
        extracted_body = extraction["values"] if extraction else None

        # -- Base URL named in the request, if any --------------------------------
        _, extracted_base_url = extract_url_from_query(user_query)
        effective_base_url = extracted_base_url or template["base_url"]

        processing_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        confidence = round(best.ce_score, 4)

        final_output = {
            "t_id": best.t_id,
            "api_name": template["api_name"],
            "base_url": template["base_url"],
            "extracted_base_url": extracted_base_url,
            "effective_base_url": effective_base_url,
            "url_source": "query" if extracted_base_url else "template",
            "endpoint": template["endpoint"],
            "method": template["method"],
            "confidence_score": confidence,
            "request_schema": template["json_schema"],
            "response_schema": template["response_schema"],
            "extracted_request_body": extracted_body,
        }

        response: Dict[str, Any] = {
            "success": True,
            "stage1_vector_search": stage1_results,
            "stage2_reranking": stage2_results,
            "final_output": final_output,
            "extracted_request_body": extracted_body,
            "extraction": extraction,
            "ranking": {
                "strategy": rerank_outcome.strategy,
                "degraded": rerank_outcome.degraded,
                "degraded_reason": rerank_outcome.degraded_reason,
                "reranker_model": rerank_outcome.model,
                "rows_cross_encoded": rerank_outcome.rows_scored,
            },
            # Top-level degradation: any stage that SHOULD have run but did not.
            "degraded": bool(
                rerank_outcome.degraded or (extraction and extraction.get("degraded"))
            ),
            # Flat fields kept for existing API clients.
            "api_name": template["api_name"],
            "endpoint": template["endpoint"],
            "method": template["method"],
            "base_url": template["base_url"],
            "confidence": confidence,
            "metadata": {
                "query": user_query,
                "embedding_model": effective_model,
                "embedding_dimension": dimension,
                "stage1_top_k": top_k,
                "stage2_top_k": STAGE2_TOP_K,
                "total_candidates": len(search_results),
                "t_id": best.t_id,
                "match_count": best.match_count,
                "best_utterance": best.best_utterance,
                "vector_score": round(best.vector_score, 4),
                "reranker_enabled": RERANKER_ENABLED,
                "timings_ms": {
                    "embed": round(embed_ms, 2),
                    "vector_search": round(vector_result.latency_ms, 2),
                    "ranking": rerank_outcome.latency_ms,
                    "extraction": extraction["latency_ms"] if extraction else 0.0,
                },
                "processing_time_ms": processing_time_ms,
                "domain_tags": template.get("domain_tags") or [],
            },
        }

        if include_alternatives and len(rerank_outcome.templates) > 1:
            response["alternatives"] = [t.to_dict() for t in rerank_outcome.templates[1:4]]

        logger.info(
            f"[route] -> {template['api_name']} (score={confidence}, "
            f"{rerank_outcome.strategy}, extraction_ok="
            f"{extraction.get('ok') if extraction else None}, {processing_time_ms}ms)"
        )
        return response

    async def _resolve_template(
        self, db: AsyncSession, t_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """Fetch the full template from PostgreSQL, the source of truth for API shape."""
        template = (
            await db.execute(
                select(Template).where(Template.t_id == t_id, Template.u_id == user_id)
            )
        ).scalar_one_or_none()
        if not template:
            return None
        return {
            "t_id": str(template.t_id),
            "api_name": template.api_name,
            "description": template.description,
            # Templates created before the `endpoint` column stored it in `Field`.
            "endpoint": template.endpoint or template.Field,
            "base_url": template.base_url,
            "method": template.method,
            "json_schema": template.json_schema,
            "response_schema": template.response_schema,
            "auth_config": template.auth_config,
            "headers": template.headers,
            "domain_tags": template.domain_tags,
        }


_service_instance: Optional[MultiModelSemanticRetrievalService] = None


def get_multi_model_semantic_service() -> MultiModelSemanticRetrievalService:
    """Singleton accessor."""
    global _service_instance
    if _service_instance is None:
        _service_instance = MultiModelSemanticRetrievalService()
    return _service_instance
