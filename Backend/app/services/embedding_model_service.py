"""
Embedding Model Service - Dynamic model discovery and dimension detection

This service handles:
1. Discovering available Ollama embedding models
2. Auto-detecting embedding dimensions on first use
3. Registering new models dynamically
4. Managing model availability

Works with the EmbeddingModelRegistry for persistent model tracking.
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import httpx

from app.core.embedding_model_registry import (
    EmbeddingModelSpec,
    get_embedding_registry,
)
from app.core.logger import logger

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class OllamaEmbeddingModel:
    """Information about an Ollama embedding model."""
    name: str
    display_name: str
    size: str  # e.g., "274 MB"
    is_local: bool  # Whether it's already pulled
    is_registered: bool  # Whether it's in the registry
    dimension: Optional[int]  # Known dimension (if registered)
    family: Optional[str]  # Model family
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "size": self.size,
            "is_local": self.is_local,
            "is_registered": self.is_registered,
            "dimension": self.dimension,
            "family": self.family,
        }


# =============================================================================
# SERVICE CLASS
# =============================================================================

class EmbeddingModelService:
    """
    Service for managing embedding models dynamically.
    
    Handles:
    - Discovering Ollama embedding models
    - Detecting embedding dimensions
    - Registering new models in the registry
    """
    
    # Known embedding model patterns (name contains these)
    EMBEDDING_MODEL_PATTERNS = [
        "embed", "embedding", "e5", "bge", "gte", "nomic",
        "minilm", "mpnet", "sentence", "instructor", "jina",
        "snowflake", "arctic", "granite", "paraphrase", "qwen"
    ]
    
    # Known embedding models with their dimensions
    # Source: https://ollama.com/search?c=embedding
    KNOWN_DIMENSIONS: Dict[str, int] = {
        # Nomic models
        "nomic-embed-text": 768,
        "nomic-embed-text-v2-moe": 768,
        
        # All-MiniLM models  
        "all-minilm": 384,
        "all-minilm:22m": 384,
        "all-minilm:33m": 384,
        
        # MxBai models
        "mxbai-embed-large": 1024,
        
        # Snowflake Arctic models
        "snowflake-arctic-embed": 1024,
        "snowflake-arctic-embed:xs": 384,
        "snowflake-arctic-embed:s": 384,
        "snowflake-arctic-embed:m": 768,
        "snowflake-arctic-embed:l": 1024,
        "snowflake-arctic-embed:22m": 384,
        "snowflake-arctic-embed:33m": 384,
        "snowflake-arctic-embed:110m": 768,
        "snowflake-arctic-embed:137m": 768,
        "snowflake-arctic-embed:335m": 1024,
        "snowflake-arctic-embed2": 1024,
        "snowflake-arctic-embed2:568m": 1024,
        
        # BGE models (BAAI) — only models available in Ollama registry
        "bge-m3": 1024,
        "bge-m3:567m": 1024,
        "bge-large": 1024,
        "bge-large:335m": 1024,
        
        # Google EmbeddingGemma
        "embeddinggemma": 768,
        "embeddinggemma:300m": 768,
        
        # Qwen3 embedding models
        "qwen3-embedding": 1024,
        "qwen3-embedding:0.6b": 1024,
        "qwen3-embedding:4b": 1024,
        "qwen3-embedding:8b": 4096,
        
        # Paraphrase multilingual
        "paraphrase-multilingual": 768,
        "paraphrase-multilingual:278m": 768,
        
        # IBM Granite embedding
        "granite-embedding": 768,
        "granite-embedding:30m": 384,
        "granite-embedding:278m": 768,
    }
    
    def __init__(self, ollama_host: Optional[str] = None):
        """
        Initialize the embedding model service.
        
        Args:
            ollama_host: Ollama server URL (default: from env or localhost:11434)
        """
        import os
        self.ollama_host = ollama_host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.registry = get_embedding_registry()
    
    def _normalize_model_name(self, name: str) -> str:
        """
        Normalize model name by removing :latest tag.
        
        Ollama returns models with tags like 'all-minilm:latest' but the
        registry uses base names like 'all-minilm'. This ensures matching.
        """
        if name.endswith(":latest"):
            return name[:-7]  # Remove ':latest' suffix
        return name
    
    def _is_model_local(self, model_name: str, local_models: set) -> bool:
        """
        Check if a model is available locally (considering tag variations).
        
        Args:
            model_name: Model name to check (e.g., 'all-minilm')
            local_models: Set of locally available model names from Ollama
            
        Returns:
            True if model is locally available
        """
        # Direct match
        if model_name in local_models:
            return True
        # Check with :latest tag
        if f"{model_name}:latest" in local_models:
            return True
        # Check normalized versions
        normalized_local = {self._normalize_model_name(m) for m in local_models}
        return self._normalize_model_name(model_name) in normalized_local
    
    async def discover_ollama_models(self) -> List[OllamaEmbeddingModel]:
        """
        Discover embedding models available from Ollama.
        
        Returns:
            List of OllamaEmbeddingModel with availability info
        """
        models = []
        local_models = set()  # Raw names from Ollama (with tags)
        local_model_info = {}  # Map normalized name -> full model info
        
        # First, get locally available models
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.ollama_host}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    for model in data.get("models", []):
                        raw_name = model.get("name", "")
                        local_models.add(raw_name)
                        
                        # Store model info by normalized name
                        normalized = self._normalize_model_name(raw_name)
                        local_model_info[normalized] = {
                            "raw_name": raw_name,
                            "size": model.get("size", 0),
                            "family": model.get("details", {}).get("family"),
                        }
                        
                        # Check if it's likely an embedding model
                        if self._is_embedding_model(raw_name):
                            # Use normalized name for consistency
                            is_registered = self.registry.is_valid_model(normalized) or \
                                          self.registry.is_valid_model(raw_name)
                            models.append(OllamaEmbeddingModel(
                                name=normalized,  # Use normalized name
                                display_name=self._format_display_name(normalized),
                                size=self._format_size(model.get("size", 0)),
                                is_local=True,
                                is_registered=is_registered,
                                dimension=self._get_known_dimension(normalized),
                                family=model.get("details", {}).get("family"),
                            ))
        except Exception as e:
            logger.warning(f"Failed to query Ollama for local models: {e}")
        
        # Track which normalized names we've already added
        added_names = {self._normalize_model_name(m.name) for m in models}
        
        # Add known embedding models that aren't local
        for model_name, dimension in self.KNOWN_DIMENSIONS.items():
            normalized = self._normalize_model_name(model_name)
            if normalized not in added_names:
                # Only add base model names (not variants except specific ones)
                if ":" not in model_name or model_name.count(":") == 1:
                    is_local = self._is_model_local(model_name, local_models)
                    raw_size = local_model_info.get(normalized, {}).get("size", "")
                    models.append(OllamaEmbeddingModel(
                        name=model_name,
                        display_name=self._format_display_name(model_name),
                        size=self._format_size(raw_size) if raw_size else "",
                        is_local=is_local,
                        is_registered=self.registry.is_valid_model(model_name),
                        dimension=dimension,
                        family=local_model_info.get(normalized, {}).get("family"),
                    ))
                    added_names.add(normalized)
        
        # Add registered models that might not be in known list
        for model_id in self.registry.list_model_ids():
            normalized = self._normalize_model_name(model_id)
            if normalized not in added_names:
                spec = self.registry.get_model(model_id)
                is_local = self._is_model_local(model_id, local_models)
                raw_size = local_model_info.get(normalized, {}).get("size", "") if is_local else ""
                models.append(OllamaEmbeddingModel(
                    name=model_id,
                    display_name=spec.display_name,
                    size=self._format_size(raw_size) if raw_size else "",
                    is_local=is_local,
                    is_registered=True,
                    dimension=spec.dimension,
                    family=local_model_info.get(normalized, {}).get("family"),
                ))
                added_names.add(normalized)
        
        # Sort: local registered first, then local unregistered, then remote
        models.sort(key=lambda m: (
            not m.is_local,
            not m.is_registered,
            m.name
        ))
        
        return models
    
    async def detect_model_dimension(self, model_name: str) -> int:
        """
        Detect the embedding dimension for a model.
        
        Generates a test embedding and measures the dimension.
        
        Args:
            model_name: Ollama model name
            
        Returns:
            Detected embedding dimension
            
        Raises:
            RuntimeError: If dimension detection fails
        """
        # First check if we already know the dimension
        known_dim = self._get_known_dimension(model_name)
        if known_dim:
            logger.info(f"Using known dimension for {model_name}: {known_dim}")
            return known_dim
        
        # Check if already registered
        if self.registry.is_valid_model(model_name):
            return self.registry.get_dimension(model_name)
        
        # Generate test embedding
        logger.info(f"🔍 Detecting embedding dimension for: {model_name}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_host}/api/embed",
                    json={
                        "model": model_name,
                        "input": "test embedding"
                    }
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    raise RuntimeError(f"Ollama embedding failed: {error_text}")
                
                data = response.json()
                embeddings = data.get("embeddings", [])
                
                if not embeddings or not embeddings[0]:
                    raise RuntimeError("Empty embedding returned")
                
                dimension = len(embeddings[0])
                logger.info(f"✅ Detected dimension for {model_name}: {dimension}")
                
                return dimension
                
        except httpx.TimeoutException:
            raise RuntimeError(f"Timeout detecting dimension for {model_name}")
        except Exception as e:
            raise RuntimeError(f"Failed to detect dimension for {model_name}: {e}")
    
    async def ensure_model_registered(
        self,
        model_name: str,
        auto_detect: bool = True,
    ) -> EmbeddingModelSpec:
        """
        Ensure a model is registered in the registry.
        
        If not registered, detects dimension and registers it.
        
        Args:
            model_name: Model identifier
            auto_detect: Automatically detect dimension if unknown
            
        Returns:
            EmbeddingModelSpec for the model
        """
        # Already registered?
        if self.registry.is_valid_model(model_name):
            return self.registry.get_model(model_name)
        
        # Need to detect and register
        if not auto_detect:
            raise ValueError(f"Model {model_name} not registered and auto_detect=False")
        
        dimension = await self.detect_model_dimension(model_name)
        
        return self.registry.register_dynamic_model(
            model_id=model_name,
            dimension=dimension,
            ollama_model_name=model_name,
        )
    
    async def pull_and_register(
        self,
        model_name: str,
        progress_callback: Optional[Callable[..., Any]] = None,
    ) -> "EmbeddingModelSpec":
        """
        Pull an Ollama model and register it.
        
        Args:
            model_name: Model to pull
            progress_callback: Optional callback for progress updates
            
        Returns:
            EmbeddingModelSpec for the registered model
            
        Raises:
            RuntimeError: If pulling the model fails
        """
        # Pull the model
        success = await self._pull_model(model_name, progress_callback)
        
        if not success:
            raise RuntimeError(f"Failed to pull model: {model_name}")
        
        # Detect dimension and register
        spec = await self.ensure_model_registered(model_name)
        
        return spec
    
    async def _pull_model(
        self,
        model_name: str,
        progress_callback: Optional[Callable[..., Any]] = None,
    ) -> bool:
        """Pull a model from Ollama registry."""
        logger.info(f"🔄 Pulling Ollama embedding model: {model_name}")
        pull_succeeded = False
        last_error: Optional[str] = None
        
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{self.ollama_host}/api/pull",
                    json={"name": model_name, "stream": True},
                ) as response:
                    if response.status_code != 200:
                        logger.error(f"Failed to pull model: {response.status_code}")
                        return False
                    
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        
                        try:
                            import json
                            data = json.loads(line)

                            # Ollama can return HTTP 200 with stream-level error payload.
                            error_message = data.get("error")
                            if error_message:
                                last_error = str(error_message)
                                logger.error(f"Ollama pull error for {model_name}: {last_error}")
                                return False

                            status = data.get("status", "")
                            status_lower = status.lower()

                            if "error" in status_lower:
                                last_error = status
                                logger.error(f"Ollama pull failed for {model_name}: {status}")
                                return False
                            
                            total = data.get("total", 0)
                            completed = data.get("completed", 0)
                            percent = (completed / total * 100) if total > 0 else 0
                            
                            if progress_callback:
                                await asyncio.to_thread(progress_callback, status, percent)
                            
                            if "success" in status_lower:
                                pull_succeeded = True
                                logger.info(f"✅ Model pulled successfully: {model_name}")
                                return True
                        except Exception:
                            pass

                    # Some Ollama versions may not emit an explicit "success" status.
                    # Verify local availability before declaring success.
                    is_local = await self.is_model_available_locally(model_name)
                    if pull_succeeded or is_local:
                        logger.info(f"✅ Model pull completed: {model_name}")
                        return True

                    if last_error:
                        logger.error(f"❌ Model pull did not complete: {model_name} ({last_error})")
                    else:
                        logger.error(f"❌ Model pull did not complete for {model_name}; model not found locally after pull")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
    
    def _is_embedding_model(self, name: str) -> bool:
        """Check if a model name looks like an embedding model."""
        name_lower = name.lower()
        return any(pattern in name_lower for pattern in self.EMBEDDING_MODEL_PATTERNS)
    
    def _get_known_dimension(self, model_name: str) -> Optional[int]:
        """Get known dimension for a model."""
        # Check exact match
        if model_name in self.KNOWN_DIMENSIONS:
            return self.KNOWN_DIMENSIONS[model_name]
        
        # Check base name (without tag)
        base_name = model_name.split(":")[0]
        if base_name in self.KNOWN_DIMENSIONS:
            return self.KNOWN_DIMENSIONS[base_name]
        
        return None
    
    # Known display names for better formatting
    DISPLAY_NAME_OVERRIDES: Dict[str, str] = {
        "bge-large": "BGE Large",
        "bge-m3": "BGE M3 (Multilingual)",
        "nomic-embed-text": "Nomic Embed Text",
        "nomic-embed-text-v2-moe": "Nomic Embed Text v2",
        "all-minilm": "All MiniLM",
        "mxbai-embed-large": "MxBai Embed Large",
        "snowflake-arctic-embed": "Snowflake Arctic Embed",
        "snowflake-arctic-embed2": "Snowflake Arctic Embed 2",
        "embeddinggemma": "Embedding Gemma",
        "qwen3-embedding": "Qwen3 Embedding",
        "paraphrase-multilingual": "Paraphrase Multilingual",
        "granite-embedding": "Granite Embedding",
    }
    
    def _format_display_name(self, model_name: str) -> str:
        """Format a model name for display with proper capitalization."""
        # Check for known display name override
        base_name = model_name.split(":")[0]
        if base_name in self.DISPLAY_NAME_OVERRIDES:
            # Handle size variants like bge-base:latest
            suffix = ""
            if ":" in model_name:
                variant = model_name.split(":")[1]
                if variant != "latest":
                    suffix = f" ({variant})"
            return self.DISPLAY_NAME_OVERRIDES[base_name] + suffix
        
        # Fallback: Basic formatting with common abbreviation handling
        name = model_name.replace("-", " ").replace("_", " ")
        
        # Handle common abbreviations that should be uppercase
        abbreviations = ["bge", "gte", "e5", "mxbai", "llm", "nlp", "api"]
        words = name.split()
        formatted_words = []
        for word in words:
            if word.lower() in abbreviations:
                formatted_words.append(word.upper())
            else:
                formatted_words.append(word.title())
        
        return " ".join(formatted_words)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human-readable string."""
        if size_bytes == 0:
            return ""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    async def is_model_available_locally(self, model_name: str) -> bool:
        """
        Check if a model is available locally in Ollama.
        
        This is a public async method that queries Ollama to check
        if a model has been pulled and is ready to use.
        
        Args:
            model_name: Model name to check (e.g., "bge-large")
            
        Returns:
            True if model is available locally, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.ollama_host}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    local_models = set()
                    for model in data.get("models", []):
                        raw_name = model.get("name", "")
                        local_models.add(raw_name)
                        # Also add normalized name
                        local_models.add(self._normalize_model_name(raw_name))
                    
                    return self._is_model_local(model_name, local_models)
                return False
        except Exception as e:
            logger.warning(f"Failed to check if model {model_name} is local: {e}")
            return False


# =============================================================================
# SINGLETON ACCESSOR
# =============================================================================

_service_instance: Optional[EmbeddingModelService] = None

def get_embedding_model_service() -> EmbeddingModelService:
    """Get singleton embedding model service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = EmbeddingModelService()
    return _service_instance


async def auto_register_local_embedding_models() -> Dict[str, Any]:
    """
    Auto-register any local Ollama embedding models on startup.
    
    This ensures that previously downloaded embedding models are available
    immediately after a container restart without needing to re-download.
    
    Returns:
        Dict with registration results
    """
    from app.core.logger import logger
    
    service = get_embedding_model_service()
    registered = []
    skipped = []
    failed = []
    
    try:
        # Get local models from Ollama
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{service.ollama_host}/api/tags")
            if response.status_code != 200:
                logger.warning("Could not connect to Ollama for auto-registration")
                return {"registered": [], "skipped": [], "failed": [], "error": "Ollama unavailable"}
            
            data = response.json()
            local_models = data.get("models", [])
            
            for model in local_models:
                raw_name = model.get("name", "")
                normalized_name = service._normalize_model_name(raw_name)
                
                # Check if it's an embedding model
                if not service._is_embedding_model(normalized_name):
                    continue
                
                # Check if already registered (built-in or dynamic)
                if service.registry.is_valid_model(normalized_name):
                    skipped.append(normalized_name)
                    continue
                
                # Try to register it
                try:
                    # Check if we have a known dimension
                    known_dim = service._get_known_dimension(normalized_name)
                    
                    if known_dim:
                        # Use known dimension (fast path)
                        service.registry.register_dynamic_model(
                            model_id=normalized_name,
                            dimension=known_dim,
                            ollama_model_name=normalized_name,
                        )
                        registered.append({"name": normalized_name, "dimension": known_dim})
                        logger.info(f"✅ Auto-registered embedding model: {normalized_name} ({known_dim}D)")
                    else:
                        # Need to detect dimension (slow path - generates test embedding)
                        dimension = await service.detect_model_dimension(normalized_name)
                        service.registry.register_dynamic_model(
                            model_id=normalized_name,
                            dimension=dimension,
                            ollama_model_name=normalized_name,
                        )
                        registered.append({"name": normalized_name, "dimension": dimension})
                        logger.info(f"✅ Auto-registered embedding model: {normalized_name} ({dimension}D) [detected]")
                        
                except Exception as e:
                    failed.append({"name": normalized_name, "error": str(e)})
                    logger.warning(f"Failed to auto-register {normalized_name}: {e}")
    
    except Exception as e:
        logger.warning(f"Auto-registration of embedding models failed: {e}")
        return {"registered": [], "skipped": [], "failed": [], "error": str(e)}
    
    if registered:
        logger.info(f"🎉 Auto-registered {len(registered)} embedding model(s) from Ollama")
    
    return {
        "registered": registered,
        "skipped": skipped,
        "failed": failed,
    }
