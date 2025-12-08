"""
Models Configuration - Ollama Embedding Models & LLM Metadata

🎯 Embedding Model System:
- All embeddings run through Ollama HTTP API (localhost:11434)
- No HuggingFace/SentenceTransformers dependency
- Models are user-selectable from Settings page
- Strict model-dataset compatibility enforcement
"""

from typing import List, Dict, Optional
from pydantic import BaseModel
from enum import Enum


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


class EmbeddingModelInfo(BaseModel):
    """Enhanced Ollama Embedding Model Metadata"""
    model_id: str                   # Ollama model name (e.g., "nomic-embed-text")
    display_name: str               # UI display name
    dimension: int                  # Vector dimension (384, 768, 1024)
    parameters: str                 # Model size (e.g., "~137M")
    context_length: str             # Max context (e.g., "8192 tokens")
    speed: ModelSpeed               # CPU inference speed
    accuracy: ModelAccuracy         # Quality classification
    color: str                      # UI accent color (blue, green, red, etc.)
    icon: str                       # Icon identifier for frontend
    best_for: List[str]             # Use case bullets
    why_choose: str                 # Marketing description
    ollama_pull_cmd: str            # Install command


class LLMInfo(BaseModel):
    """LLM metadata for dataset generation"""
    llm_id: str
    display_name: str
    description: str
    best_for: str


# =============================================================================
# OLLAMA EMBEDDING MODELS
# =============================================================================

EMBEDDING_MODELS: List[EmbeddingModelInfo] = [
    # � All-MiniLM - Super Fast Lightweight
    EmbeddingModelInfo(
        model_id="all-minilm",
        display_name="All-MiniLM",
        dimension=384,
        parameters="~22 Million",
        context_length="256-512 tokens",
        speed=ModelSpeed.FAST,
        accuracy=ModelAccuracy.GOOD,
        color="blue",
        icon="zap",
        best_for=[
            "Real-time applications",
            "Low-latency search",
            "Massive datasets",
            "High-speed indexing"
        ],
        why_choose="Perfect for speed-focused scenarios and handling millions of records with minimal compute cost.",
        ollama_pull_cmd="ollama pull all-minilm"
    ),
    
    # 🟩 Nomic-Embed-Text - Recommended Default
    EmbeddingModelInfo(
        model_id="nomic-embed-text",
        display_name="Nomic-Embed-Text",
        dimension=768,
        parameters="~137 Million",
        context_length="8192 tokens",
        speed=ModelSpeed.FAST,
        accuracy=ModelAccuracy.EXCELLENT,
        color="green",
        icon="rocket",
        best_for=[
            "General semantic search",
            "RAG applications",
            "High-quality embeddings",
            "Most production workloads"
        ],
        why_choose="The recommended default model offering the best balance between speed, context, and accuracy.",
        ollama_pull_cmd="ollama pull nomic-embed-text"
    ),
    
    # 🟥 MXBai-Embed-Large - Maximum Precision
    EmbeddingModelInfo(
        model_id="mxbai-embed-large",
        display_name="MXBai-Embed-Large",
        dimension=1024,
        parameters="~335 Million",
        context_length="512 tokens",
        speed=ModelSpeed.MODERATE,
        accuracy=ModelAccuracy.SUPERIOR,
        color="red",
        icon="target",
        best_for=[
            "Precision-critical search",
            "Legal, medical, enterprise retrieval",
            "Engineering documents",
            "When accuracy matters most"
        ],
        why_choose="Ideal for scenarios requiring maximum semantic precision and deep document understanding.",
        ollama_pull_cmd="ollama pull mxbai-embed-large"
    )
]

# =============================================================================
# DATASET GENERATION LLMs (Ollama Local)
# =============================================================================

DATASET_LLMS: List[LLMInfo] = [
    LLMInfo(
        llm_id="llama3.2:3b-instruct-q4_K_M",
        display_name="Llama 3.2 Instruct (Ollama)",
        description="Local CPU inference with quantized Llama 3.2 Instruct - optimized for diverse, hallucination-free CSV datasets",
        best_for="Complex schemas, high variation, edge cases, local inference"
    ),
    LLMInfo(
        llm_id="gemma2:2b-instruct-q4_K_M",
        display_name="Gemma 2B (Ollama Fallback)",
        description="Lightweight fallback model for faster CPU inference when Llama is unavailable",
        best_for="Speed, lighter CPU loads, quick generation"
    )
]

# =============================================================================
# DEFAULTS
# =============================================================================

DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_DATASET_LLM = "llama3.2:3b-instruct-q4_K_M"

# Model dimension lookup
MODEL_DIMENSIONS = {
    "all-minilm": 384,
    "nomic-embed-text": 768,
    "mxbai-embed-large": 1024
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_embedding_model_info(model_id: str) -> EmbeddingModelInfo:
    """Get embedding model info by ID"""
    for model in EMBEDDING_MODELS:
        if model.model_id == model_id:
            return model
    raise ValueError(f"Unknown embedding model: {model_id}. Available: {[m.model_id for m in EMBEDDING_MODELS]}")


def get_model_dimension(model_id: str) -> int:
    """Get embedding dimension for a model"""
    return MODEL_DIMENSIONS.get(model_id, 768)


def get_llm_info(llm_id: str) -> LLMInfo:
    """Get LLM info by ID"""
    for llm in DATASET_LLMS:
        if llm.llm_id == llm_id:
            return llm
    raise ValueError(f"Unknown LLM: {llm_id}")


def get_all_embedding_models() -> List[Dict]:
    """Get all embedding models as dict for API response"""
    return [model.model_dump() for model in EMBEDDING_MODELS]


def get_all_llms() -> List[Dict]:
    """Get all LLMs as dict"""
    return [llm.model_dump() for llm in DATASET_LLMS]


def validate_model_compatibility(dataset_model: str, search_model: str) -> Dict:
    """
    Check if dataset and search models are compatible.
    Returns compatibility info and recommendations.
    """
    if dataset_model == search_model:
        return {
            "compatible": True,
            "message": "Models match - search will work correctly"
        }
    
    dataset_dim = MODEL_DIMENSIONS.get(dataset_model, 0)
    search_dim = MODEL_DIMENSIONS.get(search_model, 0)
    
    return {
        "compatible": False,
        "dataset_model": dataset_model,
        "dataset_dimension": dataset_dim,
        "search_model": search_model,
        "search_dimension": search_dim,
        "message": f"Model mismatch: Dataset embedded with '{dataset_model}' ({dataset_dim}D), but search using '{search_model}' ({search_dim}D)",
        "options": [
            {
                "action": "use_dataset_model",
                "label": f"Use {dataset_model} for search",
                "description": "Search with the same model used for embedding. No re-embedding needed.",
                "recommended": False
            },
            {
                "action": "reembed_dataset",
                "label": f"Re-embed with {search_model}",
                "description": f"Re-embed the entire dataset using {search_model}. This ensures consistency.",
                "recommended": True
            }
        ]
    }


# =============================================================================
# UI CONTENT
# =============================================================================

EMBEDDING_TOOLTIP = (
    "Embedding dimension = vector length. "
    "Larger dimensions = more accurate but slower. "
    "Choose based on your needs: fast queries (384D) vs. best accuracy (1024D)."
)

MODEL_MISMATCH_WARNING = (
    "⚠️ Model Mismatch Detected\n\n"
    "This dataset was embedded with '{embedded_model}' ({embedded_dim}D).\n"
    "You're trying to search with '{search_model}' ({search_dim}D).\n\n"
    "Vectors from different models are incompatible and will produce incorrect similarity scores."
)
