"""
Custom HTTP Provider - Adapter for OpenAI-compatible API endpoints

Supports any service that exposes an OpenAI-compatible API:
- vLLM servers
- text-generation-webui with API extension
- LocalAI
- LM Studio
- Ollama (via OpenAI-compatible endpoint)
- Any custom deployment

Features:
- OpenAI-compatible chat/completions format
- Custom base URL support
- Optional API key
- Works with local and remote endpoints
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
# CUSTOM HTTP PROVIDER
# =============================================================================

class CustomHTTPProvider(BaseLLMProvider):
    """
    Custom OpenAI-compatible HTTP provider.
    
    Works with any server exposing an OpenAI-compatible API.
    Perfect for:
    - Local model servers (vLLM, LocalAI, LM Studio)
    - Self-hosted deployments
    - Custom inference endpoints
    
    Usage:
        # Local vLLM server
        provider = CustomHTTPProvider(
            model="meta-llama/Llama-3.1-8B-Instruct",
            base_url="http://localhost:8000/v1",
        )
        
        # LM Studio
        provider = CustomHTTPProvider(
            model="local-model",
            base_url="http://localhost:1234/v1",
        )
        
        response = await provider.generate(
            prompt="Hello!",
            system_prompt="You are a helpful assistant.",
        )
    """
    
    DEFAULT_MODELS = [
        # These are example placeholders - users specify their own models
        ProviderModel(
            id="custom-model",
            name="Custom Model",
            description="Specify your model name in the config",
            context_length=4096,
            supports_vision=False,
            supports_functions=False,
        ),
    ]
    
    def __init__(
        self,
        model: str = "custom-model",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
        max_retries: int = 3,
    ):
        """
        Initialize Custom HTTP provider.
        
        Args:
            model: Model name/ID as expected by the server
            api_key: Optional API key (some local servers don't need it)
            base_url: REQUIRED - URL of the OpenAI-compatible endpoint
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
        return ProviderType.CUSTOM
    
    @property
    def default_base_url(self) -> str:
        # No default - must be provided
        return "http://localhost:8000/v1"
    
    def _get_headers(self) -> Dict[str, str]:
        """Build request headers"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.effective_base_url,
                headers=self._get_headers(),
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
        Generate completion using OpenAI-compatible API.
        """
        config = config or LLMConfig()
        self._log_request(prompt, system_prompt)
        
        # Build messages (OpenAI format)
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
        
        if config.stop_sequences:
            payload["stop"] = config.stop_sequences
        
        try:
            client = await self._get_client()
            start_time = time.time()
            
            response = await client.post("/chat/completions", json=payload)
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Defensive parsing - validate response structure
                choices = data.get("choices", [])
                if not isinstance(choices, list) or len(choices) == 0:
                    raise ProviderError(f"Invalid response: missing or empty 'choices' array. Raw: {data}")
                
                first_choice = choices[0]
                message = first_choice.get("message", {})
                content = message.get("content", "") if isinstance(message, dict) else ""
                finish_reason = first_choice.get("finish_reason")
                
                # Safely extract usage
                usage_data = data.get("usage", {})
                if not isinstance(usage_data, dict):
                    usage_data = {}
                
                llm_response = LLMResponse(
                    content=content,
                    model=data.get("model", self.model),
                    provider="custom",
                    usage={
                        "prompt_tokens": usage_data.get("prompt_tokens", 0),
                        "completion_tokens": usage_data.get("completion_tokens", 0),
                        "total_tokens": usage_data.get("total_tokens", 0),
                    },
                    finish_reason=finish_reason,
                    raw_response=data,
                )
                
                self._log_response(llm_response)
                logger.debug(f"Custom endpoint request completed in {latency_ms:.0f}ms")
                
                return llm_response
            else:
                self._handle_error_response(response)
                
        except httpx.TimeoutException:
            raise TransientError(f"Request timed out after {self.timeout}s")
        except httpx.ConnectError:
            raise TransientError(f"Cannot connect to {self.effective_base_url}. Is the server running?")
        except httpx.RequestError as e:
            raise TransientError(f"Network error: {e}")
    
    def _handle_error_response(self, response: httpx.Response):
        """Parse and raise appropriate exception for error responses"""
        try:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", str(error_data))
        except Exception:
            error_msg = response.text
        
        status_code = response.status_code
        
        if status_code == 401:
            raise AuthenticationError(f"Authentication failed: {error_msg}")
        elif status_code == 403:
            raise AuthenticationError(f"Access denied: {error_msg}")
        elif status_code == 404:
            raise ModelNotFoundError(f"Model or endpoint not found: {error_msg}")
        elif status_code == 429:
            raise RateLimitError(f"Rate limit exceeded: {error_msg}")
        elif status_code == 400:
            if "context" in error_msg.lower() or "length" in error_msg.lower():
                raise ContextLengthError(error_msg)
            raise InvalidRequestError(error_msg)
        elif status_code >= 500:
            raise TransientError(f"Server error ({status_code}): {error_msg}")
        else:
            raise ProviderError(f"Error ({status_code}): {error_msg}")
    
    async def test_connection(self) -> ConnectionTestResult:
        """Test custom endpoint connectivity."""
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
                message=f"Connected to {self.effective_base_url} ({self.model}) - {latency_ms:.0f}ms",
                latency_ms=latency_ms,
                model_info={
                    "model": response.model,
                    "provider": "custom",
                    "base_url": self.effective_base_url,
                },
            )
        except TransientError as e:
            if "connect" in str(e).lower():
                return ConnectionTestResult(
                    success=False,
                    message=f"Cannot connect to server at {self.effective_base_url}",
                    error_code="CONNECTION_ERROR",
                )
            return ConnectionTestResult(
                success=False,
                message=str(e),
                error_code="TRANSIENT_ERROR",
            )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message=f"Connection failed: {e}",
                error_code="CONNECTION_ERROR",
            )
    
    async def list_models(self) -> List[ProviderModel]:
        """
        Try to list models from the endpoint.
        Many servers support GET /models or /v1/models.
        """
        try:
            client = await self._get_client()
            response = await client.get("/models")
            
            if response.status_code == 200:
                data = response.json()
                models = []
                for model_data in data.get("data", []):
                    models.append(ProviderModel(
                        id=model_data.get("id", "unknown"),
                        name=model_data.get("id", "Unknown Model"),
                        description=model_data.get("description", ""),
                        context_length=model_data.get("context_window", 4096),
                    ))
                return models if models else self.DEFAULT_MODELS
        except Exception as e:
            logger.debug(f"Could not list models from custom endpoint: {e}")
        
        return self.DEFAULT_MODELS
    
    async def close(self):
        """Close the HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
