"""
Model Service - Model registry management and queries
"""

from typing import List, Optional, Dict, Any
import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.database_models import Model
from app.core.logger import logger


class ModelService:
    """Service for managing model registry"""
    
    @staticmethod
    async def get_all_models(
        db: AsyncSession,
        model_type: Optional[str] = None,
        status: Optional[str] = None,
        cpu_friendly: Optional[bool] = None
    ) -> List[Model]:
        """
        Get all models with optional filters
        
        Args:
            db: Database session
            model_type: Filter by type ('embedding' or 'llm')
            status: Filter by status ('active' or 'deprecated')
            cpu_friendly: Filter CPU-friendly models
            
        Returns:
            List of Model objects
        """
        query = select(Model)
        
        filters = []
        if model_type:
            filters.append(Model.type == model_type)
        if status:
            filters.append(Model.status == status)
        if cpu_friendly is not None:
            filters.append(Model.cpu_friendly == (1 if cpu_friendly else 0))
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.order_by(Model.type, Model.dimension)
        
        result = await db.execute(query)
        models = result.scalars().all()
        
        logger.info(f"Retrieved {len(models)} models (type={model_type}, status={status})")
        return models
    
    @staticmethod
    async def get_model_by_id(db: AsyncSession, model_id: str) -> Optional[Model]:
        """Get model by ID"""
        query = select(Model).where(Model.model_id == model_id)
        result = await db.execute(query)
        model = result.scalar_one_or_none()
        
        if model:
            logger.info(f"Retrieved model: {model_id}")
        else:
            logger.warning(f"Model not found: {model_id}")
        
        return model
    
    @staticmethod
    async def get_embedding_models(db: AsyncSession, status: str = "active") -> List[Model]:
        """Get all embedding models"""
        return await ModelService.get_all_models(db, model_type="embedding", status=status)
    
    @staticmethod
    async def get_llm_models(db: AsyncSession, status: str = "active") -> List[Model]:
        """Get all LLM models"""
        return await ModelService.get_all_models(db, model_type="llm", status=status)
    
    @staticmethod
    def load_config_file() -> Dict[str, Any]:
        """
        Load models configuration from JSON file
        
        Returns:
            Dictionary with models config
        """
        config_path = Path(__file__).parent.parent.parent / "config" / "models.json"
        
        if not config_path.exists():
            logger.warning(f"Models config file not found: {config_path}")
            return {
                "embedding_models": [],
                "llm_models": [],
                "default_models": {}
            }
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            logger.info(f"Loaded models config from: {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading models config: {e}")
            return {
                "embedding_models": [],
                "llm_models": [],
                "default_models": {}
            }
    
    @staticmethod
    async def get_default_models(db: AsyncSession) -> Dict[str, str]:
        """
        Get default models (first try config file, fallback to DB)
        
        Returns:
            Dictionary with default model IDs by type
        """
        # Try config file first
        config = ModelService.load_config_file()
        if config.get("default_models"):
            return config["default_models"]
        
        # Fallback to DB
        embedding_models = await ModelService.get_embedding_models(db)
        llm_models = await ModelService.get_llm_models(db)
        
        defaults = {}
        if embedding_models:
            # Prefer nomic-embed-text (non-Chinese)
            default_embedding = next(
                (m for m in embedding_models if m.model_id == "nomic-embed-text"),
                embedding_models[0]
            )
            defaults["embedding"] = default_embedding.model_id
        
        if llm_models:
            # Prefer llama3.1:8b-instruct-q4_K_M (Ollama local)
            default_llm = next(
                (m for m in llm_models if m.model_id == "llama3.1:8b-instruct-q4_K_M"),
                llm_models[0]
            )
            defaults["llm"] = default_llm.model_id
        
        return defaults
    
    @staticmethod
    async def validate_model_compatibility(
        db: AsyncSession,
        current_model_id: str,
        new_model_id: str
    ) -> Dict[str, Any]:
        """
        Check if two models are compatible (same dimension)
        
        Args:
            db: Database session
            current_model_id: Current model ID
            new_model_id: New model ID to migrate to
            
        Returns:
            Dictionary with compatibility info
        """
        current_model = await ModelService.get_model_by_id(db, current_model_id)
        new_model = await ModelService.get_model_by_id(db, new_model_id)
        
        if not current_model or not new_model:
            return {
                "compatible": False,
                "reason": "One or both models not found"
            }
        
        if current_model.type != new_model.type:
            return {
                "compatible": False,
                "reason": f"Different types: {current_model.type} vs {new_model.type}"
            }
        
        if current_model.type == "embedding":
            if current_model.dimension != new_model.dimension:
                return {
                    "compatible": False,
                    "reason": f"Different dimensions: {current_model.dimension} vs {new_model.dimension}",
                    "requires_reembedding": True
                }
        
        return {
            "compatible": True,
            "reason": "Models are compatible",
            "requires_reembedding": False
        }
    
    @staticmethod
    async def sync_models_from_config(db: AsyncSession) -> Dict[str, Any]:
        """
        Sync database models with config/models.json (single source of truth)
        
        This ensures the database stays in sync with the config file.
        - Adds new models from config
        - Updates existing models if config changed
        - Marks models as deprecated if removed from config
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with sync statistics
        """
        config = ModelService.load_config_file()
        
        if not config:
            logger.warning("Cannot sync: config file not loaded")
            return {"error": "Config file not available"}
        
        stats = {
            "added": 0,
            "updated": 0,
            "deprecated": 0,
            "unchanged": 0
        }
        
        # Get all config models
        config_model_ids = set()
        config_models = []
        
        # Process embedding models from config
        for model in config.get('embedding_models', []):
            config_model_ids.add(model['model_id'])
            config_models.append({
                'model_id': model['model_id'],
                'type': 'embedding',
                'name': model['name'],
                'dimension': model['dimension'],
                'context_tokens': model['context_tokens'],
                'cpu_friendly': model['cpu_friendly'],
                'notes': model.get('notes', ''),
                'provider': model['provider'],
                'status': model.get('status', 'active')
            })
        
        # Process LLM models from config
        for model in config.get('llm_models', []):
            config_model_ids.add(model['model_id'])
            config_models.append({
                'model_id': model['model_id'],
                'type': 'llm',
                'name': model['name'],
                'dimension': None,
                'context_tokens': model['context_tokens'],
                'cpu_friendly': not model.get('api_required', True),
                'notes': model.get('notes', ''),
                'provider': model['provider'],
                'status': model.get('status', 'active')
            })
        
        # Get all existing DB models
        db_models = await ModelService.get_all_models(db, status=None)  # Get all statuses
        db_model_ids = {m.model_id for m in db_models}
        
        # Add or update models from config
        for config_model in config_models:
            existing = await ModelService.get_model_by_id(db, config_model['model_id'])
            
            if not existing:
                # Add new model
                new_model = Model(**config_model)
                db.add(new_model)
                stats["added"] += 1
                logger.info(f"Added new model from config: {config_model['model_id']}")
            else:
                # Check if update needed
                needs_update = False
                for key, value in config_model.items():
                    if key == 'model_id':
                        continue
                    if getattr(existing, key) != value:
                        setattr(existing, key, value)
                        needs_update = True
                
                if needs_update:
                    stats["updated"] += 1
                    logger.info(f"Updated model from config: {config_model['model_id']}")
                else:
                    stats["unchanged"] += 1
        
        # Mark models not in config as deprecated (don't delete, preserve history)
        for db_model in db_models:
            if db_model.model_id not in config_model_ids and db_model.status != 'deprecated':
                db_model.status = 'deprecated'
                stats["deprecated"] += 1
                logger.warning(f"Marked model as deprecated (not in config): {db_model.model_id}")
        
        await db.commit()
        
        logger.info(f"Sync complete: {stats}")
        return stats


# Singleton
_model_service = ModelService()

def get_model_service() -> ModelService:
    """Get global ModelService instance"""
    return _model_service
