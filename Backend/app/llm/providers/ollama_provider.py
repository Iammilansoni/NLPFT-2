"""
Ollama LLM Provider - Adapter for local Ollama models

Supports:
- Local Ollama installation
- All Ollama-compatible models (Llama, Mistral, Qwen, etc.)
- Auto-pull for missing models
- Model management (list, pull, delete)

Features:
- Native Ollama REST API integration
- Async HTTP calls with httpx
- Model auto-pull with progress tracking
- Streaming support (future)
"""

import time
from typing import Optional, List, Dict, Any, Callable

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
    TransientError,
    ModelNotFoundError,
    InvalidRequestError,
)


# =============================================================================
# OLLAMA PROVIDER
# =============================================================================

class OllamaLLMProvider(BaseLLMProvider):
    """
    Ollama local LLM provider.
    
    Connects to a local or remote Ollama server for inference.
    Supports automatic model pulling if model is not available.
    
    Usage:
        provider = OllamaLLMProvider(
            model="llama3.1:8b-instruct-q4_K_M",
            base_url="http://localhost:11434",  # Default
        )
        
        # Auto-pull if needed
        await provider.ensure_model_available()
        
        response = await provider.generate(
            prompt="Explain machine learning",
            system_prompt="You are a helpful AI teacher.",
        )
    """
    
    POPULAR_MODELS = [
        ProviderModel(
            id="llama3.1:8b-instruct-q4_K_M",
            name="Llama 3.1 8B Instruct",
            description="Fast, instruction-tuned Llama 3.1",
            context_length=128000,
            supports_vision=False,
            supports_functions=False,
        ),
        ProviderModel(
            id="llama3.2:3b-instruct-q4_K_M",
            name="Llama 3.2 3B Instruct",
            description="Lightweight Llama for fast inference",
            context_length=128000,
            supports_vision=False,
            supports_functions=False,
        ),
        ProviderModel(
            id="mistral:7b-instruct-q4_K_M",
            name="Mistral 7B Instruct",
            description="Efficient and capable Mistral",
            context_length=32768,
            supports_vision=False,
            supports_functions=False,
        ),
        ProviderModel(
            id="qwen2.5:7b-instruct-q4_K_M",
            name="Qwen 2.5 7B Instruct",
            description="Alibaba's latest Qwen model",
            context_length=32768,
            supports_vision=False,
            supports_functions=False,
        ),
        ProviderModel(
            id="gemma2:9b-instruct-q4_K_M",
            name="Gemma 2 9B Instruct",
            description="Google's open Gemma model",
            context_length=8192,
            supports_vision=False,
            supports_functions=False,
        ),
        ProviderModel(
            id="deepseek-r1:8b",
            name="DeepSeek R1 8B",
            description="DeepSeek reasoning model",
            context_length=64000,
            supports_vision=False,
            supports_functions=False,
        ),
    ]
    
    def __init__(
        self,
        model: str = "llama3.1:8b-instruct-q4_K_M",
        api_key: Optional[str] = None,  # Not used, for interface compatibility
        base_url: Optional[str] = None,
        timeout: float = 300.0,  # Longer timeout for local inference
        max_retries: int = 2,
        auto_pull: bool = True,
    ):
        """
        Initialize Ollama provider.
        
        Args:
            model: Model name (e.g., "llama3.1:8b-instruct-q4_K_M")
            api_key: Not used (Ollama is local)
            base_url: Ollama server URL (default: http://localhost:11434)
            timeout: Request timeout (longer for local GPU inference)
            max_retries: Retry attempts
            auto_pull: Automatically pull model if not available
        """
        # Use environment variable if base_url not provided
        import os
        default_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url or default_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.auto_pull = auto_pull
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OLLAMA
    
    @property
    def default_base_url(self) -> str:
        import os
        return os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.effective_base_url,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client
    
    async def is_available(self) -> bool:
        """Check if Ollama server is reachable"""
        try:
            client = await self._get_client()
            response = await client.get("/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False
    
    async def is_model_available(self, model_name: Optional[str] = None) -> bool:
        """Check if a specific model is pulled locally"""
        model_name = model_name or self.model
        try:
            models = await self._list_local_models()
            # Check with and without tag
            model_base = model_name.split(":")[0] if ":" in model_name else model_name
            for m in models:
                # Exact match or exact base match (split at colon and compare base)
                if m["name"] == model_name or m["name"].split(":", 1)[0] == model_base:
                    return True
            return False
        except Exception:
            return False
    
    async def _list_local_models(self) -> List[Dict[str, Any]]:
        """List locally available models"""
        client = await self._get_client()
        response = await client.get("/api/tags")
        
        if response.status_code == 200:
            data = response.json()
            return data.get("models", [])
        return []
    
    async def pull_model(
        self,
        model_name: Optional[str] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> bool:
        """
        Pull a model from Ollama registry.
        
        Args:
            model_name: Model to pull (defaults to self.model)
            progress_callback: Callback for progress updates (status, percent)
            
        Returns:
            True if pull succeeded
        """
        model_name = model_name or self.model
        logger.info(f"🔄 Pulling Ollama model: {model_name}")
        
        try:
            client = await self._get_client()
            
            # Use streaming to track progress
            async with client.stream(
                "POST",
                "/api/pull",
                json={"name": model_name, "stream": True},
                timeout=None,  # No timeout for pulls
            ) as response:
                if response.status_code != 200:
                    logger.error(f"Failed to pull model: {response.status_code}")
                    return False
                
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    
                    try:
                        import json
                        data = json.loads(line)
                        status = data.get("status", "")
                        
                        # Calculate progress
                        total = data.get("total", 0)
                        completed = data.get("completed", 0)
                        percent = (completed / total * 100) if total > 0 else 0
                        
                        if progress_callback:
                            progress_callback(status, percent)
                        
                        if "success" in status.lower():
                            logger.info(f"✅ Model pulled successfully: {model_name}")
                            return True
                            
                    except Exception as e:
                        logger.debug(f"Error parsing pull progress: {e}")
                
                logger.info(f"✅ Model pull completed: {model_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
    
    async def ensure_model_available(
        self,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> bool:
        """
        Ensure the configured model is available, pulling if needed.
        
        Args:
            progress_callback: Optional callback for pull progress
            
        Returns:
            True if model is available
        """
        if await self.is_model_available():
            logger.debug(f"Model already available: {self.model}")
            return True
        
        if not self.auto_pull:
            raise ModelNotFoundError(
                f"Model '{self.model}' not found. "
                f"Pull it with: ollama pull {self.model}"
            )
        
        logger.info(f"Model not found locally, pulling: {self.model}")
        return await self.pull_model(progress_callback=progress_callback)
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[LLMConfig] = None,
    ) -> LLMResponse:
        """
        Generate completion using Ollama API.
        
        Args:
            prompt: User message
            system_prompt: System instructions
            config: Generation configuration
            
        Returns:
            LLMResponse with generated content
        """
        config = config or LLMConfig()
        self._log_request(prompt, system_prompt)
        
        # Ensure model is available
        if self.auto_pull:
            await self.ensure_model_available()
        
        # Build request payload (Chat API format)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "top_p": config.top_p,
                "num_predict": config.max_tokens,
            },
        }
        
        if config.top_k is not None:
            payload["options"]["top_k"] = config.top_k
        
        if config.stop_sequences:
            payload["options"]["stop"] = config.stop_sequences
        
        try:
            client = await self._get_client()
            start_time = time.time()
            
            response = await client.post("/api/chat", json=payload)
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract content from message
                content = data.get("message", {}).get("content", "")
                
                llm_response = LLMResponse(
                    content=content,
                    model=data.get("model", self.model),
                    provider=self.provider_type.value,
                    usage={
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                        "total_tokens": (
                            data.get("prompt_eval_count", 0) + 
                            data.get("eval_count", 0)
                        ),
                    },
                    finish_reason=data.get("done_reason", "stop"),
                    raw_response=data,
                )
                
                self._log_response(llm_response)
                logger.debug(f"Ollama request completed in {latency_ms:.0f}ms")
                
                return llm_response
            else:
                self._handle_error_response(response)
                
        except httpx.TimeoutException:
            raise TransientError(f"Ollama request timed out after {self.timeout}s")
        except httpx.ConnectError:
            raise ProviderError(
                f"Cannot connect to Ollama at {self.effective_base_url}. "
                f"Is Ollama running? Start with: ollama serve"
            )
        except httpx.RequestError as e:
            raise TransientError(f"Network error: {e}")
    
    def _handle_error_response(self, response: httpx.Response):
        """Parse and raise appropriate exception for error responses"""
        try:
            error_data = response.json()
            error_msg = error_data.get("error", str(error_data))
        except Exception:
            error_msg = response.text
        
        status_code = response.status_code
        
        if status_code == 404:
            if "model" in error_msg.lower():
                raise ModelNotFoundError(f"Model not found: {error_msg}")
            raise ProviderError(f"Not found: {error_msg}")
        elif status_code == 400:
            raise InvalidRequestError(error_msg)
        elif status_code >= 500:
            raise TransientError(f"Ollama server error ({status_code}): {error_msg}")
        else:
            raise ProviderError(f"Ollama error ({status_code}): {error_msg}")
    
    async def test_connection(self) -> ConnectionTestResult:
        """
        Test Ollama connectivity and model availability.
        """
        # First check if server is reachable
        if not await self.is_available():
            return ConnectionTestResult(
                success=False,
                message=f"Cannot connect to Ollama at {self.effective_base_url}",
                error_code="CONNECTION_ERROR",
            )
        
        # Check if model is available, auto-pull if enabled
        if not await self.is_model_available():
            if self.auto_pull:
                logger.info(f"Model '{self.model}' not found locally, pulling automatically...")
                pulled = await self.pull_model()
                if not pulled:
                    return ConnectionTestResult(
                        success=False,
                        message=f"Model '{self.model}' not found and auto-pull failed.",
                        error_code="MODEL_PULL_FAILED",
                    )
            else:
                return ConnectionTestResult(
                    success=False,
                    message=f"Model '{self.model}' not found. Pull with: ollama pull {self.model}",
                    error_code="MODEL_NOT_FOUND",
                )

        # Test generation
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
                message=f"Connected to Ollama ({self.model})",
                latency_ms=latency_ms,
                model_info={
                    "model": response.model,
                    "provider": self.provider_type.value,
                    "base_url": self.effective_base_url,
                },
            )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message=f"Generation test failed: {e}",
                error_code="GENERATION_ERROR",
            )
    
    async def list_models(self) -> List[ProviderModel]:
        """
        List locally available models.
        """
        try:
            local_models = await self._list_local_models()
            
            models = []
            for m in local_models:
                models.append(ProviderModel(
                    id=m["name"],
                    name=m["name"],
                    description=f"Size: {m.get('size', 'unknown')}",
                    context_length=m.get("details", {}).get("context_length", 4096),
                ))
            
            # Add popular models that aren't local
            local_names = {m.id for m in models}
            for popular in self.POPULAR_MODELS:
                if popular.id not in local_names:
                    models.append(popular)
            
            return models
            
        except Exception as e:
            logger.warning(f"Failed to list Ollama models: {e}")
            return self.POPULAR_MODELS
    
    async def close(self):
        """Close the HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
