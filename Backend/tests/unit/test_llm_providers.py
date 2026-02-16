"""
LLM Provider Unit Tests with Mocked Responses
==============================================
Tests all providers without requiring actual API keys by mocking HTTP responses.

Run with: pytest tests/unit/test_llm_providers.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import json

from app.llm.providers.base import (
    LLMConfig,
    LLMResponse,
    ProviderError,
    AuthenticationError,
    RateLimitError,
    TransientError,
    ModelNotFoundError,
    InvalidRequestError,
    ContextLengthError,
)


# =============================================================================
# MOCK RESPONSES
# =============================================================================

def create_mock_response(status_code: int, json_data: dict = None, text: str = None):
    """Create a mock httpx.Response"""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = status_code
    mock_response.headers = {}
    
    if json_data:
        mock_response.json.return_value = json_data
        mock_response.text = json.dumps(json_data)
    else:
        mock_response.text = text or ""
        mock_response.json.side_effect = json.JSONDecodeError("", "", 0)
    
    return mock_response


# Mock response templates for different providers
OPENAI_SUCCESS_RESPONSE = {
    "id": "chatcmpl-test123",
    "object": "chat.completion",
    "model": "gpt-4",
    "choices": [{
        "index": 0,
        "message": {"role": "assistant", "content": "Hello! How can I help you?"},
        "finish_reason": "stop"
    }],
    "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18}
}

ANTHROPIC_SUCCESS_RESPONSE = {
    "id": "msg_test123",
    "type": "message",
    "model": "claude-sonnet-4-5-20250929",
    "content": [{"type": "text", "text": "Hello! How can I help you?"}],
    "stop_reason": "end_turn",
    "usage": {"input_tokens": 10, "output_tokens": 8}
}

GROK_SUCCESS_RESPONSE = OPENAI_SUCCESS_RESPONSE.copy()
GROK_SUCCESS_RESPONSE["model"] = "grok-3"

OLLAMA_SUCCESS_RESPONSE = {
    "model": "llama3.1:8b-instruct-q4_K_M",
    "message": {"role": "assistant", "content": "Hello! How can I help you?"},
    "done": True,
    "done_reason": "stop",
    "prompt_eval_count": 10,
    "eval_count": 8
}

HUGGINGFACE_SUCCESS_RESPONSE = [
    {"generated_text": "Hello! How can I help you?"}
]


# =============================================================================
# OPENAI PROVIDER TESTS
# =============================================================================

@pytest.mark.asyncio
class TestOpenAIProvider:
    """Tests for OpenAI Provider"""
    
    async def test_successful_generation(self):
        """Test successful text generation"""
        from app.llm.providers.openai_provider import OpenAIProvider
        
        provider = OpenAIProvider(model="gpt-4", api_key="sk-test123")
        
        mock_response = create_mock_response(200, OPENAI_SUCCESS_RESPONSE)
        
        with patch.object(provider, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            response = await provider.generate(
                prompt="Hello",
                system_prompt="You are helpful",
                config=LLMConfig(temperature=0.7)
            )
            
            assert isinstance(response, LLMResponse)
            assert response.content == "Hello! How can I help you?"
            assert response.model == "gpt-4"
            assert response.usage["total_tokens"] == 18
    
    async def test_authentication_error(self):
        """Test 401 authentication error handling"""
        from app.llm.providers.openai_provider import OpenAIProvider
        
        provider = OpenAIProvider(model="gpt-4", api_key="invalid-key")
        
        mock_response = create_mock_response(401, {
            "error": {"message": "Invalid API key", "type": "invalid_api_key"}
        })
        
        with patch.object(provider, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            with pytest.raises(AuthenticationError):
                await provider.generate(prompt="Hello")
    
    async def test_rate_limit_error(self):
        """Test 429 rate limit error handling"""
        from app.llm.providers.openai_provider import OpenAIProvider
        
        provider = OpenAIProvider(model="gpt-4", api_key="sk-test123")
        
        mock_response = create_mock_response(429, {
            "error": {"message": "Rate limit exceeded", "type": "rate_limit_exceeded"}
        })
        mock_response.headers = {"Retry-After": "30"}
        
        with patch.object(provider, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                with pytest.raises(RateLimitError):
                    await provider.generate(prompt="Hello")
    
    async def test_model_not_found_error(self):
        """Test 404 model not found error handling"""
        from app.llm.providers.openai_provider import OpenAIProvider
        
        provider = OpenAIProvider(model="nonexistent-model", api_key="sk-test123")
        
        mock_response = create_mock_response(404, {
            "error": {"message": "Model not found", "type": "model_not_found"}
        })
        
        with patch.object(provider, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            with pytest.raises(ModelNotFoundError):
                await provider.generate(prompt="Hello")
    
    async def test_context_length_error(self):
        """Test context length exceeded error handling"""
        from app.llm.providers.openai_provider import OpenAIProvider
        
        provider = OpenAIProvider(model="gpt-4", api_key="sk-test123")
        
        mock_response = create_mock_response(400, {
            "error": {"message": "This model's maximum context_length is 8192 tokens", "type": "invalid_request"}
        })
        
        with patch.object(provider, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            with pytest.raises(ContextLengthError):
                await provider.generate(prompt="Hello")


# =============================================================================
# ANTHROPIC PROVIDER TESTS
# =============================================================================

@pytest.mark.asyncio
class TestAnthropicProvider:
    """Tests for Anthropic Provider"""
    
    async def test_successful_generation(self):
        """Test successful text generation"""
        from app.llm.providers.anthropic_provider import AnthropicProvider
        
        provider = AnthropicProvider(model="claude-sonnet-4-5-20250929", api_key="sk-ant-test123")
        
        mock_response = create_mock_response(200, ANTHROPIC_SUCCESS_RESPONSE)
        
        with patch.object(provider, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            response = await provider.generate(
                prompt="Hello",
                system_prompt="You are helpful"
            )
            
            assert isinstance(response, LLMResponse)
            assert response.content == "Hello! How can I help you?"
            assert response.provider == "anthropic"
    
    async def test_authentication_error(self):
        """Test 401 authentication error handling"""
        from app.llm.providers.anthropic_provider import AnthropicProvider
        
        provider = AnthropicProvider(model="claude-sonnet-4-5-20250929", api_key="invalid")
        
        mock_response = create_mock_response(401, {
            "error": {"message": "Invalid API key", "type": "authentication_error"}
        })
        
        with patch.object(provider, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            with pytest.raises(AuthenticationError):
                await provider.generate(prompt="Hello")
    
    async def test_rate_limit_error(self):
        """Test 429 rate limit error handling"""
        from app.llm.providers.anthropic_provider import AnthropicProvider
        
        provider = AnthropicProvider(model="claude-sonnet-4-5-20250929", api_key="sk-ant-test123")
        
        mock_response = create_mock_response(429, {
            "error": {"message": "Rate limit exceeded", "type": "rate_limit_error"}
        })
        
        with patch.object(provider, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            with pytest.raises(RateLimitError):
                await provider.generate(prompt="Hello")


# =============================================================================
# GOOGLE PROVIDER TESTS
# =============================================================================

@pytest.mark.asyncio
class TestGoogleProvider:
    """Tests for Google Gemini Provider"""
    
    async def test_successful_generation(self):
        """Test successful text generation"""
        from app.llm.providers.google_provider import GoogleProvider
        
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                # Setup mock
                mock_model = MagicMock()
                mock_response = MagicMock()
                mock_response.text = "Hello! How can I help you?"
                mock_response.prompt_feedback.block_reason = None
                mock_response.candidates = [MagicMock(finish_reason="STOP")]
                mock_response.usage_metadata = MagicMock(
                    prompt_token_count=10,
                    candidates_token_count=8,
                    total_token_count=18
                )
                mock_model.generate_content.return_value = mock_response
                mock_model_class.return_value = mock_model
                
                provider = GoogleProvider(model="gemini-2.0-flash", api_key="AIzaTest123")
                
                # Generate response with mocked model
                response = await provider.generate(
                    prompt="Hello",
                    system_prompt="You are helpful"
                )
                
                assert isinstance(response, LLMResponse)
                assert response.content == "Hello! How can I help you?"
                assert response.provider == "google"
    
    async def test_safety_filter_error(self):
        """Test Gemini safety filter block handling"""
        from app.llm.providers.google_provider import GoogleProvider
        
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = MagicMock()
                # Simulate safety filter block - error contains response.text and finish_reason
                mock_model.generate_content.side_effect = Exception(
                    "response.text quick accessor requires a single candidate with finish_reason STOP"
                )
                mock_model_class.return_value = mock_model
                
                provider = GoogleProvider(model="gemini-2.0-flash", api_key="AIzaTest123")
                
                with pytest.raises(InvalidRequestError) as exc_info:
                    await provider.generate(prompt="Hello")
                
                assert "safety filters" in str(exc_info.value).lower()
    
    async def test_rate_limit_error(self):
        """Test rate limit error handling"""
        from app.llm.providers.google_provider import GoogleProvider
        
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = MagicMock()
                mock_model.generate_content.side_effect = Exception(
                    "Resource has been exhausted: quota exceeded"
                )
                mock_model_class.return_value = mock_model
                
                provider = GoogleProvider(model="gemini-2.0-flash", api_key="AIzaTest123")
                
                with pytest.raises(RateLimitError):
                    await provider.generate(prompt="Hello")
    
    async def test_authentication_error(self):
        """Test authentication error handling"""
        from app.llm.providers.google_provider import GoogleProvider
        
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = MagicMock()
                mock_model.generate_content.side_effect = Exception(
                    "API_KEY invalid or expired"
                )
                mock_model_class.return_value = mock_model
                
                provider = GoogleProvider(model="gemini-2.0-flash", api_key="invalid")
                
                with pytest.raises(AuthenticationError):
                    await provider.generate(prompt="Hello")


# =============================================================================
# GROK PROVIDER TESTS
# =============================================================================

@pytest.mark.asyncio
class TestGrokProvider:
    """Tests for Grok (xAI) Provider"""
    
    async def test_successful_generation(self):
        """Test successful text generation"""
        from app.llm.providers.grok_provider import GrokProvider
        
        provider = GrokProvider(model="grok-3", api_key="xai-test123")
        
        mock_response = create_mock_response(200, GROK_SUCCESS_RESPONSE)
        
        with patch.object(provider, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            response = await provider.generate(
                prompt="Hello",
                system_prompt="You are helpful"
            )
            
            assert isinstance(response, LLMResponse)
            assert response.content == "Hello! How can I help you?"
            assert response.provider == "grok"
    
    async def test_authentication_error(self):
        """Test 401 authentication error handling"""
        from app.llm.providers.grok_provider import GrokProvider
        
        provider = GrokProvider(model="grok-3", api_key="invalid")
        
        mock_response = create_mock_response(401, {
            "error": {"message": "Invalid API key", "type": "auth_error"}
        })
        
        with patch.object(provider, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            with pytest.raises(AuthenticationError):
                await provider.generate(prompt="Hello")


# =============================================================================
# OLLAMA PROVIDER TESTS
# =============================================================================

@pytest.mark.asyncio
class TestOllamaProvider:
    """Tests for Ollama Provider"""
    
    async def test_successful_generation(self):
        """Test successful text generation"""
        from app.llm.providers.ollama_provider import OllamaLLMProvider
        
        provider = OllamaLLMProvider(
            model="llama3.1:8b-instruct-q4_K_M",
            base_url="http://localhost:11434",
            auto_pull=False
        )
        
        mock_response = create_mock_response(200, OLLAMA_SUCCESS_RESPONSE)
        
        with patch.object(provider, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            response = await provider.generate(
                prompt="Hello",
                system_prompt="You are helpful"
            )
            
            assert isinstance(response, LLMResponse)
            assert response.content == "Hello! How can I help you?"
            assert response.provider == "ollama"
    
    async def test_model_not_found_error(self):
        """Test model not found error handling"""
        from app.llm.providers.ollama_provider import OllamaLLMProvider
        
        provider = OllamaLLMProvider(
            model="nonexistent-model",
            base_url="http://localhost:11434",
            auto_pull=False
        )
        
        mock_response = create_mock_response(404, {
            "error": "model 'nonexistent-model' not found"
        })
        
        with patch.object(provider, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            with pytest.raises(ModelNotFoundError):
                await provider.generate(prompt="Hello")
    
    async def test_connection_error(self):
        """Test connection error when Ollama is not running"""
        from app.llm.providers.ollama_provider import OllamaLLMProvider
        
        provider = OllamaLLMProvider(
            model="llama3.1:8b-instruct-q4_K_M",
            base_url="http://localhost:11434",
            auto_pull=False
        )
        
        with patch.object(provider, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
            mock_get_client.return_value = mock_client
            
            with pytest.raises(ProviderError) as exc_info:
                await provider.generate(prompt="Hello")
            
            assert "connect" in str(exc_info.value).lower() or "ollama" in str(exc_info.value).lower()


# =============================================================================
# HUGGINGFACE PROVIDER TESTS
# =============================================================================

@pytest.mark.asyncio
class TestHuggingFaceProvider:
    """Tests for HuggingFace Provider"""
    
    async def test_successful_generation(self):
        """Test successful text generation"""
        from app.llm.providers.huggingface_provider import HuggingFaceProvider
        
        provider = HuggingFaceProvider(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct",
            api_key="hf_test123"
        )
        
        mock_response = create_mock_response(200, HUGGINGFACE_SUCCESS_RESPONSE)
        
        with patch.object(provider, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            response = await provider.generate(
                prompt="Hello",
                system_prompt="You are helpful"
            )
            
            assert isinstance(response, LLMResponse)
            assert response.content == "Hello! How can I help you?"
            assert response.provider == "huggingface"
    
    async def test_authentication_error(self):
        """Test 401 authentication error handling"""
        from app.llm.providers.huggingface_provider import HuggingFaceProvider
        
        provider = HuggingFaceProvider(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct",
            api_key="invalid"
        )
        
        mock_response = create_mock_response(401, {
            "error": "Invalid API key"
        })
        
        with patch.object(provider, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            with pytest.raises(AuthenticationError):
                await provider.generate(prompt="Hello")
    
    async def test_model_loading_error(self):
        """Test 503 model loading error handling"""
        from app.llm.providers.huggingface_provider import HuggingFaceProvider
        
        provider = HuggingFaceProvider(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct",
            api_key="hf_test123"
        )
        
        mock_response = create_mock_response(503, {
            "error": "Model is currently loading"
        })
        
        with patch.object(provider, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            with patch.object(provider, '_async_sleep', new_callable=AsyncMock):
                with pytest.raises(TransientError) as exc_info:
                    await provider.generate(prompt="Hello")
                
                assert "loading" in str(exc_info.value).lower() or "retry" in str(exc_info.value).lower()


# =============================================================================
# CUSTOM PROVIDER TESTS
# =============================================================================

@pytest.mark.asyncio
class TestCustomProvider:
    """Tests for Custom HTTP Provider"""
    
    async def test_successful_generation(self):
        """Test successful text generation"""
        from app.llm.providers.custom_provider import CustomHTTPProvider
        
        provider = CustomHTTPProvider(
            model="local-model",
            base_url="http://localhost:8000/v1"
        )
        
        mock_response = create_mock_response(200, OPENAI_SUCCESS_RESPONSE)
        
        with patch.object(provider, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            response = await provider.generate(
                prompt="Hello",
                system_prompt="You are helpful"
            )
            
            assert isinstance(response, LLMResponse)
            assert response.content == "Hello! How can I help you?"
            assert response.provider == "custom"
    
    async def test_connection_error(self):
        """Test connection error handling"""
        from app.llm.providers.custom_provider import CustomHTTPProvider
        
        provider = CustomHTTPProvider(
            model="local-model",
            base_url="http://localhost:8000/v1"
        )
        
        with patch.object(provider, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
            mock_get_client.return_value = mock_client
            
            with pytest.raises(TransientError) as exc_info:
                await provider.generate(prompt="Hello")
            
            assert "connect" in str(exc_info.value).lower()


# =============================================================================
# CROSS-PROVIDER EDGE CASE TESTS
# =============================================================================

@pytest.mark.asyncio
class TestProviderEdgeCases:
    """Edge case tests across all providers"""
    
    @pytest.mark.parametrize("provider_class,provider_name,init_kwargs", [
        ("OpenAIProvider", "openai_provider", {"model": "gpt-4", "api_key": "test"}),
        ("AnthropicProvider", "anthropic_provider", {"model": "claude-sonnet-4-5-20250929", "api_key": "test"}),
        ("GrokProvider", "grok_provider", {"model": "grok-3", "api_key": "test"}),
        ("HuggingFaceProvider", "huggingface_provider", {"model": "test-model", "api_key": "test"}),
        ("CustomHTTPProvider", "custom_provider", {"model": "test", "base_url": "http://localhost:8000/v1"}),
    ])
    async def test_timeout_handling(self, provider_class, provider_name, init_kwargs):
        """Test timeout error handling for HTTP-based providers"""
        module = __import__(f"app.llm.providers.{provider_name}", fromlist=[provider_class])
        ProviderClass = getattr(module, provider_class)
        
        provider = ProviderClass(**init_kwargs)
        
        with patch.object(provider, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Request timed out"))
            mock_get_client.return_value = mock_client
            
            # Just verify TransientError is raised - message format varies by provider
            with pytest.raises(TransientError):
                await provider.generate(prompt="Hello")
    
    @pytest.mark.parametrize("provider_class,provider_name,init_kwargs", [
        ("OpenAIProvider", "openai_provider", {"model": "gpt-4", "api_key": "test"}),
        ("AnthropicProvider", "anthropic_provider", {"model": "claude-sonnet-4-5-20250929", "api_key": "test"}),
        ("GrokProvider", "grok_provider", {"model": "grok-3", "api_key": "test"}),
        ("HuggingFaceProvider", "huggingface_provider", {"model": "test-model", "api_key": "test"}),
        ("CustomHTTPProvider", "custom_provider", {"model": "test", "base_url": "http://localhost:8000/v1"}),
    ])
    async def test_server_error_handling(self, provider_class, provider_name, init_kwargs):
        """Test 500 server error handling for HTTP-based providers"""
        module = __import__(f"app.llm.providers.{provider_name}", fromlist=[provider_class])
        ProviderClass = getattr(module, provider_class)
        
        provider = ProviderClass(**init_kwargs)
        
        mock_response = create_mock_response(500, {"error": "Internal server error"})
        
        with patch.object(provider, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            with pytest.raises(TransientError):
                await provider.generate(prompt="Hello")
