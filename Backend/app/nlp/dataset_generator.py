"""
Dataset Generator - Generates synthetic datasets from prompts
Uses the SmartDatasetGenerator for actual generation
"""

from typing import Dict, Optional
from app.nlp.smart_dataset_generator import get_dataset_generator
from app.core.logger import logger


def generate_dataset_from_prompt(
    seed_prompt: str,
    num_examples: int = 50,
    api_name: str = "login",
    endpoint: str = "<base_url>/api/login"
) -> Dict:
    """
    Generate a dataset from a seed prompt
    
    Args:
        seed_prompt: Example query to base generation on
        num_examples: Number of examples to generate
        api_name: API name/intent
        endpoint: API endpoint
        
    Returns:
        Dictionary with generation results and file paths
    """
    try:
        logger.info(f"Generating dataset from prompt: {seed_prompt}")
        
        # Get dataset generator
        generator = get_dataset_generator()
        
        # Parse the seed prompt to extract intent
        from app.nlp.query_parser import parse_query
        parsed = parse_query(seed_prompt)
        intent = parsed.get("intent", api_name)
        slots = parsed.get("slots", {})
        
        logger.info(f"Detected intent: {intent}, slots: {slots}")
        
        # Generate dataset using the smart generator
        result = generator.generate_from_query(
            query=seed_prompt,
            intent=intent,
            slots=slots,
            num_variations=num_examples
        )
        
        return {
            "success": True,
            "intent": intent,
            "num_examples": result.get("total_examples", num_examples),
            "csv_path": result["paths"]["csv"],
            "json_path": result["paths"]["json"],
            "message": f"Generated {result.get('total_examples', num_examples)} examples for {intent}"
        }
        
    except Exception as e:
        logger.error(f"Error generating dataset: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to generate dataset: {str(e)}"
        }


def generate_dataset_for_intent(
    intent: str,
    num_examples: int = 100,
    use_gemini: bool = True
) -> Dict:
    """
    Generate a complete dataset for a specific intent
    
    Args:
        intent: API intent name
        num_examples: Number of examples to generate
        use_gemini: Whether to use Gemini for expansion
        
    Returns:
        Dictionary with generation results
    """
    try:
        logger.info(f"Generating dataset for intent: {intent}")
        
        # Get dataset generator
        generator = get_dataset_generator()
        
        # Generate dataset
        result = generator.generate_dataset(
            intent=intent,
            num_examples=num_examples,
            use_gemini=use_gemini,
            merge_existing=True
        )
        
        return {
            "success": True,
            "intent": intent,
            "num_examples": result.get("total_examples", num_examples),
            "csv_path": result["paths"]["csv"],
            "json_path": result["paths"]["json"],
            "message": f"Generated {result.get('total_examples', num_examples)} examples for {intent}"
        }
        
    except Exception as e:
        logger.error(f"Error generating dataset for intent: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to generate dataset: {str(e)}"
        }
