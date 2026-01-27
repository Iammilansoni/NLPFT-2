"""
User Embedding Settings Service - Settings page is the SOURCE OF TRUTH

🎯 Purpose:
This service manages user embedding model preferences and ensures
the Settings page is the SINGLE SOURCE OF TRUTH for all embedding operations.

❗ NON-NEGOTIABLE RULES:
1. Settings page controls which embedding model is used
2. All dataset embeddings MUST use the model from Settings
3. All vector searches MUST use the model from Settings
4. Dashboard CANNOT override Settings silently
5. Any mismatch MUST be explicitly surfaced to the user

📐 Architecture:
- UserSettings.default_embedding_model is the ACTIVE model
- UserSettings.embedding_dimension is derived from the model
- All components query this service before embedding/searching
"""

import uuid
import asyncio
from typing import Optional, Tuple, Dict, Any, Set
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, update

from app.core.logger import logger

# Module-level tracking for in-flight model pulls to prevent duplicates
_in_flight_pulls: Set[str] = set()
_in_flight_lock = asyncio.Lock()
from app.core.embedding_model_registry import (
    get_embedding_registry,
    EmbeddingModelSpec
)
from app.models.database_models import UserSettings, User


class UserEmbeddingSettingsService:
    """
    Service for managing user embedding model settings.
    
    This is the AUTHORITATIVE source for:
    - What embedding model a user has selected
    - What dimension their vectors should be
    - Which Redis index/namespace to use
    
    ❗ CRITICAL: All embedding and search operations MUST
    query this service to get the active model.
    """
    
    def __init__(self):
        self.registry = get_embedding_registry()
    
    # ===========================================================================
    # SYNC METHODS (for use in sync contexts)
    # ===========================================================================
    
    def get_active_embedding_model_sync(
        self, 
        db: Session, 
        user_id: uuid.UUID
    ) -> Tuple[str, int, EmbeddingModelSpec]:
        """
        Get user's active embedding model (SYNC version).
        
        This is the SOURCE OF TRUTH for what model to use.
        
        Args:
            db: SQLAlchemy Session
            user_id: User UUID
            
        Returns:
            Tuple of (model_id, dimension, model_spec)
        """
        user_settings = db.query(UserSettings).filter(
            UserSettings.u_id == user_id
        ).first()
        
        if user_settings and user_settings.default_embedding_model:
            model_id = user_settings.default_embedding_model
            # Always get dimension from registry (authoritative)
            try:
                model_spec = self.registry.get_model(model_id)
                dimension = model_spec.dimension
            except ValueError:
                # Model not in registry, use dimension from settings
                logger.warning(f"Model '{model_id}' not in registry, using stored dimension")
                model_spec = self.registry.get_default_model()
                dimension = user_settings.embedding_dimension or model_spec.dimension
        else:
            # Use default
            model_spec = self.registry.get_default_model()
            model_id = model_spec.model_id
            dimension = model_spec.dimension
        
        logger.info(
            f"🎯 Active embedding model for user {str(user_id)[:8]}: "
            f"{model_id} (dim={dimension})"
        )
        
        return model_id, dimension, model_spec
    
    def set_active_embedding_model_sync(
        self,
        db: Session,
        user_id: uuid.UUID,
        model_id: str
    ) -> Dict[str, Any]:
        """
        Set user's active embedding model (SYNC version).
        
        ❗ This should be called from Settings page only.
        
        Args:
            db: SQLAlchemy Session
            user_id: User UUID
            model_id: Model ID to set
            
        Returns:
            Dict with old/new model info
        """
        # Validate model exists
        model_spec = self.registry.get_model(model_id)  # Raises if invalid
        
        user_settings = db.query(UserSettings).filter(
            UserSettings.u_id == user_id
        ).first()
        
        old_model = None
        old_dimension = None
        
        if user_settings:
            old_model = user_settings.default_embedding_model
            old_dimension = user_settings.embedding_dimension
            user_settings.default_embedding_model = model_id
            user_settings.embedding_dimension = model_spec.dimension
            user_settings.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        else:
            # Create settings
            user_settings = UserSettings(
                u_id=user_id,
                default_embedding_model=model_id,
                embedding_dimension=model_spec.dimension
            )
            db.add(user_settings)
        
        db.commit()
        db.refresh(user_settings)
        
        logger.info(
            f"✅ Updated embedding model for user {str(user_id)[:8]}: "
            f"{old_model} -> {model_id}"
        )
        
        return {
            "success": True,
            "user_id": str(user_id),
            "old_model": old_model,
            "old_dimension": old_dimension,
            "new_model": model_id,
            "new_dimension": model_spec.dimension,
            "redis_index": model_spec.redis_index_name,
            "redis_namespace": model_spec.redis_namespace
        }
    
    # ===========================================================================
    # ASYNC METHODS (for use in async contexts)
    # ===========================================================================
    
    async def get_active_embedding_model_async(
        self, 
        db: AsyncSession, 
        user_id: uuid.UUID,
        auto_register: bool = True
    ) -> Tuple[str, int, EmbeddingModelSpec]:
        """
        Get user's active embedding model (ASYNC version).
        
        This is the SOURCE OF TRUTH for what model to use.
        
        If the model is not in the registry but exists in Ollama,
        it will be dynamically registered (dimension detected).
        
        Args:
            db: AsyncSession
            user_id: User UUID
            auto_register: If True, dynamically register unregistered models from Ollama
            
        Returns:
            Tuple of (model_id, dimension, model_spec)
        """
        result = await db.execute(
            select(UserSettings).where(UserSettings.u_id == user_id)
        )
        user_settings = result.scalar_one_or_none()
        
        if user_settings and user_settings.default_embedding_model:
            model_id = user_settings.default_embedding_model
            # Always get dimension from registry (authoritative)
            try:
                model_spec = self.registry.get_model(model_id)
                dimension = model_spec.dimension
            except ValueError:
                # Model not in registry - try to dynamically register it
                if auto_register:
                    logger.info(f"Model '{model_id}' not in registry, attempting dynamic registration...")
                    model_spec = await self._try_register_model_async(model_id)
                    if model_spec:
                        dimension = model_spec.dimension
                        logger.info(f"✅ Dynamically registered model '{model_id}' with dimension {dimension}")
                    else:
                        # Could not register - fall back to default model entirely
                        logger.warning(f"Model '{model_id}' not in registry and could not be registered, using default")
                        model_spec = self.registry.get_default_model()
                        model_id = model_spec.model_id  # Use default model_id too!
                        dimension = model_spec.dimension
                else:
                    logger.warning(f"Model '{model_id}' not in registry, using default")
                    model_spec = self.registry.get_default_model()
                    model_id = model_spec.model_id  # Use default model_id too!
                    dimension = model_spec.dimension
        else:
            # Use default
            model_spec = self.registry.get_default_model()
            model_id = model_spec.model_id
            dimension = model_spec.dimension
        
        logger.info(
            f"🎯 Active embedding model for user {str(user_id)[:8]}: "
            f"{model_id} (dim={dimension})"
        )
        
        return model_id, dimension, model_spec
    
    async def _try_register_model_async(self, model_id: str, auto_pull: bool = True) -> Optional[EmbeddingModelSpec]:
        """
        Try to dynamically register a model by detecting its dimension from Ollama.
        
        This handles the case where a model was previously pulled and set as default,
        but the dynamic registration was lost (e.g., after container restart).
        
        If auto_pull is True and the model is not available locally, it will be
        automatically pulled from Ollama (this may take time for large models).
        
        Args:
            model_id: Model identifier (e.g., "bge-large")
            auto_pull: If True, schedule a background pull of the model from Ollama if not available locally
            
        Returns:
            EmbeddingModelSpec if registered successfully, None otherwise (including when background pull is scheduled)
        """
        try:
            import asyncio
            from app.services.embedding_model_service import get_embedding_model_service
            
            service = get_embedding_model_service()
            
            # Check if model is available in Ollama
            is_available = await service.is_model_available_locally(model_id)
            
            if not is_available:
                if auto_pull:
                    # Check if pull is already in-flight to prevent duplicates
                    async with _in_flight_lock:
                        if model_id in _in_flight_pulls:
                            logger.info(f"Model '{model_id}' pull already in-flight, skipping duplicate")
                            return None
                        _in_flight_pulls.add(model_id)
                    
                    # Don't block - schedule background pull and return None immediately
                    logger.info(f"Model '{model_id}' not in Ollama, scheduling background pull...")
                    
                    async def _background_pull():
                        try:
                            spec = await service.pull_and_register(model_id)
                            logger.info(f"✅ Background pull complete: model '{model_id}' (dim={spec.dimension})")
                        except Exception as pull_error:
                            logger.error(f"Background pull failed for model '{model_id}': {pull_error}")
                        finally:
                            # Always remove from in-flight set
                            async with _in_flight_lock:
                                _in_flight_pulls.discard(model_id)
                                logger.debug(f"Removed '{model_id}' from in-flight pulls")
                    
                    # Fire and forget - don't await
                    asyncio.create_task(_background_pull())
                    return None
                else:
                    logger.warning(f"Model '{model_id}' is not available in Ollama, cannot register")
                    return None
            
            # Model is available locally - detect dimension and register
            spec = await service.ensure_model_registered(model_id, auto_detect=True)
            return spec
            
        except Exception as e:
            logger.error(f"Failed to dynamically register model '{model_id}': {e}")
            return None
    
    async def set_active_embedding_model_async(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        model_id: str
    ) -> Dict[str, Any]:
        """
        Set user's active embedding model (ASYNC version).
        
        ❗ This should be called from Settings page only.
        
        Args:
            db: AsyncSession
            user_id: User UUID
            model_id: Model ID to set
            
        Returns:
            Dict with old/new model info
        """
        # Validate model exists
        model_spec = self.registry.get_model(model_id)  # Raises if invalid
        
        result = await db.execute(
            select(UserSettings).where(UserSettings.u_id == user_id)
        )
        user_settings = result.scalar_one_or_none()
        
        old_model = None
        old_dimension = None
        
        if user_settings:
            old_model = user_settings.default_embedding_model
            old_dimension = user_settings.embedding_dimension
            user_settings.default_embedding_model = model_id
            user_settings.embedding_dimension = model_spec.dimension
            user_settings.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        else:
            # Create settings
            user_settings = UserSettings(
                u_id=user_id,
                default_embedding_model=model_id,
                embedding_dimension=model_spec.dimension
            )
            db.add(user_settings)
        
        await db.commit()
        await db.refresh(user_settings)
        
        logger.info(
            f"✅ Updated embedding model for user {str(user_id)[:8]}: "
            f"{old_model} -> {model_id}"
        )
        
        return {
            "success": True,
            "user_id": str(user_id),
            "old_model": old_model,
            "old_dimension": old_dimension,
            "new_model": model_id,
            "new_dimension": model_spec.dimension,
            "redis_index": model_spec.redis_index_name,
            "redis_namespace": model_spec.redis_namespace
        }
    
    async def ensure_settings_exist_async(
        self,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> UserSettings:
        """
        Ensure user settings exist, creating with defaults if not.
        
        Args:
            db: AsyncSession
            user_id: User UUID
            
        Returns:
            UserSettings instance
        """
        result = await db.execute(
            select(UserSettings).where(UserSettings.u_id == user_id)
        )
        user_settings = result.scalar_one_or_none()
        
        if not user_settings:
            default_model = self.registry.get_default_model()
            user_settings = UserSettings(
                u_id=user_id,
                default_embedding_model=default_model.model_id,
                embedding_dimension=default_model.dimension,
                auto_embed_on_generation=1
            )
            db.add(user_settings)
            await db.commit()
            await db.refresh(user_settings)
            logger.info(f"Created default settings for user {str(user_id)[:8]}")
        
        return user_settings
    
    # ===========================================================================
    # VALIDATION METHODS
    # ===========================================================================
    
    def validate_model_for_search(
        self,
        user_model_id: str,
        dataset_model_id: str
    ) -> Dict[str, Any]:
        """
        Validate if user's model matches dataset's model.
        
        ❗ CRITICAL: This MUST be called before any vector search.
        
        Returns compatibility info with clear actions if mismatched.
        """
        return self.registry.validate_model_compatibility(
            dataset_model_id=dataset_model_id,
            search_model_id=user_model_id
        )
    
    async def check_dataset_compatibility_async(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        dataset_model_id: str
    ) -> Dict[str, Any]:
        """
        Check if user's current model is compatible with a dataset.
        
        Args:
            db: AsyncSession
            user_id: User UUID
            dataset_model_id: Model ID the dataset was embedded with
            
        Returns:
            Compatibility info with actions
        """
        # Get user's active model
        user_model_id, user_dimension, _ = await self.get_active_embedding_model_async(
            db, user_id
        )
        
        # Check compatibility
        result = self.validate_model_for_search(user_model_id, dataset_model_id)
        
        # Add user context
        result["user_active_model"] = user_model_id
        result["user_active_dimension"] = user_dimension
        
        return result


# =============================================================================
# SINGLETON ACCESSOR
# =============================================================================

_service_instance: Optional[UserEmbeddingSettingsService] = None


def get_user_embedding_settings_service() -> UserEmbeddingSettingsService:
    """Get the singleton user embedding settings service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = UserEmbeddingSettingsService()
    return _service_instance
