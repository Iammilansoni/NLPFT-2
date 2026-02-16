"""
Anthropic Provider - Adapter for Anthropic's Claude models

Claude models offer excellent reasoning, safety, and long-context capabilities.

Supported Models:
- Claude Sonnet 4.5 (Latest flagship)
- Claude 4 Opus / Sonnet
- Claude 3.5 Sonnet / Haiku (Legacy)
- Claude 3 Opus / Sonnet / Haiku (Legacy)

Features:
- Anthropic Messages API
- Large context windows (up to 200K, 1M with beta header)
- Advanced reasoning, coding, and analysis
- Extended thinking support
- Tool/function calling
"""

import time
import json
from typing import Optional, List, Dict, Any
from enum import Enum

import httpx

from app.core.logger import logger
from app.llm.providers.base import (
    BaseLLMProvider,
    ProviderType,
    LLMConfig,
    LLMResponse,
    ProviderModel,
    ConnectionTestResult,
    ProviderError,
    AuthenticationError,
    RateLimitError,
    TransientError,
    ModelNotFoundError,
    InvalidRequestError,
    ContextLengthError,
)


# =============================================================================
# CONSTANTS
# =============================================================================

class AnthropicVersion(str, Enum):
    """Anthropic API versions"""
    V2023_06_01 = "2023-06-01"
    V2024_10_22 = "2024-10-22"  # Latest version with extended thinking
    
DEFAULT_API_VERSION = AnthropicVersion.V2023_06_01.value
DEFAULT_MAX_TOKENS = 4096
EXTENDED_CONTEXT_HEADER = "anthropic-beta"
EXTENDED_CONTEXT_VALUE = "max-tokens-3-5-sonnet-2024-07-15"


# =============================================================================
# ANTHROPIC PROVIDER
# =============================================================================

class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Claude LLM provider.
    
    Uses Anthropic Messages API for Claude models.
    
    Usage:
        provider = AnthropicProvider(
            model="claude-sonnet-4-5-20250929",
            api_key="sk-ant-...",
        )
        
        response = await provider.generate(
            prompt="Explain quantum computing",
            system_prompt="You are a helpful assistant.",
        )
        
        # Streaming
        async for chunk in provider.generate_stream(prompt="Hello"):
            print(chunk.content, end="", flush=True)
    """
    
    DEFAULT_MODELS = [
        # =========================================================================
        # Claude 4.5 Series (Latest - Recommended)
        # =========================================================================
        ProviderModel(
            id="claude-sonnet-4-5-20250929",
            name="Claude Sonnet 4.5",
            description="Best for coding & agentic tasks, 1M context with beta",
            context_length=200000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="claude-opus-4-5-20251101",
            name="Claude Opus 4.5",
            description="Most powerful Claude, highest capability",
            context_length=200000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="claude-haiku-4-5-20251001",
            name="Claude Haiku 4.5",
            description="Fast and efficient, great for quick tasks",
            context_length=200000,
            supports_vision=True,
            supports_functions=True,
        ),

        # =========================================================================
        # Claude 3.5 Series (Previous Gen - Still Supported)
        # =========================================================================
        ProviderModel(
            id="claude-3-5-sonnet-20241022",
            name="Claude 3.5 Sonnet",
            description="Previous gen, still excellent ($3/$15 per M tokens)",
            context_length=200000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="claude-3-5-haiku-20241022",
            name="Claude 3.5 Haiku",
            description="Fast and cost-effective",
            context_length=200000,
            supports_vision=True,
            supports_functions=True,
        ),
    ]
    
    def __init__(
        self,
        model: str = "claude-sonnet-4-5-20250929",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
        max_retries: int = 3,
        api_version: str = DEFAULT_API_VERSION,
        enable_extended_context: bool = False,
    ):
        """
        Initialize Anthropic provider.
        
        Args:
            model: Model ID (e.g., "claude-sonnet-4-5-20250929")
            api_key: Anthropic API key (starts with sk-ant-)
            base_url: Custom base URL (default: Anthropic API)
            timeout: Request timeout
            max_retries: Retry attempts
            api_version: Anthropic API version
            enable_extended_context: Enable 1M context window (requires beta header)
        """
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._client: Optional[httpx.AsyncClient] = None
        self.api_version = api_version
        self.enable_extended_context = enable_extended_context
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.ANTHROPIC
    
    @property
    def default_base_url(self) -> str:
        return "https://api.anthropic.com"
    
    def _get_headers(self, stream: bool = False) -> Dict[str, str]:
        """Build request headers"""
        if not self.api_key:
            raise ValueError("Anthropic API key is required")
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
        }
        
        # Add extended context header if enabled
        if self.enable_extended_context:
            headers[EXTENDED_CONTEXT_HEADER] = EXTENDED_CONTEXT_VALUE
        
        return headers
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.effective_base_url,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client
    
    def _build_messages(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Build messages array for Anthropic API.
        
        Args:
            prompt: User prompt
        
        Returns:
            Messages array in Anthropic format
        """
        messages = []
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        return messages
    
    def _build_payload(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str],
        config: LLMConfig,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Build request payload for Anthropic API"""
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": config.max_tokens or DEFAULT_MAX_TOKENS,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "stream": stream,
        }
        
        # System prompt is separate in Anthropic API
        if system_prompt:
            payload["system"] = system_prompt
        
        if config.stop_sequences:
            payload["stop_sequences"] = config.stop_sequences
        
        # Add tool/function definitions if provided
        if tools:
            payload["tools"] = tools
        
        # Add top_k if specified
        if hasattr(config, 'top_k') and config.top_k is not None:
            payload["top_k"] = config.top_k
        
        return payload
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[LLMConfig] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        """
        Generate completion using Anthropic Messages API.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            config: Generation configuration
            tools: Optional tool/function definitions
        """
        config = config or LLMConfig()
        self._log_request(prompt, system_prompt)
        
        # Build messages
        messages = self._build_messages(prompt)
        
        # Build request payload
        payload = self._build_payload(messages, system_prompt, config, stream=False, tools=tools)
        
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                client = await self._get_client()
                start_time = time.time()
                
                response = await client.post(
                    "/v1/messages",
                    json=payload,
                    headers=self._get_headers(stream=False)
                )
                latency_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract content from Anthropic response format
                    content = ""
                    tool_calls = []
                    
                    if data.get("content"):
                        for block in data["content"]:
                            if block.get("type") == "text":
                                content += block.get("text", "")
                            elif block.get("type") == "tool_use":
                                tool_calls.append({
                                    "id": block.get("id"),
                                    "name": block.get("name"),
                                    "input": block.get("input", {})
                                })
                    
                    llm_response = LLMResponse(
                        content=content,
                        model=data.get("model", self.model),
                        provider="anthropic",
                        usage={
                            "prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
                            "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
                            "total_tokens": (
                                data.get("usage", {}).get("input_tokens", 0) +
                                data.get("usage", {}).get("output_tokens", 0)
                            ),
                        },
                        finish_reason=data.get("stop_reason"),
                        raw_response=data,
                        tool_calls=tool_calls if tool_calls else None,
                    )

                    self._log_response(llm_response)
                    logger.debug(f"Anthropic request completed in {latency_ms:.0f}ms")
                    
                    return llm_response
                else:
                    self._handle_error_response(response)
                    
            except RateLimitError as e:
                last_error = e
                retry_count += 1
                if retry_count <= self.max_retries:
                    # Use retry_after if provided, otherwise exponential backoff
                    wait_time = e.retry_after if e.retry_after else min(2 ** retry_count, 60)
                    logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {retry_count}/{self.max_retries})")
                    await self._async_sleep(wait_time)
                else:
                    raise
                    
            except TransientError as e:
                last_error = e
                retry_count += 1
                if retry_count <= self.max_retries:
                    wait_time = min(2 ** retry_count, 30)
                    logger.warning(f"Transient error, retrying in {wait_time}s (attempt {retry_count}/{self.max_retries}): {e}")
                    await self._async_sleep(wait_time)
                else:
                    raise
                    
            except httpx.TimeoutException:
                last_error = TransientError(f"Anthropic request timed out after {self.timeout}s")
                retry_count += 1
                if retry_count <= self.max_retries:
                    logger.warning(f"Timeout, retrying (attempt {retry_count}/{self.max_retries})")
                    await self._async_sleep(min(2 ** retry_count, 30))
                else:
                    raise last_error
                    
            except httpx.RequestError as e:
                last_error = TransientError(f"Network error: {e}")
                retry_count += 1
                if retry_count <= self.max_retries:
                    logger.warning(f"Network error, retrying (attempt {retry_count}/{self.max_retries})")
                    await self._async_sleep(min(2 ** retry_count, 30))
                else:
                    raise last_error

            except (AuthenticationError, InvalidRequestError, ModelNotFoundError, ContextLengthError, ProviderError):
                # Don't retry permanent errors
                raise

        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise ProviderError("Max retries exceeded")
    

    def _handle_error_response(self, response: httpx.Response):
        """Parse and raise appropriate exception for error responses"""
        try:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", str(error_data))
            error_type = error_data.get("error", {}).get("type", "unknown")
        except Exception:
            error_msg = response.text or f"HTTP {response.status_code}"
            error_type = "unknown"
        
        status_code = response.status_code
        
        if status_code == 401:
            raise AuthenticationError(f"Invalid Anthropic API key: {error_msg}")
        elif status_code == 403:
            raise AuthenticationError(f"Access denied: {error_msg}")
        elif status_code == 404:
            raise ModelNotFoundError(f"Model not found: {error_msg}")
        elif status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_seconds = None
            if retry_after:
                try:
                    retry_seconds = float(retry_after)
                except ValueError:
                    pass  # Retry-After may be a date string, ignore
            raise RateLimitError(
                f"Rate limit exceeded: {error_msg}",
                retry_after=retry_seconds
            )
        elif status_code == 400:
            # Check for specific error types
            if "context" in error_msg.lower() or "length" in error_msg.lower() or "tokens" in error_msg.lower():
                raise ContextLengthError(error_msg)
            elif error_type == "invalid_request_error":
                raise InvalidRequestError(error_msg)
            raise InvalidRequestError(error_msg)
        elif status_code in (500, 502, 503, 504):
            raise TransientError(f"Anthropic server error ({status_code}): {error_msg}")
        elif status_code == 529:
            # Overloaded
            raise TransientError(f"Anthropic service overloaded: {error_msg}")
        else:
            raise ProviderError(f"Anthropic error ({status_code}): {error_msg}")
    
    async def test_connection(self) -> ConnectionTestResult:
        """Test Anthropic API connectivity."""
        try:
            start_time = time.time()
            
            response = await self.generate(
                prompt="Say 'OK' to confirm connection.",
                system_prompt="Respond only with 'OK'.",
                config=LLMConfig(max_tokens=10, temperature=0),
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            return ConnectionTestResult(
                success=True,
                message=f"Connected to Anthropic ({self.model}) - {latency_ms:.0f}ms",
                latency_ms=latency_ms,
                model_info={
                    "model": response.model,
                    "provider": "anthropic",
                    "api_version": self.api_version,
                    "extended_context": self.enable_extended_context,
                },
            )
        except AuthenticationError as e:
            return ConnectionTestResult(
                success=False,
                message=str(e),
                error_code="AUTH_ERROR",
            )
        except ModelNotFoundError as e:
            return ConnectionTestResult(
                success=False,
                message=str(e),
                error_code="MODEL_NOT_FOUND",
            )
        except Exception as e:
            logger.exception("Connection test failed")
            return ConnectionTestResult(
                success=False,
                message=f"Connection failed: {e}",
                error_code="CONNECTION_ERROR",
            )
    
    async def list_models(self) -> List[ProviderModel]:
        """
        List available Anthropic models.
        
        Note: Anthropic doesn't have a public models endpoint,
        so we return the predefined list of supported models.
        """
        return self.DEFAULT_MODELS.copy()
    
    async def _async_sleep(self, seconds: float):
        """Async sleep helper for retries"""
        import asyncio
        await asyncio.sleep(seconds)
    
    async def close(self):
        """Close the HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()