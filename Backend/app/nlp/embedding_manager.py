"""
Embedding Manager - Handle embeddings and Redis vector operations
Uses BAAI/bge-small-en-v1.5 for embeddings and Redis for vector storage
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np
import redis
from redis.commands.search.field import VectorField, TextField, NumericField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from sentence_transformers import SentenceTransformer
from app.core.config import settings, REDIS_HOST, REDIS_PORT, INDEX_NAME, MODEL_NAME
from app.core.logger import logger


class EmbeddingManager:
    """
    Manage embeddings and Redis vector database operations
    """
    
    def __init__(
        self,
        model_name: str = MODEL_NAME,
        redis_host: str = REDIS_HOST,
        redis_port: int = REDIS_PORT,
        index_name: str = INDEX_NAME
    ):
        """
        Initialize the embedding manager
        
        Args:
            model_name: Name of the sentence transformer model
            redis_host: Redis host
            redis_port: Redis port
            index_name: Name of the Redis vector index
        """
        self.model_name = model_name
        self.index_name = index_name
        
        # Load embedding model
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self.embedding_dim}")
        
        # Connect to Redis
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=False
        )
        
        # Test connection
        try:
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        
        # Create index if it doesn't exist
        self._create_index()
    
    def _create_index(self):
        """
        Create Redis vector index if it doesn't exist
        """
        try:
            # Check if index exists
            self.redis_client.ft(self.index_name).info()
            logger.info(f"Index {self.index_name} already exists")
        except:
            # Create index
            logger.info(f"Creating index {self.index_name}")
            
            schema = (
                VectorField(
                    "embedding",
                    "HNSW",
                    {
                        "TYPE": "FLOAT32",
                        "DIM": self.embedding_dim,
                        "DISTANCE_METRIC": "COSINE"
                    }
                ),
                TextField("intent"),
                TextField("slots_json"),
                TextField("query"),
                TextField("hash_id"),
                TextField("api_name"),
                TextField("endpoint"),
                NumericField("template_version"),
                TextField("created_at"),
                NumericField("confidence")
            )
            
            definition = IndexDefinition(
                prefix=[f"api:"],
                index_type=IndexType.HASH
            )
            
            self.redis_client.ft(self.index_name).create_index(
                fields=schema,
                definition=definition
            )
            logger.info(f"Index {self.index_name} created successfully")
    
    def generate_hash(self, text: str) -> str:
        """
        Generate SHA256 hash for deduplication
        
        Args:
            text: Text to hash
            
        Returns:
            SHA256 hash string
        """
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for text
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as numpy array
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of input texts
            
        Returns:
            Array of embedding vectors
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        return embeddings
    
    def upsert_embedding(
        self,
        query: str,
        intent: str,
        slots: Dict,
        api_name: str = "",
        endpoint: str = "",
        template_version: int = 1,
        confidence: float = 1.0
    ) -> str:
        """
        Insert or update embedding in Redis
        
        Args:
            query: The query text
            intent: API intent (login, signup, etc.)
            slots: Dictionary of extracted slots
            api_name: Name of the API
            endpoint: API endpoint URL
            template_version: Version of the template
            confidence: Confidence score
            
        Returns:
            Redis key of the inserted/updated record
        """
        # Generate hash for deduplication
        hash_id = self.generate_hash(query)
        redis_key = f"api:{hash_id}"
        
        # Check if already exists
        if self.redis_client.exists(redis_key):
            logger.info(f"Embedding already exists for hash: {hash_id}")
            return redis_key
        
        # Generate embedding
        embedding = self.embed_text(query)
        
        # Prepare data
        data = {
            "embedding": embedding.astype(np.float32).tobytes(),
            "intent": intent,
            "slots_json": json.dumps(slots),
            "query": query,
            "hash_id": hash_id,
            "api_name": api_name or intent,
            "endpoint": endpoint or f"<base_url>/api/{intent}",
            "template_version": template_version,
            "created_at": datetime.utcnow().isoformat(),
            "confidence": confidence
        }
        
        # Insert into Redis
        self.redis_client.hset(redis_key, mapping=data)
        logger.info(f"Inserted embedding with key: {redis_key}")
        
        return redis_key
    
    def upsert_batch(
        self,
        queries: List[str],
        intents: List[str],
        slots_list: List[Dict],
        api_names: Optional[List[str]] = None,
        endpoints: Optional[List[str]] = None,
        batch_size: int = 32
    ) -> List[str]:
        """
        Insert or update multiple embeddings in batch
        
        Args:
            queries: List of query texts
            intents: List of intents
            slots_list: List of slot dictionaries
            api_names: List of API names
            endpoints: List of endpoints
            batch_size: Batch size for processing
            
        Returns:
            List of Redis keys
        """
        if api_names is None:
            api_names = intents
        if endpoints is None:
            endpoints = [f"<base_url>/api/{intent}" for intent in intents]
        
        redis_keys = []
        total = len(queries)
        
        logger.info(f"Upserting {total} embeddings in batches of {batch_size}")
        
        for i in range(0, total, batch_size):
            batch_queries = queries[i:i+batch_size]
            batch_intents = intents[i:i+batch_size]
            batch_slots = slots_list[i:i+batch_size]
            batch_api_names = api_names[i:i+batch_size]
            batch_endpoints = endpoints[i:i+batch_size]
            
            # Generate embeddings for batch
            embeddings = self.embed_batch(batch_queries)
            
            # Insert each item
            for j, query in enumerate(batch_queries):
                hash_id = self.generate_hash(query)
                redis_key = f"api:{hash_id}"
                
                # Skip if exists
                if self.redis_client.exists(redis_key):
                    logger.debug(f"Skipping existing: {hash_id}")
                    redis_keys.append(redis_key)
                    continue
                
                data = {
                    "embedding": embeddings[j].astype(np.float32).tobytes(),
                    "intent": batch_intents[j],
                    "slots_json": json.dumps(batch_slots[j]),
                    "query": query,
                    "hash_id": hash_id,
                    "api_name": batch_api_names[j],
                    "endpoint": batch_endpoints[j],
                    "template_version": 1,
                    "created_at": datetime.utcnow().isoformat(),
                    "confidence": 1.0
                }
                
                self.redis_client.hset(redis_key, mapping=data)
                redis_keys.append(redis_key)
            
            logger.info(f"Processed batch {i//batch_size + 1}/{(total + batch_size - 1)//batch_size}")
        
        logger.info(f"Upserted {len(redis_keys)} embeddings")
        return redis_keys
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        intent_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Perform cosine similarity search
        
        Args:
            query: Query text
            top_k: Number of results to return
            intent_filter: Optional intent filter
            
        Returns:
            List of matching results with scores
        """
        # Generate query embedding
        query_embedding = self.embed_text(query)
        
        # Build Redis query
        base_query = f"*=>[KNN {top_k} @embedding $vec AS score]"
        if intent_filter:
            base_query = f"@intent:{intent_filter} =>[KNN {top_k} @embedding $vec AS score]"
        
        redis_query = (
            Query(base_query)
            .return_fields("intent", "slots_json", "query", "api_name", "endpoint", "confidence", "score")
            .sort_by("score")
            .dialect(2)
        )
        
        # Execute search
        params = {
            "vec": query_embedding.astype(np.float32).tobytes()
        }
        
        try:
            results = self.redis_client.ft(self.index_name).search(redis_query, query_params=params)
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
        
        # Parse results
        matches = []
        for doc in results.docs:
            try:
                # Calculate similarity score (Redis returns distance, convert to similarity)
                distance = float(doc.score)
                similarity = 1 - distance  # Cosine similarity
                
                matches.append({
                    "intent": doc.intent,
                    "slots": json.loads(doc.slots_json),
                    "query": doc.query,
                    "api_name": doc.api_name,
                    "endpoint": doc.endpoint,
                    "confidence": float(doc.confidence) if hasattr(doc, 'confidence') else 1.0,
                    "similarity": similarity,
                    "score": similarity
                })
            except Exception as e:
                logger.error(f"Error parsing result: {e}")
                continue
        
        logger.info(f"Found {len(matches)} matches for query: {query}")
        return matches
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the vector database
        
        Returns:
            Dictionary with statistics
        """
        try:
            info = self.redis_client.ft(self.index_name).info()
            
            # Count documents by intent
            intents = {}
            cursor = 0
            while True:
                cursor, keys = self.redis_client.scan(cursor, match="api:*", count=100)
                for key in keys:
                    data = self.redis_client.hgetall(key)
                    if b'intent' in data:
                        intent = data[b'intent'].decode('utf-8')
                        intents[intent] = intents.get(intent, 0) + 1
                
                if cursor == 0:
                    break
            
            return {
                "index_name": self.index_name,
                "total_documents": info.get('num_docs', 0),
                "embedding_dimension": self.embedding_dim,
                "model_name": self.model_name,
                "intents": intents
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def delete_by_intent(self, intent: str) -> int:
        """
        Delete all embeddings for a specific intent
        
        Args:
            intent: Intent to delete
            
        Returns:
            Number of deleted documents
        """
        deleted = 0
        cursor = 0
        
        while True:
            cursor, keys = self.redis_client.scan(cursor, match="api:*", count=100)
            for key in keys:
                data = self.redis_client.hgetall(key)
                if b'intent' in data and data[b'intent'].decode('utf-8') == intent:
                    self.redis_client.delete(key)
                    deleted += 1
            
            if cursor == 0:
                break
        
        logger.info(f"Deleted {deleted} embeddings for intent: {intent}")
        return deleted


# Global instance
_embedding_manager = None


def get_embedding_manager() -> EmbeddingManager:
    """Get or create global EmbeddingManager instance"""
    global _embedding_manager
    if _embedding_manager is None:
        _embedding_manager = EmbeddingManager()
    return _embedding_manager
