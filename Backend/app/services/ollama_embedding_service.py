"""
Ollama Embedding Service - CPU-based embedding generation using Ollama

Features:
- HTTP API integration with Ollama (localhost:11434)
- Supports: all-minilm (384), nomic-embed-text (768), mxbai-embed-large (1024)
- Automatic model pulling if not available
- Batch processing for efficiency
- Error handling and retries
- User-selected model from settings
"""

import httpx
import asyncio
import os
from typing import List, Optional
from app.core.logger import logger


class OllamaEmbeddingService:
    """
    Service for generating embeddings using Ollama API
    
    Ollama runs locally on CPU and provides embeddings through HTTP API:
    POST http://localhost:11434/api/embeddings
    """
    
    def __init__(self, base_url: str = None):
        # Default to environment `OLLAMA_HOST`, then to internal service name `http://ollama:11434`.
        if base_url is None:
            base_url = os.getenv("OLLAMA_HOST", "http://ollama:11434")
        self.base_url = base_url
        self.embeddings_endpoint = f"{base_url}/api/embeddings"
        self.pull_endpoint = f"{base_url}/api/pull"
        self.timeout = 60.0  # 60 seconds for embedding requests
        
    async def check_ollama_available(self) -> bool:
        """
        Check if Ollama service is running
        
        Returns:
            bool: True if Ollama is available, False otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, timeout=5.0)
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False
    
    async def pull_model(self, model_name: str) -> bool:
        """
        Pull (download) a model from Ollama registry
        
        Args:
            model_name: Name of the model to pull (e.g., "nomic-embed-text")
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Pulling Ollama model: {model_name}...")
            
            async with httpx.AsyncClient(timeout=300.0) as client:  # 5 min timeout for download
                response = await client.post(
                    self.pull_endpoint,
                    json={"name": model_name, "stream": False}
                )
                
                if response.status_code == 200:
                    logger.info(f"Model pulled successfully: {model_name}")
                    return True
                else:
                    logger.error(f"Failed to pull model {model_name}: {response.text}")
                    return False
        
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            return False
    
    async def generate_embedding(
        self,
        model_name: str,
        text: str,
        retry_with_pull: bool = True
    ) -> Optional[List[float]]:
        """
        Generate embedding for a single text using Ollama
        
        Args:
            model_name: Ollama model name (e.g., "nomic-embed-text")
            text: Text to embed
            retry_with_pull: If True, try to pull model on failure
        
        Returns:
            List of floats (embedding vector) or None on failure
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.embeddings_endpoint,
                    json={
                        "model": model_name,
                        "prompt": text
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("embedding")
                elif response.status_code == 404 and retry_with_pull:
                    # Model not found, try to pull it
                    logger.warning(f"Model {model_name} not found, attempting to pull...")
                    if await self.pull_model(model_name):
                        # Retry after pulling
                        return await self.generate_embedding(model_name, text, retry_with_pull=False)
                    return None
                else:
                    logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                    return None
        
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    async def generate_embeddings_batch(
        self,
        model_name: str,
        texts: List[str],
        batch_size: int = 32
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batches
        
        Args:
            model_name: Ollama model name
            texts: List of texts to embed
            batch_size: Number of texts to process in parallel
        
        Returns:
            List of embedding vectors (or None for failures)
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Process batch in parallel
            tasks = [
                self.generate_embedding(model_name, text)
                for text in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle results and exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch embedding error: {result}")
                    embeddings.append(None)
                else:
                    embeddings.append(result)
            
            logger.info(f"Processed batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
        
        return embeddings
    
    async def test_embedding(self, model_name: str = "nomic-embed-text") -> bool:
        """
        Test embedding generation with a sample text
        
        Args:
            model_name: Model to test
        
        Returns:
            bool: True if successful, False otherwise
        """
        test_text = "This is a test embedding for API test case generation."
        
        logger.info(f"Testing Ollama embedding with model: {model_name}")
        embedding = await self.generate_embedding(model_name, test_text)
        
        if embedding:
            logger.info(f"Test successful! Embedding dimension: {len(embedding)}")
            return True
        else:
            logger.error(f"Test failed for model: {model_name}")
            return False


# Singleton instance
_ollama_service = None


def get_ollama_service() -> OllamaEmbeddingService:
    """Get or create singleton instance"""
    global _ollama_service
    if _ollama_service is None:
        # Read OLLAMA_HOST from environment at runtime (docker-compose env or .env)
        base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        _ollama_service = OllamaEmbeddingService(base_url=base_url)
    else:
        # If environment changed since the singleton was created, recreate it
        base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        try:
            if getattr(_ollama_service, "base_url", None) != base_url:
                _ollama_service = OllamaEmbeddingService(base_url=base_url)
        except Exception:
            _ollama_service = OllamaEmbeddingService(base_url=base_url)
    return _ollama_service
