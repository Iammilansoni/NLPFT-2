"""
Dataset Generator - Generate and expand datasets using Gemini API
Handles intelligent dataset creation with edge cases and variations
Dynamically loads templates from template service
"""

import os
import json
import csv
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import google.generativeai as genai
from app.core.config import settings, GEMINI_API_KEY, DATASETS_DIR
from app.core.logger import logger
from app.services.template_service import get_template_service


# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Gemini API configured")
else:
    logger.warning("Gemini API key not found. Dataset generation will be limited.")


class DatasetGenerator:
    """
    Generate smart datasets for API testing with variations and edge cases
    Dynamically loads API templates from template service
    """
    
    def __init__(self, datasets_dir: str = str(DATASETS_DIR)):
        """
        Initialize the dataset generator
        
        Args:
            datasets_dir: Directory to store generated datasets
        """
        self.datasets_dir = datasets_dir
        os.makedirs(datasets_dir, exist_ok=True)
        
        # Initialize Gemini model
        if GEMINI_API_KEY:
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
        
        # Load templates from service
        self.templates = self._load_templates()
        logger.info(f"Loaded {len(self.templates)} API templates for dataset generation")
    
    def _load_templates(self) -> Dict:
        """
        Load API templates dynamically from template service
        
        Returns:
            Dictionary of templates
        """
        try:
            template_service = get_template_service()
            templates = template_service.get_all_templates()
            
            if not templates:
                logger.warning("No templates loaded, dataset generation may fail")
            
            return templates
            
        except Exception as e:
            logger.error(f"Error loading templates: {e}")
            return {}
    
    def get_template(self, intent: str) -> Dict:
        """
        Get template for specific intent
        
        Args:
            intent: API intent name
            
        Returns:
            Template dictionary or empty dict if not found
        """
        template = self.templates.get(intent, {})
        if not template:
            logger.warning(f"Template not found for intent: {intent}")
        return template
    
    def reload_templates(self):
        """
        Reload templates from template service (hot reload)
        """
        logger.info("Reloading API templates...")
        self.templates = self._load_templates()
        logger.info(f"Reloaded {len(self.templates)} API templates")
    
    def generate_base_examples(self, intent: str, num_examples: int = 10) -> List[Dict]:
        """
        Generate base examples without LLM
        
        Args:
            intent: API intent
            num_examples: Number of examples to generate
            
        Returns:
            List of example dictionaries
        """
        template = self.get_template(intent)
        if not template:
            logger.error(f"Cannot generate examples for unknown intent: {intent}")
            return []
        
        # Extract fields from template
        fields = []
        for param in template.get("parameters", []):
            if param.get("required", False):
                fields.append(param["name"])
        
        # Get example queries from template
        example_queries = template.get("example_queries", [])
        
        examples = []
        
        # If we have example queries from template, use them
        if example_queries:
            queries = example_queries[:num_examples]
        else:
            # Fallback: generate basic query
            field_placeholders = " and ".join([f"{{{f}}}" for f in fields])
            queries = [f"Test query for {intent} with {field_placeholders}"]
        
        # Generate variations
        test_data = {
            "username": ["milan", "john_doe", "test_user", "admin", "user123"],
            "password": ["MS3ESD", "Pass@123", "SecureP@ss", "Test1234!", "MyP@ssw0rd"],
            "email": ["milan@example.com", "john@test.com", "user@domain.com", "admin@company.com", "test@email.com"],
            "name": ["Milan", "John Doe", "Test User", "Admin User", "Sample Name"],
            "phone": ["+1234567890", "9876543210", "+44-1234-567890", "555-0123", "+91-9876543210"],
            "confirm": ["yes", "true", "1", "confirm", "YES"]
        }
        
        for i in range(num_examples):
            # Pick a query template
            query_template = queries[i % len(queries)]
            
            # Fill in fields
            query = query_template
            slots = {}
            
            for field in fields:
                if field in test_data:
                    value = test_data[field][i % len(test_data[field])]
                    query = query.replace(f"{{{field}}}", value)
                    slots[field] = value
            
            examples.append({
                "query": query,
                "intent": intent,
                "slots": slots,
                "api_name": intent,
                "endpoint": template.get("endpoint", f"/api/{intent}"),
                "method": template.get("method", "POST")
            })
        
        return examples
    
    def expand_with_gemini(self, intent: str, base_examples: List[Dict], target_count: int = 50) -> List[Dict]:
        """
        Expand dataset using Gemini API
        
        Args:
            intent: API intent
            base_examples: Base examples to expand from
            target_count: Target number of examples
            
        Returns:
            Expanded list of examples
        """
        if not self.model:
            logger.warning("Gemini not available. Returning base examples only.")
            return base_examples
        
        template = self.get_template(intent)
        if not template:
            logger.error(f"Cannot expand examples for unknown intent: {intent}")
            return base_examples
        
        # Extract fields from template
        fields = []
        for param in template.get("parameters", []):
            if param.get("required", False):
                fields.append(param["name"])
        
        description = template.get("description", "")
        
        # Create prompt for Gemini
        prompt = f"""
You are an expert at generating test data for API testing.

API Intent: {intent}
Description: {description}
Required Fields: {', '.join(fields)}

Here are some example queries:
{json.dumps([ex['query'] for ex in base_examples[:3]], indent=2)}

Generate {target_count - len(base_examples)} MORE varied, realistic queries for this API.
Include:
- Different phrasings and natural language variations
- Edge cases (special characters, long inputs, empty fields)
- Negative test cases
- Common user mistakes
- Different tones (formal, casual, urgent)

For each query, extract the field values and return in this EXACT JSON format:
{{
  "query": "the natural language query",
  "slots": {{
    {', '.join([f'"{field}": "value"' for field in fields])}
  }}
}}

Return ONLY a JSON array of objects, no additional text.
"""
        
        try:
            logger.info(f"Generating {target_count - len(base_examples)} examples with Gemini...")
            response = self.model.generate_content(prompt)
            
            # Parse response
            response_text = response.text.strip()
            
            # Extract JSON array
            if response_text.startswith("```"):
                # Remove markdown code blocks
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            response_text = response_text.strip()
            
            # Parse JSON
            generated = json.loads(response_text)
            
            # Add intent and metadata
            for item in generated:
                item["intent"] = intent
                item["api_name"] = intent
                item["endpoint"] = template.get("endpoint", f"/api/{intent}")
                item["method"] = template.get("method", "POST")
            
            logger.info(f"Generated {len(generated)} examples with Gemini")
            
            # Combine with base examples
            all_examples = base_examples + generated
            return all_examples[:target_count]
            
        except Exception as e:
            logger.error(f"Error generating with Gemini: {e}")
            return base_examples
    
    def load_existing_dataset(self, intent: str) -> Optional[pd.DataFrame]:
        """
        Load existing dataset for an intent
        
        Args:
            intent: API intent
            
        Returns:
            DataFrame if exists, None otherwise
        """
        csv_path = os.path.join(self.datasets_dir, f"{intent}_dataset.csv")
        if os.path.exists(csv_path):
            logger.info(f"Loading existing dataset: {csv_path}")
            return pd.read_csv(csv_path)
        return None
    
    def save_dataset(self, examples: List[Dict], intent: str, format: str = "both") -> Dict[str, str]:
        """
        Save dataset to CSV and JSON
        
        Args:
            examples: List of examples
            intent: API intent
            format: Save format ("csv", "json", or "both")
            
        Returns:
            Dictionary with file paths
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create DataFrame
        df = pd.DataFrame(examples)
        
        # Convert slots to JSON string for CSV
        if 'slots' in df.columns:
            df['slots_json'] = df['slots'].apply(json.dumps)
        
        paths = {}
        
        # Save CSV
        if format in ["csv", "both"]:
            csv_filename = f"{intent}_dataset.csv"
            csv_path = os.path.join(self.datasets_dir, csv_filename)
            
            # If exists, merge with existing
            if os.path.exists(csv_path):
                existing_df = pd.read_csv(csv_path)
                df = pd.concat([existing_df, df], ignore_index=True)
                df = df.drop_duplicates(subset=['query'], keep='last')
                logger.info(f"Merged with existing dataset. Total rows: {len(df)}")
            
            df.to_csv(csv_path, index=False)
            paths["csv"] = csv_path
            logger.info(f"Saved CSV: {csv_path}")
        
        # Save JSON
        if format in ["json", "both"]:
            json_filename = f"{intent}_dataset_{timestamp}.json"
            json_path = os.path.join(self.datasets_dir, json_filename)
            
            with open(json_path, 'w') as f:
                json.dump(examples, f, indent=2)
            
            paths["json"] = json_path
            logger.info(f"Saved JSON: {json_path}")
        
        return paths
    
    def generate_dataset(
        self,
        intent: str,
        num_examples: int = 50,
        use_gemini: bool = True,
        merge_existing: bool = True
    ) -> Dict:
        """
        Generate complete dataset for an intent
        
        Args:
            intent: API intent
            num_examples: Number of examples to generate
            use_gemini: Whether to use Gemini for expansion
            merge_existing: Whether to merge with existing dataset
            
        Returns:
            Dictionary with generation results
        """
        logger.info(f"Generating dataset for intent: {intent}")
        
        # Check for existing dataset
        existing_df = None
        if merge_existing:
            existing_df = self.load_existing_dataset(intent)
        
        # Generate base examples
        base_count = min(num_examples // 5, 10)  # 20% base examples
        base_examples = self.generate_base_examples(intent, base_count)
        
        # Expand with Gemini if enabled
        if use_gemini and GEMINI_API_KEY:
            all_examples = self.expand_with_gemini(intent, base_examples, num_examples)
        else:
            # Generate more base examples if Gemini not available
            all_examples = self.generate_base_examples(intent, num_examples)
        
        # Save dataset
        paths = self.save_dataset(all_examples, intent, format="both")
        
        return {
            "intent": intent,
            "total_examples": len(all_examples),
            "base_examples": len(base_examples),
            "generated_examples": len(all_examples) - len(base_examples),
            "paths": paths,
            "merged_with_existing": existing_df is not None,
            "existing_count": len(existing_df) if existing_df is not None else 0
        }
    
    def generate_from_query(
        self,
        query: str,
        intent: str,
        slots: Dict,
        num_variations: int = 20
    ) -> Dict:
        """
        Generate dataset variations from a single query
        
        Args:
            query: Original query
            intent: Detected intent
            slots: Extracted slots
            num_variations: Number of variations to generate
            
        Returns:
            Dictionary with generation results
        """
        logger.info(f"Generating variations from query: {query}")
        
        # Get template for intent
        template = self.get_template(intent)
        endpoint = template.get("endpoint", f"/api/{intent}") if template else f"/api/{intent}"
        method = template.get("method", "POST") if template else "POST"
        
        # Create base example
        base_example = {
            "query": query,
            "intent": intent,
            "slots": slots,
            "api_name": intent,
            "endpoint": endpoint,
            "method": method
        }
        
        # Generate variations
        result = self.generate_dataset(
            intent=intent,
            num_examples=num_variations,
            use_gemini=True,
            merge_existing=True
        )
        
        return result


# Global instance
_generator = None


def get_dataset_generator() -> DatasetGenerator:
    """Get or create global DatasetGenerator instance"""
    global _generator
    if _generator is None:
        _generator = DatasetGenerator()
    return _generator
