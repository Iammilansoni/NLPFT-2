# Backend\app\core\embedding_model_registry.py
"""
Embedding Model Registry - SINGLE SOURCE OF TRUTH for all embedding models

Purpose:
This registry is the FOUNDATION of the multi-embedding model system.
Every component in the system MUST use this registry for model information.

NON-NEGOTIABLE RULES:
1. All embedding models MUST be registered here
2. All model lookups MUST go through this registry
3. Model dimensions are IMMUTABLE once defined
4. Redis index names and namespaces are DERIVED from this registry
5. NO component should hardcode model dimensions or index names

Architecture:
- Each model has a unique model_id (used everywhere)
- Each model has an exact dimension (no approximations)
- Each model has a dedicated Redis index (dimension-safe)
- Each model has a dedicated namespace (prevents cross-contamination)

Thread-safe singleton pattern for production use.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum
from dataclasses import dataclass
from functools import lru_cache
import threading

from app.core.logger import logger


# =============================================================================
# ENUMS
# =============================================================================

class ModelSpeed(str, Enum):
    """Model inference speed classification"""
    FAST = "fast"
    MODERATE = "moderate"
    SLOW = "slow"


class ModelAccuracy(str, Enum):
    """Model accuracy classification"""
    GOOD = "good"
    EXCELLENT = "excellent"
    SUPERIOR = "superior"


class ModelCategory(str, Enum):
    """Model category for UI grouping"""
    LIGHTWEIGHT = "lightweight"
    BALANCED = "balanced"
    HIGH_ACCURACY = "high_accuracy"


# =============================================================================
# CORE DATA CLASSES
# =============================================================================

@dataclass(frozen=True)
class EmbeddingModelSpec:
    """
    Immutable embedding model specification.
    
    Using frozen=True ensures:
    - Model specs cannot be modified after creation
    - Safe for concurrent access
    - Hashable for caching
    
    ❗ CRITICAL: 'dimension' is the EXACT output dimension from the model.
    This MUST match the actual model output - no approximations allowed.
    """
    # Core identity (IMMUTABLE)
    model_id: str                   # Unique identifier, e.g., "nomic-embed-text"
    dimension: int                  # EXACT vector dimension (384, 768, 1024, etc.)
    
    # Display metadata
    display_name: str               # Human-readable name for UI
    description: str                # Brief description
    
    # Performance characteristics
    speed: ModelSpeed               # CPU inference speed
    accuracy: ModelAccuracy         # Quality classification
    category: ModelCategory         # UI grouping
    
    # Context and parameters
    max_context_length: int         # Maximum input tokens
    parameters: str                 # Model size string, e.g., "~137M"
    
    # UI metadata
    color: str                      # Accent color for UI
    icon: str                       # Icon identifier
    best_for: tuple                 # Use case bullets (tuple for immutability)
    
    # Ollama integration
    ollama_model_name: str          # Actual Ollama model name
    ollama_pull_cmd: str            # Installation command
    
    # Computed properties
    @property
    def redis_index_name(self) -> str:
        """
        Get the Redis index name for this model.
        
        Format: idx_vectors_{model_id}
        Example: idx_vectors_nomic
        
        Each model gets its own index to ensure:
        - Dimension isolation (vectors of different dims never mix)
        - Performance optimization (smaller, focused indices)
        - Easy maintenance (can rebuild one model's index)
        """
        # Sanitize model_id for Redis (replace special chars with underscore)
        safe_id = self.model_id.replace("-", "_").replace(".", "_").replace("/", "_").lower()
        return f"idx_vectors_{safe_id}"
    
    @property
    def redis_namespace(self) -> str:
        """
        Get the Redis key namespace for this model.
        
        Format: vector:{model_id}
        Example: vector:nomic
        
        All keys for this model will be prefixed with this namespace:
        vector:nomic:{user_id}:{dataset_id}:{row_id}
        
        This ensures:
        - Vectors from different models NEVER share keys
        - Easy bulk operations (delete all vectors for a model)
        - Clear audit trail in Redis
        """
        safe_id = self.model_id.replace("-", "_").replace(".", "_").replace("/", "_").lower()
        return f"vector:{safe_id}"
    
    @property
    def legacy_index_name(self) -> str:
        """
        Legacy index name for backward compatibility.
        Maps dimension -> old index naming convention.
        """
        return f"embeddings_{self.dimension}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "model_id": self.model_id,
            "display_name": self.display_name,
            "dimension": self.dimension,
            "description": self.description,
            "speed": self.speed.value,
            "accuracy": self.accuracy.value,
            "category": self.category.value,
            "max_context_length": self.max_context_length,
            "parameters": self.parameters,
            "color": self.color,
            "icon": self.icon,
            "best_for": list(self.best_for),
            "redis_index_name": self.redis_index_name,
            "redis_namespace": self.redis_namespace,
            "ollama_model_name": self.ollama_model_name,
            "ollama_pull_cmd": self.ollama_pull_cmd,
        }


# =============================================================================
# MODEL REGISTRY SINGLETON
# =============================================================================

class EmbeddingModelRegistry:
    """
    Thread-safe singleton registry for all embedding models.
    
    Usage:
        registry = get_embedding_registry()
        model = registry.get_model("nomic-embed-text")
        dimension = model.dimension
        index_name = model.redis_index_name
    
    ❗ CRITICAL: This is the ONLY place model specs should be defined.
    All other components MUST query this registry.
    """
    
    _instance: Optional['EmbeddingModelRegistry'] = None
    _lock: threading.Lock = threading.Lock()
    
    # ===========================================================================
    # REGISTERED MODELS - ADD NEW MODELS HERE
    # ===========================================================================
    _MODELS: Dict[str, EmbeddingModelSpec] = {
        # Model 1: Nomic-Embed-Text (Primary, recommended)
        "nomic-embed-text": EmbeddingModelSpec(
            model_id="nomic-embed-text",
            dimension=768,
            display_name="Nomic Embed Text",
            description="High-quality 768-dim embeddings with 8K context. Best balance of speed and accuracy.",
            speed=ModelSpeed.FAST,
            accuracy=ModelAccuracy.EXCELLENT,
            category=ModelCategory.BALANCED,
            max_context_length=8192,
            parameters="~137M",
            color="green",
            icon="rocket",
            best_for=(
                "General semantic search",
                "RAG applications",
                "Production workloads",
                "8K context support"
            ),
            ollama_model_name="nomic-embed-text",
            ollama_pull_cmd="ollama pull nomic-embed-text"
        ),
        
        # Model 2: All-MiniLM (Lightweight, fast)
        "all-minilm": EmbeddingModelSpec(
            model_id="all-minilm",
            dimension=384,
            display_name="All-MiniLM L6",
            description="Lightweight 384-dim embeddings. Fastest inference, lower memory.",
            speed=ModelSpeed.FAST,
            accuracy=ModelAccuracy.GOOD,
            category=ModelCategory.LIGHTWEIGHT,
            max_context_length=512,
            parameters="~22M",
            color="blue",
            icon="bolt",
            best_for=(
                "Fast prototyping",
                "Low-resource environments",
                "High-throughput applications",
                "CPU-only deployments"
            ),
            ollama_model_name="all-minilm",
            ollama_pull_cmd="ollama pull all-minilm"
        ),
        
        # Model 3: MxBai Embed Large (High-accuracy)
        "mxbai-embed-large": EmbeddingModelSpec(
            model_id="mxbai-embed-large",
            dimension=1024,
            display_name="MxBai Embed Large",
            description="High-accuracy 1024-dim embeddings. Strong performance on diverse tasks.",
            speed=ModelSpeed.MODERATE,
            accuracy=ModelAccuracy.SUPERIOR,
            category=ModelCategory.HIGH_ACCURACY,
            max_context_length=512,
            parameters="~335M",
            color="orange",
            icon="fire",
            best_for=(
                "Maximum accuracy",
                "Diverse domain coverage",
                "High-precision retrieval",
                "Enterprise applications"
            ),
            ollama_model_name="mxbai-embed-large",
            ollama_pull_cmd="ollama pull mxbai-embed-large"
        ),
    }
    
    # Default model
    DEFAULT_MODEL_ID = "nomic-embed-text"
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._dimension_to_models: Dict[int, List[str]] = {}
        self._build_dimension_index()
        logger.info(f"📚 EmbeddingModelRegistry initialized with {len(self._MODELS)} models")
    
    def _build_dimension_index(self):
        """Build reverse index from dimension to model IDs."""
        for model_id, spec in self._MODELS.items():
            if spec.dimension not in self._dimension_to_models:
                self._dimension_to_models[spec.dimension] = []
            self._dimension_to_models[spec.dimension].append(model_id)
    
    # ===========================================================================
    # PUBLIC API
    # ===========================================================================
    
    def get_model(self, model_id: str) -> EmbeddingModelSpec:
        """
        Get model specification by ID.
        
        Args:
            model_id: Model identifier (e.g., "nomic-embed-text")
            
        Returns:
            EmbeddingModelSpec for the model
            
        Raises:
            ValueError: If model_id is not registered
        """
        if model_id not in self._MODELS:
            available = list(self._MODELS.keys())
            raise ValueError(
                f"Unknown embedding model: '{model_id}'. "
                f"Available models: {available}"
            )
        return self._MODELS[model_id]
    
    def get_model_or_default(self, model_id: Optional[str]) -> EmbeddingModelSpec:
        """
        Get model specification, falling back to default if not found.
        
        Args:
            model_id: Model identifier (can be None)
            
        Returns:
            EmbeddingModelSpec for the model or default
        """
        if not model_id:
            return self._MODELS[self.DEFAULT_MODEL_ID]
        try:
            return self.get_model(model_id)
        except ValueError:
            logger.warning(f"Unknown model '{model_id}', using default '{self.DEFAULT_MODEL_ID}'")
            return self._MODELS[self.DEFAULT_MODEL_ID]
    
    def get_dimension(self, model_id: str) -> int:
        """
        Get the EXACT dimension for a model.
        
        ❗ This is the authoritative source for dimensions.
        Never guess or approximate dimensions.
        """
        return self.get_model(model_id).dimension
    
    def get_redis_index(self, model_id: str) -> str:
        """Get Redis index name for a model."""
        return self.get_model(model_id).redis_index_name
    
    def get_redis_namespace(self, model_id: str) -> str:
        """Get Redis key namespace for a model."""
        return self.get_model(model_id).redis_namespace
    
    def list_models(self) -> List[Dict[str, Any]]:
        """Get all registered models as dictionaries."""
        return [spec.to_dict() for spec in self._MODELS.values()]
    
    def list_model_ids(self) -> List[str]:
        """Get all registered model IDs."""
        return list(self._MODELS.keys())
    
    def get_models_by_dimension(self, dimension: int) -> List[EmbeddingModelSpec]:
        """Get all models with a specific dimension."""
        model_ids = self._dimension_to_models.get(dimension, [])
        return [self._MODELS[mid] for mid in model_ids]
    
    def get_default_model(self) -> EmbeddingModelSpec:
        """Get the default embedding model."""
        return self._MODELS[self.DEFAULT_MODEL_ID]
    
    def is_valid_model(self, model_id: str) -> bool:
        """Check if a model ID is registered."""
        return model_id in self._MODELS
    
    def validate_model_compatibility(
        self, 
        dataset_model_id: str, 
        search_model_id: str
    ) -> Dict[str, Any]:
        """
        Validate if two models are compatible for search.
        
        Models are compatible ONLY if they are the SAME model.
        Different models with same dimension are NOT compatible
        (different training = different vector space).
        
        Args:
            dataset_model_id: Model used to embed the dataset
            search_model_id: Model user wants to search with
            
        Returns:
            Dictionary with compatibility info and recommendations
        """
        if dataset_model_id == search_model_id:
            return {
                "compatible": True,
                "message": "Models match - search will work correctly",
                "dataset_model": dataset_model_id,
                "search_model": search_model_id
            }
        
        # Get model specs (with fallback for unknown models)
        try:
            dataset_spec = self.get_model(dataset_model_id)
            dataset_dim = dataset_spec.dimension
            dataset_display = dataset_spec.display_name
        except ValueError:
            dataset_dim = 0
            dataset_display = dataset_model_id
        
        try:
            search_spec = self.get_model(search_model_id)
            search_dim = search_spec.dimension
            search_display = search_spec.display_name
        except ValueError:
            search_dim = 0
            search_display = search_model_id
        
        return {
            "compatible": False,
            "message": (
                f"Model mismatch: Dataset embedded with '{dataset_display}' ({dataset_dim}D), "
                f"but search using '{search_display}' ({search_dim}D). "
                f"Vectors from different models occupy different vector spaces and cannot be compared."
            ),
            "dataset_model": dataset_model_id,
            "dataset_dimension": dataset_dim,
            "dataset_display_name": dataset_display,
            "search_model": search_model_id,
            "search_dimension": search_dim,
            "search_display_name": search_display,
            "options": [
                {
                    "action": "use_dataset_model",
                    "label": f"Use {dataset_display}",
                    "description": "Switch your settings to use the dataset's model. No re-embedding needed.",
                    "recommended": True  # Cheaper option
                },
                {
                    "action": "reembed_dataset",
                    "label": f"Re-embed with {search_display}",
                    "description": f"Re-embed the entire dataset using {search_display}. This may take time.",
                    "recommended": False  # Expensive option
                }
            ]
        }
    
    def get_all_redis_indexes(self) -> Dict[str, str]:
        """
        Get mapping of all model IDs to their Redis index names.
        Useful for initializing all indexes at startup.
        """
        return {
            model_id: spec.redis_index_name 
            for model_id, spec in self._MODELS.items()
        }
    
    def get_all_dimensions(self) -> List[int]:
        """Get all unique dimensions supported."""
        return list(self._dimension_to_models.keys())


# =============================================================================
# SINGLETON ACCESSOR
# =============================================================================

@lru_cache(maxsize=1)
def get_embedding_registry() -> EmbeddingModelRegistry:
    """
    Get the singleton embedding model registry.
    
    This is the ONLY way to access the registry.
    Using @lru_cache ensures the singleton is created once and reused.
    
    Usage:
        from app.core.embedding_model_registry import get_embedding_registry
        
        registry = get_embedding_registry()
        model = registry.get_model("nomic-embed-text")
    """
    return EmbeddingModelRegistry()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_model_dimension(model_id: str) -> int:
    """Convenience function to get model dimension."""
    return get_embedding_registry().get_dimension(model_id)


def get_model_redis_index(model_id: str) -> str:
    """Convenience function to get model's Redis index name."""
    return get_embedding_registry().get_redis_index(model_id)


def get_model_redis_namespace(model_id: str) -> str:
    """Convenience function to get model's Redis namespace."""
    return get_embedding_registry().get_redis_namespace(model_id)


def validate_models_compatible(dataset_model: str, search_model: str) -> Dict[str, Any]:
    """Convenience function to validate model compatibility."""
    return get_embedding_registry().validate_model_compatibility(dataset_model, search_model)


def get_default_model_id() -> str:
    """Get the default model ID."""
    return get_embedding_registry().DEFAULT_MODEL_ID


def list_available_models() -> List[Dict[str, Any]]:
    """List all available models as dictionaries."""
    return get_embedding_registry().list_models()