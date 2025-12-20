"""
Dataset Service - Validation utilities for dataset generation
==============================================================
Provides validation functions for template parameters and generation settings.
Dataset generation is handled directly in the API endpoint (app/api/v1/datasets.py).
"""

from typing import Dict, List, Any

from app.core.logger import logger


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_template_parameters(parameters: List[Dict], values: Dict) -> None:
    """
    Validate that all required template parameters are provided.
    
    Args:
        parameters: List of parameter definitions from template
        values: Dictionary of provided values
        
    Raises:
        ValueError: If a required parameter is missing
    """
    for param in parameters:
        param_name = param.get("name", "")
        is_required = param.get("is_required", False)
        
        if is_required and param_name not in values:
            raise ValueError(f"Required parameter '{param_name}' is missing")


def validate_generation_parameters(parameters: Dict) -> Dict:
    """
    Validate and normalize generation parameters.
    
    Args:
        parameters: Raw generation parameters
        
    Returns:
        Validated and normalized parameters
    """
    validated = {
        "num_samples": min(max(int(parameters.get("num_samples", 50)), 5), 500),
        "user_prompt": str(parameters.get("user_prompt", "")),
        "focus_areas": parameters.get("focus_areas", []),
        "scenario_distribution": parameters.get("scenario_distribution", {
            "valid": 0.70,
            "edge": 0.20,
            "extreme": 0.10
        })
    }
    return validated
