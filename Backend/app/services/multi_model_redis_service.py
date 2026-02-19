# Backend\app\services\multi_model_redis_service.py

"""
Multi-Model Redis Vector Service - Dimension-Safe & Tenant-Safe Vector Storage

🎯 Purpose:
This service provides model-isolated vector storage and search in Redis.
Each embedding model has its own index and namespace, preventing:
- Dimension mismatches (vectors of different sizes never mix)
- Cross-model contamination (different vector spaces never compared)
- Cross-tenant data leakage (user isolation enforced)

❗ NON-NEGOTIABLE RULES:
1. Each model has its OWN Redis index
2. Each model has its OWN key namespace
3. Vectors are NEVER stored in an index with wrong dimension
4. Searches NEVER cross model boundaries
5. All operations are user-scoped (multi-tenant)

📐 Redis Structure:
- Index: idx_vectors_{model_id} (e.g., idx_vectors_nomic_embed_text)
- Keys: vector:{model_id}:{user_id}:{dataset_id}:{row_id}
- Example: vector:nomic_embed_text:abc123:def456:row_0

🔒 Why This Prevents Dimension Issues:
1. Index Creation: Each index is created with EXACT dimension
2. Storage: Vectors go to model-specific namespace
3. Search: Queries run against model-specific index
4. No Overlap: Different models never share indices
"""

import redis
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
import uuid
from datetime import datetime, timezone

from redis.commands.search.field import VectorField, TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query

from app.core.config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
from app.core.logger import logger
from app.core.embedding_model_registry import (
    get_embedding_registry
)


def escape_redis_tag(value: str) -> str:
    """Escape special characters in Redis TAG field values (like hyphens in UUIDs)"""
    if value is None:
        return ""
    return str(value).replace('-', '\\-')


class MultiModelRedisVectorService:
    """
    Model-isolated Redis vector storage and search.
    
    Architecture:
    - One HNSW index per embedding model
    - Model-specific key namespaces
    - Strict dimension enforcement
    - Multi-tenant isolation via user_id filtering
    
    ❗ CRITICAL: This service uses the EmbeddingModelRegistry
    as the single source of truth for model dimensions and index names.
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=REDIS_HOST, 
            port=REDIS_PORT, 
            password=REDIS_PASSWORD, 
            decode_responses=False
        )
        self.registry = get_embedding_registry()
        self._initialized_indexes: set = set()
        
        logger.info(
            f"🔗 MultiModelRedisVectorService initialized "
            f"(Redis: {REDIS_HOST}:{REDIS_PORT})"
        )
    
    # ===========================================================================
    # INDEX MANAGEMENT (Model-Specific)
    # ===========================================================================
    
    def _get_index_name(self, model_id: str) -> str:
        """
        Get the Redis index name for a model.
        
        Uses registry as single source of truth.
        """
        return self.registry.get_redis_index(model_id)
    
    def _get_namespace(self, model_id: str) -> str:
        """
        Get the Redis key namespace for a model.
        
        Uses registry as single source of truth.
        """
        return self.registry.get_redis_namespace(model_id)
    
    def _get_dimension(self, model_id: str) -> int:
        """
        Get the EXACT dimension for a model.
        
        Uses registry as single source of truth.
        """
        return self.registry.get_dimension(model_id)
    
    def ensure_model_index_exists(self, model_id: str) -> bool:
        """
        Ensure Redis index exists for a specific model.
        
        ❗ CRITICAL: Index is created with EXACT dimension from registry.
        This prevents dimension mismatch at the storage level.
        
        Args:
            model_id: Embedding model ID
            
        Returns:
            True if index exists/created, False on error
        """
        index_name = self._get_index_name(model_id)
        
        # Skip if already initialized this session
        if index_name in self._initialized_indexes:
            return True
        
        dimension = self._get_dimension(model_id)
        namespace = self._get_namespace(model_id)
        
        try:
            # Check if index exists
            self.redis_client.ft(index_name).info()
            logger.debug(f"✅ Index exists: {index_name} (dim={dimension})")
            self._initialized_indexes.add(index_name)
            return True
            
        except redis.exceptions.ResponseError as e:
            if "Unknown index name" in str(e) or "unknown index name" in str(e).lower():
                # Create new index
                return self._create_model_index(model_id, index_name, dimension, namespace)
            else:
                logger.error(f"❌ Redis error checking index {index_name}: {e}")
                return False
    
    def _create_model_index(
        self, 
        model_id: str, 
        index_name: str, 
        dimension: int, 
        namespace: str
    ) -> bool:
        """
        Create HNSW index for a specific model.
        
        ❗ Index schema includes:
        - Vector field with EXACT dimension
        - User ID for multi-tenant filtering
        - Dataset ID for dataset scoping
        - Template ID for template scoping
        - Metadata fields for search/filter
        """
        logger.info(
            f"🔨 Creating HNSW index: {index_name} "
            f"(model={model_id}, dim={dimension}, prefix={namespace})"
        )
        
        try:
            schema = (
                # Multi-tenant isolation
                TagField("$.user_id", as_name="user_id"),
                
                # Dataset/Template scoping
                TagField("$.dataset_id", as_name="dataset_id"),
                TagField("$.template_id", as_name="template_id"),
                
                # Row identification
                NumericField("$.row_id", as_name="row_id"),
                
                # Searchable content
                TextField("$.query", as_name="query"),
                TextField("$.api_name", as_name="api_name"),
                TextField("$.endpoint", as_name="endpoint"),
                TagField("$.method", as_name="method"),
                TagField("$.scenario_type", as_name="scenario_type"),
                TagField("$.test_category", as_name="test_category"),
                TextField("$.notes", as_name="notes"),
                
                # Model tracking (for verification)
                TagField("$.embedding_model", as_name="embedding_model"),
                
                # Vector field with EXACT dimension
                VectorField(
                    "$.vector",
                    "HNSW",
                    {
                        "TYPE": "FLOAT32",
                        "DIM": dimension,  # EXACT dimension from registry
                        "DISTANCE_METRIC": "COSINE",
                        "M": 16,  # HNSW parameter
                        "EF_CONSTRUCTION": 200  # HNSW parameter
                    },
                    as_name="vector"
                )
            )
            
            # Index only keys with model-specific namespace
            definition = IndexDefinition(
                prefix=[f"{namespace}:"],
                index_type=IndexType.JSON
            )
            
            self.redis_client.ft(index_name).create_index(
                schema,
                definition=definition
            )
            
            logger.info(f"✅ Created HNSW index: {index_name}")
            self._initialized_indexes.add(index_name)
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create index {index_name}: {e}")
            return False
    
    def initialize_all_model_indexes(self) -> Dict[str, bool]:
        """
        Initialize indexes for all registered models.
        
        Called at application startup to ensure all indexes exist.
        
        Returns:
            Dict mapping model_id to success status
        """
        results = {}
        for model_id in self.registry.list_model_ids():
            results[model_id] = self.ensure_model_index_exists(model_id)
        
        success_count = sum(1 for v in results.values() if v)
        logger.info(
            f"📚 Initialized {success_count}/{len(results)} model indexes"
        )
        
        return results
    
    # ===========================================================================
    # KEY GENERATION (Model-Specific Namespace)
    # ===========================================================================
    
    def generate_vector_key(
        self,
        model_id: str,
        user_id: uuid.UUID,
        dataset_id: uuid.UUID,
        row_id: int
    ) -> str:
        """
        Generate Redis key for a vector.
        
        Format: vector:{model_id}:{user_id}:{dataset_id}:{row_id}
        
        ❗ Model-specific namespace ensures:
        - Vectors from different models never share keys
        - Easy bulk deletion per model
        - Clear audit trail
        
        Args:
            model_id: Embedding model ID
            user_id: User UUID
            dataset_id: Dataset UUID
            row_id: Row number in dataset
            
        Returns:
            Redis key string
        """
        namespace = self._get_namespace(model_id)
        return f"{namespace}:{user_id}:{dataset_id}:{row_id}"
    
    def parse_vector_key(self, key: str) -> Optional[Dict[str, str]]:
        """
        Parse components from a vector key.
        
        Returns:
            Dict with namespace, user_id, dataset_id, row_id
            or None if invalid format
        """
        try:
            parts = key.split(":")
            if len(parts) >= 4 and parts[0] == "vector":
                return {
                    "namespace": f"{parts[0]}:{parts[1]}",
                    "model_namespace": parts[1],
                    "user_id": parts[2],
                    "dataset_id": parts[3],
                    "row_id": parts[4] if len(parts) > 4 else None
                }
        except Exception:
            pass
        return None
    
    # ===========================================================================
    # VECTOR STORAGE (Model-Isolated)
    # ===========================================================================
    
    def store_vector(
        self,
        model_id: str,
        user_id: uuid.UUID,
        dataset_id: uuid.UUID,
        template_id: uuid.UUID,
        row_id: int,
        vector: np.ndarray,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Store a vector in the model-specific index.
        
        ❗ CRITICAL VALIDATION:
        1. Verify vector dimension matches model's expected dimension
        2. Store in model-specific namespace
        3. Index in model-specific HNSW index
        
        Args:
            model_id: Embedding model ID
            user_id: User UUID
            dataset_id: Dataset UUID
            template_id: Template UUID
            row_id: Row number in dataset
            vector: Embedding vector (numpy array)
            metadata: Additional metadata (query, api_name, etc.)
            
        Returns:
            Redis key where vector was stored
            
        Raises:
            ValueError: If vector dimension doesn't match model
        """
        # Get expected dimension
        expected_dim = self._get_dimension(model_id)
        
        # Validate vector dimension
        actual_dim = vector.shape[0] if vector.ndim == 1 else vector.shape[-1]
        if actual_dim != expected_dim:
            raise ValueError(
                f"Vector dimension mismatch for model '{model_id}': "
                f"expected {expected_dim}, got {actual_dim}. "
                f"This is a critical error - check embedding generation."
            )
        
        # Ensure index exists
        self.ensure_model_index_exists(model_id)
        
        # Generate key
        key = self.generate_vector_key(model_id, user_id, dataset_id, row_id)
        
        # Prepare document
        document = {
            "user_id": str(user_id),
            "dataset_id": str(dataset_id),
            "template_id": str(template_id) if template_id else None,
            "row_id": row_id,
            "embedding_model": model_id,
            "dimension": expected_dim,
            "vector": vector.astype(np.float32).tolist(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            # Metadata fields
            "query": metadata.get("query", ""),
            "api_name": metadata.get("api_name", ""),
            "endpoint": metadata.get("endpoint", ""),
            "method": metadata.get("method", "POST"),
            "scenario_type": metadata.get("scenario_type", "valid"),
            "test_category": metadata.get("test_category", "valid_flow"),
            "notes": metadata.get("notes", ""),
        }
        
        # Store in Redis
        self.redis_client.json().set(key, "$", document)
        
        logger.debug(
            f"📦 Stored vector: {key} (model={model_id}, dim={expected_dim})"
        )
        
        return key
    
    def store_vectors_batch(
        self,
        model_id: str,
        user_id: uuid.UUID,
        dataset_id: uuid.UUID,
        template_id: uuid.UUID,
        vectors_data: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """
        Store multiple vectors in batch.
        
        Args:
            model_id: Embedding model ID
            user_id: User UUID
            dataset_id: Dataset UUID
            template_id: Template UUID
            vectors_data: List of dicts with 'row_id', 'vector', 'metadata'
            
        Returns:
            Tuple of (success_count, failure_count)
        """
        expected_dim = self._get_dimension(model_id)
        self.ensure_model_index_exists(model_id)
        
        success_count = 0
        failure_count = 0
        
        pipeline = self.redis_client.pipeline()
        
        for item in vectors_data:
            try:
                row_id = item["row_id"]
                vector = np.asarray(item["vector"], dtype=np.float32)
                metadata = item.get("metadata", {})
                
                # Validate dimension
                actual_dim = vector.shape[0] if vector.ndim == 1 else vector.shape[-1]
                if actual_dim != expected_dim:
                    logger.warning(
                        f"Skipping row {row_id}: dimension mismatch "
                        f"(expected {expected_dim}, got {actual_dim})"
                    )
                    failure_count += 1
                    continue
                
                # Generate key
                key = self.generate_vector_key(model_id, user_id, dataset_id, row_id)
                
                # Prepare document
                document = {
                    "user_id": str(user_id),
                    "dataset_id": str(dataset_id),
                    "template_id": str(template_id) if template_id else None,
                    "row_id": row_id,
                    "embedding_model": model_id,
                    "dimension": expected_dim,
                    "vector": vector.tolist(),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "query": metadata.get("query", ""),
                    "api_name": metadata.get("api_name", ""),
                    "endpoint": metadata.get("endpoint", ""),
                    "method": metadata.get("method", "POST"),
                    "scenario_type": metadata.get("scenario_type", "valid"),
                    "test_category": metadata.get("test_category", "valid_flow"),
                    "notes": metadata.get("notes", ""),
                }
                
                # Add to pipeline
                pipeline.json().set(key, "$", document)
                success_count += 1
                
            except Exception as e:
                logger.warning(f"Error preparing vector for batch: {e}")
                failure_count += 1
        
        # Execute pipeline
        if success_count > 0:
            try:
                pipeline.execute()
                logger.info(
                    f"📦 Stored {success_count} vectors in batch "
                    f"(model={model_id}, failures={failure_count})"
                )
            except Exception as e:
                logger.error(f"Batch store failed: {e}")
                failure_count += success_count
                success_count = 0
        
        return success_count, failure_count
    
    # ===========================================================================
    # VECTOR SEARCH (Model-Isolated)
    # ===========================================================================
    
    def search_similar_vectors(
        self,
        model_id: str,
        user_id: uuid.UUID,
        query_vector: np.ndarray,
        top_k: int = 10,
        dataset_id: Optional[uuid.UUID] = None,
        template_id: Optional[uuid.UUID] = None,
        filters: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors using KNN in model-specific index.
        
        ❗ CRITICAL:
        1. Searches ONLY in the model-specific index
        2. ALWAYS filters by user_id (multi-tenant security)
        3. Validates query vector dimension
        
        Args:
            model_id: Embedding model ID (MUST match dataset's model)
            user_id: User UUID (REQUIRED for multi-tenant isolation)
            query_vector: Query embedding vector
            top_k: Number of results to return
            dataset_id: Optional dataset filter
            template_id: Optional template filter
            filters: Optional additional filters
            
        Returns:
            List of search results with similarity scores
        """
        # Validate query vector dimension
        expected_dim = self._get_dimension(model_id)
        actual_dim = query_vector.shape[0] if query_vector.ndim == 1 else query_vector.shape[-1]
        
        if actual_dim != expected_dim:
            logger.error(
                f"Query vector dimension mismatch: expected {expected_dim}, "
                f"got {actual_dim} for model '{model_id}'"
            )
            return []
        
        # Get model-specific index
        index_name = self._get_index_name(model_id)
        
        # Ensure index exists
        if not self.ensure_model_index_exists(model_id):
            logger.error(f"Index {index_name} does not exist")
            return []
        
        # Build filter query (ALWAYS include user_id for security)
        escaped_user_id = escape_redis_tag(str(user_id))
        filter_parts = [f"@user_id:{{{escaped_user_id}}}"]
        
        if dataset_id:
            escaped_dataset_id = escape_redis_tag(str(dataset_id))
            filter_parts.append(f"@dataset_id:{{{escaped_dataset_id}}}")
        
        if template_id:
            escaped_template_id = escape_redis_tag(str(template_id))
            filter_parts.append(f"@template_id:{{{escaped_template_id}}}")
        
        if filters:
            for field, value in filters.items():
                escaped_value = escape_redis_tag(value)
                filter_parts.append(f"@{field}:{{{escaped_value}}}")
        
        filter_query = " ".join(filter_parts)
        
        # Build KNN query
        knn_query = f"({filter_query})=>[KNN {top_k} @vector $vec AS vector_score]"
        
        q = (
            Query(knn_query)
            .sort_by("vector_score")
            .return_fields(
                "vector_score", "user_id", "dataset_id", "template_id",
                "row_id", "query", "api_name", "endpoint", "method",
                "scenario_type", "test_category", "notes", "embedding_model"
            )
            .dialect(2)
        )
        
        # Prepare query vector
        query_vec_bytes = np.asarray(query_vector, dtype=np.float32).tobytes()
        
        try:
            logger.info(
                f"🔍 Searching index '{index_name}' "
                f"(model={model_id}, dim={expected_dim}, user={str(user_id)[:8]}...)"
            )
            
            results = self.redis_client.ft(index_name).search(
                q, 
                query_params={"vec": query_vec_bytes}
            )
            
            # Parse results
            search_results = []
            for doc in results.docs:
                try:
                    vector_distance = float(getattr(doc, "vector_score", 1.0))
                    similarity = 1.0 - vector_distance  # Convert distance to similarity
                    
                    search_results.append({
                        "redis_key": doc.id,
                        "similarity": similarity,
                        "vector_score": vector_distance,
                        "user_id": getattr(doc, "user_id", None),
                        "dataset_id": getattr(doc, "dataset_id", None),
                        "template_id": getattr(doc, "template_id", None),
                        "t_id": getattr(doc, "template_id", None),  # Alias for compatibility
                        "row_id": int(getattr(doc, "row_id", 0)),
                        "query": getattr(doc, "query", ""),
                        "api_name": getattr(doc, "api_name", ""),
                        "endpoint": getattr(doc, "endpoint", ""),
                        "method": getattr(doc, "method", "POST"),
                        "scenario_type": getattr(doc, "scenario_type", "valid"),
                        "test_category": getattr(doc, "test_category", "valid_flow"),
                        "notes": getattr(doc, "notes", ""),
                        "embedding_model": getattr(doc, "embedding_model", model_id),
                    })
                except Exception as e:
                    logger.warning(f"Error parsing search result: {e}")
            
            logger.info(f"🔍 Found {len(search_results)} results")
            return search_results
            
        except redis.exceptions.ResponseError as e:
            if "unknown index name" in str(e).lower():
                logger.error(f"Index '{index_name}' does not exist")
            else:
                logger.error(f"Search error: {e}")
            return []
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    # ===========================================================================
    # DELETION (Model-Specific)
    # ===========================================================================
    
    def delete_dataset_vectors(
        self,
        model_id: str,
        user_id: uuid.UUID,
        dataset_id: uuid.UUID
    ) -> int:
        """
        Delete all vectors for a dataset.
        
        Args:
            model_id: Embedding model ID
            user_id: User UUID
            dataset_id: Dataset UUID
            
        Returns:
            Number of keys deleted
        """
        namespace = self._get_namespace(model_id)
        pattern = f"{namespace}:{user_id}:{dataset_id}:*"
        
        keys = []
        cursor = 0
        
        while True:
            cursor, batch = self.redis_client.scan(
                cursor=cursor, 
                match=pattern.encode(), 
                count=100
            )
            keys.extend(batch)
            if cursor == 0:
                break
        
        if keys:
            self.redis_client.delete(*keys)
            logger.info(
                f"🗑️ Deleted {len(keys)} vectors for dataset {str(dataset_id)[:8]} "
                f"(model={model_id})"
            )
            return len(keys)
        
        return 0
    
    def delete_user_vectors_for_model(
        self,
        model_id: str,
        user_id: uuid.UUID
    ) -> int:
        """
        Delete all vectors for a user in a specific model's namespace.
        
        Args:
            model_id: Embedding model ID
            user_id: User UUID
            
        Returns:
            Number of keys deleted
        """
        namespace = self._get_namespace(model_id)
        pattern = f"{namespace}:{user_id}:*"
        
        keys = []
        cursor = 0
        
        while True:
            cursor, batch = self.redis_client.scan(
                cursor=cursor, 
                match=pattern.encode(), 
                count=100
            )
            keys.extend(batch)
            if cursor == 0:
                break
        
        if keys:
            self.redis_client.delete(*keys)
            logger.info(
                f"🗑️ Deleted {len(keys)} vectors for user {str(user_id)[:8]} "
                f"(model={model_id})"
            )
            return len(keys)
        
        return 0
    
    # ===========================================================================
    # UTILITY METHODS
    # ===========================================================================
    
    def count_vectors(
        self,
        model_id: str,
        user_id: uuid.UUID,
        dataset_id: Optional[uuid.UUID] = None
    ) -> int:
        """
        Count vectors for a user/dataset in a model's index.
        
        Uses FT.SEARCH with LIMIT 0 0 (returns total count without fetching
        document bodies) and falls back to key-scan counting if the index
        query returns a suspicious result.
        
        Args:
            model_id: Embedding model ID
            user_id: User UUID
            dataset_id: Optional dataset UUID filter
            
        Returns:
            Count of matching vectors
        """
        index_name = self._get_index_name(model_id)
        
        # Build filter
        escaped_user_id = escape_redis_tag(str(user_id))
        filter_query = f"@user_id:{{{escaped_user_id}}}"
        
        if dataset_id:
            escaped_dataset_id = escape_redis_tag(str(dataset_id))
            filter_query += f" @dataset_id:{{{escaped_dataset_id}}}"
        
        try:
            # Use paging(0, 0) to request ONLY the total count, no doc bodies.
            # This avoids any default LIMIT cap issues on result.total.
            q = Query(filter_query).no_content().paging(0, 0).dialect(2)
            result = self.redis_client.ft(index_name).search(q)
            ft_total = result.total
            
            # Cross-check with scan-based count for reliability
            scan_total = self._count_vectors_by_scan(model_id, user_id, dataset_id)
            
            if ft_total != scan_total:
                logger.warning(
                    f"⚠️ Vector count mismatch for index {index_name}: "
                    f"FT.SEARCH reports {ft_total}, key scan found {scan_total}. "
                    f"Using scan count (more reliable)."
                )
                return scan_total
            
            return ft_total
        except Exception as e:
            logger.debug(f"FT.SEARCH count failed for index {index_name}: {e}")
            # Fall back to scan-based counting
            return self._count_vectors_by_scan(model_id, user_id, dataset_id)
    
    def _count_vectors_by_scan(
        self,
        model_id: str,
        user_id: uuid.UUID,
        dataset_id: Optional[uuid.UUID] = None
    ) -> int:
        """
        Count vectors by scanning Redis keys directly.
        
        This is a reliable fallback that doesn't depend on RediSearch
        index state. It scans keys matching the model namespace pattern
        and filters by user_id (and optionally dataset_id).
        
        Args:
            model_id: Embedding model ID
            user_id: User UUID
            dataset_id: Optional dataset UUID filter
            
        Returns:
            Count of matching keys
        """
        namespace = self._get_namespace(model_id)
        
        if dataset_id:
            pattern = f"{namespace}:{user_id}:{dataset_id}:*"
        else:
            pattern = f"{namespace}:{user_id}:*"
        
        try:
            count = 0
            for _ in self.redis_client.scan_iter(
                match=pattern.encode() if isinstance(pattern, str) else pattern,
                count=500
            ):
                count += 1
            return count
        except Exception as e:
            logger.debug(f"Scan count failed for pattern {pattern}: {e}")
            return 0
    
    def get_index_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a model's index.
        
        Args:
            model_id: Embedding model ID
            
        Returns:
            Index info dict or None if index doesn't exist
        """
        index_name = self._get_index_name(model_id)
        
        try:
            info = self.redis_client.ft(index_name).info()
            return {
                "index_name": index_name,
                "model_id": model_id,
                "dimension": self._get_dimension(model_id),
                "num_docs": info.get("num_docs", 0),
                "max_doc_id": info.get("max_doc_id", 0),
                "num_terms": info.get("num_terms", 0),
            }
        except Exception as e:
            logger.debug(f"Index info failed for {index_name}: {e}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check Redis connection and index health.
        
        Returns:
            Health status dict
        """
        try:
            self.redis_client.ping()
            
            # Check each model's index
            indexes_status = {}
            for model_id in self.registry.list_model_ids():
                index_info = self.get_index_info(model_id)
                indexes_status[model_id] = {
                    "exists": index_info is not None,
                    "docs": index_info.get("num_docs", 0) if index_info else 0
                }
            
            return {
                "status": "healthy",
                "redis": "connected",
                "indexes": indexes_status
            }
        except redis.exceptions.ConnectionError:
            return {
                "status": "unhealthy",
                "redis": "disconnected",
                "indexes": {}
            }
    
    async def ensure_index_exists(self, model_id: str) -> bool:
        """
        Async wrapper to ensure index exists for a model.
        
        This is called when registering new dynamic models to ensure
        their Redis HNSW index is created.
        
        Args:
            model_id: Embedding model ID
            
        Returns:
            True if index exists or was created successfully
        """
        import asyncio
        # Run synchronous method in thread pool to avoid blocking
        return await asyncio.to_thread(self.ensure_model_index_exists, model_id)


# =============================================================================
# SINGLETON ACCESSOR
# =============================================================================

_service_instance: Optional[MultiModelRedisVectorService] = None


def get_multi_model_redis_service() -> MultiModelRedisVectorService:
    """Get the singleton multi-model Redis vector service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = MultiModelRedisVectorService()
    return _service_instance