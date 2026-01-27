"""
Grok Provider - Adapter for xAI's Grok models

xAI's Grok models offer advanced reasoning and vision capabilities,
with both standard and reasoning-optimized variants.

Supported Models:
- Grok 4.1 Fast (Reasoning & Non-Reasoning)
- Grok 4 (Flagship and Fast)
- Grok Code Fast
- Grok 3 / 3 Mini
- Grok 2 Vision

Features:
- OpenAI-compatible API
- Large context windows (up to 2M tokens)
- Vision support
- Function/tool calling
"""

import time
import json
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
# CONSTANTS
# =============================================================================

DEFAULT_MAX_TOKENS = 4096


# =============================================================================
# GROK PROVIDER (xAI)
# =============================================================================

class GrokProvider(BaseLLMProvider):
    """
    xAI Grok LLM provider.
    
    Uses OpenAI-compatible API format with xAI's Grok models.
    
    Usage:
        provider = GrokProvider(
            model="grok-3",
            api_key="xai-...",
        )
        
        response = await provider.generate(
            prompt="Explain the theory of relativity",
            system_prompt="You are a helpful assistant.",
        )
        
        # Streaming
        async for chunk in provider.generate_stream(prompt="Hello"):
            print(chunk.content, end="", flush=True)
    """
    
    DEFAULT_MODELS = [
        # =========================================================================
        # Grok 4.1 Fast Series
        # =========================================================================
        ProviderModel(
            id="grok-4.1-fast-reasoning",
            name="Grok 4.1 Fast Reasoning",
            description="Fast reasoning with 2M context ($0.20/$0.50 per M tokens)",
            context_length=2000000,
            supports_vision=False,
            supports_functions=True,
        ),
        ProviderModel(
            id="grok-4.1-fast-non-reasoning",
            name="Grok 4.1 Fast Non-Reasoning",
            description="Fast non-reasoning with 2M context ($0.20/$0.50 per M tokens)",
            context_length=2000000,
            supports_vision=False,
            supports_functions=True,
        ),
        # =========================================================================
        # Grok Code
        # =========================================================================
        ProviderModel(
            id="grok-code-fast-1",
            name="Grok Code Fast 1",
            description="Optimized for code generation ($0.20/$1.50 per M tokens)",
            context_length=256000,
            supports_vision=False,
            supports_functions=True,
        ),
        # =========================================================================
        # Grok 4 Fast Series
        # =========================================================================
        ProviderModel(
            id="grok-4-fast-reasoning",
            name="Grok 4 Fast Reasoning",
            description="Fast reasoning model ($0.20/$0.50 per M tokens)",
            context_length=2000000,
            supports_vision=False,
            supports_functions=True,
        ),
        ProviderModel(
            id="grok-4-fast-non-reasoning",
            name="Grok 4 Fast Non-Reasoning",
            description="Fast general model ($0.20/$0.50 per M tokens)",
            context_length=2000000,
            supports_vision=False,
            supports_functions=True,
        ),
        ProviderModel(
            id="grok-4-0709",
            name="Grok 4 (0709)",
            description="Flagship Grok 4 model ($3.00/$15.00 per M tokens)",
            context_length=256000,
            supports_vision=False,
            supports_functions=True,
        ),
        # =========================================================================
        # Grok 3 Series
        # =========================================================================
        ProviderModel(
            id="grok-3-mini",
            name="Grok 3 Mini",
            description="Lightweight Grok 3 ($0.30/$0.50 per M tokens)",
            context_length=131072,
            supports_vision=False,
            supports_functions=True,
        ),
        ProviderModel(
            id="grok-3",
            name="Grok 3",
            description="Standard Grok 3 model ($3.00/$15.00 per M tokens)",
            context_length=131072,
            supports_vision=False,
            supports_functions=True,
        ),
        # =========================================================================
        # Grok 2 Vision
        # =========================================================================
        ProviderModel(
            id="grok-2-vision-1212",
            name="Grok 2 Vision",
            description="Multimodal vision model ($2.00/$10.00 per M tokens)",
            context_length=32768,
            supports_vision=True,
            supports_functions=True,
        ),
    ]
    
    def __init__(
        self,
        model: str = "grok-3",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
        max_retries: int = 3,
    ):
        """
        Initialize Grok provider.
        
        Args:
            model: Model ID (e.g., "grok-3", "grok-4-fast-reasoning")
            api_key: xAI API key (starts with xai-)
            base_url: Custom base URL (default: xAI API)
            timeout: Request timeout
            max_retries: Retry attempts
        """
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.GROK if hasattr(ProviderType, 'GROK') else ProviderType.CUSTOM
    
    @property
    def default_base_url(self) -> str:
        return "https://api.x.ai/v1"
    
    def _get_headers(self) -> Dict[str, str]:
        """Build request headers"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.effective_base_url,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client
    
    def _build_messages(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Build messages array for OpenAI-compatible API.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            Messages array
        """
        messages = []
        
        # Add system prompt
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        return messages
    
    def _build_payload(
        self,
        messages: List[Dict[str, str]],
        config: LLMConfig,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Build request payload"""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens or DEFAULT_MAX_TOKENS,
            "top_p": config.top_p,
            "stream": stream,
        }
        
        if config.stop_sequences:
            payload["stop"] = config.stop_sequences
        
        # Add tools if provided
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        # Add top_k if supported and specified
        if hasattr(config, 'top_k') and config.top_k is not None:
            payload["top_k"] = config.top_k
        
        # Add frequency/presence penalties if specified
        if hasattr(config, 'frequency_penalty') and config.frequency_penalty is not None:
            payload["frequency_penalty"] = config.frequency_penalty
        
        if hasattr(config, 'presence_penalty') and config.presence_penalty is not None:
            payload["presence_penalty"] = config.presence_penalty
        
        return payload
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[LLMConfig] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        """
        Generate completion using Grok's API.
        
        Args:
            prompt: User message
            system_prompt: Optional system prompt
            config: Generation configuration
            tools: Optional tool/function definitions
        """
        config = config or LLMConfig()
        self._log_request(prompt, system_prompt)
        
        # Build messages
        messages = self._build_messages(prompt, system_prompt)
        
        # Build request payload
        payload = self._build_payload(messages, config, stream=False, tools=tools)
        
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                client = await self._get_client()
                start_time = time.time()
                
                response = await client.post(
                    "/chat/completions",
                    json=payload,
                    headers=self._get_headers()
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
                    
                    choice = choices[0]
                    message = choice.get("message", {})
                    if not isinstance(message, dict):
                        message = {}
                    
                    # Extract content
                    content = message.get("content", "")
                    
                    # Extract tool calls if present (with defensive checks)
                    tool_calls = []
                    raw_tool_calls = message.get("tool_calls")
                    if raw_tool_calls and isinstance(raw_tool_calls, list):
                        for tc in raw_tool_calls:
                            if not isinstance(tc, dict):
                                continue
                            func = tc.get("function", {})
                            if not isinstance(func, dict):
                                continue
                            if "name" in func and "arguments" in func:
                                tool_calls.append({
                                    "id": tc.get("id"),
                                    "type": tc.get("type"),
                                    "function": {
                                        "name": func["name"],
                                        "arguments": func["arguments"]
                                    }
                                })
                    
                    # Safely extract usage
                    usage_data = data.get("usage", {})
                    if not isinstance(usage_data, dict):
                        usage_data = {}
                    
                    llm_response = LLMResponse(
                        content=content,
                        model=data.get("model", self.model),
                        provider="grok",
                        usage={
                            "prompt_tokens": usage_data.get("prompt_tokens", 0),
                            "completion_tokens": usage_data.get("completion_tokens", 0),
                            "total_tokens": usage_data.get("total_tokens", 0),
                        },
                        finish_reason=choice.get("finish_reason"),
                        raw_response=data,
                    )
                    
                    # Add tool calls if present
                    if tool_calls:
                        llm_response.tool_calls = tool_calls
                    
                    self._log_response(llm_response)
                    logger.debug(f"Grok request completed in {latency_ms:.0f}ms")
                    
                    return llm_response
                else:
                    self._handle_error_response(response)
            
            except RateLimitError as e:
                last_error = e
                retry_count += 1
                if retry_count <= self.max_retries:
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
                last_error = TransientError(f"Grok request timed out after {self.timeout}s")
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
            error_code = error_data.get("error", {}).get("code", "unknown")
        except Exception:
            error_msg = response.text or f"HTTP {response.status_code}"
            error_type = "unknown"
            error_code = "unknown"
        
        status_code = response.status_code
        
        if status_code == 401:
            raise AuthenticationError(f"Invalid xAI API key: {error_msg}")
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
            elif error_code == "invalid_request_error":
                raise InvalidRequestError(error_msg)
            raise InvalidRequestError(error_msg)
        elif status_code in (500, 502, 503, 504):
            raise TransientError(f"Grok server error ({status_code}): {error_msg}")
        elif status_code == 529:
            # Overloaded
            raise TransientError(f"Grok service overloaded: {error_msg}")
        else:
            raise ProviderError(f"Grok error ({status_code}): {error_msg}")
    
    async def test_connection(self) -> ConnectionTestResult:
        """Test Grok API connectivity."""
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
                message=f"Connected to Grok ({self.model}) - {latency_ms:.0f}ms",
                latency_ms=latency_ms,
                model_info={
                    "model": response.model,
                    "provider": "grok",
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
        List available Grok models.
        
        Attempts to fetch from API, falls back to predefined list.
        """
        try:
            client = await self._get_client()
            response = await client.get("/models", headers=self._get_headers())
            
            # Handle non-200 responses - surface auth errors
            if response.status_code != 200:
                try:
                    self._handle_error_response(response)
                except AuthenticationError:
                    # Re-raise auth errors so they're not hidden
                    raise
                except Exception as e:
                    logger.warning(f"Failed to fetch Grok models (status {response.status_code}): {e}")
                    return self.DEFAULT_MODELS.copy()
            
            data = response.json()
            models = []
            
            for model_data in data.get("data", []):
                model_id = model_data.get("id")
                
                # Skip malformed entries without id
                if not model_id:
                    logger.debug(f"Skipping Grok model entry with missing id: {model_data}")
                    continue
                
                # Try to find matching default model
                matching = next((m for m in self.DEFAULT_MODELS if m.id == model_id), None)
                
                if matching:
                    models.append(matching)
                else:
                    # Create new model from API data
                    models.append(ProviderModel(
                        id=model_id,
                        name=model_data.get("name", model_id),
                        description=model_data.get("description", ""),
                        context_length=model_data.get("context_window", 32768),
                        supports_vision=model_data.get("vision", False),
                        supports_functions=True,
                    ))
            
            if models:
                logger.info(f"Fetched {len(models)} Grok models from API")
                return models
        
        except AuthenticationError:
            # Re-raise auth errors
            raise
        except Exception as e:
            logger.warning(f"Failed to fetch Grok models from API: {e}, using defaults")
        
        return self.DEFAULT_MODELS
    
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