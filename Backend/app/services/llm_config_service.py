"""
LLM Configuration Service - CRUD operations for LLM provider configurations

Provides:
- Create, Read, Update, Delete for LLM configs
- Encryption/decryption of API keys
- Default config management
- Connection testing
- Provider factory integration

Usage:
    from app.services.llm_config_service import LLMConfigService
    
    service = LLMConfigService(db_session)
    
    # Create new config
    config = await service.create_config(user_id, {
        "name": "My OpenAI",
        "provider": "openai",
        "model_name": "gpt-4",
        "api_key": "sk-...",  # Will be encrypted
    })
    
    # Test connectivity
    result = await service.test_connection(config.config_id)
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.exc import IntegrityError

from app.core.logger import logger
from app.core.encryption import (
    encrypt_api_key,
    decrypt_api_key,
    mask_api_key,
    is_encryption_configured,
)
from app.models.database_models import LLMProviderConfig, UserSettings
from app.llm.provider_factory import LLMProviderFactory
from app.llm.providers.base import (
    ConnectionTestResult,
)


# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

from pydantic import BaseModel, Field, field_validator
import re


class LLMProviderConfigCreate(BaseModel):
    """Schema for creating a new LLM config"""
    name: str = Field(..., min_length=1, max_length=100, description="User-friendly name")
    provider: str = Field(..., description="Provider type: openai, google, ollama, etc.")
    model_name: str = Field(..., min_length=1, max_length=200, description="Model identifier")
    api_key: Optional[str] = Field(None, description="API key (will be encrypted)")
    base_url: Optional[str] = Field(None, description="Custom base URL")
    model_type: str = Field(default="chat", description="Model capability type")
    config_params: Optional[Dict[str, Any]] = Field(default=None, description="Generation parameters")
    is_default: bool = Field(default=False, description="Set as default provider")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name contains only safe characters to prevent XSS/injection"""
        if not re.match(r'^[\w\s\-\.\(\)]+$', v):
            raise ValueError(
                'Name can only contain letters, numbers, spaces, hyphens, dots, and parentheses'
            )
        return v.strip()
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate provider is alphanumeric with underscores only"""
        if not re.match(r'^[a-z][a-z0-9_]*$', v.lower()):
            raise ValueError('Provider must be lowercase alphanumeric with underscores')
        return v.lower().strip()
    
    @field_validator('model_name')
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        """Validate model_name contains only safe characters"""
        if not re.match(r'^[\w\s\-\.:/@]+$', v):
            raise ValueError(
                'Model name can only contain letters, numbers, spaces, hyphens, dots, colons, slashes, and @'
            )
        return v.strip()


class LLMProviderConfigUpdate(BaseModel):
    """Schema for updating an LLM config"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    model_name: Optional[str] = Field(None, min_length=1, max_length=200)
    api_key: Optional[str] = None  # If provided, will be re-encrypted
    base_url: Optional[str] = None
    model_type: Optional[str] = None
    config_params: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate name contains only safe characters"""
        if v is None:
            return v
        if not re.match(r'^[\w\s\-\.\(\)]+$', v):
            raise ValueError(
                'Name can only contain letters, numbers, spaces, hyphens, dots, and parentheses'
            )
        return v.strip()
    
    @field_validator('model_name')
    @classmethod
    def validate_model_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate model_name contains only safe characters"""
        if v is None:
            return v
        if not re.match(r'^[\w\s\-\.:/@]+$', v):
            raise ValueError(
                'Model name can only contain letters, numbers, spaces, hyphens, dots, colons, slashes, and @'
            )
        return v.strip()


class LLMProviderConfigResponse(BaseModel):
    """Schema for API response"""
    config_id: UUID
    name: str
    provider: str
    model_name: str
    base_url: Optional[str]
    model_type: str
    config_params: Dict[str, Any]
    is_default: bool
    is_active: bool
    has_api_key: bool
    api_key_masked: Optional[str]
    last_tested_at: Optional[datetime]
    last_test_success: Optional[bool]
    last_test_message: Optional[str]
    last_test_latency_ms: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# =============================================================================
# SERVICE CLASS
# =============================================================================

class LLMConfigService:
    """
    Service for managing LLM provider configurations.
    
    Handles:
    - CRUD operations with encryption
    - Default config management  
    - Connection testing via providers
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =========================================================================
    # CREATE
    # =========================================================================
    
    async def create_config(
        self,
        user_id: UUID,
        data: LLMProviderConfigCreate,
    ) -> LLMProviderConfig:
        """
        Create a new LLM provider configuration.
        
        Args:
            user_id: User's UUID
            data: Configuration data
            
        Returns:
            Created LLMProviderConfig
        """
        # Check for duplicate name (Issue #4: Data Integrity)
        existing_name = await self.db.execute(
            select(LLMProviderConfig).where(
                and_(
                    LLMProviderConfig.u_id == user_id,
                    LLMProviderConfig.name == data.name
                )
            )
        )
        if existing_name.scalar_one_or_none():
            raise ValueError(f"A configuration named '{data.name}' already exists")
        
        # Encrypt API key if provided
        encrypted_key = None
        if data.api_key:
            if not is_encryption_configured():
                raise ValueError(
                    "API key encryption not configured. "
                    "Set SECRET_KEY_ENCRYPTION in .env"
                )
            encrypted_key = encrypt_api_key(data.api_key)
        
        # Default config params
        config_params = data.config_params or {
            "temperature": 0.7,
            "max_tokens": 4096,
            "top_p": 0.9,
            "timeout": 120.0,
            "max_retries": 3,
        }
        
        # Create config
        config = LLMProviderConfig(
            u_id=user_id,
            name=data.name,
            provider=data.provider.lower(),
            model_name=data.model_name,
            base_url=data.base_url,
            api_key_encrypted=encrypted_key,
            model_type=data.model_type,
            config_params=config_params,
            is_default=1 if data.is_default else 0,
            is_active=1,
        )
        
        self.db.add(config)
        
        try:
            await self.db.flush()  # Ensure config_id is assigned before use
            
            # If this is set as default, unset other defaults
            if data.is_default:
                await self._set_single_default(user_id, config.config_id)
            
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise ValueError(f"A configuration named '{data.name}' already exists")
        
        await self.db.refresh(config)
        
        logger.info(f"Created LLM config: id={config.config_id}")
        
        return config
    
    # =========================================================================
    # READ
    # =========================================================================
    
    async def get_config(self, config_id: UUID) -> Optional[LLMProviderConfig]:
        """Get a specific config by ID"""
        result = await self.db.execute(
            select(LLMProviderConfig).where(LLMProviderConfig.config_id == config_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_configs(
        self,
        user_id: UUID,
        active_only: bool = True,
    ) -> List[LLMProviderConfig]:
        """Get all configs for a user"""
        query = select(LLMProviderConfig).where(LLMProviderConfig.u_id == user_id)
        
        if active_only:
            query = query.where(LLMProviderConfig.is_active == 1)
        
        query = query.order_by(LLMProviderConfig.is_default.desc(), LLMProviderConfig.name)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_default_config(self, user_id: UUID) -> Optional[LLMProviderConfig]:
        """Get user's default LLM config"""
        result = await self.db.execute(
            select(LLMProviderConfig).where(
                and_(
                    LLMProviderConfig.u_id == user_id,
                    LLMProviderConfig.is_default == 1,
                    LLMProviderConfig.is_active == 1,
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_config_by_provider(
        self,
        user_id: UUID,
        provider: str,
    ) -> Optional[LLMProviderConfig]:
        """Get first active config for a specific provider"""
        result = await self.db.execute(
            select(LLMProviderConfig).where(
                and_(
                    LLMProviderConfig.u_id == user_id,
                    LLMProviderConfig.provider == provider.lower(),
                    LLMProviderConfig.is_active == 1,
                )
            ).limit(1)
        )
        return result.scalar_one_or_none()
    
    # =========================================================================
    # UPDATE
    # =========================================================================
    
    async def update_config(
        self,
        config_id: UUID,
        data: LLMProviderConfigUpdate,
        user_id: Optional[UUID] = None,
    ) -> Optional[LLMProviderConfig]:
        """Update an existing config
        
        Args:
            config_id: The config ID to update
            data: Update data
            user_id: If provided, verify ownership before updating
        """
        config = await self.get_config(config_id)
        if not config:
            return None
        
        # Verify ownership if user_id is provided
        if user_id is not None and config.u_id != user_id:
            logger.warning(f"Ownership check failed: config {config_id} belongs to {config.u_id}, not {user_id}")
            return None
        
        # Update fields
        if data.name is not None:
            config.name = data.name
        if data.model_name is not None:
            config.model_name = data.model_name
        if data.base_url is not None:
            config.base_url = data.base_url
        if data.model_type is not None:
            config.model_type = data.model_type
        if data.config_params is not None:
            config.config_params = data.config_params
        if data.is_active is not None:
            config.is_active = 1 if data.is_active else 0
        
        # Re-encrypt API key if provided
        if data.api_key is not None:
            if data.api_key == "":
                config.api_key_encrypted = None
            else:
                # SECURITY FIX: Never store API keys in plaintext
                if not is_encryption_configured():
                    raise ValueError(
                        "Cannot store API key: encryption not configured. "
                        "Set SECRET_KEY_ENCRYPTION in environment variables."
                    )
                config.api_key_encrypted = encrypt_api_key(data.api_key)
        
        await self.db.commit()
        await self.db.refresh(config)
        
        logger.info(f"Updated LLM config: id={config.config_id}")
        
        return config
    
    async def set_default(self, user_id: UUID, config_id: UUID) -> bool:
        """Set a config as the user's default (atomic operation)"""
        config = await self.get_config(config_id)
        if not config or config.u_id != user_id:
            return False
        
        # Perform both updates in a single transaction
        await self._set_single_default(user_id, config_id)
        
        # Also update user_settings
        await self.db.execute(
            update(UserSettings)
            .where(UserSettings.u_id == user_id)
            .values(default_llm_config_id=config_id)
        )
        
        # Single commit for atomicity
        await self.db.commit()
        
        logger.info(f"Set default LLM config: {config.name}")
        return True
    
    async def _set_single_default(self, user_id: UUID, config_id: UUID):
        """Ensure only one config is default for user (atomic operation using CASE)"""
        from sqlalchemy import case
        
        # SECURITY FIX: Use single atomic UPDATE with CASE expression
        # This prevents race conditions when concurrent requests set different defaults
        await self.db.execute(
            update(LLMProviderConfig)
            .where(LLMProviderConfig.u_id == user_id)
            .values(
                is_default=case(
                    (LLMProviderConfig.config_id == config_id, 1),
                    else_=0
                )
            )
        )
    
    # =========================================================================
    # DELETE
    # =========================================================================
    
    async def delete_config(self, config_id: UUID, user_id: Optional[UUID] = None) -> bool:
        """Delete a config, handling UserSettings references
        
        Args:
            config_id: The config ID to delete
            user_id: If provided, verify ownership before deleting
        """
        # Load the config first to verify ownership
        config = await self.get_config(config_id)
        if not config:
            return False
        
        # Verify ownership if user_id is provided
        if user_id is not None and config.u_id != user_id:
            logger.warning(f"Ownership check failed for delete: config {config_id} belongs to {config.u_id}, not {user_id}")
            return False
        
        # First, clear any UserSettings that reference this config
        await self.db.execute(
            update(UserSettings)
            .where(UserSettings.default_llm_config_id == config_id)
            .values(default_llm_config_id=None)
        )
        
        result = await self.db.execute(
            delete(LLMProviderConfig).where(LLMProviderConfig.config_id == config_id)
        )
        await self.db.commit()
        
        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"Deleted LLM config: {config_id}")
        
        return deleted
    
    # =========================================================================
    # CONNECTION TESTING
    # =========================================================================
    
    async def test_connection(self, config_id: UUID) -> ConnectionTestResult:
        """
        Test connectivity for a config.
        
        Creates a provider instance and performs a test generation.
        Updates the config with test results.
        """
        config = await self.get_config(config_id)
        if not config:
            return ConnectionTestResult(
                success=False,
                message="Configuration not found",
                error_code="NOT_FOUND",
            )
        
        # Decrypt API key
        decrypted_key = None
        if config.api_key_encrypted:
            try:
                decrypted_key = decrypt_api_key(config.api_key_encrypted)
            except Exception as e:
                # SECURITY FIX: Don't expose decryption details in error message
                logger.error(f"API key decryption failed for config {config_id}: {e}")
                return ConnectionTestResult(
                    success=False,
                    message="Failed to decrypt API key. The encryption key may have changed.",
                    error_code="DECRYPTION_ERROR",
                )
        
        # Create provider
        try:
            config_params = config.config_params or {}
            provider = LLMProviderFactory.create(
                provider_type=config.provider,
                model=config.model_name,
                api_key=decrypted_key,
                base_url=config.base_url,
                timeout=config_params.get("timeout", 120.0),
                max_retries=1,  # Only one attempt for testing
            )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message=f"Failed to create provider: {e}",
                error_code="PROVIDER_ERROR",
            )
        
        # Run test
        result = await provider.test_connection()
        
        # Update config with test results
        # Use timezone-naive for PostgreSQL TIMESTAMP WITHOUT TIME ZONE columns
        config.last_tested_at = datetime.now(timezone.utc).replace(tzinfo=None)
        config.last_test_success = 1 if result.success else 0
        config.last_test_message = result.message
        config.last_test_latency_ms = result.latency_ms
        
        await self.db.commit()
        
        return result
    
    # =========================================================================
    # PROVIDER CREATION
    # =========================================================================
    
    async def get_provider_for_config(self, config_id: UUID):
        """
        Get a ready-to-use provider instance for a config.
        
        Returns:
            Configured BaseLLMProvider instance
        """
        config = await self.get_config(config_id)
        if not config:
            raise ValueError(f"Config not found: {config_id}")
        
        decrypted_key = None
        if config.api_key_encrypted:
            try:
                decrypted_key = decrypt_api_key(config.api_key_encrypted)
            except Exception as e:
                logger.error(f"Failed to decrypt API key for config {config_id}: {e}")
                # Leave decrypted_key as None - the provider may still work without a key
                # or will fail with a clear error message
        
        config_params = config.config_params or {}
        return LLMProviderFactory.create(
            provider_type=config.provider,
            model=config.model_name,
            api_key=decrypted_key,
            base_url=config.base_url,
            timeout=config_params.get("timeout", 120.0),
            max_retries=config_params.get("max_retries", 3),
        )
    
    async def get_default_provider(self, user_id: UUID):
        """
        Get user's default LLM provider instance.
        
        Falls back to environment-based provider if no config.
        """
        config = await self.get_default_config(user_id)
        
        if config:
            return await self.get_provider_for_config(config.config_id)
        
        # Fallback to environment-based provider
        from app.llm.provider_factory import get_default_provider
        return await get_default_provider()
    
    # =========================================================================
    # RESPONSE FORMATTING
    # =========================================================================
    
    def to_response(self, config: LLMProviderConfig) -> LLMProviderConfigResponse:
        """Convert DB model to API response with masked key"""
        # Mask API key for display
        api_key_masked = None
        if config.api_key_encrypted:
            try:
                decrypted = decrypt_api_key(config.api_key_encrypted)
                api_key_masked = mask_api_key(decrypted)
            except Exception:
                api_key_masked = "***encrypted***"
        
        return LLMProviderConfigResponse(
            config_id=config.config_id,
            name=config.name,
            provider=config.provider,
            model_name=config.model_name,
            base_url=config.base_url,
            model_type=config.model_type,
            config_params=config.config_params or {},
            is_default=config.is_default == 1,
            is_active=config.is_active == 1,
            has_api_key=config.api_key_encrypted is not None,
            api_key_masked=api_key_masked,
            last_tested_at=config.last_tested_at,
            last_test_success=config.last_test_success == 1 if config.last_test_success is not None else None,
            last_test_message=config.last_test_message,
            last_test_latency_ms=float(config.last_test_latency_ms) if config.last_test_latency_ms else None,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )
