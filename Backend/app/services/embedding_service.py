
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import torch

logger = logging.getLogger(__name__)


class EmbeddingService:
    
    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_DIM = 384
    
    def __init__(self):
        self.model: Optional[SentenceTransformer] = None
        self.device = "cpu"
        logger.info(f"Initializing EmbeddingService with model: {self.MODEL_NAME}")
    
    def _load_model(self):
        if self.model is None:
            try:
                logger.info(f"Loading model {self.MODEL_NAME} on {self.device}...")
                self.model = SentenceTransformer(self.MODEL_NAME, device=self.device)
                self.model.eval()
                logger.info(f"Model loaded successfully. Vector dimension: {self.VECTOR_DIM}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise RuntimeError(f"Could not load embedding model: {e}")
    
    def generate_embedding(self, text: str, normalize: bool = True) -> np.ndarray:
        self._load_model()
        
        try:
            with torch.no_grad():
                embedding = self.model.encode(
                    text,
                    convert_to_numpy=True,
                    normalize_embeddings=normalize,
                    show_progress_bar=False
                )
            
            return embedding
        
        except Exception as e:
            logger.error(f"Error generating embedding for text: {text[:50]}... Error: {e}")
            raise
    
    def generate_embeddings_batch(
        self, 
        texts: List[str], 
        normalize: bool = True,
        batch_size: int = 32
    ) -> np.ndarray:
        self._load_model()
        
        if not texts:
            return np.array([])
        
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts...")
            
            with torch.no_grad():
                embeddings = self.model.encode(
                    texts,
                    convert_to_numpy=True,
                    normalize_embeddings=normalize,
                    batch_size=batch_size,
                    show_progress_bar=len(texts) > 100
                )
            
            logger.info(f"Generated {len(embeddings)} embeddings successfully")
            return embeddings
        
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    def embed_chunks(
        self, 
        chunks: List[Dict[str, Any]],
        text_field: str = "text_joined"
    ) -> List[Dict[str, Any]]:
        self._load_model()
        
        if not chunks:
            return []
        
        try:
            texts = [chunk.get(text_field, "") for chunk in chunks]
            
            embeddings = self.generate_embeddings_batch(texts, normalize=True)
            
            enriched_chunks = []
            for chunk, embedding in zip(chunks, embeddings):
                enriched_chunk = chunk.copy()
                enriched_chunk["embedding"] = embedding.tolist()
                enriched_chunk["vector_dim"] = self.VECTOR_DIM
                enriched_chunks.append(enriched_chunk)
            
            logger.info(f"Successfully embedded {len(enriched_chunks)} chunks")
            return enriched_chunks
        
        except Exception as e:
            logger.error(f"Error embedding chunks: {e}")
            raise
    
    def compute_similarity(
        self, 
        embedding1: np.ndarray, 
        embedding2: np.ndarray,
        metric: str = "cosine"
    ) -> float:
        try:
            if metric == "cosine":
                similarity = np.dot(embedding1, embedding2)
            elif metric == "euclidean":
                similarity = -np.linalg.norm(embedding1 - embedding2)
            else:
                raise ValueError(f"Unknown metric: {metric}")
            
            return float(similarity)
        
        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            raise
    
    def find_similar_chunks(
        self,
        query_embedding: np.ndarray,
        chunk_embeddings: List[np.ndarray],
        top_k: int = 5,
        metric: str = "cosine"
    ) -> List[Tuple[int, float]]:
        try:
            similarities = []
            for idx, chunk_emb in enumerate(chunk_embeddings):
                sim = self.compute_similarity(query_embedding, chunk_emb, metric)
                similarities.append((idx, sim))
            
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities[:top_k]
        
        except Exception as e:
            logger.error(f"Error finding similar chunks: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_name": self.MODEL_NAME,
            "vector_dim": self.VECTOR_DIM,
            "device": self.device,
            "similarity_metric": "cosine",
            "normalization": "L2",
            "framework": "sentence-transformers"
        }
    
    def approximate_token_count(self, text: str) -> int:
        import re
        
        tokens = re.findall(r'\b\w+\b|[^\w\s]', text)
        
        approx_count = int(len(tokens) * 1.2)
        
        return approx_count
    
    def chunk_texts(
        self,
        texts: List[str],
        target_min_tokens: int = 350,
        target_max_tokens: int = 450,
        preserve_integrity: bool = True
    ) -> List[Dict[str, Any]]:
        chunks = []
        current_chunk_texts = []
        current_chunk_ids = []
        current_token_count = 0
        chunk_id = 0
        
        for idx, text in enumerate(texts):
            token_count = self.approximate_token_count(text)
            
            if current_chunk_texts and (current_token_count + token_count > target_max_tokens):
                if current_token_count >= target_min_tokens or not chunks:
                    chunks.append({
                        "chunk_id": chunk_id,
                        "paraphrase_ids": current_chunk_ids.copy(),
                        "approx_token_count": current_token_count,
                        "text_joined": "\n".join(current_chunk_texts),
                        "embedding_model": self.MODEL_NAME,
                        "start_index": current_chunk_ids[0] if current_chunk_ids else 0,
                        "end_index": current_chunk_ids[-1] if current_chunk_ids else 0
                    })
                    chunk_id += 1
                
                current_chunk_texts = []
                current_chunk_ids = []
                current_token_count = 0
            
            current_chunk_texts.append(text)
            current_chunk_ids.append(idx)
            current_token_count += token_count
        
        if current_chunk_texts:
            chunks.append({
                "chunk_id": chunk_id,
                "paraphrase_ids": current_chunk_ids.copy(),
                "approx_token_count": current_token_count,
                "text_joined": "\n".join(current_chunk_texts),
                "embedding_model": self.MODEL_NAME,
                "start_index": current_chunk_ids[0] if current_chunk_ids else 0,
                "end_index": current_chunk_ids[-1] if current_chunk_ids else 0
            })
        
        logger.info(f"Created {len(chunks)} chunks from {len(texts)} texts")
        return chunks


_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
