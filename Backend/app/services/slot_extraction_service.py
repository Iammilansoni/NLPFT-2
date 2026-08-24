# Backend\app\services\slot_extraction_service.py

"""
Slot Extraction Service - Extract values from NL queries using Ollama LLM

Purpose:
This service extracts slot values from natural language queries and populates
the API request schema. It uses Ollama's LLM capability (not embeddings) to
understand the query and map values to schema fields.

Example:
    Query: "Authenticate me with credentials Milan and milan@393"
    Schema: {"username": {"type": "string"}, "password": {"type": "string"}}
    
    Output: {"username": "Milan", "password": "milan@393"}

Performance:
    - Uses llama3.2:3b (small, fast, ~2GB RAM)
    - CPU-optimized, no GPU required
    - ~500-800ms per extraction
"""

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.core.logger import logger


class SlotExtractionService:
    """
    Extract slot values from natural language queries using Ollama LLM.
    
    This service uses a lightweight LLM to parse user queries and extract
    values that match the API's request schema.
    """
    
    # Use the full model name that Ollama has
    DEFAULT_MODEL = "llama3.2:3b-instruct-q4_K_M"
    OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or self.DEFAULT_MODEL
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=60.0)  # Increased timeout
        return self._http_client
    
    async def check_model_available(self) -> bool:
        """Check if the extraction model is available in Ollama."""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                data = response.json()
                model_names = [m.get("name", "") for m in data.get("models", [])]
                return self.model_name in model_names
        except Exception as e:
            logger.warning(f"Could not check Ollama models: {e}")
        return False
    
    @staticmethod
    def extract_url_from_query(query: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract URL from a natural language query.
        
        Args:
            query: Natural language query that may contain a URL
            
        Returns:
            Tuple of (raw_url, normalized_url):
            - raw_url: The exact URL as found in the query (e.g., "www.example.com")
            - normalized_url: URL with https:// prefix (e.g., "https://www.example.com")
            
        Examples:
            "Go to www.Iammilansoni.com and login" -> ("www.Iammilansoni.com", "https://www.iammilansoni.com")
            "Login with my credentials" -> (None, None)
            "Visit https://api.example.com/v1" -> ("https://api.example.com/v1", "https://api.example.com/v1")
        """
        if not query:
            return None, None
        
        # Regex pattern to match URLs with or without protocol
        # Matches: https://example.com, http://example.com, www.example.com, example.com/path
        url_pattern = r'(?:https?://)?(?:www\.)?([a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)+)(?:[/\w\-._~:/?#\[\]@!$&\'()*+,;=%]*)?'
        
        match = re.search(url_pattern, query, re.IGNORECASE)
        
        if match:
            raw_url = match.group(0).strip()
            
            # Normalize: ensure https:// prefix
            if raw_url.startswith('http://') or raw_url.startswith('https://'):
                normalized_url = raw_url.lower()
            else:
                # Add https:// if no protocol
                normalized_url = f"https://{raw_url.lower()}"
            
            # Remove trailing punctuation that might have been captured
            for char in ['.', ',', '!', '?', ')', ']']:
                if normalized_url.endswith(char) and not raw_url.endswith(char):
                    normalized_url = normalized_url[:-1]
                if raw_url.endswith(char):
                    raw_url = raw_url[:-1]
            
            logger.debug(f"Extracted URL from query: raw='{raw_url}', normalized='{normalized_url}'")
            return raw_url, normalized_url
        
        logger.debug("No URL found in query")
        return None, None
    
    def _flatten_schema_for_prompt(self, schema: Dict[str, Any], prefix: str = "") -> List[str]:
        """Recursively flatten schema to simple field descriptions for LLM."""
        if not schema:
            return []
        
        fields = []
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        for field_name, field_def in properties.items():
            full_name = f"{prefix}{field_name}" if prefix else field_name
            
            if not isinstance(field_def, dict):
                fields.append(f'- "{full_name}": (any)')
                continue
            
            field_type = field_def.get("type", "string")
            description = field_def.get("description", "")
            is_required = field_name in required
            req_marker = "*" if is_required else ""
            
            # Handle nested objects
            if field_type == "object" and "properties" in field_def:
                fields.append(f'- "{full_name}"{req_marker}: object containing:')
                nested = self._flatten_schema_for_prompt(field_def, f"  {full_name}.")
                fields.extend(nested)
            # Handle arrays of objects
            elif field_type == "array" and field_def.get("items", {}).get("type") == "object":
                fields.append(f'- "{full_name}"{req_marker}: array of objects, each with:')
                nested = self._flatten_schema_for_prompt(field_def.get("items", {}), f"  {full_name}[].")
                fields.extend(nested)
            else:
                desc_part = f" ({description})" if description else ""
                fields.append(f'- "{full_name}"{req_marker}: {field_type}{desc_part}')
        
        return fields
    
    def _build_extraction_prompt(
        self, 
        query: str, 
        schema: Dict[str, Any],
        api_name: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> str:
        """Build the prompt for slot extraction."""
        schema_fields = self._flatten_schema_for_prompt(schema)
        schema_desc = "\n".join(schema_fields) if schema_fields else "No schema"
        
        prompt = f"""Extract data from this query into JSON for the {api_name or 'API'} endpoint.

Query: "{query}"

Expected fields (* = required):
{schema_desc}

RULES:
1. Extract ONLY values explicitly mentioned in the query
2. For nested objects, use proper JSON structure
3. For arrays, use [] syntax
4. Skip fields not mentioned in the query
5. Return ONLY valid JSON, no explanation

Example for order API:
Query: "Create order for customer C123 with product P456 quantity 2, pay by COD"
Output: {{"customer_id": "C123", "items": [{{"product_id": "P456", "quantity": 2}}], "payment": {{"method": "cod"}}}}

Now extract from the query above. JSON:"""
        
        return prompt
    
    async def extract_slots(
        self,
        query: str,
        request_schema: Dict[str, Any],
        api_name: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract slot values from a natural language query.
        """
        if not request_schema:
            logger.debug("No schema provided, returning empty extraction")
            return {}
        
        try:
            prompt = self._build_extraction_prompt(
                query=query,
                schema=request_schema,
                api_name=api_name,
                endpoint=endpoint
            )
            
            logger.debug(f"Slot extraction prompt: {prompt[:200]}...")
            
            client = await self._get_client()
            
            response = await client.post(
                f"{self.OLLAMA_URL}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent extraction
                        "num_predict": 512,  # More tokens for complex schemas
                    }
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return {}
            
            result = response.json()
            generated_text = result.get("response", "").strip()
            
            logger.debug(f"LLM response: {generated_text}")
            
            # Parse the JSON from the response
            extracted = self._parse_json_response(generated_text, request_schema)
            
            logger.info(f"Slot extraction complete: {len(extracted)} fields extracted: {list(extracted.keys())}")
            return extracted
            
        except Exception as e:
            logger.error(f"Slot extraction failed: {e}", exc_info=True)
            return {}
    
    def _parse_json_response(
        self, 
        response_text: str, 
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling common formatting issues."""
        if not response_text:
            return {}
        
        # Try to extract JSON from the response
        text = response_text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # Try to find JSON object in the response
        start_idx = text.find("{")
        end_idx = text.rfind("}") + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = text[start_idx:end_idx]
            try:
                parsed = json.loads(json_str)
                
                # Validate against schema - only keep fields that exist in schema
                properties = schema.get("properties", schema)
                validated = {}
                for key, value in parsed.items():
                    if key in properties and value is not None:
                        validated[key] = value
                
                return validated
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON: {e}")
                logger.debug(f"Raw response: {response_text}")
        
        return {}
    
    async def extract_slots_batch(
        self,
        queries: List[str],
        request_schema: Dict[str, Any],
        api_name: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract slots from multiple queries.
        
        Useful for batch processing or testing.
        """
        results = []
        for query in queries:
            extracted = await self.extract_slots(
                query=query,
                request_schema=request_schema,
                api_name=api_name,
                endpoint=endpoint
            )
            results.append(extracted)
        return results
    
    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None




_slot_service_instance: Optional[SlotExtractionService] = None


def get_slot_extraction_service() -> SlotExtractionService:
    """Get the singleton slot extraction service."""
    global _slot_service_instance
    if _slot_service_instance is None:
        _slot_service_instance = SlotExtractionService()
    return _slot_service_instance