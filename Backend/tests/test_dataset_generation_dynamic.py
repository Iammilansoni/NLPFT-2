import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os
import json
import re
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

        # Generation BATCHES: 50 examples at BATCH_SIZE=10 is five calls, each
        # asking for a batch, never one call asking for 50. This previously
        # asserted "Generate exactly 50 test cases" appeared in the prompt, which
        # the batching design has never produced -- the assertion was testing a
        # behaviour that did not exist, not catching a regression.
        assert mock_client.generate_content.call_count == 5, (
            f"expected 5 batches of 10, got {mock_client.generate_content.call_count} calls"
        )

        # Every batch prompt carries an explicit per-batch count, and the counts
        # sum to what the caller asked for.
        requested_per_batch = []
        for call in mock_client.generate_content.call_args_list:
            batch_prompt = call[0][0]
            match = re.search(r"Generate exactly (\d+) test cases", batch_prompt)
            assert match, f"batch prompt missing an explicit count: {batch_prompt[:200]}"
            requested_per_batch.append(int(match.group(1)))

        assert sum(requested_per_batch) == 50, (
            f"batch counts {requested_per_batch} do not sum to the requested 50"
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_dynamic_dataset_generation())
    print("Test passed!")
