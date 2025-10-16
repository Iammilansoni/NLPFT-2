
import logging
import json
import csv
import io
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import redis
from redis.commands.search.field import TextField, VectorField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
import numpy as np

from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class DatasetService:
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or "redis://localhost:6379"
        self.redis_client: Optional[redis.Redis] = None
        self.embedding_service = get_embedding_service()
        self.index_name = "automation:intents"
        self.key_prefix = "api:"
        logger.info(f"DatasetService initialized with Redis URL: {self.redis_url}")
    
    def _get_redis_client(self) -> redis.Redis:
        if self.redis_client is None:
            try:
                self.redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=False
                )
                self.redis_client.ping()
                logger.info("Successfully connected to Redis")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise RuntimeError(f"Redis connection failed: {e}")
        
        return self.redis_client
    
    def create_vector_index(self, force_recreate: bool = False) -> bool:
        try:
            client = self._get_redis_client()
            
            try:
                client.ft(self.index_name).info()
                if force_recreate:
                    logger.info(f"Dropping existing index: {self.index_name}")
                    client.ft(self.index_name).dropindex(delete_documents=False)
                else:
                    logger.info(f"Index {self.index_name} already exists")
                    return True
            except:
                pass
            
            schema = (
                TextField("text", weight=5.0),
                TextField("api", weight=3.0),
                TextField("endpoint"),
                TextField("style"),
                NumericField("chunk_id"),
                NumericField("paraphrase_id"),
                NumericField("token_count"),
                TagField("embedding_model"),
                VectorField(
                    "embedding",
                    "FLAT",
                    {
                        "TYPE": "FLOAT32",
                        "DIM": 384,
                        "DISTANCE_METRIC": "COSINE"
                    }
                )
            )
            
            definition = IndexDefinition(
                prefix=[self.key_prefix],
                index_type=IndexType.HASH
            )
            
            client.ft(self.index_name).create_index(
                fields=schema,
                definition=definition
            )
            
            logger.info(f"Successfully created vector index: {self.index_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error creating vector index: {e}")
            raise
    
    def store_dataset_in_redis(
        self,
        dataset: Dict[str, Any],
        embed_chunks: bool = True
    ) -> Dict[str, int]:
        try:
            client = self._get_redis_client()
            
            self.create_vector_index(force_recreate=False)
            
            stats = {
                "apis_stored": 0,
                "chunks_stored": 0,
                "paraphrases_stored": 0,
                "embeddings_generated": 0
            }
            
            datasets = dataset.get("datasets", [])
            
            for api_data in datasets:
                api = api_data.get("api")
                endpoint = api_data.get("endpoint")
                chunks = api_data.get("chunks", [])
                nl_inputs = api_data.get("nl_inputs", [])
                
                if embed_chunks:
                    logger.info(f"Generating embeddings for {api}...")
                    chunks = self.embedding_service.embed_chunks(chunks)
                    stats["embeddings_generated"] += len(chunks)
                
                for chunk in chunks:
                    chunk_id = chunk.get("chunk_id", 0)
                    text_joined = chunk.get("text_joined", "")
                    embedding = chunk.get("embedding")
                    paraphrase_ids = chunk.get("paraphrase_ids", [])
                    
                    if not embedding:
                        logger.warning(f"Chunk {chunk_id} for {api} has no embedding, skipping")
                        continue
                    
                    redis_key = f"{self.key_prefix}{api}:chunk:{chunk_id}"
                    
                    embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()
                    
                    hash_data = {
                        "text": text_joined,
                        "api": api,
                        "endpoint": endpoint,
                        "chunk_id": chunk_id,
                        "style": "mixed",
                        "paraphrase_id": json.dumps(paraphrase_ids),
                        "token_count": chunk.get("approx_token_count", 0),
                        "embedding_model": chunk.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2"),
                        "embedding": embedding_bytes
                    }
                    
                    client.hset(redis_key, mapping=hash_data)
                    stats["chunks_stored"] += 1
                
                stats["apis_stored"] += 1
                stats["paraphrases_stored"] += len(nl_inputs)
            
            logger.info(f"Successfully stored dataset in Redis: {stats}")
            return stats
        
        except Exception as e:
            logger.error(f"Error storing dataset in Redis: {e}")
            raise
    
    def search_similar_intents(
        self,
        query_text: str,
        top_k: int = 5,
        api_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        try:
            client = self._get_redis_client()
            
            query_embedding = self.embedding_service.generate_embedding(query_text, normalize=True)
            query_bytes = query_embedding.astype(np.float32).tobytes()
            
            base_query = f"*"
            if api_filter:
                base_query = f"@api:{api_filter}"
            
            query = (
                Query(f"({base_query})=>[KNN {top_k} @embedding $vec AS score]")
                .return_fields("api", "endpoint", "text", "style", "chunk_id", "score")
                .sort_by("score")
                .dialect(2)
            )
            
            results = client.ft(self.index_name).search(
                query,
                query_params={"vec": query_bytes}
            )
            
            formatted_results = []
            for doc in results.docs:
                formatted_results.append({
                    "api": doc.api,
                    "endpoint": doc.endpoint,
                    "text": doc.text[:200] + "..." if len(doc.text) > 200 else doc.text,
                    "style": doc.style,
                    "chunk_id": doc.chunk_id,
                    "similarity_score": 1 - float(doc.score)
                })
            
            logger.info(f"Found {len(formatted_results)} similar intents for query: {query_text[:50]}...")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error searching similar intents: {e}")
            raise
    
    def export_to_jsonl(
        self,
        dataset: Dict[str, Any],
        output_path: Optional[Path] = None
    ) -> str:
        try:
            jsonl_lines = []
            
            datasets = dataset.get("datasets", [])
            embedding_model = dataset.get("project", {}).get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
            
            for api_data in datasets:
                api = api_data.get("api")
                endpoint = api_data.get("endpoint")
                nl_inputs = api_data.get("nl_inputs", [])
                
                for inp in nl_inputs:
                    line = {
                        "api": api,
                        "endpoint": endpoint,
                        "text": inp.get("text"),
                        "style": inp.get("style"),
                        "token_count": inp.get("token_count"),
                        "embedding_model": embedding_model
                    }
                    jsonl_lines.append(json.dumps(line, ensure_ascii=False))
            
            jsonl_content = "\n".join(jsonl_lines)
            
            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(jsonl_content, encoding="utf-8")
                logger.info(f"Exported {len(jsonl_lines)} lines to {output_path}")
                return str(output_path)
            
            return jsonl_content
        
        except Exception as e:
            logger.error(f"Error exporting to JSONL: {e}")
            raise
    
    def export_to_csv(
        self,
        dataset: Dict[str, Any],
        output_path: Optional[Path] = None
    ) -> str:
        try:
            output = io.StringIO()
            
            fieldnames = [
                "api", "endpoint", "paraphrase_id", "text", 
                "style", "token_count", "char_count", "chunk_id", "embedding_model"
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            datasets = dataset.get("datasets", [])
            embedding_model = dataset.get("project", {}).get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
            
            for api_data in datasets:
                api = api_data.get("api")
                endpoint = api_data.get("endpoint")
                nl_inputs = api_data.get("nl_inputs", [])
                chunks = api_data.get("chunks", [])
                
                paraphrase_to_chunk = {}
                for chunk in chunks:
                    chunk_id = chunk.get("chunk_id")
                    for pid in chunk.get("paraphrase_ids", []):
                        paraphrase_to_chunk[pid] = chunk_id
                
                for inp in nl_inputs:
                    pid = inp.get("id", 0)
                    row = {
                        "api": api,
                        "endpoint": endpoint,
                        "paraphrase_id": pid,
                        "text": inp.get("text"),
                        "style": inp.get("style"),
                        "token_count": inp.get("token_count"),
                        "char_count": inp.get("char_count"),
                        "chunk_id": paraphrase_to_chunk.get(pid, 0),
                        "embedding_model": embedding_model
                    }
                    writer.writerow(row)
            
            csv_content = output.getvalue()
            
            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(csv_content, encoding="utf-8")
                logger.info(f"Exported CSV to {output_path}")
                return str(output_path)
            
            return csv_content
        
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise
    
    def generate_export_files(
        self,
        dataset: Dict[str, Any],
        output_dir: Path
    ) -> Dict[str, str]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        jsonl_path = output_dir / f"dataset_export_{timestamp}.jsonl"
        csv_path = output_dir / f"dataset_export_{timestamp}.csv"
        
        jsonl_result = self.export_to_jsonl(dataset, jsonl_path)
        csv_result = self.export_to_csv(dataset, csv_path)
        
        return {
            "jsonl": jsonl_result,
            "csv": csv_result,
            "timestamp": timestamp
        }
    
    def get_stats(self) -> Dict[str, Any]:
        try:
            client = self._get_redis_client()
            
            try:
                index_info = client.ft(self.index_name).info()
                num_docs = index_info.get("num_docs", 0)
            except:
                num_docs = 0
            
            keys = client.keys(f"{self.key_prefix}*")
            
            return {
                "index_name": self.index_name,
                "total_documents": num_docs,
                "total_keys": len(keys),
                "key_prefix": self.key_prefix,
                "embedding_model": self.embedding_service.MODEL_NAME,
                "vector_dim": self.embedding_service.VECTOR_DIM
            }
        
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}


_dataset_service: Optional[DatasetService] = None


def get_dataset_service(redis_url: Optional[str] = None) -> DatasetService:
    global _dataset_service
    if _dataset_service is None:
        _dataset_service = DatasetService(redis_url=redis_url)
    return _dataset_service
