# Backend\app\services\embedding_service.py


"""
Enhanced Embedding Service - Automatic embeddings after dataset generation using Ollama

Features:
- Automatic embedding after CSV generation
- Multi-tenant separation: embedding:{user_id}:{template_id}:{csv_row_id}
- Ollama-based embedding models (384/768/1024 dimensions)
- Redis HNSW index per dimension
- PostgreSQL metadata tracking
- User settings integration
- CPU-only, no GPU required

Key Design: One Embedding Model Per Dataset
- Once embedded, a dataset is locked to that model
- Search with different model returns MODEL_MISMATCH error
- Re-embedding requires explicit user action via /reembed endpoint
"""

import os
import uuid
import asyncio
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import numpy as np

from app.core.logger import logger
from app.models.database_models import Template, Metadata, UserSettings, Dataset
from app.services.redis_vector_service import RedisVectorService
from app.services.ollama_embedding_service import get_ollama_service
from app.core.models_config import get_embedding_model_info, DEFAULT_EMBEDDING_MODEL
from app.models.schemas.embedding_schemas import (
    ModelMismatchError,
    EmbeddingStatus,
    ErrorCode,
)

import warnings
warnings.warn(
    "embedding_service.py is deprecated. Use multi_model_embedding_service.py instead.",
    DeprecationWarning,
    stacklevel=2
)


def escape_redis_tag(value: str) -> str:
    """Escape special characters in Redis TAG field values (like hyphens in UUIDs)"""
    if value is None:
        return value
    return str(value).replace('-', '\\-')


class EnhancedEmbeddingService:
    """
    Enhanced embedding service with Ollama integration
    
    Architecture:
    - Redis keys: embedding:{user_id}:{template_id}:{csv_row_id}
    - PostgreSQL: Metadata tracking (model, dimension, namespace, timestamps)
    - HNSW indices: Per dimension (384, 768, 1024)
    - Ollama: CPU-based embedding generation (localhost:11434)
    """
    
    def __init__(self):
        self.redis_service = RedisVectorService()
        self.ollama_service = get_ollama_service()
        # LEGACY: Dimension-based indexes - bypasses model governance
        # For new development, use multi_model_embedding_service.py
        self.index_mapping = {
            384: "embeddings_384",   # DEPRECATED: Use idx_vectors_{model_id}
            768: "embeddings_768",   # DEPRECATED: Use idx_vectors_{model_id}
            1024: "embeddings_1024"  # DEPRECATED: Use idx_vectors_{model_id}
        }
    
    def _get_user_embedding_model(self, db: Session, user_id: uuid.UUID) -> tuple[str, int]:
        """
        Get user's preferred embedding model from settings (SYNC version)
        
        Returns:
            Tuple of (model_id, dimension)
        """
        user_settings = db.query(UserSettings).filter(
            UserSettings.u_id == user_id
        ).first()
        
        if user_settings and user_settings.default_embedding_model:
            model_id = user_settings.default_embedding_model
            dimension = user_settings.embedding_dimension
        else:
            model_id = DEFAULT_EMBEDDING_MODEL
            model_info = get_embedding_model_info(model_id)
            dimension = model_info.dimension
        
        logger.info(f"Using Ollama model: {model_id} (dimension={dimension})")
        return model_id, dimension
    
    async def _get_user_embedding_model_async(self, db: AsyncSession, user_id: uuid.UUID) -> tuple[str, int]:
        """
        Get user's preferred embedding model from settings (ASYNC version)
        
        Returns:
            Tuple of (model_id, dimension)
        """
        result = await db.execute(
            select(UserSettings).where(UserSettings.u_id == user_id)
        )
        user_settings = result.scalar_one_or_none()
        
        if user_settings and user_settings.default_embedding_model:
            model_id = user_settings.default_embedding_model
            dimension = user_settings.embedding_dimension
        else:
            model_id = DEFAULT_EMBEDDING_MODEL
            model_info = get_embedding_model_info(model_id)
            dimension = model_info.dimension
        
        logger.info(f"Using Ollama model: {model_id} (dimension={dimension})")
        return model_id, dimension
    
    def _generate_redis_key(
        self,
        user_id: uuid.UUID,
        template_id: uuid.UUID,
        csv_row_id: int
    ) -> str:
        """
        Generate Redis key with multi-tenant separation
        
        Format: embedding:{user_id}:{template_id}:{csv_row_id}
        """
        return f"embedding:{user_id}:{template_id}:{csv_row_id}"
    
    def _ensure_hnsw_index(self, dimension: int):
        """
        Ensure HNSW index exists for the given dimension
        
        Creates dimension-based Redis Search index (embeddings_384, embeddings_768, etc.).
        Each embedding model dimension gets its own index.
        """
        index_name = self.index_mapping.get(dimension, f"embeddings_{dimension}")
        
        try:
            # Check if index exists
            self.redis_service.redis_client.ft(index_name).info()
            logger.info(f"HNSW index already exists: {index_name}")
        except Exception:
            # Create HNSW index
            logger.info(f"Creating HNSW index: {index_name} (dimension={dimension})")
            
            from redis.commands.search.field import VectorField, TextField, NumericField, TagField
            from redis.commands.search.indexDefinition import IndexDefinition, IndexType
            
            schema = (
                TagField("$.user_id", as_name="user_id"),
                TagField("$.t_id", as_name="t_id"),
                NumericField("$.csv_row_id", as_name="csv_row_id"),
                TextField("$.query", as_name="query"),
                TextField("$.api", as_name="api"),
                TextField("$.endpoint", as_name="endpoint"),
                TextField("$.method", as_name="method"),
                TextField("$.intent_type", as_name="intent_type"),
                TextField("$.scenario_type", as_name="scenario_type"),
                TextField("$.test_category", as_name="test_category"),
                NumericField("$.confidence_score", as_name="confidence_score"),
                TextField("$.notes", as_name="notes"),
                VectorField(
                    "$.vector",
                    "HNSW",
                    {
                        "TYPE": "FLOAT32",
                        "DIM": dimension,
                        "DISTANCE_METRIC": "COSINE"
                    },
                    as_name="vector"
                )
            )
            
            definition = IndexDefinition(
                prefix=["embedding:"],
                index_type=IndexType.JSON
            )
            
            self.redis_service.redis_client.ft(index_name).create_index(
                schema,
                definition=definition
            )
            logger.info(f"Created HNSW index: {index_name}")
    
    async def auto_embed_generated_dataset(
        self,
        user_id: uuid.UUID,
        template_id: uuid.UUID,
        csv_path: str,
        db: Session,
        batch_size: int = 32
    ) -> str:
        """
        Automatically embed generated CSV dataset using Ollama
        
        Triggered after dataset generation completes.
        
        Args:
            user_id: User ID
            template_id: Template ID used for generation
            csv_path: Path to generated CSV file
            db: Database session
            batch_size: Batch size for embedding (Ollama processes in parallel)
        
        Returns:
            Task ID for tracking
        """
        task_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Starting automatic embedding with Ollama for: {csv_path}", extra={"user_id": user_id})
            
            # Check if Ollama is available
            if not await self.ollama_service.check_ollama_available():
                raise RuntimeError(f"Ollama service not available at {os.getenv('OLLAMA_HOST', 'http://ollama:11434')}. Please start Ollama first.")
            
            # Get user's preferred embedding model
            model_id, dimension = self._get_user_embedding_model(db, user_id)
            logger.info(f"Using embedding model: {model_id}", extra={"user_id": user_id})
            
            # Ensure HNSW index exists for this dimension
            self._ensure_hnsw_index(dimension)
            
            # Fetch template details from PostgreSQL
            template = db.query(Template).filter(
                Template.t_id == template_id,
                Template.u_id == user_id  # Multi-tenant security
            ).first()
            
            template_api_name = template.api_name if template else ""
            template_endpoint = template.endpoint if template else ""
            template_method = template.method if template else "POST"
            logger.info(f"Template: {template_api_name} ({template_method} {template_endpoint})", extra={"user_id": user_id})
            
            # Read CSV
            logger.info("Reading CSV dataset...", extra={"user_id": user_id})
            df = pd.read_csv(csv_path)
            total_rows = len(df)
            logger.info(f"Found {total_rows} rows to embed", extra={"user_id": user_id})
            
            if total_rows == 0:
                logger.warning("CSV is empty, skipping embedding", extra={"user_id": user_id})
                return task_id
            
            # Generate Redis namespace for metadata tracking
            redis_namespace = f"embedding:{user_id}:{template_id}"
            
            # Process in batches
            embedded_count = 0
            
            for i in range(0, total_rows, batch_size):
                batch = df.iloc[i:i + batch_size]
                
                # Prepare texts for embedding
                texts = []
                for _, row in batch.iterrows():
                    # Combine multiple fields for rich context
                    query = row.get('query', '')
                    api = row.get('api', '')
                    notes = row.get('notes', '')
                    
                    text = f"{query} {api} {notes}".strip()
                    if not text:
                        text = f"API test case {i + _}"
                    texts.append(text)
                
                # Generate embeddings using Ollama
                logger.info(f"Embedding batch {i//batch_size + 1}/{(total_rows + batch_size - 1)//batch_size}...", extra={"user_id": user_id})
                embeddings = await self.ollama_service.generate_embeddings_batch(
                    model_name=model_id,
                    texts=texts,
                    batch_size=batch_size
                )
                
                # Store in Redis with JSON format
                for j, (idx, row) in enumerate(batch.iterrows()):
                    if embeddings[j] is None:
                        logger.warning(f"Failed to embed row {idx}, skipping", extra={"user_id": user_id})
                        continue
                    
                    csv_row_id = int(idx)
                    redis_key = self._generate_redis_key(user_id, template_id, csv_row_id)
                    vector = embeddings[j]  # Already a list from Ollama
                    
                    # Store as JSON document for RedisSearch
                    # Use template values from PostgreSQL, CSV values where available
                    
                    # Auto-classify intent if missing
                    intent_type = row.get('intent_type', '')
                    if not intent_type or intent_type == 'unknown' or str(intent_type).lower() == 'nan':
                        from app.services.intent_classification_service import get_intent_from_method
                        intent_type = get_intent_from_method(template_method)
                    
                    # Get confidence score, default based on scenario
                    confidence_score = row.get('confidence_score', None)
                    try:
                        confidence_score = float(confidence_score) if confidence_score is not None else 0.7
                    except (ValueError, TypeError):
                        confidence_score = 0.7
                    
                    document = {
                        "user_id": str(user_id),
                        "t_id": str(template_id),
                        "csv_row_id": csv_row_id,
                        "query": row.get('query', ''),
                        "api": template_api_name,  # From PostgreSQL template
                        "endpoint": template_endpoint,  # From PostgreSQL template
                        "method": template_method,  # From PostgreSQL template
                        "intent_type": intent_type,  # Auto-classified if missing
                        "scenario_type": row.get('scenario_type', row.get('intent_type', 'valid')),  # Fallback
                        "test_category": row.get('test_category', 'valid_flow'),
                        "confidence_score": confidence_score,  # From CSV or default
                        "notes": row.get('notes', ''),
                        "vector": vector,
                        "dimension": dimension,
                        "model": model_id,
                        "embedded_at": datetime.now(timezone.utc).isoformat()
                    }
                    
                    # Store in Redis
                    self.redis_service.redis_client.json().set(redis_key, '$', document)
                    embedded_count += 1
                
                logger.info(f"Embedded {i + len(batch)}/{total_rows} rows", extra={"user_id": user_id})
            
            # Update template metadata with embedding info
            metadata = db.query(Metadata).filter(
                Metadata.t_id == template_id
            ).first()
            
            if metadata:
                # Store embedding metadata as JSONB
                embedding_metadata = {
                    "embedded_with_model": model_id,
                    "embedding_dim": dimension,
                    "redis_namespace": redis_namespace,
                    "total_embedded": embedded_count,
                    "embedded_at": datetime.now(timezone.utc).isoformat(),
                    "csv_path": csv_path,
                    "hnsw_index": self.index_mapping[dimension],
                    "ollama_service": os.getenv("OLLAMA_HOST", "http://ollama:11434")
                }
                
                # Update or create metadata field
                if not metadata.remarks:
                    metadata.remarks = {}
                
                if isinstance(metadata.remarks, dict):
                    metadata.remarks['embedding_info'] = embedding_metadata
                
                db.commit()
                logger.info("Updated template metadata with embedding info", extra={"user_id": user_id})
            
            logger.info(f"Automatic embedding completed: {embedded_count} vectors stored", extra={"user_id": user_id})
            logger.info(f"Redis namespace: {redis_namespace}", extra={"user_id": user_id})
            logger.info(f"Dimension: {dimension}, Index: {self.index_mapping[dimension]}", extra={"user_id": user_id})
            logger.info(f"Ollama model: {model_id}", extra={"user_id": user_id})
            
            return task_id
        
        except Exception as e:
            logger.error(f"Error during automatic embedding: {e}", exc_info=True)
            raise
    
    async def search_similar_test_cases(
        self,
        user_id: uuid.UUID,
        dataset_id: uuid.UUID,
        query: str,
        top_k: int = 10,
        db: AsyncSession = None,
        filter_scenario_type: Optional[str] = None,
        filter_test_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for similar test cases using vector similarity with Ollama
        
        ENFORCES ONE MODEL PER DATASET RULE:
        - Validates that search model matches dataset's embedded model
        - Returns MODEL_MISMATCH structured error if mismatch detected
        
        Args:
            user_id: User ID
            dataset_id: Dataset ID (REQUIRED for model governance)
            query: Search query
            top_k: Number of results to return
            db: Database session (AsyncSession)
            filter_scenario_type: Optional filter
            filter_test_category: Optional filter
        
        Returns:
            Dict with results or MODEL_MISMATCH error structure
        """
        try:
            # 1. Get dataset info to check embedded model
            result = await db.execute(
                select(Dataset).where(
                    Dataset.dataset_id == dataset_id,
                    Dataset.u_id == user_id  # Multi-tenant check
                )
            )
            dataset = result.scalar_one_or_none()
            
            if not dataset:
                return {
                    "error": ErrorCode.DATASET_NOT_FOUND,
                    "message": f"Dataset {dataset_id} not found or you don't have access to it",
                    "dataset_id": str(dataset_id)
                }
            
            # 2. Check if dataset has been embedded
            if dataset.embedding_status == EmbeddingStatus.PENDING:
                return {
                    "error": ErrorCode.NOT_EMBEDDED,
                    "message": "Dataset has not been embedded yet. Start embedding first.",
                    "dataset_id": str(dataset_id)
                }
            
            if dataset.embedding_status == EmbeddingStatus.IN_PROGRESS:
                return {
                    "error": ErrorCode.EMBEDDING_IN_PROGRESS,
                    "message": f"Embedding is in progress ({dataset.embedding_progress}%). Please wait.",
                    "dataset_id": str(dataset_id),
                    "progress": dataset.embedding_progress
                }
            
            if dataset.embedding_status == EmbeddingStatus.FAILED:
                return {
                    "error": ErrorCode.EMBEDDING_FAILED,
                    "message": f"Embedding failed: {dataset.embedding_error}",
                    "dataset_id": str(dataset_id)
                }
            
            # 3. Get user's current preferred model
            current_model_id, current_dimension = await self._get_user_embedding_model_async(db, user_id)
            
            # 4. Get dataset's embedded model
            embedded_model_id = dataset.embedding_model
            embedded_dimension = dataset.embedding_dimension
            
            # 5. ENFORCE MODEL MATCH - Return structured MODEL_MISMATCH error
            if embedded_model_id != current_model_id:
                logger.warning(
                    f"MODEL_MISMATCH: Dataset {dataset_id} embedded with '{embedded_model_id}', "
                    f"but user wants to search with '{current_model_id}'"
                )
                
                mismatch_error = ModelMismatchError(
                    error="MODEL_MISMATCH",
                    message=(
                        f"This dataset was embedded with '{embedded_model_id}' (dim={embedded_dimension}). "
                        f"You are trying to search with '{current_model_id}' (dim={current_dimension}). "
                        f"Vectors from different models are incompatible."
                    ),
                    dataset_id=str(dataset_id),
                    embedded_with_model=embedded_model_id,
                    embedded_with_dimension=embedded_dimension,
                    current_model=current_model_id,
                    current_dimension=current_dimension,
                    embedded_rows=dataset.embedded_rows,
                    reembed_endpoint=f"/api/v1/datasets/{dataset_id}/reembed"
                )
                
                return mismatch_error.model_dump()
            
            # 6. Proceed with search using the MATCHING model
            logger.info(f"Generating query embedding with Ollama ({current_model_id})")
            query_vector = await self.ollama_service.generate_embedding(current_model_id, query)
            
            if not query_vector:
                logger.error("Failed to generate query embedding")
                return {"error": "EMBEDDING_FAILED", "message": "Failed to generate query embedding", "results": []}
            
            # Get HNSW index name
            index_name = self.index_mapping.get(current_dimension)
            if not index_name:
                # Try to find dimension in mapping
                index_name = self.index_mapping.get(embedded_dimension, f"embeddings_{embedded_dimension}")
            
            # Build Redis Search query with vector similarity
            from redis.commands.search.query import Query
            
            # Filter by user_id and template_id (from dataset)
            template_id = dataset.t_id
            escaped_user_id = escape_redis_tag(str(user_id))
            escaped_template_id = escape_redis_tag(str(template_id))
            base_query = f"@user_id:{{{escaped_user_id}}} @template_id:{{{escaped_template_id}}}"
            
            # Add optional filters
            if filter_scenario_type:
                base_query += f" @scenario_type:{{{filter_scenario_type}}}"
            if filter_test_category:
                base_query += f" @test_category:{{{filter_test_category}}}"
            
            # Create KNN query
            query_obj = Query(
                f"({base_query})=>[KNN {top_k} @vector $vec AS score]"
            ).return_fields(
                "user_id", "template_id", "csv_row_id", "query", "api",
                "endpoint", "method", "scenario_type", "test_category",
                "notes", "score"
            ).sort_by("score").dialect(2)
            
            # Execute search
            import time
            start_time = time.time()
            
            results = self.redis_service.redis_client.ft(index_name).search(
                query_obj,
                query_params={"vec": np.array(query_vector, dtype=np.float32).tobytes()}
            )
            
            search_time_ms = int((time.time() - start_time) * 1000)
            
            # Format results
            similar_cases = []
            for doc in results.docs:
                similar_cases.append({
                    "csv_row_id": getattr(doc, 'csv_row_id', None),
                    "query": getattr(doc, 'query', ''),
                    "api": getattr(doc, 'api', ''),
                    "endpoint": getattr(doc, 'endpoint', ''),
                    "method": getattr(doc, 'method', ''),
                    "scenario_type": getattr(doc, 'scenario_type', ''),
                    "test_category": getattr(doc, 'test_category', ''),
                    "notes": getattr(doc, 'notes', ''),
                    "similarity_score": 1 - float(getattr(doc, 'score', 1))  # Convert distance to similarity
                })
            
            logger.info(f"Found {len(similar_cases)} similar test cases in {search_time_ms}ms")
            
            return {
                "success": True,
                "query": query,
                "dataset_id": str(dataset_id),
                "template_id": str(template_id),
                "embedding_model": embedded_model_id,
                "embedding_dimension": embedded_dimension,
                "total_results": len(similar_cases),
                "results": similar_cases,
                "search_time_ms": search_time_ms
            }
        
        except Exception as e:
            logger.error(f"Error searching similar test cases: {e}", exc_info=True)
            return {"error": "SEARCH_ERROR", "message": str(e), "results": []}
    
    def get_embedding_stats(
        self,
        user_id: uuid.UUID,
        template_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Get embedding statistics for a template
        
        Returns:
            Dictionary with embedding stats (count, dimension, model, etc.)
        """
        try:
            # Count keys matching pattern
            pattern = f"embedding:{user_id}:{template_id}:*"
            keys = list(self.redis_service.redis_client.scan_iter(match=pattern, count=100))
            total_embeddings = len(keys)
            
            # Get sample document for metadata
            if keys:
                sample_doc = self.redis_service.redis_client.json().get(keys[0])
                
                return {
                    "total_embeddings": total_embeddings,
                    "model": sample_doc.get("model"),
                    "dimension": sample_doc.get("dimension"),
                    "hnsw_index": self.index_mapping.get(sample_doc.get("dimension")),
                    "redis_namespace": f"embedding:{user_id}:{template_id}",
                    "sample_embedded_at": sample_doc.get("embedded_at")
                }
            
            return {
                "total_embeddings": 0,
                "message": "No embeddings found for this template"
            }
        
        except Exception as e:
            logger.error(f"Error getting embedding stats: {e}")
            return {"error": str(e)}
    
    async def reembed_dataset(
        self,
        user_id: uuid.UUID,
        dataset_id: uuid.UUID,
        db: AsyncSession,
        new_model: Optional[str] = None,
        force: bool = False,
        chunk_size: int = 100
    ) -> Dict[str, Any]:
        """
        Re-embed a dataset with a new model
        
        This will:
        1. Validate the dataset exists and user has access
        2. Delete ALL existing embeddings for the dataset
        3. Update dataset's embedding_model field
        4. Run embedding in background thread
        
        Args:
            user_id: User ID
            dataset_id: Dataset ID
            db: Database session (AsyncSession)
            new_model: New embedding model (uses user's default if None)
            force: Force re-embed even if same model
            chunk_size: Rows per embedding batch
        
        Returns:
            Dict with task info or error
        """
        try:
            # 1. Get dataset
            result = await db.execute(
                select(Dataset).where(
                    Dataset.dataset_id == dataset_id,
                    Dataset.u_id == user_id
                )
            )
            dataset = result.scalar_one_or_none()
            
            if not dataset:
                return {
                    "error": ErrorCode.DATASET_NOT_FOUND,
                    "message": f"Dataset {dataset_id} not found",
                    "success": False
                }
            
            # 2. Check if embedding is already in progress
            if dataset.embedding_status == EmbeddingStatus.IN_PROGRESS:
                return {
                    "error": ErrorCode.EMBEDDING_IN_PROGRESS,
                    "message": f"Embedding is already in progress ({dataset.embedding_progress}%)",
                    "success": False,
                    "task_id": dataset.task_id
                }
            
            # 3. Get new model info
            if new_model:
                try:
                    model_info = get_embedding_model_info(new_model)
                    model_id = new_model
                    dimension = model_info.dimension
                except ValueError:
                    return {
                        "error": ErrorCode.INVALID_MODEL,
                        "message": f"Invalid embedding model: {new_model}",
                        "success": False
                    }
            else:
                model_id, dimension = await self._get_user_embedding_model_async(db, user_id)
            
            # 4. Check if re-embedding is necessary
            if not force and dataset.embedding_model == model_id and dataset.embedding_status == EmbeddingStatus.COMPLETED:
                return {
                    "error": "ALREADY_EMBEDDED",
                    "message": f"Dataset is already embedded with {model_id}. Use force=True to re-embed.",
                    "success": False,
                    "current_model": model_id,
                    "embedded_rows": dataset.embedded_rows
                }
            
            # 5. Delete existing Redis embeddings
            logger.info(f"Deleting existing embeddings for dataset {dataset_id}")
            pattern = f"embedding:{user_id}:{dataset.t_id}:*"
            deleted_count = 0
            for key in self.redis_service.redis_client.scan_iter(match=pattern, count=100):
                self.redis_service.redis_client.delete(key)
                deleted_count += 1
            logger.info(f"Deleted {deleted_count} existing embeddings")
            
            # 6. Update dataset status
            dataset.embedding_model = model_id
            dataset.embedding_dimension = dimension
            dataset.embedding_status = EmbeddingStatus.IN_PROGRESS
            dataset.embedding_progress = 0
            dataset.embedded_rows = 0
            dataset.embedding_started_at = datetime.now(timezone.utc).replace(tzinfo=None)
            dataset.embedding_completed_at = None
            dataset.embedding_error = None
            await db.commit()
            
            # 7. Generate a task ID for tracking
            import secrets
            task_id = f"embed_{secrets.token_hex(8)}"
            
            # 8. Store task ID and start background embedding
            dataset.task_id = task_id
            await db.commit()
            
            # 9. Start background embedding in a separate thread
            import threading
            embed_thread = threading.Thread(
                target=reembed_dataset_sync,
                args=(
                    str(dataset_id),
                    str(user_id),
                    model_id,
                    dimension,
                    chunk_size,
                    dataset.csv_path
                ),
                daemon=True
            )
            embed_thread.start()
            
            # 10. Estimate time
            estimated_seconds = (dataset.total_rows / chunk_size) * 5  # ~5 seconds per chunk
            
            logger.info(f"Started re-embedding: task_id={task_id}, model={model_id}")
            
            return {
                "success": True,
                "message": f"Re-embedding started with {model_id}",
                "dataset_id": str(dataset_id),
                "new_model": model_id,
                "new_dimension": dimension,
                "task_id": task_id,
                "total_rows": dataset.total_rows,
                "estimated_time_seconds": int(estimated_seconds),
                "warnings": [
                    f"Deleted {deleted_count} existing embeddings"
                ] if deleted_count > 0 else None
            }
        
        except Exception as e:
            logger.error(f"Error starting re-embed: {e}", exc_info=True)
            return {"error": "REEMBED_ERROR", "message": str(e), "success": False}
    
    async def get_dataset_embedding_status(
        self,
        user_id: uuid.UUID,
        dataset_id: uuid.UUID,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get detailed embedding status for a dataset
        
        Returns:
            Dict with status, progress, counts, etc.
        """
        try:
            result = await db.execute(
                select(Dataset).where(
                    Dataset.dataset_id == dataset_id,
                    Dataset.u_id == user_id
                )
            )
            dataset = result.scalar_one_or_none()
            
            if not dataset:
                return {
                    "error": ErrorCode.DATASET_NOT_FOUND,
                    "message": f"Dataset {dataset_id} not found"
                }
            
            # Calculate estimated completion
            estimated_completion = None
            if dataset.embedding_status == EmbeddingStatus.IN_PROGRESS and dataset.embedding_started_at:
                elapsed = (datetime.now(timezone.utc) - dataset.embedding_started_at).total_seconds()
                if dataset.embedding_progress > 0:
                    total_estimated = elapsed / (dataset.embedding_progress / 100)
                    remaining = total_estimated - elapsed
                    estimated_completion = (datetime.now(timezone.utc) + timedelta(seconds=remaining)).isoformat()
            
            return {
                "dataset_id": str(dataset_id),
                "status": dataset.embedding_status,
                "progress": dataset.embedding_progress,
                "total_rows": dataset.total_rows,
                "embedded_rows": dataset.embedded_rows,
                "embedding_model": dataset.embedding_model,
                "embedding_dimension": dataset.embedding_dimension,
                "started_at": dataset.embedding_started_at.isoformat() if dataset.embedding_started_at else None,
                "completed_at": dataset.embedding_completed_at.isoformat() if dataset.embedding_completed_at else None,
                "estimated_completion": estimated_completion,
                "error_message": dataset.embedding_error,
                "task_id": dataset.task_id
            }
        
        except Exception as e:
            logger.error(f"Error getting embedding status: {e}")
            return {"error": str(e)}


# Singleton
_enhanced_embedding_service = None


def get_enhanced_embedding_service() -> EnhancedEmbeddingService:
    """Get or create singleton instance"""
    global _enhanced_embedding_service
    if _enhanced_embedding_service is None:
        _enhanced_embedding_service = EnhancedEmbeddingService()
    return _enhanced_embedding_service


# Background embedding task - runs synchronously in FastAPI BackgroundTask
def create_embedding_task(csv_path: str, user_id: str, template_id: str, model_name: str = None):
    """
    Background task for embedding creation
    
    Creates embeddings for a CSV dataset using Ollama embedding models.
    Runs synchronously within a FastAPI BackgroundTask context.
    """
    from sqlalchemy.engine import make_url
    from app.core.config import settings
    from app.services.redis_vector_service import RedisVectorService

    try:
        logger.info(f"Starting background embedding task: {template_id}")

        # 1. Validate DB Connection URL
        sync_db_url = settings.database_url.replace("+asyncpg", "")
        make_url(sync_db_url)  # Lightweight URL validation without creating a connection pool

        # 2. Parse and validate IDs
        try:
            uuid.UUID(user_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid user_id (not a UUID): {user_id}")
            return {
                "status": "failed",
                "message": f"Invalid user_id: {user_id}. Must be a valid UUID.",
                "csv_path": csv_path,
                "user_id": user_id,
                "template_id": template_id
            }
        
        try:
            parsed_template_id = uuid.UUID(template_id)
        except (ValueError, TypeError):
            parsed_template_id = uuid.uuid5(uuid.NAMESPACE_DNS, str(template_id))
            logger.info(f"Non-UUID template_id '{template_id}' converted to UUID: {parsed_template_id}")
        
        # 3. Run embedding synchronously using ollama service
        # Read CSV
        df = pd.read_csv(csv_path)
        if len(df) == 0:
            logger.warning("⚠️ CSV is empty, nothing to embed")
            return {"status": "completed", "task_id": f"embed_empty_{template_id}", "embedded_rows": 0}
        
        # Get embedding model
        model_id = model_name or "nomic-embed-text"

        # Initialize services
        redis_service = RedisVectorService()
        
        # Generate task ID
        import secrets
        task_id = f"embed_{secrets.token_hex(8)}"
        
        # Prepare texts from CSV rows
        texts = []
        for row_idx, row in df.iterrows():
            query = row.get('query', '')
            api = row.get('api', '')
            notes = row.get('notes', '')
            text = f"{query} {api} {notes}".strip() or f"API test case (row_id: {row_idx})"
            texts.append(text)
        
        # Generate embeddings using PARALLEL async HTTP calls for speed
        import httpx
        import asyncio
        
        embedded_count = 0
        batch_size = 50  # Larger batches for faster embedding
        
        logger.info(f"Embedding {len(texts)} rows in batches of {batch_size} (PARALLEL)...")
        
        async def embed_single(client: httpx.AsyncClient, text: str, model: str):
            """Embed a single text asynchronously"""
            try:
                response = await client.post(
                    f"{os.getenv('OLLAMA_HOST', 'http://ollama:11434')}/api/embeddings",
                    json={"model": model, "prompt": text},
                    timeout=60.0
                )
                if response.status_code == 200:
                    return response.json().get("embedding", [])
            except Exception as e:
                logger.debug(f"Embedding failed: {e}")
            return None
        
        async def embed_batch_parallel(batch_texts: list, model: str):
            """Embed all texts in batch in parallel"""
            async with httpx.AsyncClient() as client:
                tasks = [embed_single(client, text, model) for text in batch_texts]
                return await asyncio.gather(*tasks)
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # Run parallel embedding
            batch_embeddings = asyncio.run(embed_batch_parallel(batch_texts, model_id))
            
            # Store in Redis
            for j, embedding in enumerate(batch_embeddings):
                if embedding is None:
                    continue
                    
                row_idx = i + j
                row = df.iloc[row_idx]
                csv_row_id = row_idx
                
                redis_key = f"embedding:{user_id}:{template_id}:{csv_row_id}"
                
                document = {
                    "user_id": str(user_id),
                    "t_id": str(template_id),  # Changed from template_id to t_id to match search
                    "csv_row_id": csv_row_id,
                    "query": row.get('query', ''),
                    "api": row.get('api', ''),
                    "endpoint": row.get('endpoint', ''),
                    "method": row.get('method', ''),
                    "scenario_type": row.get('scenario_type', 'valid'),
                    "test_category": row.get('test_category', 'valid_flow'),
                    "notes": row.get('notes', ''),
                    "vector": embedding,
                    "dimension": len(embedding),
                    "model": model_id,
                    "embedded_at": datetime.now(timezone.utc).isoformat()
                }
                
                redis_service.redis_client.json().set(redis_key, '$', document)
                embedded_count += 1
            
            logger.info(f"Embedded {embedded_count}/{len(texts)} rows")
        
        logger.info(f"Background embedding task completed: {embedded_count} rows embedded")
        
        return {
            "status": "completed",
            "task_id": task_id,
            "csv_path": csv_path,
            "user_id": user_id,
            "template_id": template_id,
            "embedded_rows": embedded_count
        }
        
    except Exception as e:
        logger.error(f"Embedding creation failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "message": str(e),
            "csv_path": csv_path,
            "user_id": user_id,
            "template_id": template_id
        }


# ============= BACKGROUND RE-EMBEDDING TASK =============

def reembed_dataset_sync(
    dataset_id: str,
    user_id: str,
    model_id: str,
    dimension: int,
    chunk_size: int,
    csv_path: str
):
    """
    Background task for re-embedding a dataset with chunking and progress tracking
    
    Features:
    - Processes in chunks (50-200 rows per chunk)
    - Updates progress (0-100%) after each chunk
    - Error recovery: failed rows are tracked, job continues
    - Atomic completion: status only set to 'completed' when 100% done
    
    Args:
        dataset_id: Dataset UUID string
        user_id: User UUID string
        model_id: Embedding model ID (e.g., "nomic-embed-text")
        dimension: Vector dimension (384, 768, 1024)
        chunk_size: Rows per chunk (default 100)
        csv_path: Path to CSV file
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    from app.models.database_models import Dataset
    from app.services.redis_vector_service import RedisVectorService
    from app.services.ollama_embedding_service import get_ollama_service
    
    try:
        logger.info(f"Starting re-embedding task: dataset={dataset_id}, model={model_id}")
        
        # 1. Create Synchronous DB Connection
        sync_db_url = settings.database_url.replace("+asyncpg", "")
        engine = create_engine(sync_db_url)
        SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # 2. Initialize services
        redis_service = RedisVectorService()
        ollama_service = get_ollama_service()
        
        # 3. Read CSV
        df = pd.read_csv(csv_path)
        total_rows = len(df)
        
        if total_rows == 0:
            logger.warning("CSV is empty, nothing to embed")
            # Update status to completed with 0 rows
            db = SyncSessionLocal()
            try:
                dataset = db.query(Dataset).filter(Dataset.dataset_id == uuid.UUID(dataset_id)).first()
                if dataset:
                    dataset.embedding_status = "completed"
                    dataset.embedding_progress = 100
                    dataset.embedding_completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    db.commit()
            finally:
                db.close()
            return {"status": "completed", "embedded_rows": 0}
        
        # 4. Ensure HNSW index exists
        index_mapping = {384: "embeddings_384", 768: "embeddings_768", 1024: "embeddings_1024"}
        index_name = index_mapping.get(dimension, f"embeddings_{dimension}")
        
        try:
            redis_service.redis_client.ft(index_name).info()
        except Exception:
            # Create index if not exists
            from redis.commands.search.field import VectorField, TextField, NumericField
            from redis.commands.search.indexDefinition import IndexDefinition, IndexType
            
            schema = (
                TextField("$.user_id", as_name="user_id"),
                TextField("$.template_id", as_name="template_id"),
                NumericField("$.csv_row_id", as_name="csv_row_id"),
                TextField("$.query", as_name="query"),
                TextField("$.api", as_name="api"),
                TextField("$.scenario_type", as_name="scenario_type"),
                TextField("$.test_category", as_name="test_category"),
                VectorField(
                    "$.vector", "HNSW",
                    {"TYPE": "FLOAT32", "DIM": dimension, "DISTANCE_METRIC": "COSINE"},
                    as_name="vector"
                )
            )
            definition = IndexDefinition(prefix=["embedding:"], index_type=IndexType.JSON)
            redis_service.redis_client.ft(index_name).create_index(schema, definition=definition)
            logger.info(f"Created HNSW index: {index_name}")
        
        # 5. Get template_id from dataset
        db = SyncSessionLocal()
        try:
            dataset = db.query(Dataset).filter(Dataset.dataset_id == uuid.UUID(dataset_id)).first()
            template_id = str(dataset.t_id) if dataset else None
        finally:
            db.close()
        
        if not template_id:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        # 6. Process in chunks with progress tracking
        embedded_count = 0
        failed_count = 0
        failed_row_ids = []
        num_chunks = (total_rows + chunk_size - 1) // chunk_size
        
        async def embed_batch(texts: List[str]) -> List[Optional[List[float]]]:
            """Generate embeddings for a batch of texts"""
            return await ollama_service.generate_embeddings_batch(
                model_name=model_id,
                texts=texts,
                batch_size=len(texts)
            )
        
        for chunk_idx in range(num_chunks):
            start_idx = chunk_idx * chunk_size
            end_idx = min(start_idx + chunk_size, total_rows)
            batch = df.iloc[start_idx:end_idx]
            
            logger.info(f"Processing chunk {chunk_idx + 1}/{num_chunks} (rows {start_idx}-{end_idx})")
            
            # Prepare texts
            texts = []
            for _, row in batch.iterrows():
                query = row.get('query', '')
                api = row.get('api', '')
                notes = row.get('notes', '')
                text = f"{query} {api} {notes}".strip() or f"API test case row {start_idx + _}"
                texts.append(text)
            
            # Generate embeddings
            try:
                embeddings = asyncio.run(embed_batch(texts))
            except Exception as e:
                logger.error(f"Embedding batch failed: {e}")
                # Track all rows in this batch as failed
                for idx in range(start_idx, end_idx):
                    failed_count += 1
                    failed_row_ids.append(idx)
                continue
            
            # Store in Redis
            for j, (idx, row) in enumerate(batch.iterrows()):
                if embeddings[j] is None:
                    failed_count += 1
                    failed_row_ids.append(int(idx))
                    continue
                
                csv_row_id = int(idx)
                redis_key = f"embedding:{user_id}:{template_id}:{csv_row_id}"
                
                document = {
                    "user_id": user_id,
                    "t_id": template_id,  # Changed from template_id to t_id to match search
                    "csv_row_id": csv_row_id,
                    "query": row.get('query', ''),
                    "api": row.get('api', ''),
                    "endpoint": row.get('endpoint', ''),
                    "method": row.get('method', ''),
                    "scenario_type": row.get('scenario_type', 'valid'),
                    "test_category": row.get('test_category', 'valid_flow'),
                    "notes": row.get('notes', ''),
                    "vector": embeddings[j],
                    "dimension": dimension,
                    "model": model_id,
                    "embedded_at": datetime.now(timezone.utc).isoformat()
                }
                
                redis_service.redis_client.json().set(redis_key, '$', document)
                embedded_count += 1
            
            # 7. Update progress in database
            progress = int(((chunk_idx + 1) / num_chunks) * 100)
            
            db = SyncSessionLocal()
            try:
                dataset = db.query(Dataset).filter(Dataset.dataset_id == uuid.UUID(dataset_id)).first()
                if dataset:
                    dataset.embedding_progress = progress
                    dataset.embedded_rows = embedded_count
                    db.commit()
                    logger.info(f"Progress: {progress}% ({embedded_count}/{total_rows} rows)")
            finally:
                db.close()
        
        # 8. Mark as completed
        db = SyncSessionLocal()
        try:
            dataset = db.query(Dataset).filter(Dataset.dataset_id == uuid.UUID(dataset_id)).first()
            if dataset:
                dataset.embedding_status = "completed"
                dataset.embedding_progress = 100
                dataset.embedded_rows = embedded_count
                dataset.embedding_completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
                
                if failed_count > 0:
                    dataset.embedding_error = f"{failed_count} rows failed to embed"
                
                db.commit()
        finally:
            db.close()
        
        logger.info(f"Re-embedding completed: {embedded_count} embedded, {failed_count} failed")
        
        return {
            "status": "completed",
            "dataset_id": dataset_id,
            "model": model_id,
            "dimension": dimension,
            "embedded_rows": embedded_count,
            "failed_rows": failed_count,
            "failed_row_ids": failed_row_ids[:100] if failed_row_ids else []  # Limit to first 100
        }
    
    except Exception as e:
        logger.error(f"Re-embedding task failed: {e}", exc_info=True)
        
        # Update dataset status to failed
        try:
            sync_db_url = settings.database_url.replace("+asyncpg", "")
            engine = create_engine(sync_db_url)
            SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            
            db = SyncSessionLocal()
            try:
                dataset = db.query(Dataset).filter(Dataset.dataset_id == uuid.UUID(dataset_id)).first()
                if dataset:
                    dataset.embedding_status = "failed"
                    dataset.embedding_error = str(e)
                    db.commit()
            finally:
                db.close()
        except Exception as db_error:
            logger.error(f"Failed to update dataset status: {db_error}")
        
        return {
            "status": "failed",
            "dataset_id": dataset_id,
            "error": str(e)
        }