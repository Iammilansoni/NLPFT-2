"""
HuggingFace Provider - Adapter for HuggingFace Inference API

HuggingFace provides access to thousands of open-source models
via their Inference API and dedicated endpoints.

Supported:
- HuggingFace Inference API (serverless)
- Inference Endpoints (dedicated)
- Text Generation Inference (TGI)

Features:
- OpenAI-compatible messaging format
- Access to open-source models
- Custom endpoint support
- Model loading detection
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
# CONSTANTS & ENUMS
# =============================================================================

DEFAULT_MAX_TOKENS = 512


class HuggingFaceEndpointType(str, Enum):
    """HuggingFace endpoint types"""
    SERVERLESS = "serverless"  # api-inference.huggingface.co
    DEDICATED = "dedicated"    # Inference Endpoints
    TGI = "tgi"               # Text Generation Inference


# =============================================================================
# HUGGINGFACE PROVIDER
# =============================================================================

class HuggingFaceProvider(BaseLLMProvider):
    """
    HuggingFace Inference API provider.
    
    Supports both serverless Inference API and dedicated endpoints.
    
    Usage:
        # Serverless Inference API
        provider = HuggingFaceProvider(
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            api_key="hf_...",
        )
        
        # Dedicated Endpoint
        provider = HuggingFaceProvider(
            model="tgi",
            api_key="hf_...",
            base_url="https://your-endpoint.endpoints.huggingface.cloud",
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
        # Llama 3 Series
        ProviderModel(
            id="meta-llama/Meta-Llama-3.1-8B-Instruct",
            name="Llama 3.1 8B Instruct",
            description="Meta's latest open model",
            context_length=128000,
            supports_vision=False,
            supports_functions=False,
        ),
        ProviderModel(
            id="meta-llama/Meta-Llama-3.1-70B-Instruct",
            name="Llama 3.1 70B Instruct",
            description="Large Llama for complex tasks",
            context_length=128000,
            supports_vision=False,
            supports_functions=False,
        ),
        ProviderModel(
            id="meta-llama/Meta-Llama-3.3-70B-Instruct",
            name="Llama 3.3 70B Instruct",
            description="Latest Llama with improved capabilities",
            context_length=128000,
            supports_vision=False,
            supports_functions=False,
        ),
        # Mistral Series
        ProviderModel(
            id="mistralai/Mistral-7B-Instruct-v0.3",
            name="Mistral 7B Instruct v0.3",
            description="Fast and efficient open model",
            context_length=32768,
            supports_vision=False,
            supports_functions=False,
        ),
        ProviderModel(
            id="mistralai/Mixtral-8x7B-Instruct-v0.1",
            name="Mixtral 8x7B Instruct",
            description="Mixture of experts model",
            context_length=32768,
            supports_vision=False,
            supports_functions=False,
        ),
        ProviderModel(
            id="mistralai/Mistral-Nemo-Instruct-2407",
            name="Mistral Nemo Instruct",
            description="12B parameter efficient model",
            context_length=128000,
            supports_vision=False,
            supports_functions=False,
        ),
        # Qwen Series
        ProviderModel(
            id="Qwen/Qwen2.5-72B-Instruct",
            name="Qwen 2.5 72B Instruct",
            description="Alibaba's powerful model",
            context_length=131072,
            supports_vision=False,
            supports_functions=False,
        ),
        ProviderModel(
            id="Qwen/Qwen2.5-7B-Instruct",
            name="Qwen 2.5 7B Instruct",
            description="Smaller but capable Qwen model",
            context_length=131072,
            supports_vision=False,
            supports_functions=False,
        ),
        # Microsoft Phi
        ProviderModel(
            id="microsoft/Phi-3-mini-4k-instruct",
            name="Phi-3 Mini 4K",
            description="Small but capable model",
            context_length=4096,
            supports_vision=False,
            supports_functions=False,
        ),
        ProviderModel(
            id="microsoft/Phi-3.5-mini-instruct",
            name="Phi-3.5 Mini",
            description="Updated Phi model with better performance",
            context_length=128000,
            supports_vision=False,
            supports_functions=False,
        ),
        # Google Gemma
        ProviderModel(
            id="google/gemma-2-9b-it",
            name="Gemma 2 9B Instruct",
            description="Google's open model",
            context_length=8192,
            supports_vision=False,
            supports_functions=False,
        ),
    ]
    
    def __init__(
        self,
        model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
        max_retries: int = 3,
        wait_for_model: bool = True,
    ):
        """
        Initialize HuggingFace provider.
        
        Args:
            model: Model ID (e.g., "meta-llama/Meta-Llama-3.1-8B-Instruct")
            api_key: HuggingFace API key (starts with hf_)
            base_url: Custom endpoint URL (for dedicated endpoints)
            timeout: Request timeout
            max_retries: Retry attempts
            wait_for_model: Wait for model to load if not ready (serverless only)
        """
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._client: Optional[httpx.AsyncClient] = None
        self.wait_for_model = wait_for_model
        self.endpoint_type = self._detect_endpoint_type()
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.HUGGINGFACE
    
    @property
    def default_base_url(self) -> str:
        return "https://api-inference.huggingface.co"
    
    def _detect_endpoint_type(self) -> HuggingFaceEndpointType:
        """Detect the type of endpoint being used"""
        if self.base_url:
            if "endpoints.huggingface.cloud" in self.base_url:
                return HuggingFaceEndpointType.DEDICATED
            return HuggingFaceEndpointType.TGI
        return HuggingFaceEndpointType.SERVERLESS
    
    def _get_headers(self) -> Dict[str, str]:
        """Build request headers"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        # Add wait_for_model option for serverless API
        if self.endpoint_type == HuggingFaceEndpointType.SERVERLESS and self.wait_for_model:
            headers["x-wait-for-model"] = "true"
        
        return headers
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None or self._client.is_closed:
            # For custom endpoints, use as-is; for serverless, build model URL
            if self.base_url:
                base = self.base_url
            else:
                base = self.default_base_url
            
            self._client = httpx.AsyncClient(
                base_url=base,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client
    
    def _get_endpoint_url(self) -> str:
        """Get the appropriate endpoint URL based on endpoint type"""
        if self.endpoint_type == HuggingFaceEndpointType.SERVERLESS:
            return f"/models/{self.model}"
        else:
            # TGI and dedicated endpoints
            return "/generate"
    
    def _get_stream_endpoint_url(self) -> str:
        """Get the streaming endpoint URL"""
        if self.endpoint_type == HuggingFaceEndpointType.SERVERLESS:
            return f"/models/{self.model}"
        else:
            return "/generate_stream"
    
    def _build_prompt(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Build the full prompt"""
        if system_prompt:
            return f"{system_prompt}\n\n{prompt}"
        return prompt
    
    def _build_payload(
        self,
        prompt: str,
        config: LLMConfig,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Build request payload for HuggingFace API"""
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": config.max_tokens or DEFAULT_MAX_TOKENS,
                "temperature": config.temperature,
                "top_p": config.top_p,
                "return_full_text": False,
            },
        }
        
        # Add streaming option
        if stream:
            payload["stream"] = True
        
        # Add optional parameters
        if config.stop_sequences:
            payload["parameters"]["stop"] = config.stop_sequences
        
        if hasattr(config, 'top_k') and config.top_k is not None:
            payload["parameters"]["top_k"] = config.top_k
        
        if hasattr(config, 'repetition_penalty') and config.repetition_penalty is not None:
            payload["parameters"]["repetition_penalty"] = config.repetition_penalty
        
        return payload
    
    def _extract_content(self, data: Any) -> str:
        """Extract generated content from response"""
        # Handle different response formats
        if isinstance(data, list):
            if len(data) > 0:
                if isinstance(data[0], dict):
                    return data[0].get("generated_text", "")
                return str(data[0])
            return ""
        elif isinstance(data, dict):
            return data.get("generated_text", "")
        else:
            return str(data)
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (words * 1.3)"""
        return int(len(text.split()) * 1.3)
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[LLMConfig] = None,
    ) -> LLMResponse:
        """
        Generate completion using HuggingFace Inference API.
        
        Args:
            prompt: User message
            system_prompt: Optional system prompt
            config: Generation configuration
        """
        config = config or LLMConfig()
        self._log_request(prompt, system_prompt)
        
        # Build the full prompt
        full_prompt = self._build_prompt(prompt, system_prompt)
        
        # Build request payload
        payload = self._build_payload(full_prompt, config, stream=False)
        
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                client = await self._get_client()
                start_time = time.time()
                
                url = self._get_endpoint_url()
                
                response = await client.post(
                    url,
                    json=payload,
                    headers=self._get_headers()
                )
                latency_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract content
                    content = self._extract_content(data)
                    
                    # Estimate tokens
                    prompt_tokens = self._estimate_tokens(full_prompt)
                    completion_tokens = self._estimate_tokens(content)
                    
                    llm_response = LLMResponse(
                        content=content,
                        model=self.model,
                        provider="huggingface",
                        usage={
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "total_tokens": prompt_tokens + completion_tokens,
                        },
                        finish_reason="stop",
                        raw_response=data,
                    )
                    
                    self._log_response(llm_response)
                    logger.debug(f"HuggingFace request completed in {latency_ms:.0f}ms")
                    
                    return llm_response
                else:
                    self._handle_error_response(response)
            
            except RateLimitError as e:
                last_error = e
                retry_count += 1
                if retry_count <= self.max_retries:
                    wait_time = min(2 ** retry_count, 60)
                    logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {retry_count}/{self.max_retries})")
                    await self._async_sleep(wait_time)
                else:
                    raise
            
            except TransientError as e:
                last_error = e
                retry_count += 1
                if retry_count <= self.max_retries:
                    # For model loading, wait longer
                    if "loading" in str(e).lower():
                        wait_time = min(10 + (retry_count * 5), 60)
                        logger.info(f"Model loading, waiting {wait_time}s (attempt {retry_count}/{self.max_retries})")
                    else:
                        wait_time = min(2 ** retry_count, 30)
                        logger.warning(f"Transient error, retrying in {wait_time}s: {e}")
                    await self._async_sleep(wait_time)
                else:
                    raise
            
            except httpx.TimeoutException:
                last_error = TransientError(f"HuggingFace request timed out after {self.timeout}s")
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
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[LLMConfig] = None,
    ):
        """
        Generate completion with streaming using HuggingFace Inference API.
        
        Args:
            prompt: User message
            system_prompt: Optional system prompt
            config: Generation configuration
            
        Yields:
            Chunk objects with .content attribute containing partial text
        """
        config = config or LLMConfig()
        self._log_request(prompt, system_prompt)
        
        # Build the full prompt
        full_prompt = self._build_prompt(prompt, system_prompt)
        
        # Build request payload with streaming enabled
        payload = self._build_payload(full_prompt, config, stream=True)
        
        # Create a simple chunk class for streaming
        class StreamChunk:
            def __init__(self, content: str):
                self.content = content
        
        try:
            client = await self._get_client()
            url = self._get_stream_endpoint_url()
            
            async with client.stream(
                "POST",
                url,
                json=payload,
                headers=self._get_headers()
            ) as response:
                if response.status_code != 200:
                    # Read error and delegate to error handler for granular error types
                    error_text = await response.aread()
                    try:
                        error_data = error_text.decode()
                    except Exception:
                        error_data = str(error_text)
                    self._handle_error_response(response, error_data)
                
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        if data_str and data_str != "[DONE]":
                            try:
                                data = json.loads(data_str)
                                # Handle different response formats
                                content = ""
                                if isinstance(data, dict):
                                    if "token" in data:
                                        content = data["token"].get("text", "")
                                    elif "generated_text" in data:
                                        content = data["generated_text"]
                                if content:
                                    yield StreamChunk(content)
                            except Exception:
                                pass  # Skip malformed chunks
                                
        except httpx.TimeoutException:
            raise TransientError(f"HuggingFace streaming request timed out after {self.timeout}s")
        except httpx.RequestError as e:
            raise TransientError(f"Network error during streaming: {e}")

    async def _handle_error_response(self, response: httpx.Response, error_data: Optional[str] = None):
        """Parse and raise appropriate exception for error responses
        
        Args:
            response: The HTTP response object
            error_data: Pre-read error data (optional, avoids re-reading body)
        """
        try:
            # Use pre-read error_data if provided, otherwise try to parse response
            if error_data is not None:
                import json
                try:
                    parsed_data = json.loads(error_data)
                    error_msg = parsed_data.get("error", str(parsed_data))
                except (json.JSONDecodeError, TypeError):
                    error_msg = error_data
            else:
                parsed_data = response.json()
                error_msg = parsed_data.get("error", str(parsed_data))
            
            # Extract more details if available
            if isinstance(error_msg, dict):
                error_msg = error_msg.get("message", str(error_msg))
        except Exception:
            error_msg = error_data or response.text or f"HTTP {response.status_code}"
        
        status_code = response.status_code
        error_lower = error_msg.lower()
        
        if status_code == 401:
            raise AuthenticationError(f"Invalid HuggingFace API key: {error_msg}")
        elif status_code == 403:
            raise AuthenticationError(f"Access denied: {error_msg}")
        elif status_code == 404:
            raise ModelNotFoundError(f"Model not found: {error_msg}")
        elif status_code == 429:
            raise RateLimitError(f"Rate limit exceeded: {error_msg}")
        elif status_code == 400:
            # Check for specific error types
            if "length" in error_lower or "tokens" in error_lower or "too long" in error_lower:
                raise ContextLengthError(error_msg)
            elif "input" in error_lower:
                raise InvalidRequestError(error_msg)
            raise InvalidRequestError(error_msg)
        elif status_code == 503:
            # Model loading or unavailable
            if "loading" in error_lower:
                estimated_time = self._extract_estimated_time(error_msg)
                msg = f"Model loading, estimated time: {estimated_time}s" if estimated_time else "Model loading, please retry"
                raise TransientError(msg)
            raise TransientError(f"Service unavailable: {error_msg}")
        elif status_code in (500, 502, 504):
            raise TransientError(f"HuggingFace server error ({status_code}): {error_msg}")
        else:
            raise ProviderError(f"HuggingFace error ({status_code}): {error_msg}")
    
    def _extract_estimated_time(self, error_msg: str) -> Optional[int]:
        """Extract estimated loading time from error message"""
        try:
            import re
            match = re.search(r"estimated_time[\"']?\s*:\s*(\d+)", error_msg)
            if match:
                return int(match.group(1))
        except Exception:
            pass
        return None
    
    async def test_connection(self) -> ConnectionTestResult:
        """Test HuggingFace API connectivity."""
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
                message=f"Connected to HuggingFace ({self.model}) - {latency_ms:.0f}ms",
                latency_ms=latency_ms,
                model_info={
                    "model": self.model,
                    "provider": "huggingface",
                    "endpoint_type": self.endpoint_type.value,
                    "wait_for_model": self.wait_for_model,
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
        except TransientError as e:
            # Model might be loading
            if "loading" in str(e).lower():
                return ConnectionTestResult(
                    success=False,
                    message=str(e),
                    error_code="MODEL_LOADING",
                )
            return ConnectionTestResult(
                success=False,
                message=str(e),
                error_code="TRANSIENT_ERROR",
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
        List available HuggingFace models.
        
        Returns predefined list (HF has too many models to enumerate effectively).
        """
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