# Backend\app\services\multi_model_semantic_service.py

"""
Multi-Model Semantic Retrieval Service - Complete Search Pipeline

Purpose:
This service implements the complete semantic retrieval pipeline with
strict model governance. It ensures searches use the correct model
and dimension-safe Redis indices.

Non-Negotiable Rules:
1. Read active embedding model from Settings (SOURCE OF TRUTH)
2. Validate model matches dataset before search
3. Embed query using the SAME model as dataset
4. Search ONLY in model-specific Redis index
5. NEVER cross model boundaries
6. Always filter by user_id (multi-tenant)

Vector Search Flow (Correct Order):
1. Read active embedding model from Settings
2. Check compatibility with dataset's model
3. If mismatch: return error (do NOT search)
4. Embed user query using that model
5. Search Redis ONLY in model-specific index/namespace
6. Filter by user_id
7. Retrieve top-K results
8. Group by t_id
9. Re-rank results
10. Select best t_id
11. Fetch API template from PostgreSQL
12. Return final JSON output

Why Re-ranking is Model-Agnostic:
Re-ranking operates on:
- Similarity scores (normalized 0-1)
- Metadata (query text, confidence scores)
- NOT on vector dimensions

This means re-ranking works correctly regardless of which model
was used for embedding, as long as the search was done correctly.
"""

import uuid
import time
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from statistics import mean
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import numpy as np

from app.core.logger import logger
from app.core.embedding_model_registry import get_embedding_registry
from app.models.database_models import Template, Dataset
from app.services.user_embedding_settings_service import get_user_embedding_settings_service
from app.services.multi_model_redis_service import get_multi_model_redis_service
from app.services.ollama_embedding_service import get_ollama_service
from app.services.slot_extraction_service import get_slot_extraction_service
from app.models.schemas.embedding_schemas import ErrorCode


class MultiModelSemanticRetrievalService:
    """
    Complete semantic retrieval pipeline with multi-model support.
    
    This service:
    1. Enforces model compatibility before search
    2. Uses model-specific Redis indices
    3. Implements proper grouping and re-ranking
    4. Returns final API template from PostgreSQL
    
    CRITICAL: This is the ONLY service that should perform
    semantic search. All query endpoints should use this.
    """
    
    def __init__(self):
        self.registry = get_embedding_registry()
        self.settings_service = get_user_embedding_settings_service()
        self.redis_service = get_multi_model_redis_service()
        self.ollama_service = get_ollama_service()
        self.slot_extractor = get_slot_extraction_service()
    
    # --- Main Retrieval Method ---
    
    async def semantic_search(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        user_query: str,
        top_k: int = 10,
        dataset_id: Optional[uuid.UUID] = None,
        template_id: Optional[uuid.UUID] = None,
        user_query_intent: Optional[str] = None,
        include_alternatives: bool = False,
        skip_compatibility_check: bool = False,
        include_slot_extraction: bool = True
    ) -> Dict[str, Any]:
        """
        Complete semantic search pipeline with model governance.
        
        Flow (Strict Order):
        1. Get user's active model from Settings
        2. Check compatibility with dataset (if specified)
        3. If mismatch and not skip_compatibility_check: FAIL
        4. Generate query embedding using correct model
        5. Search model-specific Redis index
        6. Group by t_id
        7. Re-rank candidates
        8. Resolve best template from PostgreSQL
        9. Return final JSON
        
        Args:
            db: AsyncSession
            user_id: User UUID
            user_query: Natural language query
            top_k: Number of results
            dataset_id: Optional dataset filter
            template_id: Optional template filter
            user_query_intent: Optional detected intent
            include_alternatives: Include alternative APIs
            skip_compatibility_check: Skip model check (dangerous)
            
        Returns:
            Complete API resolution response
        """
        start_time = time.time()
        
        logger.info(
            f"[Semantic Search] Starting for query: '{user_query[:50]}...' "
            f"(user={str(user_id)[:8]})"
        )
        
        # =====================================================================
        # STEP 1: Get user's active embedding model from Settings
        # =====================================================================
        model_id, dimension, model_spec = await self.settings_service.get_active_embedding_model_async(
            db, user_id
        )
        
        logger.info(f"Step 1: Active model from Settings: {model_id} (dim={dimension})")
        
        # =====================================================================
        # STEP 2: Check compatibility with dataset (if specified)
        # =====================================================================
        effective_model = model_id
        
        if not skip_compatibility_check and (dataset_id or template_id):
            # Get dataset to check embedded model
            if dataset_id:
                result = await db.execute(
                    select(Dataset).where(
                        Dataset.dataset_id == dataset_id,
                        Dataset.u_id == user_id
                    )
                )
                dataset = result.scalar_one_or_none()
            elif template_id:
                result = await db.execute(
                    select(Dataset).where(
                        Dataset.t_id == template_id,
                        Dataset.u_id == user_id
                    ).order_by(Dataset.created_at.desc()).limit(1)
                )
                dataset = result.scalar_one_or_none()
            else:
                dataset = None
            
            if dataset and dataset.embedding_model:
                if dataset.embedding_model != model_id:
                    # MISMATCH DETECTED - FAIL
                    logger.warning(
                        f"Step 2: Model mismatch! Settings={model_id}, "
                        f"Dataset={dataset.embedding_model}"
                    )
                    
                    return {
                        "success": False,
                        "error": ErrorCode.MODEL_MISMATCH,
                        "message": (
                            f"Model mismatch: Your Settings use '{model_id}', "
                            f"but dataset was embedded with '{dataset.embedding_model}'."
                        ),
                        "settings_model": model_id,
                        "dataset_model": dataset.embedding_model,
                        "dataset_id": str(dataset.dataset_id),
                        "options": [
                            {
                                "action": "switch_settings",
                                "label": f"Use {dataset.embedding_model}",
                                "description": "Update Settings to match dataset"
                            },
                            {
                                "action": "reembed",
                                "label": f"Re-embed with {model_id}",
                                "description": "Re-embed dataset with current model"
                            }
                        ]
                    }
                
                logger.info(f"Step 2: Model compatibility verified")
        
        # =====================================================================
        # STEP 3: Generate query embedding using correct model
        # =====================================================================
        logger.info(f"Step 3: Generating query embedding with {effective_model}")
        
        try:
            query_embedding = await self.ollama_service.generate_embedding(
                model_name=effective_model,
                text=user_query
            )
            
            if not query_embedding:
                return {
                    "success": False,
                    "error": "EMBEDDING_FAILED",
                    "message": "Failed to generate query embedding"
                }
            
            query_vector = np.array(query_embedding, dtype=np.float32)
            
            # Verify dimension
            if query_vector.shape[0] != dimension:
                logger.error(
                    f"Query vector dimension mismatch: expected {dimension}, "
                    f"got {query_vector.shape[0]}"
                )
                return {
                    "success": False,
                    "error": "DIMENSION_MISMATCH",
                    "message": f"Query embedding dimension mismatch"
                }
                
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return {
                "success": False,
                "error": "EMBEDDING_FAILED",
                "message": str(e)
            }
        
        logger.info(f"Step 3: Query embedded (dim={query_vector.shape[0]})")
        
        # =====================================================================
        # STEP 4: Search model-specific Redis index
        # =====================================================================
        logger.info(
            f"Step 4: Searching Redis index '{model_spec.redis_index_name}'"
        )
        
        search_results = self.redis_service.search_similar_vectors(
            model_id=effective_model,
            user_id=user_id,
            query_vector=query_vector,
            top_k=top_k,
            dataset_id=dataset_id,
            template_id=template_id
        )
        
        # Format Stage 1 results
        stage1_results = [
            {
                "query": r.get("query", ""),
                "similarity_score": round(r.get("similarity", 0.0), 4),
                "t_id": r.get("template_id", r.get("t_id", "")),
                "row_id": r.get("row_id", 0)
            }
            for r in search_results
        ]
        
        if not search_results:
            logger.info("Step 4: No matching results found")
            return {
                "success": False,
                "error": "NO_RESULTS",
                "message": "No matching APIs found for your query",
                "stage1_vector_search": [],
                "metadata": {"query": user_query, "top_k": top_k}
            }
        
        logger.info(f"Step 4: Retrieved {len(search_results)} candidates")
        
        # =====================================================================
        # STEP 5: Group by t_id (template ID)
        # =====================================================================
        logger.info("Step 5: Grouping by template ID")
        
        grouped = self._group_by_template(search_results)
        
        if not grouped:
            return {
                "success": False,
                "error": "NO_VALID_TEMPLATES",
                "message": "No valid template references found",
                "stage1_vector_search": stage1_results
            }
        
        logger.info(f"Step 5: Grouped into {len(grouped)} template candidates")
        
        # =====================================================================
        # STEP 6: Re-rank candidates (MODEL-AGNOSTIC)
        # =====================================================================
        # Auto-detect intent if not provided to maximize intent alignment bonus
        effective_intent = user_query_intent or self._auto_detect_intent(user_query)
        logger.info(f"Step 6: Re-ranking candidates (intent={effective_intent})")
        
        best_t_id, ranking_metadata, all_scored = self._rerank_by_template(
            grouped_results=grouped,
            user_query_intent=effective_intent
        )
        
        # Format Stage 2 results
        stage2_results = [
            {
                "t_id": t.get("t_id", ""),
                "avg_similarity": round(t.get("avg_similarity", 0.0), 4),
                "avg_confidence_score": round(t.get("avg_confidence", 0.5), 4),
                "final_score": round(t.get("final_score", 0.0), 4),
                "rank": t.get("rank", 0),
                "match_count": t.get("match_count", 0)
            }
            for t in all_scored
        ]
        
        if not best_t_id:
            return {
                "success": False,
                "error": "RERANKING_FAILED",
                "message": "Re-ranking failed to select a candidate",
                "stage1_vector_search": stage1_results,
                "stage2_reranking": stage2_results
            }
        
        logger.info(
            f"Step 6: Best t_id={best_t_id[:8]}... "
            f"(score={ranking_metadata['final_score']:.4f})"
        )
        
        # =====================================================================
        # STEP 7: Resolve template from PostgreSQL
        # =====================================================================
        logger.info("Step 7: Resolving template from PostgreSQL")
        
        template = await self._resolve_template(
            db=db,
            t_id=uuid.UUID(best_t_id),
            user_id=user_id
        )
        
        if not template:
            return {
                "success": False,
                "error": "TEMPLATE_NOT_FOUND",
                "message": f"Template {best_t_id} not found",
                "stage1_vector_search": stage1_results,
                "stage2_reranking": stage2_results
            }
        
        logger.info(f"Step 7: Resolved '{template['api_name']}'")
        
        # =====================================================================
        # STEP 8: Extract slots from query (OPTIONAL)
        # =====================================================================
        extracted_request_body = None
        if include_slot_extraction and template.get("json_schema"):
            logger.info("Step 8: Extracting slots from query")
            try:
                extracted_request_body = await self.slot_extractor.extract_slots(
                    query=user_query,
                    request_schema=template["json_schema"],
                    api_name=template["api_name"],
                    endpoint=template["endpoint"]
                )
                logger.info(f"Step 8: Extracted {len(extracted_request_body)} slot values")
            except Exception as e:
                logger.warning(f"Slot extraction failed: {e}")
                extracted_request_body = {}
        
        # =====================================================================
        # STEP 8.5: Extract URL from query (if present)
        # =====================================================================
        raw_url, extracted_base_url = self.slot_extractor.extract_url_from_query(user_query)
        
        # Determine URL source
        if extracted_base_url:
            url_source = "query"
            effective_base_url = extracted_base_url
            logger.info(f"Step 8.5: URL extracted from query: {extracted_base_url}")
        else:
            url_source = "template"
            effective_base_url = template["base_url"]
            logger.info(f"Step 8.5: No URL in query, using template base_url: {effective_base_url}")
        
        # =====================================================================
        # STEP 9: Construct final response
        # =====================================================================
        processing_time_ms = round((time.time() - start_time) * 1000, 2)
        
        # Final output (clean JSON)
        final_output = {
            "t_id": best_t_id,
            "api_name": template["api_name"],
            "base_url": template["base_url"],
            "extracted_base_url": extracted_base_url,
            "effective_base_url": effective_base_url,
            "url_source": url_source,
            "endpoint": template["endpoint"],
            "method": template["method"],
            "confidence_score": round(ranking_metadata["final_score"], 4),
            "request_schema": template["json_schema"],
            "response_schema": template["response_schema"],
            "extracted_request_body": extracted_request_body
        }
        
        response = {
            "success": True,
            
            # Stage-by-stage data for dashboard
            "stage1_vector_search": stage1_results,
            "stage2_reranking": stage2_results,
            "final_output": final_output,
            
            # Legacy fields for backward compatibility
            "api_name": template["api_name"],
            "endpoint": template["endpoint"],
            "method": template["method"],
            "base_url": template["base_url"],
            "request_schema": template["json_schema"],
            "response_schema": template["response_schema"],
            "auth_config": template["auth_config"],
            "headers": template["headers"],
            "confidence": round(ranking_metadata["final_score"], 4),
            "extracted_request_body": extracted_request_body,
            
            # Metadata
            "metadata": {
                "query": user_query,
                "embedding_model": effective_model,
                "top_k": top_k,
                "total_candidates": len(search_results),
                "processing_time_ms": processing_time_ms,
                "t_id": best_t_id,
                "match_count": ranking_metadata["match_count"],
                "avg_similarity": round(ranking_metadata["avg_similarity"], 4),
                "avg_confidence": round(ranking_metadata["avg_confidence"], 4),
                "intent_alignment": round(ranking_metadata.get("intent_alignment", 0.5), 4),
                "dominant_intent": ranking_metadata.get("dominant_intent", "unknown"),
                "domain_tags": template.get("domain_tags", [])
            }
        }
        
        # Include alternatives if requested
        if include_alternatives and len(grouped) > 1:
            alternatives = await self._get_alternatives(
                db=db,
                user_id=user_id,
                grouped=grouped,
                best_t_id=best_t_id,
                max_alternatives=3
            )
            response["alternatives"] = alternatives
        
        logger.info(
            f"[Semantic Search] Complete: '{template['api_name']}' "
            f"(confidence={response['confidence']}, time={processing_time_ms}ms)"
        )
        
        return response
    
    # --- Helper Methods ---
    
    def _auto_detect_intent(self, query: str) -> str:
        """
        Automatically detect user intent from query text.
        
        Returns:
            "action" - if query implies performing an action (create, submit, make, etc.)
            "info" - if query implies getting information (what, how, where, etc.)
        
        This enables intent alignment bonus in re-ranking even when
        the caller doesn't explicitly provide user_query_intent.
        """
        query_lower = query.lower().strip()
        
        # Action intent keywords (user wants to DO something)
        action_keywords = [
            "create", "make", "add", "submit", "place", "generate", "process",
            "initiate", "start", "begin", "execute", "run", "perform", "send",
            "post", "put", "delete", "update", "modify", "change", "set",
            "upload", "download", "install", "configure", "enable", "disable",
            "authorize", "authenticate", "login", "logout", "register", "signup",
            "order", "purchase", "buy", "subscribe", "cancel", "refund",
            "i need to", "i want to", "let me", "gimme", "hook me up",
            "wanna", "gotta", "lemme", "plz", "please"
        ]
        
        # Info intent keywords (user wants to KNOW something)
        info_keywords = [
            "what", "how", "where", "when", "why", "which", "who",
            "is there", "are there", "can i", "does", "do you",
            "tell me", "show me", "explain", "describe", "list",
            "documentation", "docs", "guide", "tutorial", "help",
            "info", "information", "details", "about", "overview",
            "endpoint", "api for", "what api", "what is the"
        ]
        
        # Check for action keywords first (more specific)
        for keyword in action_keywords:
            if keyword in query_lower:
                return "action"
        
        # Check for info keywords
        for keyword in info_keywords:
            if keyword in query_lower:
                return "info"
        
        # Default to "action" for short/ambiguous queries
        # (most API usage is action-oriented)
        return "action"
    

    def _group_by_template(
        self, 
        results: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict]]:
        """
        Group search results by template ID.
        
        Each group represents one candidate API template.
        """
        grouped: Dict[str, List[Dict]] = defaultdict(list)
        
        for result in results:
            # Handle both 'template_id' and 't_id' for compatibility
            t_id = result.get("template_id") or result.get("t_id")
            if t_id:
                grouped[t_id].append(result)
            else:
                logger.debug(f"Result missing t_id: {result.get('query', '')[:30]}")
        
        return dict(grouped)
    
    def _rerank_by_template(
        self,
        grouped_results: Dict[str, List[Dict]],
        user_query_intent: Optional[str] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> Tuple[Optional[str], Optional[Dict], List[Dict]]:
        """
        Re-rank API template candidates and select the best one.
        
        IMPORTANT: This is MODEL-AGNOSTIC
        
        Re-ranking operates on:
        - Similarity scores (normalized 0-1) from search
        - Confidence scores from metadata
        - Intent alignment bonus
        
        It does NOT use:
        - Vector dimensions
        - Raw embeddings
        
        This is why re-ranking works correctly regardless of
        which embedding model was used.
        
        Scoring formula:
        final_score = (
            0.5 × avg_similarity +
            0.3 × avg_confidence +
            0.2 × intent_alignment
        )
        """
        if not grouped_results:
            return None, None, []
        
        w = weights or {"similarity": 0.6, "confidence": 0.2, "intent": 0.2}
        scored_templates = []
        
        for t_id, rows in grouped_results.items():
            # Calculate averages from NORMALIZED scores (not dimensions)
            avg_similarity = mean(r.get("similarity", 0.0) for r in rows)
            avg_confidence = mean(r.get("confidence_score", 0.5) for r in rows)
            
            # Intent alignment bonus
            if user_query_intent:
                matching = sum(
                    1 for r in rows 
                    if r.get("intent_type") == user_query_intent
                )
                intent_alignment = matching / len(rows) if rows else 0
            else:
                intent_alignment = 0.5  # Neutral
            
            # Compute final score
            final_score = (
                w["similarity"] * avg_similarity +
                w["confidence"] * avg_confidence +
                w["intent"] * intent_alignment
            )
            
            # Dominant intent
            intent_counts: Dict[str, int] = defaultdict(int)
            for r in rows:
                intent_counts[r.get("intent_type", "unknown")] += 1
            dominant_intent = (
                max(intent_counts, key=intent_counts.get) 
                if intent_counts else "unknown"
            )
            
            scored_templates.append({
                "t_id": t_id,
                "final_score": final_score,
                "avg_similarity": avg_similarity,
                "avg_confidence": avg_confidence,
                "intent_alignment": intent_alignment,
                "dominant_intent": dominant_intent,
                "match_count": len(rows)
            })
        
        # Sort by final score
        scored_templates.sort(key=lambda x: x["final_score"], reverse=True)
        
        # Add rank
        for idx, template in enumerate(scored_templates):
            template["rank"] = idx + 1
        
        best = scored_templates[0] if scored_templates else None
        
        return (
            (best["t_id"], best, scored_templates) 
            if best else (None, None, scored_templates)
        )
    
    async def _resolve_template(
        self,
        db: AsyncSession,
        t_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch full API template from PostgreSQL.
        
        PostgreSQL is the SINGLE SOURCE OF TRUTH for API structure.
        """
        stmt = select(Template).where(
            Template.t_id == t_id,
            Template.u_id == user_id  # Multi-tenant security
        )
        
        result = await db.execute(stmt)
        template = result.scalar_one_or_none()
        
        if not template:
            return None
        
        return {
            "t_id": str(template.t_id),
            "api_name": template.api_name,
            "description": template.description,
            "endpoint": template.endpoint,
            "base_url": template.base_url,
            "method": template.method,
            "json_schema": template.json_schema,
            "response_schema": template.response_schema,
            "auth_config": template.auth_config,
            "headers": template.headers,
            "domain_tags": template.domain_tags,
            "sample_requests": template.sample_requests,
            "sample_responses": template.sample_responses,
        }
    
    async def _get_alternatives(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        grouped: Dict[str, List[Dict]],
        best_t_id: str,
        max_alternatives: int = 3
    ) -> List[Dict[str, Any]]:
        """Get alternative API suggestions."""
        alternatives = []
        
        for t_id in list(grouped.keys())[:max_alternatives + 1]:
            if t_id == best_t_id:
                continue
            if len(alternatives) >= max_alternatives:
                break
            
            template = await self._resolve_template(
                db, uuid.UUID(t_id), user_id
            )
            if template:
                rows = grouped[t_id]
                alternatives.append({
                    "t_id": t_id,
                    "api_name": template["api_name"],
                    "endpoint": template["endpoint"],
                    "method": template["method"],
                    "avg_similarity": round(
                        mean(r.get("similarity", 0) for r in rows), 4
                    ),
                    "match_count": len(rows)
                })
        
        return alternatives


# --- Singleton Accessor ---

_service_instance: Optional[MultiModelSemanticRetrievalService] = None


def get_multi_model_semantic_service() -> MultiModelSemanticRetrievalService:
    """Get the singleton multi-model semantic retrieval service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = MultiModelSemanticRetrievalService()
    return _service_instance