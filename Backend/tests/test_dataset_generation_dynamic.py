import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os
import json
import tempfile

# Add Backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.nlp.dataset_generator import EnterpriseDatasetGenerator

# Sample valid JSON response that the mock LLM will return
_MOCK_LLM_RESPONSE = json.dumps([
    {
        "query": "Test query 1",
        "api": "Test API",
        "endpoint": "/test",
        "method": "POST",
        "request": {"foo": "bar"},
        "expected_response": {"status": "ok"},
        "scenario_type": "valid",
        "test_category": "valid_flow",
        "notes": "Test note"
    }
])

@pytest.mark.asyncio
@patch('app.nlp.dataset_generator._gemini_available', True)
@patch('app.nlp.dataset_generator._gemini_client')
async def test_dynamic_dataset_generation(mock_client):
    """Test dataset generation with dynamic (None) and fixed num_examples."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.text = _MOCK_LLM_RESPONSE
    mock_client.generate_content.return_value = mock_response

    with tempfile.TemporaryDirectory() as tmpdir:
        generator = EnterpriseDatasetGenerator(datasets_dir=tmpdir)

        template_data = {
            "id": "test-id",
            "name": "Test API",
            "description": "A test API",
            "base_url": "http://test.com",
            "endpoint": "/test",
            "method": "POST",
            "parameters": [],
            "sample_requests": [],
            "sample_responses": [],
            "json_schema": {},
            "domain_tags": ["test"]
        }

        # Test with num_examples=None (dynamic mode)
        result = await generator.generate_dataset_from_template(
            template_data=template_data,
            num_examples=None,
            user_prompt="Generate some test cases"
        )

        assert result["success"] is True
        assert result["requested"] == "dynamic"

        # Verify the LLM was called and prompt contains expected content
        call_args = mock_client.generate_content.call_args
        assert call_args is not None
        # The prompt is passed as the first positional arg to generate_content
        prompt = call_args[0][0]
        assert "Generate exactly" in prompt
        assert "test cases" in prompt

        # Reset mock for next test
        mock_client.generate_content.reset_mock()
        mock_client.generate_content.return_value = mock_response

        # Test with num_examples=50
        result_fixed = await generator.generate_dataset_from_template(
            template_data=template_data,
            num_examples=50,
            user_prompt="Generate 50 cases"
        )

        assert result_fixed["success"] is True
        assert result_fixed["requested"] == 50

        # Verify prompt contains the fixed count
        call_args_fixed = mock_client.generate_content.call_args
        prompt_fixed = call_args_fixed[0][0]
        assert "Generate exactly 50 test cases" in prompt_fixed

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_dynamic_dataset_generation())
    print("Test passed!")
