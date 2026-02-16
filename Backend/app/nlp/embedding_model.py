#app/nlp/embedding_model.py

"""
Embedding Model - Now uses Ollama for CPU-based embeddings
No HuggingFace/SentenceTransformers dependency - uses HTTP API instead
"""

import asyncio
from typing import List, Optional
from app.core.logger import logger

# Default Ollama embedding model
DEFAULT_OLLAMA_MODEL = "nomic-embed-text"


class OllamaEmbeddingModel:
    """
    Wrapper class to provide SentenceTransformer-like interface using Ollama
    """
    
    def __init__(self, model_name: str = DEFAULT_OLLAMA_MODEL):
        self.model_name = model_name
        self.max_seq_length = 256
        self._dimension = None
        
    def get_sentence_embedding_dimension(self) -> int:
        """Get embedding dimension (lazy load by generating a test embedding)"""
        if self._dimension is None:
            # Run a test embedding to get dimension
            try:
                test_embedding = asyncio.get_event_loop().run_until_complete(
                    self._generate_single("test")
                )
                if test_embedding:
                    self._dimension = len(test_embedding)
                else:
                    # Default dimensions for known models
                    model_dims = {
                        "nomic-embed-text": 768,
                        "all-minilm": 384,
                        "mxbai-embed-large": 1024
                    }
                    self._dimension = model_dims.get(self.model_name, 768)
            except Exception as e:
                logger.debug(f"Could not get dimension from test embedding: {e}")
                self._dimension = 768  # Default fallback
        return self._dimension
    
    async def _generate_single(self, text: str) -> Optional[List[float]]:
        """Generate embedding for single text using Ollama"""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "http://localhost:11434/api/embeddings",
                    json={"model": self.model_name, "prompt": text}
                )
                if response.status_code == 200:
                    return response.json().get("embedding")
        except Exception as e:
            logger.warning(f"Ollama embedding failed: {e}")
        return None
    
    def encode(self, texts, normalize_embeddings: bool = True, convert_to_numpy: bool = True, show_progress_bar: bool = False) -> list:
        """
        Encode texts to embeddings using Ollama (sync wrapper)
        Compatible with SentenceTransformer interface
        """
        import numpy as np
        
        # Handle single text or list
        if isinstance(texts, str):
            texts = [texts]
        
        async def generate_all():
            results = []
            for text in texts:
                embedding = await self._generate_single(text)
                if embedding:
                    results.append(embedding)
                else:
                    # Return zero vector on failure
                    dim = self._dimension or 768
                    results.append([0.0] * dim)
            return results
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, use nest_asyncio or thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, generate_all())
                    embeddings = future.result()
            else:
                embeddings = loop.run_until_complete(generate_all())
        except RuntimeError:
            # No event loop, create one
            embeddings = asyncio.run(generate_all())
        
        if convert_to_numpy:
            import numpy as np
            embeddings = np.array(embeddings, dtype=np.float32)
            if normalize_embeddings:
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                norms[norms == 0] = 1  # Avoid division by zero
                embeddings = embeddings / norms
        
        return embeddings


# Singleton instance
_model = None


def get_model() -> OllamaEmbeddingModel:
    """
    Returns a shared OllamaEmbeddingModel instance.
    Uses Ollama HTTP API instead of HuggingFace.
    """
    global _model
    if _model is None:
        _model = OllamaEmbeddingModel(DEFAULT_OLLAMA_MODEL)
        logger.info(f"Using Ollama embedding model: {DEFAULT_OLLAMA_MODEL}")
    return _model