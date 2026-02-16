import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add Backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.nlp.dataset_generator import EnterpriseDatasetGenerator

@pytest.mark.asyncio
async def test_dynamic_dataset_generation():
    # Mock Gemini response (dataset_generator uses Gemini for fallback inference)
    with patch('app.nlp.dataset_generator._gemini_client') as mock_client:
        # Setup mock response
        mock_response = MagicMock()
        mock_response.text = """
        [
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
        ]
        """
        mock_client.models.generate_content.return_value = mock_response
        
        generator = EnterpriseDatasetGenerator()
        generator.client = mock_client # Ensure client is set
        
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
        
        # Test with num_examples=None
        result = await generator.generate_dataset_from_template(
            template_data=template_data,
            num_examples=None,
            user_prompt="Generate some test cases"
        )
        
        assert result["success"] is True
        assert result["requested"] == "dynamic"
        
        # Verify prompt contains dynamic instructions
        call_args = mock_client.models.generate_content.call_args
        assert call_args is not None
        prompt = call_args[1]['contents']
        assert "DETERMINE THE NUMBER OF TEST CASES" in prompt
        assert "DEFAULT TO 100 TEST CASES" in prompt
        
        # Test with num_examples=50
        result_fixed = await generator.generate_dataset_from_template(
            template_data=template_data,
            num_examples=50,
            user_prompt="Generate 50 cases"
        )
        
        assert result_fixed["success"] is True
        assert result_fixed["requested"] == 50
        
        # Verify prompt contains fixed count instructions
        call_args_fixed = mock_client.models.generate_content.call_args
        prompt_fixed = call_args_fixed[1]['contents']
        assert "Generate EXACTLY **50**" in prompt_fixed

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_dynamic_dataset_generation())
    print("Test passed!")
