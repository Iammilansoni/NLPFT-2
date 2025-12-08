"""Redis Vector Service - Vector embeddings storage and search using Ollama"""

import redis
import numpy as np
from typing import List, Dict, Optional, Tuple, Union
import uuid
from datetime import datetime

from redis.commands.search.field import VectorField, TextField, NumericField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query

from app.core.config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, MODEL_NAME
from app.core.logger import logger
from app.core.redis_security import (
    RedisKeyValidator, 
    validate_embedding_access, 
    RedisAccessDeniedError
)


class RedisVectorService:
    """Manages vector embeddings in Redis with HNSW index - Uses Ollama for embeddings"""
    
    def __init__(self):
        self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=False)
        self.model = None
        # Default fallback (will be overridden by dynamic model loading)
        self.vector_dimension = 384  
        self.index_name = "embeddings_idx" # Legacy index name
        
        # Mapping dimensions to index names (aligns with EnhancedEmbeddingService)
        self.index_mapping = {
            384: "embeddings_384",
            768: "embeddings_768",
            1024: "embeddings_1024"
        }
    
    def _get_model(self, model_name: str = None):
        """
        Get embedding model using Ollama.
        If model_name is provided, loads that specific model.
        Otherwise loads the default model.
        """
        from app.nlp.embedding_model import OllamaEmbeddingModel
        
        target_model = model_name or "nomic-embed-text"
        logger.info(f"Using Ollama model: {target_model}")
        return OllamaEmbeddingModel(target_model)

    def get_index_name(self, dimension: int) -> str:
        """Get index name for a specific dimension"""
        return self.index_mapping.get(dimension, f"embeddings_{dimension}")

    def create_vector_index(self, dimension: int = 384) -> bool:
        """
        Create Redis vector index for a specific dimension
        """
        index_name = self.get_index_name(dimension)
        
        try:
            # Check if index exists
            self.redis_client.ft(index_name).info()
            logger.debug(f"Index {index_name} already exists")
            return True
        except:
            logger.info(f"Creating index {index_name} for dimension {dimension}")
            
            schema = (
                TextField("$.user_id", as_name="user_id"),
                TextField("$.t_id", as_name="t_id"), # Template ID
                TextField("$.csv_id", as_name="csv_id"),
                TextField("$.query", as_name="query"),
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
                prefix=[f"embedding:"],
                index_type=IndexType.JSON
            )
            
            try:
                self.redis_client.ft(index_name).create_index(
                    schema,
                    definition=definition
                )
                logger.info(f"✅ Created index: {index_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to create index {index_name}: {e}")
                return False

    def store_embedding(self, user_id: uuid.UUID, query: str, t_id: Optional[uuid.UUID] = None,
                       csv_id: Optional[uuid.UUID] = None, vector: Optional[np.ndarray] = None,
                       model_name: str = None) -> Tuple[str, np.ndarray]:
        """
        Store embedding in Redis
        """
        # Generate vector if not provided
        if vector is None:
            model = self._get_model(model_name)
            vector = model.encode(query, normalize_embeddings=True)
            
        # Convert to numpy array if it's a tensor
        if hasattr(vector, 'numpy'):
            vector = vector.numpy()
        vector = np.asarray(vector, dtype=np.float32)

        dimension = vector.shape[0]
        
        # Ensure index exists for this dimension
        self.create_vector_index(dimension)
        
        # Generate safe key using validator
        validator = RedisKeyValidator()
        key = validator.generate_safe_embedding_key(user_id, t_id, csv_id)
        
        # If key already exists (collision), append uuid
        if self.redis_client.exists(key):
             key = f"{key}:{str(uuid.uuid4())[:8]}"
        
        # Create document
        doc = {
            "user_id": str(user_id),
            "query": query,
            "vector": vector.tolist(),
            "dimension": dimension,
            "model": model_name or "unknown",
            "created_at": datetime.utcnow().isoformat()
        }
        
        if t_id:
            doc["t_id"] = str(t_id)
        if csv_id:
            doc["csv_id"] = str(csv_id)
            
        # Store in Redis
        self.redis_client.json().set(key, '$', doc)
        logger.info(f"Stored embedding: {key}")
        
        return key, vector

    def get_embedding(self, redis_key: str, user_id: Optional[uuid.UUID] = None) -> Optional[Dict]:
        """
        Retrieve embedding from Redis
        """
        # Validate access if user_id provided
        if user_id:
            try:
                validate_embedding_access(redis_key, user_id)
            except RedisAccessDeniedError as e:
                logger.error(f"Access denied: {e}")
                return None
        
        data = self.redis_client.json().get(redis_key)
        if not data:
            return None
            
        # Convert vector back to numpy if needed, but returning dict is usually fine
        return data

    def search_similar(self, query: str, user_id: Optional[uuid.UUID] = None,
                      t_id: Optional[uuid.UUID] = None, top_k: int = 5,
                      model_name: str = None) -> List[Dict]:
        """
        Search for similar embeddings
        """
        # Encode query
        model = self._get_model(model_name)
        query_vector = model.encode(query, normalize_embeddings=True)
        
        if hasattr(query_vector, 'numpy'):
            query_vector = query_vector.numpy()
        query_vector = np.asarray(query_vector, dtype=np.float32)
        
        dimension = query_vector.shape[0]
        index_name = self.get_index_name(dimension)
        
        # Build query
        filter_query = "*"
        if user_id:
            filter_query = f"@user_id:{{{user_id}}}"
            if t_id:
                filter_query += f" @t_id:{{{t_id}}}"
                
        q = Query(f"({filter_query})=>[KNN {top_k} @vector $vec AS vector_score]")\
            .sort_by("vector_score")\
            .return_fields("vector_score", "query", "user_id", "t_id", "csv_id")\
            .dialect(2)
            
        params = {"vec": query_vector.tobytes()}
        
        try:
            results = self.redis_client.ft(index_name).search(q, query_params=params)
            
            return [{
                "query": doc.query,
                "score": 1 - float(doc.vector_score), # Convert distance to similarity
                "user_id": getattr(doc, "user_id", None),
                "t_id": getattr(doc, "t_id", None),
                "csv_id": getattr(doc, "csv_id", None),
                "redis_key": doc.id
            } for doc in results.docs]
            
        except Exception as e:
            logger.error(f"Search failed on index {index_name}: {e}")
            # If index doesn't exist, return empty list
            return []

    def delete_embedding(self, redis_key: str, user_id: Optional[uuid.UUID] = None) -> bool:
        """Delete embedding from Redis"""
        if user_id:
            try:
                validate_embedding_access(redis_key, user_id)
            except RedisAccessDeniedError:
                return False
                
        return bool(self.redis_client.delete(redis_key))

    def delete_template_embeddings(self, user_id: uuid.UUID, template_id: uuid.UUID) -> int:
        """Delete all embeddings for a template"""
        # Scan for keys matching the pattern
        # Note: RedisKeyValidator generates keys like embedding:{user_id}:{t_id}:{csv_id}
        # So we can match embedding:{user_id}:{template_id}:*
        
        pattern = f"embedding:{user_id}:{template_id}:*"
        keys = []
        cursor = '0'
        while cursor != 0:
            cursor, batch = self.redis_client.scan(cursor=cursor, match=pattern, count=100)
            keys.extend(batch)
            
        if keys:
            self.redis_client.delete(*keys)
            logger.info(f"Deleted {len(keys)} embeddings for template {template_id}")
            return len(keys)
        return 0

    def count_embeddings(self, user_id: uuid.UUID, t_id: Optional[uuid.UUID] = None) -> int:
        """Count embeddings for a user/template"""
        total = 0
        # We need to check all indices since we don't know which dimension the user used
        for dim, index_name in self.index_mapping.items():
            try:
                filter_query = f"@user_id:{{{user_id}}}"
                if t_id:
                    filter_query += f" @t_id:{{{t_id}}}"
                
                # Use limit 0 to just get count
                q = Query(filter_query).no_content().dialect(2)
                res = self.redis_client.ft(index_name).search(q)
                total += res.total
            except:
                pass
        return total

    def health_check(self) -> bool:
        try:
            self.redis_client.ping()
            return True
        except:
            return False


# Singleton
_redis_vector_service = None

def get_redis_vector_service() -> RedisVectorService:
    global _redis_vector_service
    if _redis_vector_service is None:
        _redis_vector_service = RedisVectorService()
        # Ensure default index exists
        _redis_vector_service.create_vector_index(384)
    return _redis_vector_service
