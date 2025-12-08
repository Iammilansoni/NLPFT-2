"""
Unit Tests for Dataset Generation Service
==========================================
Tests dataset generation logic and validation.
"""

import pytest
from app.services.dataset_service import validate_template_parameters


@pytest.mark.unit
class TestTemplateValidation:
    """Test template parameter validation."""
    
    def test_validate_required_parameters_present(self):
        """Test validation passes when all required parameters provided."""
        parameters = [
            {"name": "email", "is_required": True},
            {"name": "password", "is_required": True},
        ]
        values = {"email": "test@example.com", "password": "pass123"}
        
        # Should not raise exception
        validate_template_parameters(parameters, values)
    
    def test_validate_missing_required_parameter(self):
        """Test validation fails when required parameter missing."""
        parameters = [
            {"name": "email", "is_required": True},
            {"name": "password", "is_required": True},
        ]
        values = {"email": "test@example.com"}  # Missing password
        
        with pytest.raises(ValueError) as exc_info:
            validate_template_parameters(parameters, values)
        
        assert "required" in str(exc_info.value).lower()
        assert "password" in str(exc_info.value).lower()
    
    def test_validate_optional_parameter_missing(self):
        """Test validation passes when optional parameter missing."""
        parameters = [
            {"name": "email", "is_required": True},
            {"name": "name", "is_required": False},
        ]
        values = {"email": "test@example.com"}  # Optional name missing
        
        # Should not raise exception
        validate_template_parameters(parameters, values)
    
    def test_validate_extra_parameters_allowed(self):
        """Test validation allows extra parameters not in template."""
        parameters = [
            {"name": "email", "is_required": True},
        ]
        values = {
            "email": "test@example.com",
            "extra_field": "extra_value",
        }
        
        # Should not raise exception
        validate_template_parameters(parameters, values)
