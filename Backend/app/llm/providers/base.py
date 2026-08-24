"""
Base LLM Provider - Abstract interface for all LLM providers

This module defines the contract that all LLM providers must implement.
Using the adapter pattern ensures consistent behavior across providers.

Architecture:
    BaseLLMProvider (Abstract)
        ├── OpenAIProvider
        ├── AnthropicProvider
        ├── GoogleProvider
        ├── OllamaLLMProvider
        ├── HuggingFaceProvider
        └── CustomHTTPProvider
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.logger import logger

# =============================================================================
# ENUMS
# =============================================================================

class ProviderType(str, Enum):
    """Supported LLM provider types"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    DEEPSEEK = "deepseek"
    GROK = "grok"  # xAI's Grok models
    CUSTOM = "custom"


class ModelType(str, Enum):
    """Model capability types"""
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDINGS = "embeddings"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class LLMConfig:
    """
    Configuration for LLM generation requests.
    
    Attributes:
        temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
        max_tokens: Maximum tokens to generate
        top_p: Nucleus sampling threshold
        top_k: Top-k sampling (only some providers)
        stop_sequences: Sequences that stop generation
        presence_penalty: Penalize repeated topics
        frequency_penalty: Penalize repeated tokens
    """
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.9
    top_k: Optional[int] = None
    stop_sequences: Optional[List[str]] = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values"""
        result = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }
        if self.top_k is not None:
            result["top_k"] = self.top_k
        if self.stop_sequences:
            result["stop_sequences"] = self.stop_sequences
        if self.presence_penalty != 0.0:
            result["presence_penalty"] = self.presence_penalty
        if self.frequency_penalty != 0.0:
            result["frequency_penalty"] = self.frequency_penalty
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMConfig":
        """Create from dictionary with defaults"""
        return cls(
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 4096),
            top_p=data.get("top_p", 0.9),
            top_k=data.get("top_k"),
            stop_sequences=data.get("stop_sequences"),
            presence_penalty=data.get("presence_penalty", 0.0),
            frequency_penalty=data.get("frequency_penalty", 0.0),
        )


@dataclass
class LLMResponse:
    """
    Standardized response from LLM generation.
    
    Attributes:
        content: Generated text content
        model: Model used for generation
        provider: Provider name
        usage: Token usage statistics
        finish_reason: Why generation stopped
        raw_response: Original provider response (for debugging)
    """
    content: str
    model: str
    provider: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    @property
    def prompt_tokens(self) -> int:
        return self.usage.get("prompt_tokens", 0)
    
    @property
    def completion_tokens(self) -> int:
        return self.usage.get("completion_tokens", 0)
    
    @property
    def total_tokens(self) -> int:
        return self.usage.get("total_tokens", self.prompt_tokens + self.completion_tokens)


@dataclass
class ProviderModel:
    """
    Information about a model available from a provider.
    
    Attributes:
        id: Model identifier (e.g., "gpt-4", "claude-3-opus")
        name: Human-readable name
        description: Brief description
        context_length: Maximum context window
        supports_vision: Whether model handles images
        supports_functions: Whether model supports function calling
    """
    id: str
    name: str
    description: str = ""
    context_length: int = 4096
    supports_vision: bool = False
    supports_functions: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "context_length": self.context_length,
            "supports_vision": self.supports_vision,
            "supports_functions": self.supports_functions,
        }


@dataclass
class ConnectionTestResult:
    """
    Result of testing provider connectivity.
    
    Attributes:
        success: Whether connection succeeded
        message: Human-readable status message
        latency_ms: Response time in milliseconds
        model_info: Information about the tested model
        error_code: Error code if failed
    """
    success: bool
    message: str
    latency_ms: Optional[float] = None
    model_info: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "latency_ms": self.latency_ms,
            "model_info": self.model_info,
            "error_code": self.error_code,
        }


# =============================================================================
# ABSTRACT BASE CLASS
# =============================================================================

class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All LLM providers must implement this interface to ensure
    consistent behavior across the application.
    
    Usage:
        class MyProvider(BaseLLMProvider):
            @property
            def provider_type(self) -> ProviderType:
                return ProviderType.CUSTOM
            
            async def generate(self, prompt, system_prompt, config):
                # Implementation
                pass
    """
    
    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
        max_retries: int = 3,
    ):
        """
        Initialize the provider.
        
        Args:
            model: Model identifier to use
            api_key: API key for authentication (encrypted in storage)
            base_url: Custom base URL (for self-hosted or proxies)
            timeout: Request timeout in seconds
            max_retries: Number of retry attempts on failure
        """
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = None  # Lazy initialization
    
    # =========================================================================
    # ABSTRACT PROPERTIES
    # =========================================================================
    
    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Return the provider type enum value"""
        ...
    
    @property
    @abstractmethod
    def default_base_url(self) -> str:
        """Return the default API base URL"""
        ...
    
    @property
    def effective_base_url(self) -> str:
        """Return the effective base URL (custom or default)"""
        return self.base_url or self.default_base_url
    
    # =========================================================================
    # ABSTRACT METHODS
    # =========================================================================
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[LLMConfig] = None,
    ) -> LLMResponse:
        """
        Generate text completion.
        
        Args:
            prompt: User prompt/message
            system_prompt: Optional system instructions
            config: Generation configuration
            
        Returns:
            LLMResponse with generated content
            
        Raises:
            ProviderError: On API errors
            RateLimitError: On rate limiting
            AuthenticationError: On auth failures
        """
        ...
    
    @abstractmethod
    async def test_connection(self) -> ConnectionTestResult:
        """
        Test connectivity to the provider.
        
        Performs a minimal API call to verify:
        - API key is valid
        - Model is accessible
        - Network connectivity works
        
        Returns:
            ConnectionTestResult with status
        """
        ...
    
    @abstractmethod
    async def list_models(self) -> List[ProviderModel]:
        """
        List available models from the provider.
        
        Returns:
            List of ProviderModel objects
        """
        ...
    
    # =========================================================================
    # COMMON METHODS
    # =========================================================================
    
    async def generate_with_retry(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[LLMConfig] = None,
    ) -> LLMResponse:
        """
        Generate with automatic retry on transient failures.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            config: Generation config
            
        Returns:
            LLMResponse on success
            
        Raises:
            ProviderError: After all retries exhausted
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return await self.generate(prompt, system_prompt, config)
            except RateLimitError as e:
                last_error = e
                # Use retry_after if provided and valid, otherwise exponential backoff
                if e.retry_after is not None and e.retry_after > 0:
                    wait_time = min(e.retry_after, 30)  # Cap at 30s
                    logger.warning(
                        f"Rate limit hit for {self.provider_type.value}, "
                        f"using retry_after={wait_time}s (attempt {attempt + 1}/{self.max_retries})"
                    )
                else:
                    wait_time = min(2 ** attempt * 2, 30)  # Exponential backoff, max 30s
                    logger.warning(
                        f"Rate limit hit for {self.provider_type.value}, "
                        f"waiting {wait_time}s (attempt {attempt + 1}/{self.max_retries})"
                    )
                await asyncio.sleep(wait_time)
            except TransientError as e:
                last_error = e
                wait_time = 2 ** attempt
                logger.warning(
                    f"Transient error for {self.provider_type.value}: {e}, "
                    f"retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})"
                )
                await asyncio.sleep(wait_time)
            except (AuthenticationError, ProviderError):
                # Don't retry auth or permanent errors
                raise
        
        raise ProviderError(
            f"All {self.max_retries} retry attempts failed for {self.provider_type.value}",
            original_error=last_error
        )
    
    def _log_request(self, prompt: str, system_prompt: Optional[str]):
        """Log request details (without sensitive data)"""
        logger.info(
            f"🤖 {self.provider_type.value.upper()} request: "
            f"model={self.model}, "
            f"prompt_len={len(prompt)}, "
            f"system_len={len(system_prompt or '')}"
        )
    
    def _log_response(self, response: LLMResponse):
        """Log response details"""
        logger.info(
            f"✅ {self.provider_type.value.upper()} response: "
            f"content_len={len(response.content)}, "
            f"tokens={response.total_tokens}, "
            f"finish={response.finish_reason}"
        )
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"model='{self.model}', "
            f"base_url='{self.effective_base_url}')"
        )


# =============================================================================
# EXCEPTIONS
# =============================================================================

class ProviderError(Exception):
    """Base exception for provider errors"""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class AuthenticationError(ProviderError):
    """API key or authentication failure"""
    pass


class RateLimitError(ProviderError):
    """Rate limit exceeded"""
    
    def __init__(self, message: str, retry_after: Optional[float] = None, original_error: Optional[Exception] = None):
        super().__init__(message, original_error=original_error)
        self.retry_after = retry_after


class TransientError(ProviderError):
    """Temporary error that may resolve on retry"""
    pass


class ModelNotFoundError(ProviderError):
    """Requested model is not available"""
    pass


class InvalidRequestError(ProviderError):
    """Request was malformed or invalid"""
    pass


class ContextLengthError(ProviderError):
    """Input exceeded model's context length"""
    pass
