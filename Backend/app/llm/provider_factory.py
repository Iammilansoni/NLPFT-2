"""
LLM Provider Factory - Creates provider instances from configuration

This factory pattern allows dynamic creation of LLM providers based on
user configuration stored in the database.

Usage:
    from app.llm.provider_factory import LLMProviderFactory
    
    # From database config
    provider = LLMProviderFactory.create_from_db_config(llm_config)
    
    # Direct creation
    provider = LLMProviderFactory.create(
        provider_type="groq",
        model="<a model id from the model catalogue>",
        api_key="gsk_...",
    )
"""

from typing import Any, Dict, List, Optional, Type

from app.core.logger import logger
from app.llm import provider_registry as registry
from app.llm.providers.anthropic_provider import AnthropicProvider
from app.llm.providers.base import BaseLLMProvider, ProviderError
from app.llm.providers.custom_provider import CustomHTTPProvider
from app.llm.providers.google_provider import GoogleProvider
from app.llm.providers.grok_provider import GrokProvider
from app.llm.providers.huggingface_provider import HuggingFaceProvider
from app.llm.providers.ollama_provider import OllamaLLMProvider
from app.llm.providers.openai_provider import OpenAIProvider

# Chat class per wire protocol. Every OpenAI-compatible provider in the
# registry (Groq, OpenRouter, Mistral, Together, ...) shares OpenAIProvider and
# differs only by its registry base URL.
CHAT_CLASSES: Dict[str, Type[BaseLLMProvider]] = {
    registry.OPENAI: OpenAIProvider,
    registry.GEMINI: GoogleProvider,
    registry.OLLAMA: OllamaLLMProvider,
    registry.XAI: GrokProvider,
    registry.ANTHROPIC: AnthropicProvider,
    registry.HUGGINGFACE: HuggingFaceProvider,
    registry.CUSTOM: CustomHTTPProvider,
}


# =============================================================================
# FACTORY CLASS
# =============================================================================

class LLMProviderFactory:
    """
    Factory for creating LLM provider instances.
    
    Supports:
    - Creating providers from database configuration
    - Creating providers directly with parameters
    - Validating provider configurations
    """
    
    @classmethod
    def create(
        cls,
        provider_type: str,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
        max_retries: int = 3,
        **kwargs,
    ) -> BaseLLMProvider:
        """
        Create a provider instance.
        
        Args:
            provider_type: Provider identifier (openai, google, ollama, etc.)
            model: Model name
            api_key: API key (decrypted)
            base_url: Custom base URL
            timeout: Request timeout
            max_retries: Retry attempts
            **kwargs: Additional provider-specific arguments
            
        Returns:
            Configured BaseLLMProvider instance
            
        Raises:
            ProviderError: If provider type is unsupported
        """
        spec = registry.get_provider(provider_type.lower())
        if spec is None or not spec.chat or spec.api not in CHAT_CLASSES:
            chat_ids = [p.id for p in registry.PROVIDERS if p.chat]
            raise ProviderError(f"'{provider_type}' is not a chat provider. Supported: {chat_ids}")

        # Only self-hosted providers (Ollama, custom) take a user-supplied URL.
        # OpenAI-compatible hosts use their registry endpoint; Gemini, Anthropic
        # and Hugging Face classes already know theirs.
        if spec.custom_base_url:
            base_url = base_url or None
        elif spec.api in (registry.OPENAI, registry.XAI):
            base_url = spec.base_url
        else:
            base_url = None

        logger.info(f"Creating {spec.id} provider with model: {model}")
        provider = CHAT_CLASSES[spec.api](
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )
        provider._catalog_provider = spec.id
        return provider

    @classmethod
    def create_from_db_config(
        cls,
        config: Any,  # LLMProviderConfig model
        decrypted_api_key: Optional[str] = None,
    ) -> BaseLLMProvider:
        """
        Create provider from database configuration.
        
        Args:
            config: LLMProviderConfig database model
            decrypted_api_key: Pre-decrypted API key
            
        Returns:
            Configured BaseLLMProvider instance
        """
        # Extract config parameters
        config_params = config.config_params or {}
        
        # Use longer default timeout for Ollama (local CPU inference is slow)
        default_timeout = 600.0 if config.provider == "ollama" else 120.0
        return cls.create(
            provider_type=config.provider,
            model=config.model_name,
            api_key=decrypted_api_key,
            base_url=config.base_url,
            timeout=config_params.get("timeout", default_timeout),
            max_retries=config_params.get("max_retries", 3),
        )
    
    @classmethod
    def create_from_dict(cls, config_dict: Dict[str, Any]) -> BaseLLMProvider:
        """
        Create provider from dictionary configuration.
        
        Args:
            config_dict: Configuration dictionary with provider settings
            
        Returns:
            Configured BaseLLMProvider instance
        """
        # Use longer default timeout for Ollama (local CPU inference is slow)
        default_timeout = 600.0 if config_dict.get("provider") == "ollama" else 120.0
        return cls.create(
            provider_type=config_dict["provider"],
            model=config_dict["model_name"],
            api_key=config_dict.get("api_key"),
            base_url=config_dict.get("base_url"),
            timeout=config_dict.get("timeout", default_timeout),
            max_retries=config_dict.get("max_retries", 3),
        )
    
    @classmethod
    def get_supported_providers(cls) -> List[Dict[str, Any]]:
        """Every provider in the registry, in display order, for the settings UI."""
        return [spec.public_dict() for spec in registry.PROVIDERS]

    @classmethod
    def is_provider_implemented(cls, provider_type: str) -> bool:
        """True for any registry provider a connection can be saved for."""
        return registry.get_provider(provider_type.lower()) is not None
