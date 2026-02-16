"""
Google Gemini Provider - Adapter for Google's Generative AI API

Supports:
- Gemini 3.0 Series (Preview)
- Gemini 2.5 Series (Recommended)
- Gemini 2.0 Series (Retiring March 2026)
- Gemini 1.5 Series (Legacy)

Features:
- Native Google AI SDK integration
- Async generation with thread pool
- Safety settings configuration
- Token counting
- Function/tool calling
"""

import time
import asyncio
import threading
from typing import Optional, List, Dict, Any
from enum import Enum

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

class SafetyThreshold(str, Enum):
    """Gemini safety filter thresholds"""
    BLOCK_NONE = "BLOCK_NONE"
    BLOCK_ONLY_HIGH = "BLOCK_ONLY_HIGH"
    BLOCK_MEDIUM_AND_ABOVE = "BLOCK_MEDIUM_AND_ABOVE"
    BLOCK_LOW_AND_ABOVE = "BLOCK_LOW_AND_ABOVE"


class HarmCategory(str, Enum):
    """Gemini harm categories"""
    HARM_CATEGORY_HARASSMENT = "HARM_CATEGORY_HARASSMENT"
    HARM_CATEGORY_HATE_SPEECH = "HARM_CATEGORY_HATE_SPEECH"
    HARM_CATEGORY_SEXUALLY_EXPLICIT = "HARM_CATEGORY_SEXUALLY_EXPLICIT"
    HARM_CATEGORY_DANGEROUS_CONTENT = "HARM_CATEGORY_DANGEROUS_CONTENT"


DEFAULT_MAX_TOKENS = 8192
DEFAULT_SAFETY_THRESHOLD = SafetyThreshold.BLOCK_MEDIUM_AND_ABOVE

# Thread lock for genai.configure() which sets process-wide global state.
# Without this, concurrent GoogleProvider instances with different API keys
# would race on the global configuration.
_genai_configure_lock = threading.Lock()


# =============================================================================
# GOOGLE PROVIDER
# =============================================================================

class GoogleProvider(BaseLLMProvider):
    """
    Google Gemini API provider.
    
    Uses the official google-generativeai SDK for API access.
    
    Usage:
        provider = GoogleProvider(
            model="gemini-2.5-flash",
            api_key="AIza...",
        )
        
        response = await provider.generate(
            prompt="Explain quantum computing",
            system_prompt="You are a physics teacher.",
        )
        
        # Streaming
        async for chunk in provider.generate_stream(prompt="Hello"):
            print(chunk.content, end="", flush=True)
    """
    
    DEFAULT_MODELS = [
        # Gemini 3.0 Series (Preview)
        ProviderModel(
            id="gemini-3-pro-preview",
            name="Gemini 3 Pro Preview",
            description="Latest flagship model preview",
            context_length=1000000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gemini-3-flash-preview",
            name="Gemini 3 Flash Preview",
            description="Fast, efficient next-gen model",
            context_length=1000000,
            supports_vision=True,
            supports_functions=True,
        ),
        # Gemini 2.5 Series (Stable)
        ProviderModel(
            id="gemini-2.5-pro",
            name="Gemini 2.5 Pro",
            description="State-of-the-art thinking model for complex reasoning",
            context_length=1000000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gemini-2.5-pro-preview-06-05",
            name="Gemini 2.5 Pro Preview",
            description="Latest 2.5 Pro preview with enhanced capabilities",
            context_length=1000000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gemini-2.5-flash",
            name="Gemini 2.5 Flash",
            description="Best price-performance, great for high-volume tasks",
            context_length=1000000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gemini-2.5-flash-preview-05-20",
            name="Gemini 2.5 Flash Preview",
            description="Latest 2.5 Flash preview",
            context_length=1000000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gemini-2.5-flash-lite",
            name="Gemini 2.5 Flash-Lite",
            description="Lightweight, ultra-fast for simple tasks",
            context_length=1000000,
            supports_vision=True,
            supports_functions=True,
        ),
        # Gemini 2.0 Series (Retiring March 3, 2026)
        ProviderModel(
            id="gemini-2.0-flash",
            name="Gemini 2.0 Flash",
            description="[RETIRING Mar 2026] Fast multimodal model",
            context_length=1000000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gemini-2.0-flash-lite",
            name="Gemini 2.0 Flash-Lite",
            description="[RETIRING Mar 2026] Lightweight for high throughput",
            context_length=1000000,
            supports_vision=True,
            supports_functions=True,
        ),
        # Gemini 1.5 Series (Legacy - Retired for new projects Apr 2025)
        ProviderModel(
            id="gemini-1.5-pro",
            name="Gemini 1.5 Pro",
            description="[LEGACY] Advanced reasoning with 1M context",
            context_length=1000000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gemini-1.5-flash",
            name="Gemini 1.5 Flash",
            description="[LEGACY] Fast and efficient for high-volume",
            context_length=1000000,
            supports_vision=True,
            supports_functions=True,
        ),
        ProviderModel(
            id="gemini-1.5-flash-8b",
            name="Gemini 1.5 Flash 8B",
            description="[LEGACY] Smallest Gemini, fastest inference",
            context_length=1000000,
            supports_vision=True,
            supports_functions=True,
        ),
    ]
    
    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,  # Not used but kept for interface
        timeout: float = 120.0,
        max_retries: int = 3,
        safety_threshold: SafetyThreshold = DEFAULT_SAFETY_THRESHOLD,
        enable_safety_filters: bool = True,
    ):
        """
        Initialize Google Gemini provider.
        
        Args:
            model: Model ID (e.g., "gemini-2.5-flash")
            api_key: Google AI API key
            base_url: Not used (for interface compatibility)
            timeout: Request timeout in seconds
            max_retries: Retry attempts on failure
            safety_threshold: Safety filter threshold level
            enable_safety_filters: Whether to use safety filters
        """
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._genai = None
        self._model_client = None
        self._initialized = False
        self.safety_threshold = safety_threshold
        self.enable_safety_filters = enable_safety_filters
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.GOOGLE
    
    @property
    def default_base_url(self) -> str:
        return "https://generativelanguage.googleapis.com"
    
    def _ensure_initialized(self):
        """Initialize Google AI SDK on first use"""
        if self._initialized:
            return

        if not self.api_key:
            raise AuthenticationError("Google API key is required")

        try:
            import google.generativeai as genai
            self._genai = genai

            # Use lock around genai.configure() which sets process-wide state.
            # Each call to _ensure_initialized re-configures with this instance's key.
            # For truly concurrent different-key usage, separate processes are needed.
            with _genai_configure_lock:
                genai.configure(api_key=self.api_key)
                self._model_client = genai.GenerativeModel(self.model)

            self._initialized = True

            logger.info(f"Google Gemini provider initialized with model: {self.model}")
            
        except ImportError:
            raise ProviderError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )
        except Exception as e:
            error_str = str(e).upper()
            if "API_KEY" in error_str or "AUTHENTICATION" in error_str or "INVALID_ARGUMENT" in error_str:
                raise AuthenticationError(f"Google API key error: {e}")
            raise ProviderError(f"Failed to initialize Google AI: {e}")
    
    def _get_safety_settings(self) -> Optional[List[Dict[str, str]]]:
        """Build safety settings configuration"""
        if not self.enable_safety_filters:
            # Disable all safety filters
            return [
                {
                    "category": category.value,
                    "threshold": SafetyThreshold.BLOCK_NONE.value
                }
                for category in HarmCategory
            ]
        
        # Use configured threshold
        return [
            {
                "category": category.value,
                "threshold": self.safety_threshold.value
            }
            for category in HarmCategory
        ]
    
    def _convert_tools_to_gemini_format(self, tools: List[Dict[str, Any]]) -> List:
        """
        Convert OpenAI-style tools to Gemini function declarations format.
        
        Args:
            tools: List of tool definitions in OpenAI format
            
        Returns:
            List of Gemini-compatible tool objects
        """
        if not tools:
            return None
        
        try:
            import google.generativeai as genai
            
            function_declarations = []
            for tool in tools:
                if tool.get("type") == "function":
                    func = tool.get("function", {})
                    function_declarations.append({
                        "name": func.get("name", ""),
                        "description": func.get("description", ""),
                        "parameters": func.get("parameters", {})
                    })
            
            if function_declarations:
                return [genai.protos.Tool(function_declarations=function_declarations)]
            return None
        except Exception as e:
            logger.warning(f"Failed to convert tools to Gemini format: {e}")
            return None
    
    def _build_generation_config(self, config: LLMConfig) -> Dict[str, Any]:
        """Build generation configuration"""
        generation_config = {
            "temperature": config.temperature,
            "top_p": config.top_p,
            "max_output_tokens": config.max_tokens or DEFAULT_MAX_TOKENS,
        }
        
        if hasattr(config, 'top_k') and config.top_k is not None:
            generation_config["top_k"] = config.top_k
        
        if config.stop_sequences:
            generation_config["stop_sequences"] = config.stop_sequences
        
        return generation_config
    
    def _build_prompt(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Build combined prompt for Gemini.
        
        Args:
            prompt: User message
            system_prompt: System instructions (prepended to message)
            
        Returns:
            Combined prompt string
        """
        if system_prompt:
            return f"{system_prompt}\n\n{prompt}"
        return prompt
    
    def _extract_response_content(self, response) -> str:
        """Extract text content from Gemini response"""
        if not response:
            raise ProviderError("Empty response from Gemini")
        
        # Check for safety blocks first
        if hasattr(response, 'prompt_feedback'):
            feedback = response.prompt_feedback
            if hasattr(feedback, 'block_reason') and feedback.block_reason:
                raise InvalidRequestError(
                    f"Content blocked by safety filters: {feedback.block_reason}"
                )
        
        # Try to get text
        try:
            return response.text
        except ValueError as e:
            # response.text raises ValueError if blocked
            error_str = str(e).lower()
            if "finish_reason" in error_str or "safety" in error_str:
                # Get detailed safety ratings if available
                safety_info = []
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'safety_ratings'):
                        for rating in candidate.safety_ratings:
                            if hasattr(rating, 'probability') and rating.probability != "NEGLIGIBLE":
                                safety_info.append(f"{rating.category}: {rating.probability}")
                
                detail = f" ({', '.join(safety_info)})" if safety_info else ""
                raise InvalidRequestError(
                    f"Content blocked by Gemini safety filters{detail}. "
                    f"Try adjusting your prompt or disabling safety filters."
                )
            raise ProviderError(f"Failed to extract response text: {e}")
    
    def _extract_usage(self, response) -> Dict[str, int]:
        """Extract token usage from response"""
        usage = {}
        if hasattr(response, 'usage_metadata'):
            metadata = response.usage_metadata
            usage = {
                "prompt_tokens": getattr(metadata, 'prompt_token_count', 0),
                "completion_tokens": getattr(metadata, 'candidates_token_count', 0),
                "total_tokens": getattr(metadata, 'total_token_count', 0),
            }
        return usage
    
    def _extract_finish_reason(self, response) -> Optional[str]:
        """Extract finish reason from response"""
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason'):
                return str(candidate.finish_reason)
        return None
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[LLMConfig] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        """
        Generate completion using Gemini API.
        
        Args:
            prompt: User message
            system_prompt: System instructions
            config: Generation configuration
            tools: Optional tool/function definitions
            
        Returns:
            LLMResponse with generated content
        """
        config = config or LLMConfig()
        self._log_request(prompt, system_prompt)
        self._ensure_initialized()
        
        # Build generation config
        generation_config = self._build_generation_config(config)
        safety_settings = self._get_safety_settings()
        
        # Build prompt
        full_prompt = self._build_prompt(prompt, system_prompt)
        
        # Prepare tools if provided
        gemini_tools = None
        if tools:
            # Convert OpenAI-style tools to Gemini format
            gemini_tools = self._convert_tools_to_gemini_format(tools)
        
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                start_time = time.time()

                # Ensure correct API key and get a client for this key.
                # Only hold the lock during configure+client creation, NOT the network call.
                def _get_configured_client():
                    with _genai_configure_lock:
                        self._genai.configure(api_key=self.api_key)
                        # Re-create model client each time under lock to ensure
                        # it's bound to the correct api_key configuration.
                        return self._genai.GenerativeModel(self.model)

                client = await asyncio.to_thread(_get_configured_client)

                # Network call happens outside the lock so other providers
                # with different API keys can proceed concurrently.
                def _call_generate(c):
                    if gemini_tools:
                        return c.generate_content(
                            full_prompt,
                            generation_config=generation_config,
                            safety_settings=safety_settings,
                            tools=gemini_tools,
                        )
                    else:
                        return c.generate_content(
                            full_prompt,
                            generation_config=generation_config,
                            safety_settings=safety_settings,
                        )

                response = await asyncio.to_thread(_call_generate, client)
                
                latency_ms = (time.time() - start_time) * 1000
                
                # Check if response contains function calls
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate.content, 'parts'):
                        import uuid
                        tool_calls = []
                        tool_call_counter = 0
                        for part in candidate.content.parts:
                            if hasattr(part, 'function_call') and part.function_call:
                                # Extract function call details with unique ID
                                func_call = part.function_call
                                unique_suffix = uuid.uuid4().hex[:8]
                                tool_call_counter += 1
                                tool_calls.append({
                                    "id": f"call_{func_call.name}_{tool_call_counter}_{unique_suffix}",
                                    "type": "function",
                                    "function": {
                                        "name": func_call.name,
                                        "arguments": dict(func_call.args) if func_call.args else {}
                                    }
                                })
                        
                        # If we collected any function calls, return them all
                        if tool_calls:
                            llm_response = LLMResponse(
                                content="",  # No text content when function is called
                                model=self.model,
                                provider=self.provider_type.value,
                                usage=self._extract_usage(response),
                                finish_reason="function_call",
                                raw_response=None,
                                tool_calls=tool_calls,
                            )

                            self._log_response(llm_response)
                            logger.debug(f"Gemini {len(tool_calls)} function call(s) in {latency_ms:.0f}ms: {[tc['function']['name'] for tc in tool_calls]}")
                            
                            return llm_response
                
                # Extract response content
                content = self._extract_response_content(response)
                usage = self._extract_usage(response)
                finish_reason = self._extract_finish_reason(response)
                
                llm_response = LLMResponse(
                    content=content,
                    model=self.model,
                    provider=self.provider_type.value,
                    usage=usage,
                    finish_reason=finish_reason,
                    raw_response=None,  # SDK response not JSON serializable
                )
                
                self._log_response(llm_response)
                logger.debug(f"Gemini request completed in {latency_ms:.0f}ms")
                
                return llm_response
            
            except (AuthenticationError, InvalidRequestError, ModelNotFoundError, ContextLengthError):
                # Don't retry these errors
                raise
            
            except RateLimitError as e:
                last_error = e
                retry_count += 1
                if retry_count <= self.max_retries:
                    wait_time = min(2 ** retry_count, 60)
                    logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {retry_count}/{self.max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    raise
            
            except TransientError as e:
                last_error = e
                retry_count += 1
                if retry_count <= self.max_retries:
                    wait_time = min(2 ** retry_count, 30)
                    logger.warning(f"Transient error, retrying in {wait_time}s (attempt {retry_count}/{self.max_retries}): {e}")
                    await asyncio.sleep(wait_time)
                else:
                    raise
            
            except Exception as e:
                # Classify and potentially retry
                error_str = str(e).lower()
                
                if "quota" in error_str or ("rate" in error_str and "limit" in error_str):
                    last_error = RateLimitError(f"Gemini rate limit: {e}")
                    retry_count += 1
                    if retry_count <= self.max_retries:
                        wait_time = min(2 ** retry_count, 60)
                        logger.warning(f"Rate limit, retrying in {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                    raise last_error
                
                elif "timeout" in error_str or "deadline" in error_str:
                    last_error = TransientError(f"Gemini timeout: {e}")
                    retry_count += 1
                    if retry_count <= self.max_retries:
                        logger.warning(f"Timeout, retrying (attempt {retry_count}/{self.max_retries})")
                        await asyncio.sleep(min(2 ** retry_count, 30))
                        continue
                    raise last_error
                
                elif "503" in error_str or "unavailable" in error_str:
                    last_error = TransientError(f"Gemini service unavailable: {e}")
                    retry_count += 1
                    if retry_count <= self.max_retries:
                        logger.warning("Service unavailable, retrying")
                        await asyncio.sleep(min(2 ** retry_count, 30))
                        continue
                    raise last_error
                
                # Non-retryable errors
                elif "api_key" in error_str or "authentication" in error_str:
                    raise AuthenticationError(f"Gemini auth error: {e}")
                elif "not found" in error_str or "invalid model" in error_str:
                    raise ModelNotFoundError(f"Model not found: {self.model}")
                elif "context" in error_str or "too long" in error_str:
                    raise ContextLengthError(f"Context too long: {e}")
                else:
                    raise ProviderError(f"Gemini error: {e}")
        
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
        Generate completion with streaming using Gemini API.
        
        Args:
            prompt: User message
            system_prompt: System instructions
            config: Generation configuration
            
        Yields:
            Chunk objects with .content attribute containing partial text
        """
        config = config or LLMConfig()
        self._log_request(prompt, system_prompt)
        self._ensure_initialized()
        
        # Build generation config
        generation_config = self._build_generation_config(config)
        safety_settings = self._get_safety_settings()
        
        # Build prompt
        full_prompt = self._build_prompt(prompt, system_prompt)
        
        try:
            # Configure + create client under lock, then stream outside the lock
            def _get_configured_client():
                with _genai_configure_lock:
                    self._genai.configure(api_key=self.api_key)
                    return self._genai.GenerativeModel(self.model)

            client = await asyncio.to_thread(_get_configured_client)

            def _stream_sync():
                return client.generate_content(
                    full_prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings,
                    stream=True,
                )
            
            response_stream = await asyncio.to_thread(_stream_sync)
            
            # Create a simple chunk class for streaming
            class StreamChunk:
                def __init__(self, content: str):
                    self.content = content
            
            # Use asyncio queue for true streaming with background thread
            chunk_queue: asyncio.Queue[Optional[str]] = asyncio.Queue()
            
            # Capture event loop before defining producer (for thread-safe access)
            loop = asyncio.get_running_loop()
            
            def _producer():
                """Producer: iterate response_stream in background and enqueue chunks."""
                try:
                    for chunk in response_stream:
                        if chunk.text:
                            loop.call_soon_threadsafe(
                                chunk_queue.put_nowait, chunk.text
                            )
                finally:
                    # Signal completion with sentinel None
                    loop.call_soon_threadsafe(
                        chunk_queue.put_nowait, None
                    )
            
            # Start producer in background thread
            producer_future = loop.run_in_executor(None, _producer)
            
            # Consumer: async loop that dequeues and yields StreamChunk
            while True:
                text = await chunk_queue.get()
                if text is None:  # Sentinel: producer finished
                    break
                yield StreamChunk(text)
            
            # Await producer completion to catch any exceptions
            await producer_future
                
        except Exception as e:
            error_str = str(e).lower()
            if "api_key" in error_str or "authentication" in error_str:
                raise AuthenticationError(f"Gemini auth error: {e}")
            elif "not found" in error_str or "invalid model" in error_str:
                raise ModelNotFoundError(f"Model not found: {self.model}")
            else:
                raise ProviderError(f"Gemini streaming error: {e}")

    async def test_connection(self) -> ConnectionTestResult:
        """
        Test Gemini API connectivity.
        """
        try:
            start_time = time.time()

            await self.generate(
                prompt="Respond with the single word: Hello",
                system_prompt="You are a helpful assistant. Reply with one word only.",
                config=LLMConfig(max_tokens=10, temperature=0),
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            return ConnectionTestResult(
                success=True,
                message=f"Connected to Google Gemini ({self.model}) - {latency_ms:.0f}ms",
                latency_ms=latency_ms,
                model_info={
                    "model": self.model,
                    "provider": self.provider_type.value,
                    "safety_filters": self.enable_safety_filters,
                    "safety_threshold": self.safety_threshold.value,
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
        except InvalidRequestError as e:
            return ConnectionTestResult(
                success=False,
                message=f"Safety filter triggered: {e}",
                error_code="SAFETY_BLOCK",
            )
        except RateLimitError:
            return ConnectionTestResult(
                success=False,
                message="Gemini API quota exceeded. Please check your Google Cloud billing or wait for quota reset.",
                error_code="RATE_LIMITED",
            )
        except Exception as e:
            error_str = str(e).lower()
            # Check for quota/rate limit in generic exceptions too
            # Use precise matching to avoid false positives from words like "generate" or "moderate"
            if "quota" in error_str or "429" in error_str or ("rate" in error_str and "limit" in error_str):
                return ConnectionTestResult(
                    success=False,
                    message="Gemini API quota exceeded. Please check your Google Cloud billing or wait for quota reset.",
                    error_code="RATE_LIMITED",
                )
            logger.exception("Connection test failed")
            return ConnectionTestResult(
                success=False,
                message=f"Connection failed: {e}",
                error_code="CONNECTION_ERROR",
            )
    
    async def list_models(self) -> List[ProviderModel]:
        """
        List available Gemini models.
        
        Returns predefined list for reliability. Could fetch from API
        using genai.list_models() but that requires initialization.
        """
        return self.DEFAULT_MODELS
    
    async def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using Gemini's tokenizer.
        
        Args:
            text: Text to tokenize
            
        Returns:
            Token count
        """
        self._ensure_initialized()
        
        try:
            result = await asyncio.to_thread(
                self._model_client.count_tokens,
                text
            )
            return result.total_tokens
        except Exception as e:
            logger.warning(f"Failed to count tokens: {e}")
            # Fallback to rough estimate (4 chars per token)
            return len(text) // 4
    
    async def close(self):
        """Clean up resources"""
        self._model_client = None
        self._genai = None
        self._initialized = False
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()