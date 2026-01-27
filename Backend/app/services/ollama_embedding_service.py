"""
Ollama Embedding Service - CPU-based embedding generation using Ollama

Features:
- HTTP API integration with Ollama (localhost:11434)
- Supports: all-minilm (384), nomic-embed-text (768), mxbai-embed-large (1024)
- Automatic model pulling if not available
- AUTO-DIMENSION DETECTION: Detects embedding dimensions automatically
- Batch processing for efficiency
- Error handling and retries
- User-selected model from settings
"""

import httpx
import asyncio
import os
from typing import List, Optional, Dict, Any, Tuple
from app.core.logger import logger


class OllamaEmbeddingService:
    """
    Service for generating embeddings using Ollama API
    
    Ollama runs locally on CPU and provides embeddings through HTTP API:
    POST http://localhost:11434/api/embeddings
    
    Features:
    - Auto-dimension detection for unknown models
    - Automatic model registration with detected dimensions
    - Model pull on demand
    """
    
    # Cache for detected dimensions (model_name -> dimension)
    _dimension_cache: Dict[str, int] = {}
    
    def __init__(self, base_url: str = None):
        # Default to environment `OLLAMA_HOST`, then to internal service name `http://ollama:11434`.
        if base_url is None:
            base_url = os.getenv("OLLAMA_HOST", "http://ollama:11434")
        self.base_url = base_url
        self.embeddings_endpoint = f"{base_url}/api/embeddings"
        self.pull_endpoint = f"{base_url}/api/pull"
        self.tags_endpoint = f"{base_url}/api/tags"
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
    
    async def detect_dimension(self, model_name: str, auto_pull: bool = True) -> Optional[int]:
        """
        Auto-detect embedding dimension for a model.
        
        This is the KEY function for dynamic model registration.
        It generates a test embedding and returns the dimension.
        
        Args:
            model_name: Ollama model name (e.g., "nomic-embed-text")
            auto_pull: If True, automatically pull the model if not found
            
        Returns:
            Embedding dimension (int) or None if detection failed
        """
        # Check cache first
        if model_name in self._dimension_cache:
            logger.debug(f"Using cached dimension for {model_name}: {self._dimension_cache[model_name]}")
            return self._dimension_cache[model_name]
        
        test_text = "Dimension detection test."
        
        try:
            logger.info(f"🔍 Detecting embedding dimension for: {model_name}")
            embedding = await self.generate_embedding(model_name, test_text, retry_with_pull=auto_pull)
            
            if embedding:
                dimension = len(embedding)
                # Cache the result
                self._dimension_cache[model_name] = dimension
                logger.info(f"✅ Detected dimension for {model_name}: {dimension}")
                return dimension
            else:
                logger.warning(f"❌ Could not detect dimension for {model_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error detecting dimension for {model_name}: {e}")
            return None
    
    async def register_model_with_auto_dimension(
        self, 
        model_name: str,
        auto_pull: bool = True
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Detect dimension and register model in the embedding registry.
        
        This is the main entry point for dynamic model registration:
        1. Pull the model if needed (auto_pull=True)
        2. Generate test embedding to detect dimension
        3. Register in EmbeddingModelRegistry
        4. Return registration details
        
        Args:
            model_name: Ollama model name
            auto_pull: Pull model if not available
            
        Returns:
            Tuple of (success: bool, model_info: dict or None)
        """
        try:
            from app.core.embedding_model_registry import get_embedding_registry
            
            registry = get_embedding_registry()
            
            # Check if already registered
            try:
                existing = registry.get_model(model_name)
                return True, {
                    "model_id": existing.model_id,
                    "dimension": existing.dimension,
                    "display_name": existing.display_name,
                    "redis_index_name": existing.redis_index_name,
                    "already_registered": True,
                }
            except ValueError:
                pass  # Not registered, continue with detection
            
            # Detect dimension
            dimension = await self.detect_dimension(model_name, auto_pull=auto_pull)
            
            if dimension is None:
                return False, {"error": f"Could not detect dimension for model: {model_name}"}
            
            # Register the model
            spec = registry.register_dynamic_model(
                model_id=model_name,
                dimension=dimension,
                ollama_model_name=model_name,
            )
            
            return True, {
                "model_id": spec.model_id,
                "dimension": spec.dimension,
                "display_name": spec.display_name,
                "redis_index_name": spec.redis_index_name,
                "already_registered": False,
            }
            
        except Exception as e:
            logger.error(f"Error registering model {model_name}: {e}")
            return False, {"error": str(e)}
    
    async def list_available_models(self) -> List[Dict[str, Any]]:
        """
        List all available Ollama models (embedding-capable).
        
        Returns:
            List of model info dicts with name, size, modified date
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.tags_endpoint)
                
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    
                    # Filter and format models - include embedding models
                    # Embedding models typically have "embed" in name or are known embedding models
                    embedding_keywords = ["embed", "minilm", "bge", "e5", "gte", "nomic", "mxbai"]
                    
                    result = []
                    for model in models:
                        name = model.get("name", "")
                        # Include all models - user may want to try any model for embeddings
                        result.append({
                            "name": name,
                            "size": model.get("size", 0),
                            "modified_at": model.get("modified_at", ""),
                            "is_likely_embedding": any(kw in name.lower() for kw in embedding_keywords),
                        })
                    
                    return result
                else:
                    logger.warning(f"Failed to list models: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
            return []
    
    async def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed info about a specific model.
        
        Args:
            model_name: Model name (e.g., "nomic-embed-text")
            
        Returns:
            Model info dict or None
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/show",
                    json={"name": model_name}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "name": model_name,
                        "modelfile": data.get("modelfile", ""),
                        "parameters": data.get("parameters", ""),
                        "template": data.get("template", ""),
                        "details": data.get("details", {}),
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting model info for {model_name}: {e}")
            return None


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
