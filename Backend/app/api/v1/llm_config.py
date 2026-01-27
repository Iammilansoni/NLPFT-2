"""
LLM Configuration API Endpoints

Provides REST API for managing LLM provider configurations:
- CRUD operations for provider configs
- Connection testing
- Default provider management
- Provider information

All endpoints require authentication.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.core.postgres import get_db
from app.api.v1.auth import get_current_user
from app.models.database_models import User
from app.services.llm_config_service import (
    LLMConfigService,
    LLMProviderConfigCreate,
    LLMProviderConfigUpdate,
    LLMProviderConfigResponse,
)
from app.llm.provider_factory import LLMProviderFactory
from app.llm.providers.base import ProviderType


router = APIRouter(prefix="/llm-config", tags=["LLM Configuration"])


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_service(db: AsyncSession = Depends(get_db)) -> LLMConfigService:
    """Get LLM config service instance"""
    return LLMConfigService(db)


# =============================================================================
# PROVIDER INFO
# =============================================================================

@router.get("/providers", summary="List available LLM providers")
async def list_providers(
    current_user: User = Depends(get_current_user),
):
    """
    Get information about all supported LLM providers.
    
    Returns provider name, description, requirements, and default models.
    Requires authentication.
    """
    return {
        "providers": LLMProviderFactory.get_supported_providers(),
        "implemented": [
            p.value for p in ProviderType 
            if LLMProviderFactory.is_provider_implemented(p.value)
        ],
    }


# =============================================================================
# CONFIG CRUD
# =============================================================================

@router.get("", response_model=List[LLMProviderConfigResponse], summary="List user's LLM configs")
async def list_configs(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    service: LLMConfigService = Depends(get_service),
):
    """
    Get all LLM provider configurations for the current user.
    
    Args:
        active_only: Only return active configs (default: true)
    """
    configs = await service.get_user_configs(current_user.u_id, active_only=active_only)
    return [service.to_response(c) for c in configs]


@router.get("/default", response_model=Optional[LLMProviderConfigResponse], summary="Get default config")
async def get_default_config(
    current_user: User = Depends(get_current_user),
    service: LLMConfigService = Depends(get_service),
):
    """Get the user's default LLM provider configuration."""
    config = await service.get_default_config(current_user.u_id)
    
    if not config:
        return None
    
    return service.to_response(config)


@router.get("/{config_id}", response_model=LLMProviderConfigResponse, summary="Get specific config")
async def get_config(
    config_id: UUID,
    current_user: User = Depends(get_current_user),
    service: LLMConfigService = Depends(get_service),
):
    """Get a specific LLM provider configuration."""
    config = await service.get_config(config_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )
    
    if config.u_id != current_user.u_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return service.to_response(config)


@router.post("", response_model=LLMProviderConfigResponse, status_code=status.HTTP_201_CREATED, summary="Create new config")
async def create_config(
    data: LLMProviderConfigCreate,
    current_user: User = Depends(get_current_user),
    service: LLMConfigService = Depends(get_service),
):
    """
    Create a new LLM provider configuration.
    
    The API key will be encrypted before storage.
    """
    # Validate provider
    if not LLMProviderFactory.is_provider_implemented(data.provider):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider '{data.provider}' is not implemented. "
                   f"Available: {[p.value for p in ProviderType if LLMProviderFactory.is_provider_implemented(p.value)]}",
        )
    
    try:
        config = await service.create_config(current_user.u_id, data)
        return service.to_response(config)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to create LLM config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create configuration",
        )


@router.put("/{config_id}", response_model=LLMProviderConfigResponse, summary="Update config")
async def update_config(
    config_id: UUID,
    data: LLMProviderConfigUpdate,
    current_user: User = Depends(get_current_user),
    service: LLMConfigService = Depends(get_service),
):
    """
    Update an existing LLM provider configuration.
    
    Provide only the fields you want to update.
    If api_key is provided, it will be re-encrypted.
    """
    # Verify ownership
    existing = await service.get_config(config_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )
    
    if existing.u_id != current_user.u_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    try:
        config = await service.update_config(config_id, data)
        return service.to_response(config)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{config_id}", summary="Delete config")
async def delete_config(
    config_id: UUID,
    current_user: User = Depends(get_current_user),
    service: LLMConfigService = Depends(get_service),
):
    """Delete an LLM provider configuration."""
    # Verify ownership
    existing = await service.get_config(config_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )
    
    if existing.u_id != current_user.u_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    await service.delete_config(config_id)
    return {"message": "Configuration deleted successfully"}


# =============================================================================
# DEFAULT MANAGEMENT
# =============================================================================

@router.post("/{config_id}/set-default", summary="Set as default")
async def set_default_config(
    config_id: UUID,
    current_user: User = Depends(get_current_user),
    service: LLMConfigService = Depends(get_service),
):
    """Set a configuration as the user's default LLM provider."""
    success = await service.set_default(current_user.u_id, config_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found or access denied",
        )
    
    return {"message": "Default configuration updated"}


# =============================================================================
# CONNECTION TESTING
# =============================================================================

@router.post("/{config_id}/test", summary="Test connection")
async def test_connection(
    config_id: UUID,
    current_user: User = Depends(get_current_user),
    service: LLMConfigService = Depends(get_service),
):
    """
    Test connectivity for an LLM provider configuration.
    
    Performs a minimal API call to verify:
    - API key is valid
    - Model is accessible
    - Network connectivity works
    
    Results are stored on the configuration.
    """
    # Verify ownership
    existing = await service.get_config(config_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )
    
    if existing.u_id != current_user.u_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    result = await service.test_connection(config_id)
    
    return {
        "success": result.success,
        "message": result.message,
        "latency_ms": result.latency_ms,
        "model_info": result.model_info,
        "error_code": result.error_code,
    }


# =============================================================================
# OLLAMA-SPECIFIC ENDPOINTS
# =============================================================================

@router.get("/ollama/models", summary="List Ollama models")
async def list_ollama_models(
    current_user: User = Depends(get_current_user),
):
    """
    List available Ollama models (local and remote).
    
    Requires Ollama server to be running.
    """
    try:
        provider = LLMProviderFactory.create(
            provider_type="ollama",
            model="llama3.1:8b-instruct-q4_K_M",
        )
        
        if not await provider.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Ollama server is not running",
            )
        
        models = await provider.list_models()
        local_models = await provider._list_local_models()
        local_names = {m["name"] for m in local_models}
        
        return {
            "models": [
                {
                    **m.to_dict(),
                    "is_local": m.id in local_names,
                }
                for m in models
            ],
            "local_count": len(local_names),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list Ollama models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list models",
        )


@router.post("/ollama/pull", summary="Pull Ollama model")
async def pull_ollama_model(
    model_name: str,
    current_user: User = Depends(get_current_user),
):
    """
    Pull an Ollama model from the registry.
    
    This is a synchronous operation that may take several minutes
    for large models.
    """
    try:
        provider = LLMProviderFactory.create(
            provider_type="ollama",
            model=model_name,
        )
        
        if not await provider.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Ollama server is not running",
            )
        
        # Check if already available
        if await provider.is_model_available(model_name):
            return {
                "status": "already_available",
                "message": f"Model {model_name} is already available",
            }
        
        # Pull the model
        success = await provider.pull_model(model_name)
        
        if success:
            return {
                "status": "success",
                "message": f"Model {model_name} pulled successfully",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to pull model {model_name}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pull Ollama model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to pull model",
        )
