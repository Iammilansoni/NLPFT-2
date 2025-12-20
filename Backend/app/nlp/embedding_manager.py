"""
Embedding Manager - Handle embeddings and Redis vector operations
Uses Ollama for CPU-based embeddings (no HuggingFace dependency)
"""

import os
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np
import redis
from redis.commands.search.field import VectorField, TextField, NumericField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query

from app.core.config import settings, REDIS_HOST, REDIS_PORT, INDEX_NAME, MODEL_NAME
from app.core.logger import logger
from app.nlp.embedding_model import OllamaEmbeddingModel


class EmbeddingManager:
    """
    Manage embeddings and Redis vector database operations
    """
    
    def __init__(
        self,
        model_name: str = "nomic-embed-text",
        redis_host: str = REDIS_HOST,
        redis_port: int = REDIS_PORT,
        index_name: str = INDEX_NAME
    ):
        """
        Initialize the embedding manager with Ollama
        
        Args:
            model_name: Name of the Ollama embedding model
            redis_host: Redis host
            redis_port: Redis port
            index_name: Name of the Redis vector index
        """
        self.model_name = model_name
        self.index_name = index_name
        
        # Load Ollama embedding model (no HuggingFace download)
        logger.info(f"Initializing Ollama embedding model: {model_name}")
        self.model = OllamaEmbeddingModel(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Ollama model ready. Embedding dimension: {self.embedding_dim}")
        
        # Connect to Redis
        redis_password = os.getenv("REDIS_PASSWORD", "nlpforge_redis_secure_password_2024")
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
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
        except redis.exceptions.ResponseError:
            # Create index
            logger.info(f"Creating index {self.index_name}")
            
            schema = (
                TextField("query"),
                TextField("api"),
                TextField("endpoint"),
                TextField("request"),
                TextField("response"),
                VectorField(
                    "query_embedding",
                    "HNSW",
                    {
                        "TYPE": "FLOAT32",
                        "DIM": self.embedding_dim,
                        "DISTANCE_METRIC": "COSINE",
                        "M": 16,
                        "EF_CONSTRUCTION": 200
                    }
                ),
                # Additional fields for compatibility and metadata
                TextField("intent"),  # Alias for 'api' for backward compatibility
                TextField("slots_json"),  # Alias for 'request' for backward compatibility
                TextField("hash_id"),  # For deduplication
                TextField("api_name"),  # Alias for 'api'
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
        
        # Prepare data in unified schema format (matching csv_dataset.csv structure)
        # Primary fields (matching csv_dataset.csv format)
        data = {
            "query": query,
            "api": intent,  # 'api' is the primary field, 'intent' is alias
            "endpoint": endpoint or f"<base_url>/api/{intent}",
            "request": json.dumps(slots),  # 'request' contains slots as JSON
            "response": json.dumps({"definition": f"API endpoint for {intent}"}),  # Default response
            "query_embedding": embedding.astype(np.float32).tobytes(),  # Vector field name matching old schema
            # Additional fields for compatibility
            "intent": intent,  # Alias for backward compatibility
            "slots_json": json.dumps(slots),  # Alias for backward compatibility
            "hash_id": hash_id,
            "api_name": api_name or intent,
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
        responses: Optional[List[str]] = None,
        batch_size: int = 32
    ) -> Dict:
        """
        Insert or update multiple embeddings in batch
        
        Args:
            queries: List of query texts
            intents: List of intents
            slots_list: List of slot dictionaries
            api_names: List of API names
            endpoints: List of endpoints
            responses: List of response JSON strings (optional)
            batch_size: Batch size for processing
            
        Returns:
            Dictionary with redis_keys, new_count, and skipped_count
        """
        if api_names is None:
            api_names = intents
        if endpoints is None:
            endpoints = [f"<base_url>/api/{intent}" for intent in intents]
        if responses is None:
            responses = [json.dumps({"definition": f"API endpoint for {intent}"}) for intent in intents]
        
        redis_keys = []
        new_count = 0
        skipped_count = 0
        total = len(queries)
        
        logger.info(f"Upserting {total} embeddings in batches of {batch_size}")
        
        for i in range(0, total, batch_size):
            batch_queries = queries[i:i+batch_size]
            batch_intents = intents[i:i+batch_size]
            batch_slots = slots_list[i:i+batch_size]
            batch_api_names = api_names[i:i+batch_size]
            batch_endpoints = endpoints[i:i+batch_size]
            batch_responses = responses[i:i+batch_size]
            
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
                    skipped_count += 1
                    continue
                
                # Prepare data in unified schema format (matching csv_dataset.csv structure)
                slots_json = json.dumps(batch_slots[j])
                # Use provided response or generate default
                response_data = batch_responses[j] if isinstance(batch_responses[j], str) else json.dumps(batch_responses[j])
                
                data = {
                    # Primary fields (matching csv_dataset.csv format)
                    "query": query,
                    "api": batch_intents[j],  # 'api' is the primary field
                    "endpoint": batch_endpoints[j],
                    "request": slots_json,  # 'request' contains slots as JSON
                    "response": response_data,  # Response field matching csv_dataset.csv
                    "query_embedding": embeddings[j].astype(np.float32).tobytes(),  # Vector field matching old schema
                    # Additional fields for compatibility
                    "intent": batch_intents[j],  # Alias for backward compatibility
                    "slots_json": slots_json,  # Alias for backward compatibility
                    "hash_id": hash_id,
                    "api_name": batch_api_names[j],
                    "template_version": 1,
                    "created_at": datetime.utcnow().isoformat(),
                    "confidence": 1.0
                }
                
                self.redis_client.hset(redis_key, mapping=data)
                redis_keys.append(redis_key)
                new_count += 1
            
            logger.info(f"Processed batch {i//batch_size + 1}/{(total + batch_size - 1)//batch_size}")
        
        logger.info(f"Upserted {len(redis_keys)} embeddings ({new_count} new, {skipped_count} skipped)")
        return {
            "redis_keys": redis_keys,
            "new_count": new_count,
            "skipped_count": skipped_count,
            "total": len(redis_keys)
        }
    
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
        
        # Build Redis query (using query_embedding field name matching csv_dataset.csv schema)
        base_query = f"*=>[KNN {top_k} @query_embedding $vec AS score]"
        if intent_filter:
            base_query = f"@api:{intent_filter} =>[KNN {top_k} @query_embedding $vec AS score]"
        
        redis_query = (
            Query(base_query)
            .return_fields("query", "api", "endpoint", "request", "response", "intent", "slots_json", "api_name", "confidence", "score")
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
        
       
        matches = []
        for doc in results.docs:
            try:
                # Calculate similarity score (Redis returns distance, convert to similarity)
                distance = float(doc.score)
                similarity = 1 - distance  # Cosine similarity
                
                # Extract data - support both old schema (api, request) and new schema (intent, slots_json)
                intent = getattr(doc, 'api', None) or getattr(doc, 'intent', 'unknown')
                request_data = getattr(doc, 'request', None) or getattr(doc, 'slots_json', '{}')
                
                # Parse slots from request field
                try:
                    if isinstance(request_data, str):
                        slots = json.loads(request_data)
                    else:
                        slots = request_data
                except json.JSONDecodeError:
                    slots = {}
                
                matches.append({
                    "query": doc.query,
                    "api": intent,  # Primary field matching csv_dataset.csv
                    "intent": intent,  # Alias for backward compatibility
                    "endpoint": doc.endpoint,
                    "request": request_data,  # Primary field matching csv_dataset.csv
                    "slots": slots,  # Parsed slots
                    "slots_json": request_data,  # Alias for backward compatibility
                    "api_name": getattr(doc, 'api_name', intent),
                    "response": getattr(doc, 'response', '{}'),
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
            
            # Handle both byte and string keys (decode_responses=False returns bytes)
            def get_info_value(key: str, default=0):
                """Get value from info dict, handling both byte and string keys"""
                if key in info:
                    return info[key]
                byte_key = key.encode('utf-8') if isinstance(key, str) else key
                if byte_key in info:
                    val = info[byte_key]
                    return val.decode('utf-8') if isinstance(val, bytes) else val
                return default
            
            num_docs = get_info_value('num_docs', 0)
            # Ensure num_docs is an integer
            if isinstance(num_docs, str):
                num_docs = int(num_docs)
            elif isinstance(num_docs, bytes):
                num_docs = int(num_docs.decode('utf-8'))
            
            # Count documents by intent/api using aggregation (much faster)
            intents = {}
            cursor = 0
            sample_limit = 1000  # Only sample first 1000 for intent breakdown
            count = 0
            
            while count < sample_limit:
                cursor, keys = self.redis_client.scan(cursor, match="api:*", count=100)
                for key in keys:
                    if count >= sample_limit:
                        break
                    # Only get the intent field, not all data
                    intent_value = self.redis_client.hget(key, b'api') or self.redis_client.hget(key, b'intent')
                    if intent_value:
                        intent = intent_value.decode('utf-8')
                        intents[intent] = intents.get(intent, 0) + 1
                    count += 1
                
                if cursor == 0:
                    break
            
            logger.info(f"Stats: index={self.index_name}, num_docs={num_docs}, intents={len(intents)}")
            
            return {
                "index_name": self.index_name,
                "total_embeddings": num_docs,  # Frontend expects this field name
                "total_documents": num_docs,  # Keep for backward compatibility
                "embedding_dimension": self.embedding_dim,
                "model_name": self.model_name,
                "model": self.model_name,  # Frontend expects this field name
                "intents": intents,
                "intents_sampled": count < num_docs  # Indicate if this is a sample
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
                # Support both 'api' (primary) and 'intent' (alias) fields
                api_value = None
                if b'api' in data:
                    api_value = data[b'api'].decode('utf-8')
                elif b'intent' in data:
                    api_value = data[b'intent'].decode('utf-8')
                
                if api_value == intent:
                    self.redis_client.delete(key)
                    deleted += 1
            
            if cursor == 0:
                break
        
        logger.info(f"Deleted {deleted} embeddings for intent: {intent}")
        return deleted
    
    def clear_all_embeddings(self) -> int:
        """
        Clear all embeddings from Redis (use with caution!)
        
        Returns:
            Number of deleted documents
        """
        deleted = 0
        cursor = 0
        
        logger.warning("Clearing all embeddings from Redis...")
        
        while True:
            cursor, keys = self.redis_client.scan(cursor, match="api:*", count=100)
            if keys:
                deleted += len(keys)
                self.redis_client.delete(*keys)
            
            if cursor == 0:
                break
        
        logger.warning(f"Cleared {deleted} embeddings from Redis")
        return deleted


# Global instance cache (keyed by model name for dynamic model support)
_embedding_managers: Dict[str, "EmbeddingManager"] = {}


def get_embedding_manager(model_name: str = "nomic-embed-text") -> EmbeddingManager:
    """
    Get or create EmbeddingManager instance for a specific model.
    
    Supports dynamic model selection - different models have different dimensions
    and require separate Redis indices.
    
    Args:
        model_name: Ollama embedding model name (all-minilm, nomic-embed-text, mxbai-embed-large)
    
    Returns:
        EmbeddingManager instance for the specified model
    """
    global _embedding_managers
    
    if model_name not in _embedding_managers:
        logger.info(f"Creating EmbeddingManager for model: {model_name}")
        _embedding_managers[model_name] = EmbeddingManager(model_name=model_name)
    
    return _embedding_managers[model_name]
