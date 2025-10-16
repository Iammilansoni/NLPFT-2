"""
Singleton Model Manager for managing heavy ML models across the application.
Ensures only one instance of each model is loaded in memory.
"""

import threading
from typing import Optional, Dict, Any
from transformers import AutoTokenizer, pipeline
import torch
from sentence_transformers import SentenceTransformer

from app.core.logger import logger


class ModelManager:
    """Singleton class to manage ML model instances"""
    
    _instance: Optional['ModelManager'] = None
    _lock = threading.Lock()
    
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
        self._models: Dict[str, Any] = {}
        self._loading_lock = threading.Lock()
        logger.info("🤖 ModelManager initialized")
    
    def get_embedding_model(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> SentenceTransformer:
        """Get or load embedding model (cached)"""
        cache_key = f"embedding:{model_name}"
        
        if cache_key not in self._models:
            with self._loading_lock:
                # Double-check after acquiring lock
                if cache_key not in self._models:
                    logger.info(f"📥 Loading embedding model: {model_name}")
                    # Use local_files_only=True to fail fast if not cached
                    # This prevents unnecessary network calls
                    try:
                        self._models[cache_key] = SentenceTransformer(
                            model_name,
                            device='cpu'  # Explicit CPU for consistency
                        )
                        logger.info(f"✅ Embedding model loaded: {model_name}")
                    except Exception as e:
                        logger.warning(f"⚠️ Loading from cache failed, downloading: {e}")
                        self._models[cache_key] = SentenceTransformer(model_name)
                        logger.info(f"✅ Embedding model loaded: {model_name}")
        
        return self._models[cache_key]
    
    def get_llm_pipeline(
        self,
        model_name: str = "microsoft/Phi-3-mini-4k-instruct",
        use_quantization: bool = True
    ) -> Optional[Any]:
        """Get or load LLM pipeline (cached)"""
        cache_key = f"llm:{model_name}"
        
        if cache_key not in self._models:
            with self._loading_lock:
                # Double-check after acquiring lock
                if cache_key not in self._models:
                    logger.info(f"📥 Loading LLM model: {model_name}")
                    logger.info(f"   This may take a few minutes on first load...")
                    
                    try:
                        tokenizer = AutoTokenizer.from_pretrained(
                            model_name,
                            trust_remote_code=True,
                            use_fast=True  # Use fast tokenizer for better performance
                        )
                        
                        llm_pipeline = pipeline(
                            "text-generation",
                            model=model_name,
                            tokenizer=tokenizer,
                            device=-1,  # CPU
                            trust_remote_code=True,
                            dtype=torch.float32,
                            model_kwargs={
                                "use_cache": False,  # Fix DynamicCache error
                                "low_cpu_mem_usage": True  # Reduce memory usage during loading
                            }
                        )
                        
                        self._models[cache_key] = {
                            "pipeline": llm_pipeline,
                            "tokenizer": tokenizer
                        }
                        
                        logger.info(f"✅ LLM model loaded successfully: {model_name}")
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to load LLM model: {e}")
                        self._models[cache_key] = None
                        return None
        
        model_data = self._models.get(cache_key)
        return model_data["pipeline"] if model_data else None
    
    def get_llm_tokenizer(self, model_name: str = "microsoft/Phi-3-mini-4k-instruct") -> Optional[Any]:
        """Get LLM tokenizer (loads pipeline if not already loaded)"""
        cache_key = f"llm:{model_name}"
        
        # Ensure pipeline is loaded
        self.get_llm_pipeline(model_name)
        
        model_data = self._models.get(cache_key)
        return model_data["tokenizer"] if model_data else None
    
    def is_llm_loaded(self, model_name: str = "microsoft/Phi-3-mini-4k-instruct") -> bool:
        """Check if LLM model is already loaded"""
        cache_key = f"llm:{model_name}"
        return cache_key in self._models and self._models[cache_key] is not None
    
    def unload_model(self, model_type: str, model_name: str):
        """Unload a specific model from memory"""
        cache_key = f"{model_type}:{model_name}"
        if cache_key in self._models:
            del self._models[cache_key]
            logger.info(f"🗑️ Unloaded model: {cache_key}")
    
    def clear_all_models(self):
        """Clear all loaded models from memory"""
        self._models.clear()
        logger.info("🗑️ All models cleared from memory")


# Global singleton instance
model_manager = ModelManager()
