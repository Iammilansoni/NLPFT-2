"""
OpenAI Provider - Adapter for OpenAI API and compatible endpoints

Supports:
- OpenAI GPT-4, GPT-4 Turbo, GPT-3.5 Turbo
- OpenAI-compatible APIs (DeepSeek, Azure OpenAI, local proxies)
- Custom base URLs for self-hosted endpoints

Features:
- Async API calls with httpx
- Automatic retry with exponential backoff
- Streaming support (future)
- Token usage tracking
"""

import time
from typing import Optional, List, Dict, Any

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
# OPENAI PROVIDER
# =============================================================================

class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI API provider with support for compatible endpoints.
    
    Works with:
    - OpenAI API (api.openai.com)
    - Azure OpenAI
    - DeepSeek API (deepseek.com)
    - Local OpenAI-compatible servers (vLLM, text-generation-webui)
    - Any OpenAI-compatible proxy
    
    Usage:
        provider = OpenAIProvider(
            model="gpt-4",
            api_key="sk-...",
        )
        
        response = await provider.generate(
            prompt="Hello, how are you?",
            system_prompt="You are a helpful assistant.",
            config=LLMConfig(temperature=0.7)
        )
    """
    
    DEFAULT_MODELS = [
        # =========================================================================
        # GPT-5.x Frontier Models (Latest)
        # =========================================================================
        ProviderModel(
            id="gpt-5.2",
            name="GPT-5.2",
            description="Best model for coding and agentic tasks across industries",
            context_length=128000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gpt-5.2-pro",
            name="GPT-5.2 Pro",
            description="Smarter and more precise responses",
            context_length=128000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gpt-5.1",
            name="GPT-5.1",
            description="Intelligent reasoning model with configurable reasoning effort",
            context_length=128000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gpt-5",
            name="GPT-5",
            description="Previous intelligent reasoning model for coding and agentic tasks",
            context_length=128000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gpt-5-pro",
            name="GPT-5 Pro",
            description="Version of GPT-5 with smarter, more precise responses",
            context_length=128000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gpt-5-mini",
            name="GPT-5 Mini",
            description="Faster, cost-efficient version of GPT-5 for well-defined tasks",
            context_length=128000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gpt-5-nano",
            name="GPT-5 Nano",
            description="Fastest, most cost-efficient version of GPT-5",
            context_length=128000,
            supports_vision=True,
            supports_functions=True,
        ),
        # =========================================================================
        # GPT-5 Codex Models (Agentic Coding)
        # =========================================================================
        ProviderModel(
            id="gpt-5.2-codex",
            name="GPT-5.2 Codex",
            description="Most intelligent coding model for long-horizon agentic coding",
            context_length=128000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gpt-5.1-codex",
            name="GPT-5.1 Codex",
            description="Optimized for agentic coding in Codex",
            context_length=128000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gpt-5.1-codex-max",
            name="GPT-5.1 Codex Max",
            description="Optimized for long running coding tasks",
            context_length=128000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gpt-5-codex",
            name="GPT-5 Codex",
            description="Optimized for agentic coding in Codex",
            context_length=128000,
            supports_vision=True,
            supports_functions=True,
        ),
        # =========================================================================
        # o3/o4 Reasoning Models
        # =========================================================================
        ProviderModel(
            id="o3",
            name="o3",
            description="Reasoning model for complex tasks, succeeded by GPT-5",
            context_length=200000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="o3-pro",
            name="o3 Pro",
            description="Version of o3 with more compute for better responses",
            context_length=200000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="o3-mini",
            name="o3 Mini",
            description="Small model alternative to o3",
            context_length=200000,
            supports_vision=False,
            supports_functions=True,
        ),
        ProviderModel(
            id="o3-deep-research",
            name="o3 Deep Research",
            description="Most powerful deep research model",
            context_length=200000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="o4-mini",
            name="o4 Mini",
            description="Fast, cost-efficient reasoning model",
            context_length=200000,
            supports_vision=False,
            supports_functions=True,
        ),
        ProviderModel(
            id="o4-mini-deep-research",
            name="o4 Mini Deep Research",
            description="Faster, more affordable deep research model",
            context_length=200000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="o1",
            name="o1",
            description="Previous full o-series reasoning model",
            context_length=200000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="o1-pro",
            name="o1 Pro",
            description="Version of o1 with more compute for better responses",
            context_length=200000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="o1-mini",
            name="o1 Mini",
            description="Small model alternative to o1 (deprecated)",
            context_length=128000,
            supports_vision=False,
            supports_functions=True,
        ),
        # =========================================================================
        # GPT-4.1 Series
        # =========================================================================
        ProviderModel(
            id="gpt-4.1",
            name="GPT-4.1",
            description="Smartest non-reasoning model",
            context_length=128000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gpt-4.1-mini",
            name="GPT-4.1 Mini",
            description="Smaller, faster version of GPT-4.1",
            context_length=128000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gpt-4.1-nano",
            name="GPT-4.1 Nano",
            description="Fastest, most cost-efficient version of GPT-4.1",
            context_length=128000,
            supports_vision=True,
            supports_functions=True,
        ),
        # =========================================================================
        # GPT-4o Series
        # =========================================================================
        ProviderModel(
            id="gpt-4o",
            name="GPT-4o",
            description="Fast, intelligent, flexible GPT model",
            context_length=128000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gpt-4o-mini",
            name="GPT-4o Mini",
            description="Fast, affordable small model for focused tasks",
            context_length=128000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gpt-4o-search-preview",
            name="GPT-4o Search Preview",
            description="GPT model for web search in Chat Completions",
            context_length=128000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gpt-4o-mini-search-preview",
            name="GPT-4o Mini Search Preview",
            description="Fast, affordable small model for web search",
            context_length=128000,
            supports_vision=True,
            supports_functions=True,
        ),
        # =========================================================================
        # Open-Weight Models (Apache 2.0)
        # =========================================================================
        ProviderModel(
            id="gpt-oss-120b",
            name="GPT-OSS 120B",
            description="Most powerful open-weight model, fits into an H100 GPU",
            context_length=128000,
            supports_vision=False,
            supports_functions=True,
        ),
        ProviderModel(
            id="gpt-oss-20b",
            name="GPT-OSS 20B",
            description="Medium-sized open-weight model for low latency",
            context_length=128000,
            supports_vision=False,
            supports_functions=True,
        ),
        # =========================================================================
        # Legacy Models (Still Available)
        # =========================================================================
        ProviderModel(
            id="gpt-4-turbo",
            name="GPT-4 Turbo",
            description="Older high-intelligence GPT model with 128K context",
            context_length=128000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gpt-4",
            name="GPT-4",
            description="Older high-intelligence GPT model",
            context_length=8192,
            supports_vision=False,
            supports_functions=True,
        ),
        ProviderModel(
            id="gpt-3.5-turbo",
            name="GPT-3.5 Turbo",
            description="Legacy GPT model for cheaper chat and non-chat tasks",
            context_length=16385,
            supports_vision=False,
            supports_functions=True,
        ),
    ]
    
    def __init__(
        self,
        model: str = "gpt-4",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
        max_retries: int = 3,
        organization: Optional[str] = None,
    ):
        """
        Initialize OpenAI provider.
        
        Args:
            model: Model ID (e.g., "gpt-4", "gpt-4-turbo")
            api_key: OpenAI API key
            base_url: Custom base URL (for compatible APIs)
            timeout: Request timeout in seconds
            max_retries: Retry attempts on failure
            organization: OpenAI organization ID (optional)
        """
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.organization = organization
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OPENAI
    
    @property
    def default_base_url(self) -> str:
        return "https://api.openai.com/v1"
    
    def _get_headers(self) -> Dict[str, str]:
        """Build request headers"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        return headers
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.effective_base_url,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[LLMConfig] = None,
    ) -> LLMResponse:
        """
        Generate completion using OpenAI Chat Completions API.
        
        Implements automatic retry with exponential backoff for transient errors.
        
        Args:
            prompt: User message
            system_prompt: System instructions
            config: Generation configuration
            
        Returns:
            LLMResponse with generated content
        """
        config = config or LLMConfig()
        self._log_request(prompt, system_prompt)
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Build request payload
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
        }
        
        if config.presence_penalty != 0.0:
            payload["presence_penalty"] = config.presence_penalty
        if config.frequency_penalty != 0.0:
            payload["frequency_penalty"] = config.frequency_penalty
        if config.stop_sequences:
            payload["stop"] = config.stop_sequences
        
        # Retry loop with exponential backoff
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                client = await self._get_client()
                start_time = time.time()
                
                response = await client.post(
                    "/chat/completions",
                    json=payload,
                    headers=self._get_headers(),
                )
                latency_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Defensive validation of response structure
                    if not isinstance(data, dict):
                        raise ProviderError(f"Invalid response format: expected dict, got {type(data).__name__}")
                    
                    choices = data.get("choices", [])
                    if not isinstance(choices, list) or len(choices) == 0:
                        raise ProviderError(f"Invalid response: missing or empty 'choices' array. Raw: {data}")
                    
                    first_choice = choices[0]
                    message = first_choice.get("message", {})
                    if not isinstance(message, dict):
                        message = {}
                    content = message.get("content") or ""  # Coerce None to empty string
                    finish_reason = first_choice.get("finish_reason")
                    
                    # Safely extract usage
                    usage_data = data.get("usage", {})
                    if not isinstance(usage_data, dict):
                        usage_data = {}
                    
                    llm_response = LLMResponse(
                        content=content,
                        model=data.get("model", self.model),
                        provider=self.provider_type.value,
                        usage={
                            "prompt_tokens": usage_data.get("prompt_tokens", 0),
                            "completion_tokens": usage_data.get("completion_tokens", 0),
                            "total_tokens": usage_data.get("total_tokens", 0),
                        },
                        finish_reason=finish_reason,
                        raw_response=data,
                    )
                    
                    self._log_response(llm_response)
                    logger.debug(f"OpenAI request completed in {latency_ms:.0f}ms")
                    
                    return llm_response
                else:
                    self._handle_error_response(response)
            
            except RateLimitError as e:
                last_error = e
                retry_count += 1
                if retry_count <= self.max_retries:
                    # Use retry_after if provided, otherwise exponential backoff
                    wait_time = e.retry_after if e.retry_after else min(2 ** retry_count * 2, 30)
                    logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {retry_count}/{self.max_retries})")
                    import asyncio
                    await asyncio.sleep(wait_time)
                else:
                    raise
                    
            except TransientError as e:
                last_error = e
                retry_count += 1
                if retry_count <= self.max_retries:
                    wait_time = min(2 ** retry_count, 30)
                    logger.warning(f"Transient error, retrying in {wait_time}s (attempt {retry_count}/{self.max_retries}): {e}")
                    import asyncio
                    await asyncio.sleep(wait_time)
                else:
                    raise
                    
            except httpx.TimeoutException:
                last_error = TransientError(f"OpenAI request timed out after {self.timeout}s")
                retry_count += 1
                if retry_count <= self.max_retries:
                    logger.warning(f"Timeout, retrying (attempt {retry_count}/{self.max_retries})")
                    import asyncio
                    await asyncio.sleep(min(2 ** retry_count, 30))
                else:
                    raise last_error
                    
            except httpx.RequestError as e:
                last_error = TransientError(f"Network error: {e}")
                retry_count += 1
                if retry_count <= self.max_retries:
                    logger.warning(f"Network error, retrying (attempt {retry_count}/{self.max_retries})")
                    import asyncio
                    await asyncio.sleep(min(2 ** retry_count, 30))
                else:
                    raise last_error
                    
            except (AuthenticationError, ProviderError):
                # Don't retry auth or permanent errors
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
            error_msg = response.text
            error_type = "unknown"
        
        status_code = response.status_code
        
        if status_code == 401:
            raise AuthenticationError(f"Invalid API key: {error_msg}")
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
            if "context_length" in error_msg.lower():
                raise ContextLengthError(error_msg)
            raise InvalidRequestError(error_msg)
        elif status_code >= 500:
            raise TransientError(f"OpenAI server error ({status_code}): {error_msg}")
        else:
            raise ProviderError(f"OpenAI error ({status_code}): {error_msg}")
    
    async def test_connection(self) -> ConnectionTestResult:
        """
        Test OpenAI API connectivity.
        
        Performs a minimal Chat Completion to verify API access.
        """
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
                message=f"Connected to OpenAI ({self.model})",
                latency_ms=latency_ms,
                model_info={
                    "model": response.model,
                    "provider": self.provider_type.value,
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
            return ConnectionTestResult(
                success=False,
                message=f"Connection failed: {e}",
                error_code="CONNECTION_ERROR",
            )
    
    async def list_models(self) -> List[ProviderModel]:
        """
        List available models.
        
        Returns default models for standard OpenAI API.
        For custom endpoints, attempts to fetch from /models.
        """
        # If using standard OpenAI, return known models
        if self.effective_base_url == self.default_base_url:
            return self.DEFAULT_MODELS
        
        # Try to fetch models from custom endpoint
        try:
            client = await self._get_client()
            response = await client.get("/models", headers=self._get_headers())
            
            if response.status_code == 200:
                data = response.json()
                models = []
                for model_data in data.get("data", []):
                    models.append(ProviderModel(
                        id=model_data["id"],
                        name=model_data.get("id", model_data["id"]),
                        description=model_data.get("description", ""),
                        context_length=model_data.get("context_length", 4096),
                    ))
                return models or self.DEFAULT_MODELS
        except Exception as e:
            logger.warning(f"Failed to fetch models from custom endpoint: {e}")
        
        return self.DEFAULT_MODELS
    
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

    def __del__(self):
        """Cleanup on deletion - best effort, no guarantees"""
        # Note: __del__ is unreliable for async cleanup
        # The close() method should be called explicitly when possible
        if self._client and not self._client.is_closed:
            try:
                # Synchronously close the transport layer
                self._client._transport.close()
            except Exception:
                pass  # Best effort cleanup, ignore errors
