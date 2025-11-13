"""Redis Vector Service - Vector embeddings storage and search"""

import redis
import numpy as np
from typing import List, Dict, Optional, Tuple
import uuid
from sentence_transformers import SentenceTransformer

from app.core.config import REDIS_HOST, REDIS_PORT
from app.core.logger import logger


class RedisVectorService:
    """Manages vector embeddings in Redis with HNSW index"""
    
    def __init__(self):
        self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=False)
        self.model = None
        self.vector_dimension = 384  # BAAI/bge-small-en-v1.5
        self.index_name = "embeddings_idx"
    
    def _get_model(self):
        """Lazy load embedding model"""
        if self.model is None:
            logger.info("Loading model: BAAI/bge-small-en-v1.5")
            self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")
            self.vector_dimension = self.model.get_sentence_embedding_dimension()
        return self.model
    
    def _generate_redis_key(self, user_id: uuid.UUID, t_id: Optional[uuid.UUID] = None, 
                           csv_id: Optional[uuid.UUID] = None) -> str:
        """Generate Redis key: embedding:{user_id}:{t_id}:{csv_id}"""
        return f"embedding:{user_id}:{t_id or 'none'}:{csv_id or 'none'}"
    
    def create_vector_index(self) -> bool:
        """Create Redis HNSW vector index"""
        try:
            try:
                self.redis_client.execute_command("FT.INFO", self.index_name)
                logger.info(f"Index '{self.index_name}' exists")
                return True
            except redis.exceptions.ResponseError:
                pass
            
            self.redis_client.execute_command(
                "FT.CREATE", self.index_name, "ON", "HASH", "PREFIX", "1", "embedding:",
                "SCHEMA",
                "vector", "VECTOR", "HNSW", "6", "TYPE", "FLOAT32", "DIM", str(self.vector_dimension), 
                "DISTANCE_METRIC", "COSINE",
                "user_id", "TAG", "t_id", "TAG", "csv_id", "TAG", "query", "TEXT"
            )
            logger.info(f"✅ Created index: {self.index_name}")
            return True
        except Exception as e:
            logger.error(f"Index creation failed: {e}")
            return False
    
    def store_embedding(self, user_id: uuid.UUID, query: str, t_id: Optional[uuid.UUID] = None,
                       csv_id: Optional[uuid.UUID] = None, vector: Optional[np.ndarray] = None) -> Tuple[str, np.ndarray]:
        """Store embedding in Redis"""
        if vector is None:
            vector = np.asarray(self._get_model().encode(query, normalize_embeddings=True), dtype=np.float32)
        
        redis_key = self._generate_redis_key(user_id, t_id, csv_id)
        self.redis_client.hset(redis_key, mapping={
            "vector": vector.tobytes(),
            "user_id": str(user_id),
            "t_id": str(t_id) if t_id else "",
            "csv_id": str(csv_id) if csv_id else "",
            "query": query,
            "dimension": str(self.vector_dimension)
        })
        logger.info(f"Stored: {redis_key}")
        return redis_key, vector
    
    def get_embedding(self, redis_key: str) -> Optional[Dict]:
        """Retrieve embedding from Redis"""
        data = self.redis_client.hgetall(redis_key)
        if not data:
            return None
        
        result = {}
        for key, value in data.items():
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            if key_str == "vector":
                result["vector"] = np.frombuffer(value, dtype=np.float32)
            else:
                result[key_str] = value.decode('utf-8') if isinstance(value, bytes) else value
        return result
    
    def delete_embedding(self, redis_key: str) -> bool:
        """Delete embedding from Redis"""
        result = self.redis_client.delete(redis_key) > 0
        if result:
            logger.info(f"Deleted: {redis_key}")
        return result
    
    def search_similar(self, query: str, user_id: Optional[uuid.UUID] = None,
                      t_id: Optional[uuid.UUID] = None, top_k: int = 5) -> List[Dict]:
        """Search for similar embeddings using vector similarity"""
        try:
            query_vector = np.asarray(self._get_model().encode(query, normalize_embeddings=True), dtype=np.float32)
            
            filter_parts = []
            if user_id:
                filter_parts.append(f"@user_id:{{{str(user_id)}}}")
            if t_id:
                filter_parts.append(f"@t_id:{{{str(t_id)}}}")
            filter_str = " ".join(filter_parts) if filter_parts else "*"
            
            results = self.redis_client.execute_command(
                "FT.SEARCH", self.index_name, filter_str,
                "RETURN", "4", "query", "user_id", "t_id", "csv_id",
                "SORTBY", "__vector_score", "LIMIT", "0", str(top_k), "DIALECT", "2",
                "PARAMS", "2", "vec", query_vector.tobytes()
            )
            
            parsed = []
            if results and len(results) > 1:
                for i in range(1, len(results), 2):
                    if i + 1 < len(results):
                        redis_key = results[i].decode('utf-8') if isinstance(results[i], bytes) else results[i]
                        fields = results[i + 1]
                        result_dict = {"redis_key": redis_key}
                        
                        for j in range(0, len(fields), 2):
                            if j + 1 < len(fields):
                                field_name = fields[j].decode('utf-8') if isinstance(fields[j], bytes) else fields[j]
                                field_value = fields[j + 1].decode('utf-8') if isinstance(fields[j + 1], bytes) else fields[j + 1]
                                result_dict[field_name] = field_value
                        parsed.append(result_dict)
            
            logger.info(f"Found {len(parsed)} similar embeddings")
            return parsed
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def count_embeddings(self, user_id: Optional[uuid.UUID] = None, t_id: Optional[uuid.UUID] = None) -> int:
        """Count embeddings with optional filters"""
        try:
            filter_parts = []
            if user_id:
                filter_parts.append(f"@user_id:{{{str(user_id)}}}")
            if t_id:
                filter_parts.append(f"@t_id:{{{str(t_id)}}}")
            filter_str = " ".join(filter_parts) if filter_parts else "*"
            
            results = self.redis_client.execute_command("FT.SEARCH", self.index_name, filter_str, "LIMIT", "0", "0")
            return results[0] if results else 0
        except Exception as e:
            logger.error(f"Count failed: {e}")
            return 0
    
    def delete_user_embeddings(self, user_id: uuid.UUID) -> int:
        """Delete all embeddings for a user"""
        keys = self.redis_client.keys(f"embedding:{user_id}:*")
        if keys:
            deleted = self.redis_client.delete(*keys)
            logger.info(f"Deleted {deleted} embeddings for user {user_id}")
            return deleted
        return 0
    
    def delete_template_embeddings(self, user_id: uuid.UUID, t_id: uuid.UUID) -> int:
        """Delete all embeddings for a template"""
        keys = self.redis_client.keys(f"embedding:{user_id}:{t_id}:*")
        if keys:
            deleted = self.redis_client.delete(*keys)
            logger.info(f"Deleted {deleted} embeddings for template {t_id}")
            return deleted
        return 0
    
    def health_check(self) -> bool:
        """Check Redis connection"""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# Singleton
_redis_vector_service = None

def get_redis_vector_service() -> RedisVectorService:
    global _redis_vector_service
    if _redis_vector_service is None:
        _redis_vector_service = RedisVectorService()
        _redis_vector_service.create_vector_index()
    return _redis_vector_service
