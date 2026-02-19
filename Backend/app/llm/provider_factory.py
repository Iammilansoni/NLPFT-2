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
        provider_type="openai",
        model="gpt-4",
        api_key="sk-...",
    )
"""

from typing import Optional, Dict, Any, Type

from app.core.logger import logger
from app.llm.providers.base import (
    BaseLLMProvider,
    ProviderType,
    ProviderError,
)
from app.llm.providers.openai_provider import OpenAIProvider
from app.llm.providers.google_provider import GoogleProvider
from app.llm.providers.ollama_provider import OllamaLLMProvider
from app.llm.providers.grok_provider import GrokProvider
from app.llm.providers.anthropic_provider import AnthropicProvider
from app.llm.providers.huggingface_provider import HuggingFaceProvider
from app.llm.providers.custom_provider import CustomHTTPProvider


# =============================================================================
# PROVIDER REGISTRY
# =============================================================================

PROVIDER_CLASSES: Dict[ProviderType, Type[BaseLLMProvider]] = {
    ProviderType.OPENAI: OpenAIProvider,
    ProviderType.GOOGLE: GoogleProvider,
    ProviderType.OLLAMA: OllamaLLMProvider,
    ProviderType.GROK: GrokProvider,  # xAI Grok
    ProviderType.DEEPSEEK: OpenAIProvider,  # DeepSeek uses OpenAI-compatible API
    ProviderType.ANTHROPIC: AnthropicProvider,  # Anthropic Claude
    ProviderType.HUGGINGFACE: HuggingFaceProvider,  # HuggingFace Inference
    ProviderType.CUSTOM: CustomHTTPProvider,  # Custom HTTP endpoints
}

# Default base URLs for providers using OpenAI-compatible API
COMPATIBLE_BASE_URLS: Dict[ProviderType, str] = {
    ProviderType.DEEPSEEK: "https://api.deepseek.com/v1",
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
        # Parse provider type
        try:
            ptype = ProviderType(provider_type.lower())
        except ValueError:
            raise ProviderError(
                f"Unsupported provider type: '{provider_type}'. "
                f"Supported: {[p.value for p in PROVIDER_CLASSES.keys()]}"
            )
        
        # Get provider class
        provider_class = PROVIDER_CLASSES.get(ptype)
        if not provider_class:
            raise ProviderError(f"Provider not implemented: {ptype.value}")
        
        # Handle OpenAI-compatible providers with custom base URLs
        if ptype in COMPATIBLE_BASE_URLS and not base_url:
            base_url = COMPATIBLE_BASE_URLS[ptype]
        
        # Create provider instance
        logger.info(f"Creating {ptype.value} provider with model: {model}")
        
        return provider_class(
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )
    
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
    def get_supported_providers(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get information about supported providers.
        
        Returns:
            Dictionary of provider info
        """
        return {
            ProviderType.OPENAI.value: {
                "name": "OpenAI",
                "description": "GPT-5.x, o3/o4 Reasoning, GPT-4.1, GPT-4o, Open-Weight OSS",
                "requires_api_key": True,
                "supports_custom_base_url": True,
                "default_models": ["gpt-5.2", "gpt-5-mini", "o3", "gpt-4.1", "gpt-4o", "gpt-oss-120b"],
                "implemented": True,
            },
            ProviderType.GOOGLE.value: {
                "name": "Google Gemini",
                "description": "Gemini 3.0, 2.5 Pro/Flash, 2.0 Flash, 1.5 series",
                "requires_api_key": True,
                "supports_custom_base_url": False,
                "default_models": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"],
                "implemented": True,
            },
            ProviderType.GROK.value: {
                "name": "xAI Grok",
                "description": "Grok 4/3 models from xAI with reasoning and vision capabilities",
                "requires_api_key": True,
                "supports_custom_base_url": False,
                "default_models": ["grok-3", "grok-4", "grok-4-fast-reasoning"],
                "implemented": True,
            },
            ProviderType.OLLAMA.value: {
                "name": "Ollama",
                "description": "Local LLMs (Llama, Mistral, Qwen, DeepSeek, etc.)",
                "requires_api_key": False,
                "supports_custom_base_url": True,
                "default_models": ["llama3.1:8b-instruct-q4_K_M", "mistral:7b-instruct-q4_K_M", "qwen2.5:7b-instruct-q4_K_M"],
                "implemented": True,
            },
            ProviderType.DEEPSEEK.value: {
                "name": "DeepSeek",
                "description": "DeepSeek Chat, Coder, and R1 Reasoning models",
                "requires_api_key": True,
                "supports_custom_base_url": True,
                "default_models": ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
                "implemented": True,
            },
            ProviderType.ANTHROPIC.value: {
                "name": "Anthropic Claude",
                "description": "Claude 4 Opus/Sonnet, Claude 3.5 Sonnet/Haiku, Claude 3 Opus",
                "requires_api_key": True,
                "supports_custom_base_url": False,
                "default_models": ["claude-sonnet-4-5-20250929", "claude-opus-4-5-20251101", "claude-haiku-4-5-20251001", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"],
                "implemented": True,
            },
            ProviderType.HUGGINGFACE.value: {
                "name": "HuggingFace",
                "description": "Inference API and custom endpoints",
                "requires_api_key": True,
                "supports_custom_base_url": True,
                "default_models": ["meta-llama/Llama-3.3-70B-Instruct", "mistralai/Mistral-7B-Instruct-v0.3", "microsoft/Phi-3-mini-4k-instruct"],
                "implemented": True,
            },
            ProviderType.CUSTOM.value: {
                "name": "Custom HTTP",
                "description": "Custom HTTP endpoints with configurable request/response format",
                "requires_api_key": False,
                "supports_custom_base_url": True,
                "default_models": [],
                "implemented": True,
            },
        }
    
    @classmethod
    def is_provider_implemented(cls, provider_type: str) -> bool:
        """Check if a provider is implemented"""
        try:
            ptype = ProviderType(provider_type.lower())
            return ptype in PROVIDER_CLASSES
        except ValueError:
            return False


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def get_default_provider() -> Optional[BaseLLMProvider]:
    """
    Get the default LLM provider from environment/config.
    
    Checks for configured providers in order:
    1. GEMINI_API_KEY -> Google
    2. OPENAI_API_KEY -> OpenAI
    3. Ollama available -> Ollama
    
    Returns:
        Configured provider or None
    """
    import os
    
    # Try Google Gemini
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        return LLMProviderFactory.create(
            provider_type="google",
            model="gemini-2.0-flash",
            api_key=gemini_key,
        )
    
    # Try OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        return LLMProviderFactory.create(
            provider_type="openai",
            model="gpt-4",
            api_key=openai_key,
        )
    
    # Try Ollama
    try:
        provider = LLMProviderFactory.create(
            provider_type="ollama",
            model="llama3.1:8b-instruct-q4_K_M",
        )
        if await provider.is_available():
            return provider
    except Exception as e:
        logger.debug(f"Ollama provider not available: {e}")
    
    logger.warning("No default LLM provider available")
    return None
