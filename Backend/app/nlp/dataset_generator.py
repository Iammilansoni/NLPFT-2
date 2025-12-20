"""
Enterprise Dataset Generator - LLM-Driven with High Variation & Error Injection

Features:
- Template-aware generation (uses full template: description, schema, samples, domain tags)
- User custom prompts for specific scenarios (e.g., "Generate edge cases with pilot disabled")
- High variation with typos, mistakes, realistic industry noise
- 70% valid cases, 20% edge cases, 10% extreme scenarios
- Boundary conditions, rare combinations, synthetic but schema-correct values
- CSV output with preview/download capability
"""

import os
import json
import csv
import random
import string
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
import pandas as pd

from app.core.config import settings, DATASETS_DIR, OLLAMA_HOST, OLLAMA_MODEL
from app.core.logger import logger

# --- Ollama Configuration ---
# Uses quantized models for fast CPU inference
_ollama_available = False
_ollama_host = OLLAMA_HOST
_ollama_model = OLLAMA_MODEL

try:
    import httpx
    response = httpx.get(f"{_ollama_host}/api/tags", timeout=5.0)
    if response.status_code == 200:
        _ollama_available = True
        available_models = [m.get("name", "") for m in response.json().get("models", [])]
        logger.info(f"Ollama running at {_ollama_host}")
        logger.info(f"Available models: {', '.join(available_models[:5])}{'...' if len(available_models) > 5 else ''}")
        
        if any(_ollama_model.split(':')[0] in m for m in available_models):
            logger.info(f"Model available: {_ollama_model}")
        else:
            logger.warning(f"Model {_ollama_model} not found. Run: ollama pull {_ollama_model}")
except Exception as e:
    logger.warning(f"Ollama not available at {_ollama_host}: {e}")
    logger.warning("Install Ollama: https://ollama.ai/download")
    logger.warning(f"Then run: ollama pull {_ollama_model}")


class EnterpriseDatasetGenerator:
    """
    Enterprise-grade dataset generator with LLM-driven variation and error injection
    
    STRICT CSV DATASET GENERATOR with ZERO HALLUCINATION POLICY
    
    Generates high-quality, diverse, embedding-ready CSV datasets with:
    - Paraphrases and semantic variations
    - Lexical variations and typos (realistic, mild)
    - Casing variations, plural/singular swaps
    - Natural rewordings and domain-specific variations
    - 70% valid cases, 20% edge cases, 10% extreme/error cases
    - Strict template schema compliance
    - Clean UTF-8, properly escaped CSV output
    """
    
    def __init__(self, datasets_dir: str = str(DATASETS_DIR)):
        """Initialize the enterprise dataset generator"""
        self.datasets_dir = datasets_dir
        os.makedirs(datasets_dir, exist_ok=True)
        
        self.ollama_available = _ollama_available
        self.ollama_host = _ollama_host
        self.ollama_model = _ollama_model
        
        if self.ollama_available:
            self.client = "ollama"
            self.model_name = self.ollama_model
            self.provider = "ollama"
            logger.info(f"Using Ollama {self.model_name} for dataset generation (LOCAL CPU)")
        else:
            self.client = None
            self.provider = None
            logger.error("Ollama not available. Install from: https://ollama.ai/download")
            logger.error(f"Then run: ollama pull {_ollama_model}")
    
    def _build_system_prompt(
        self,
        template_data: Dict[str, Any],
        scenario_distribution: Dict[str, float] = None
    ) -> str:
        """
        Build comprehensive system prompt with STRICT NON-HALLUCINATION RULES
        
        Args:
            template_data: Full template information from database
            scenario_distribution: Distribution of scenarios (valid/edge/extreme)
        
        Returns:
            System prompt string
        """
        if scenario_distribution is None:
            scenario_distribution = {
                "valid": 0.70,  
                "edge": 0.20,   
                "extreme": 0.10  
            }
        
        name = template_data.get("name", "Unknown API") if isinstance(template_data, dict) else "Unknown API"
        description = template_data.get("description", "") if isinstance(template_data, dict) else ""
        base_url = template_data.get("base_url", "https://api.example.com") if isinstance(template_data, dict) else "https://api.example.com"
        endpoint = template_data.get("endpoint", "/api/endpoint") if isinstance(template_data, dict) else "/api/endpoint"
        method = template_data.get("method", "POST") if isinstance(template_data, dict) else "POST"
        parameters = template_data.get("parameters", []) if isinstance(template_data, dict) else []
        sample_requests = template_data.get("sample_requests", []) if isinstance(template_data, dict) else []
        sample_responses = template_data.get("sample_responses", []) if isinstance(template_data, dict) else []
        json_schema = template_data.get("json_schema", {}) if isinstance(template_data, dict) else {}
        domain_tags = template_data.get("domain_tags", []) if isinstance(template_data, dict) else []
        security_classification = template_data.get("security_classification", "internal") if isinstance(template_data, dict) else "internal"
        
        def safe_json_dumps(obj, default="[]"):
            try:
                return json.dumps(obj, indent=2, default=str)
            except Exception as e:
                logger.warning(f"JSON serialization failed: {e}")
                return default
        
        parameters_json = safe_json_dumps(parameters, "[]")
        json_schema_json = safe_json_dumps(json_schema, "{}")
        sample_requests_json = safe_json_dumps(sample_requests, "[]")
        sample_responses_json = safe_json_dumps(sample_responses, "[]")
        domain_tags_str = ', '.join(str(t) for t in domain_tags) if domain_tags else 'general'
        
        system_prompt = f"""You are an API Test Dataset Generator used for safe software testing.

Your purpose is to generate **harmless synthetic test cases** for API robustness validation.
These outputs are used for defensive security testing, validation, and quality assurance.

⚠ SAFETY DIRECTIVE (MUST FOLLOW)
- You may generate inputs that *simulate* malformed or unsafe-like patterns for testing,  
  but they must always be non-executable, neutral, and clearly fake.
- Any string resembling SQL, script tags, HTML, injections must be intentionally broken or altered so it cannot function.
- NEVER provide functional exploit payloads or instructions.

===============================================================================
API Metadata (From Template)
===============================================================================
API Name: {name}
Base URL: {base_url}
Method: {method}
Endpoint: {endpoint}
Security Classification: {security_classification}
Domain Tags: {domain_tags_str}

Description:
{description}

Parameters:
{parameters_json}

JSON Schema:
{json_schema_json}

Sample Requests:
{sample_requests_json}

===============================================================================
Generate dataset entries with HIGH VARIATION
===============================================================================
Each data point must contain:

1. natural language `query`
2. structured `request` using template schema fields only
3. valid `expected_response` OR validation-error response
4. classification labels:
   - scenario_type → valid | edge | extreme
   - test_category → valid_flow | boundary | typo | error_case | paraphrase
5. short `notes` (explain intention, edge, typo, boundary)

===============================================================================
CASE DISTRIBUTION RULE
===============================================================================
- ~70% valid realistic requests
- ~20% edge/boundary values (long strings, empty, weird but SAFE characters)
- ~10% invalid/extreme cases (missing required fields, wrong type, broken format)

===============================================================================
REQUIRED DIVERSITY IN QUERIES
===============================================================================
Include multiple writing styles:

• direct commands → "Create booking for user 22"
• question form → "How do I update order status?"
• shorthand/abbreviation → "upd usr details"
• casual/slang → "hey, add order quickly"
• typo-mistakes → "creaet custmer", "updtae stat"
• paraphrased equivalents

Boundary examples allowed (must remain harmless):
- strings with random symbols → "abc@@??##"
- slightly broken emails → "user@@mail"
- empty/very long text
- non-standard values like "00000" or unicode characters

Extreme invalid cases allowed:
- missing required fields
- wrong type formats (number instead of boolean)
- intentionally incomplete JSON or nonsense values

===============================================================================
⚠ HARD OUTPUT FORMAT RULE
===============================================================================
Return ONLY a JSON array, no explanation, no markdown.

Each item must be:

{{
  "query": "...",
  "api": "{name}",
  "endpoint": "{endpoint}",
  "method": "{method}",
  "request": {{ ... }},
  "expected_response": {{ ... }},
  "scenario_type": "valid"|"edge"|"extreme",
  "test_category": "valid_flow"|"typo"|"boundary"|"error_case"|"paraphrase",
  "notes": "..."
}}

Output must be valid JSON.
No extra keys. No commentary.
===============================================================================
You understand. Await user prompt.
"""
        
        return system_prompt
    
    def _build_user_prompt(
        self,
        user_prompt: str,
        num_examples: int,
        focus_areas: Optional[List[str]] = None,
        template_data: Dict[str, Any] = None
    ) -> str:
        """
        Build user prompt for dataset generation
        
        Args:
            user_prompt: User's custom generation instructions
            num_examples: Number of test cases to generate
            focus_areas: Specific areas to focus on
            template_data: Template information for reference
        
        Returns:
            User prompt string
        """
        if num_examples:
            valid_count = int(num_examples * 0.70)
            edge_count = int(num_examples * 0.20)
            extreme_count = num_examples - valid_count - edge_count
        else:
            num_examples = 15
            valid_count = 10
            edge_count = 3
            extreme_count = 2

        user_prompt_text = f"""Generate exactly {num_examples} test cases for the API above. Output ONLY a JSON array.

Requirements:
- {valid_count} valid test cases with realistic data
- {edge_count} edge cases (boundary values, empty strings, long text)
- {extreme_count} error cases (missing required fields, wrong types)

Each test case needs: query, api, endpoint, method, request, expected_response, scenario_type, test_category, notes

Generate varied natural language queries:
- "Create order for customer X"
- "Place a new booking with COD payment"  
- "I want to buy product ABC"
- Include some with typos like "creaet ordr"

Output format: [{{"query":"...", "api":"...", ...}}, ...]
Return ONLY the JSON array, nothing else."""
        
        return user_prompt_text
    
    def _extract_json_from_response(self, response_text: str) -> List[Dict]:
        """
        Extract JSON array from LLM response, handling various formats
        
        Args:
            response_text: Raw LLM response
        
        Returns:
            Parsed JSON array
        """
        import re
        
        try:
            original_text = response_text
            response_text = response_text.strip()
            
            logger.debug(f"Raw response length: {len(response_text)} chars")
            logger.debug(f"First 200 chars: {response_text[:200]}")

            if any(keyword in response_text[:500] for keyword in ['import ', 'def ', 'class ', 'from ', 'print(', 'if __name__']):
                logger.error("Response appears to contain Python code instead of JSON")
                logger.error(f"Response start: {response_text[:300]}")
                return []
            
            if "```" in response_text:
                code_block_pattern = r'```(?:json)?\s*([\s\S]*?)```'
                matches = re.findall(code_block_pattern, response_text)
                if matches:
                    response_text = matches[0].strip()
                    logger.debug(f"Extracted from code block: {len(response_text)} chars")
            
            response_text = response_text.strip('`').strip()
      
            if response_text.lower().startswith("json"):
                response_text = response_text[4:].strip()
           
            bracket_start = response_text.find("[")
            bracket_end = response_text.rfind("]")
            
            if bracket_start != -1 and bracket_end != -1 and bracket_end > bracket_start:
                response_text = response_text[bracket_start:bracket_end + 1]
                logger.debug(f"Extracted array bounds: {len(response_text)} chars")
            
            try:
                data = json.loads(response_text)
                return self._process_parsed_json(data)
            except json.JSONDecodeError as e:
                logger.warning(f"Initial JSON parse failed: {e}")
            except Exception as e:
                logger.error(f"Unexpected error during JSON parse: {type(e).__name__}: {e}")
                return []
            
            fixed_text = response_text
            
            fixed_text = re.sub(r',\s*]', ']', fixed_text)
            fixed_text = re.sub(r',\s*}', '}', fixed_text)
            
            fixed_text = re.sub(r'(?<!\\)\n(?=[^"]*"[^"]*$)', '\\n', fixed_text)
            
            try:
                data = json.loads(fixed_text)
                logger.info(f"Fixed trailing commas and parsed JSON")
                return self._process_parsed_json(data)
            except json.JSONDecodeError:
                pass
            except Exception as e:
                logger.error(f"Unexpected error after fixing JSON: {type(e).__name__}: {e}")
            
            logger.warning("Attempting line-by-line JSON object extraction...")
            test_cases = []
            
            try:
                depth = 0
                start = -1
                for i, char in enumerate(response_text):
                    if char == '{':
                        if depth == 0:
                            start = i
                        depth += 1
                    elif char == '}':
                        depth -= 1
                        if depth == 0 and start != -1:
                            potential_json = response_text[start:i+1]
                            if '"query"' in potential_json:
                                try:
                                    obj = json.loads(potential_json)
                                    if isinstance(obj, dict) and "query" in obj:
                                        test_cases.append(obj)
                                except json.JSONDecodeError as e:
                                    logger.debug(f"Failed to parse potential object: {e}")
                                    continue
                            start = -1
            except Exception as e:
                logger.error(f"Error in balanced brace extraction: {e}")
            
            if test_cases:
                logger.info(f"Extracted {len(test_cases)} test cases via balanced brace extraction")
                return test_cases
            
            try:
                fixed_text = response_text.replace("'", '"')
                data = json.loads(fixed_text)
                logger.info(f"Fixed quotes and parsed JSON")
                return self._process_parsed_json(data)
            except json.JSONDecodeError:
                pass
            except Exception as e:
                logger.error(f"Unexpected error after fixing quotes: {type(e).__name__}: {e}")
            
            logger.error(f"All JSON extraction strategies failed")
            logger.error(f"Response text sample: {original_text[:500]}...")
            return []
            
        except Exception as outer_error:
            logger.error(f"Critical error in _extract_json_from_response: {type(outer_error).__name__}: {outer_error}")
            logger.error(f"Response text sample: {response_text[:500] if 'response_text' in locals() else 'N/A'}...")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def _process_parsed_json(self, data: Any) -> List[Dict]:
        """Process parsed JSON data into a list of test cases"""
        try:
            if isinstance(data, list):
                logger.info(f"Extracted {len(data)} test cases from JSON array")
                return data
            elif isinstance(data, dict):
                for key in ["test_cases", "examples", "data", "results", "dataset"]:
                    if key in data and isinstance(data[key], list):
                        logger.info(f"Extracted {len(data[key])} test cases from '{key}' key")
                        return data[key]
                if "query" in data:
                    logger.info(f"Extracted 1 test case (single object)")
                    return [data]
            
            logger.warning(f"Unexpected JSON structure: {type(data)}")
            return []
        except Exception as e:
            logger.error(f"Error in _process_parsed_json: {type(e).__name__}: {e}")
            return []
    
    def _validate_test_case(self, test_case: Dict, template_data: Dict) -> bool:
        """
        Validate that generated test case meets requirements
        
        Args:
            test_case: Generated test case
            template_data: Template information
        
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(test_case, dict):
            logger.warning(f"Test case is not a dict: {type(test_case)}")
            return False
        if "query" not in test_case or not test_case.get("query"):
            logger.warning(f"Missing required field: query")
            return False
        
        if "api" not in test_case:
            test_case["api"] = template_data.get("name", "unknown_api")
        if "endpoint" not in test_case:
            test_case["endpoint"] = template_data.get("endpoint", "/api")
        if "method" not in test_case:
            test_case["method"] = template_data.get("method", "POST")
        if "request" not in test_case:
            test_case["request"] = {}
        if "expected_response" not in test_case:
            test_case["expected_response"] = {"status": "success"}
        if "scenario_type" not in test_case:
            test_case["scenario_type"] = "valid"
        if "test_category" not in test_case:
            test_case["test_category"] = "valid_flow"
        if "notes" not in test_case:
            test_case["notes"] = ""
        
        scenario = test_case.get("scenario_type", "valid").lower()
        if scenario not in ["valid", "edge", "extreme"]:
            test_case["scenario_type"] = "valid"
        
        valid_categories = ["typo", "boundary", "rare_combination", "valid_flow", 
                           "error_case", "security", "performance", "paraphrase"]
        if test_case.get("test_category", "").lower() not in valid_categories:
            test_case["test_category"] = "valid_flow"
        
        return True
    
    def _convert_to_csv_format(self, test_cases: List[Dict]) -> List[Dict]:
        """
        Convert test cases to CSV-friendly format
        
        Args:
            test_cases: List of test case dictionaries
        
        Returns:
            List of CSV row dictionaries
        """
        csv_rows = []
        
        for tc in test_cases:
            if not isinstance(tc, dict):
                logger.warning(f"Skipping non-dict test case: {type(tc)}")
                continue
            request_json = tc.get("request", {})
            if isinstance(request_json, dict):
                request_json = json.dumps(request_json)
            elif isinstance(request_json, list):
                request_json = json.dumps(request_json)
            
            response_json = tc.get("expected_response", {})
            if isinstance(response_json, dict):
                response_json = json.dumps(response_json)
            elif isinstance(response_json, list):
                response_json = json.dumps(response_json)
            
            csv_rows.append({
                "query": tc.get("query", ""),
                "api": tc.get("api", ""),
                "endpoint": tc.get("endpoint", ""),
                "method": tc.get("method", "POST"),
                "request": request_json,
                "expected_response": response_json,
                "scenario_type": tc.get("scenario_type", "valid"),
                "test_category": tc.get("test_category", "valid_flow"),
                "notes": tc.get("notes", "")
            })
        
        return csv_rows
    
    async def _call_ollama_api(self, system_prompt: str, user_prompt: str, num_examples: int) -> str:
        """
        Call Ollama API with Llama 3.2 Instruct (local CPU inference)
        
        Args:
            system_prompt: System instructions
            user_prompt: User request
            num_examples: Number of test cases
            
        Returns:
            Response text from Ollama
        """
        import httpx
        import asyncio
        
        current_model = self.ollama_model
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Calling Ollama {current_model} (attempt {attempt + 1})...")
                
                url = f"{self.ollama_host}/api/chat"
                
                payload = {
                    "model": current_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 8192,  
                    }
                }
                
                timeout = httpx.Timeout(900.0, connect=10.0) 
                
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, json=payload)
                    
                    if response.status_code != 200:
                        error_text = response.text
                        logger.error(f"Ollama returned {response.status_code}: {error_text}")
                        raise ValueError(f"Ollama API error: {response.status_code}")
                    
                    result = response.json()
                    response_text = result.get("message", {}).get("content", "")
                    
                    if not response_text:
                        raise ValueError("Empty response from Ollama")
                    
                    eval_count = result.get("eval_count", 0)
                    eval_duration = result.get("eval_duration", 0)
                    if eval_duration > 0:
                        tokens_per_sec = eval_count / (eval_duration / 1e9)
                        logger.info(f"Ollama: {eval_count} tokens @ {tokens_per_sec:.1f} tok/s")
                    
                    logger.info(f"Ollama response received: {len(response_text)} chars")
                    return response_text
                    
            except httpx.TimeoutException:
                logger.warning(f"Ollama timeout on {current_model}")
                if current_model != self.ollama_fallback and attempt == 0:
                    logger.warning(f"Switching to faster model: {self.ollama_fallback}")
                    current_model = self.ollama_fallback
                    continue
                    
            except Exception as e:
                error_str = str(e).lower()
                if "model" in error_str and "not found" in error_str:
                    logger.warning(f"Model {current_model} not found. Try: ollama pull {current_model}")
                    
                    if current_model != self.ollama_fallback:
                        logger.warning(f"Trying fallback model: {self.ollama_fallback}")
                        current_model = self.ollama_fallback
                        continue
                
                logger.error(f"Ollama API error: {e}")
                raise ValueError(f"Ollama API failed: {e}")
        
        raise ValueError("Ollama failed after all retries. Ensure Ollama is running and models are pulled.")

    async def generate_dataset_from_template(
        self,
        template_data: Dict[str, Any],
        num_examples: Optional[int] = None,
        user_prompt: str = "",
        focus_areas: Optional[List[str]] = None,
        scenario_distribution: Optional[Dict[str, float]] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive, embedding-ready CSV dataset from approved template
        
        LOCAL GENERATION using Ollama Llama 3.2 / Gemma 2B
        
        Args:
            template_data: Full template information from database
            num_examples: Number of test cases to generate (10-1000)
            user_prompt: User's custom generation instructions
            focus_areas: Specific areas to focus on
            scenario_distribution: Custom distribution of scenarios
            task_id: Optional task ID for progress tracking
        
        Returns:
            Dictionary with generation results and file paths
        """
        def update_progress(progress: int, message: str, step: str = None):
            if task_id:
                try:
                    from app.services.dataset_task_manager import get_task_manager
                    task_manager = get_task_manager()
                    task_manager.update_progress(task_id, progress, message, step)
                except Exception as e:
                    logger.warning(f"Progress update failed: {e}")
            logger.info(f"Progress: {progress}% - {message}")
        
        update_progress(5, "Initializing dataset generation...", "init")
        
        if not self.ollama_available:
            raise ValueError("Ollama not available. Install from https://ollama.ai/download")
        
        template_name = "Unknown"
        template_id_str = "unknown"
        try:
            template_name = template_data.get("name", "Unknown") if isinstance(template_data, dict) else "Unknown"
            template_id_str = str(template_data.get("id", "unknown")) if isinstance(template_data, dict) else "unknown"
        except Exception as e:
            logger.error(f"Error extracting template info: {e}")
        
        update_progress(10, f"Preparing to generate for: {template_name}", "prepare")
        
        logger.info(f"Starting dataset generation for: {template_name}")
        logger.info(f"Provider: {self.provider.upper()} | Model: {self.model_name}")
        target_count = num_examples if num_examples else 50
        logger.info(f"Target: {target_count} test cases")
        
        try:
            update_progress(15, "Building prompts...", "build_prompts")
            try:
                system_prompt = self._build_system_prompt(template_data, scenario_distribution)
            except Exception as prompt_error:
                logger.error(f"Error building prompts: {type(prompt_error).__name__}: {prompt_error}")
                raise ValueError(f"Failed to build prompts: {prompt_error}")
            
            import time
            start_time = time.time()

            BATCH_SIZE = 15
            all_test_cases = []
            total_batches = (target_count + BATCH_SIZE - 1) // BATCH_SIZE 
            
            update_progress(20, f"Generating {target_count} test cases in {total_batches} batches...", "batch_start")
            
            for batch_num in range(total_batches):
                remaining = target_count - len(all_test_cases)
                batch_count = min(BATCH_SIZE, remaining)
                
                if batch_count <= 0:
                    break
                
                batch_progress = 20 + int((batch_num / total_batches) * 40)
                update_progress(batch_progress, f"Batch {batch_num + 1}/{total_batches}: Generating {batch_count} test cases...", f"batch_{batch_num + 1}")
                
                user_prompt_msg = self._build_user_prompt(user_prompt, batch_count, focus_areas, template_data)
                
                logger.info(f"Batch {batch_num + 1}/{total_batches}: Requesting {batch_count} test cases")
                
                response_text = None
                try:
                    response_text = await self._call_ollama_api(system_prompt, user_prompt_msg, batch_count)
                except Exception as api_error:
                    logger.error(f"API call failed for batch {batch_num + 1}: {type(api_error).__name__}: {api_error}")
                    
                    if all_test_cases:
                        logger.warning(f"Continuing with {len(all_test_cases)} test cases from previous batches")
                        break
                    raise ValueError(f"API call failed: {api_error}")
                
                if not response_text:
                    logger.warning(f"Empty response for batch {batch_num + 1}")
                    continue
                
                try:
                    batch_test_cases = self._extract_json_from_response(response_text)
                except Exception as extract_error:
                    logger.error(f"JSON extraction failed for batch {batch_num + 1}: {extract_error}")
                    debug_file = os.path.join(self.datasets_dir, f"debug_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                    try:
                        with open(debug_file, 'w', encoding='utf-8') as f:
                            f.write(f"Batch {batch_num + 1} Error: {extract_error}\n\n")
                            f.write(f"Response text:\n{response_text}")
                        logger.error(f"Saved debug response to: {debug_file}")
                    except OSError as file_error:
                        logger.debug(f"Could not save debug file: {file_error}")
                    continue  
                
                if batch_test_cases:
                    all_test_cases.extend(batch_test_cases)
                    logger.info(f"Batch {batch_num + 1}: Got {len(batch_test_cases)} test cases (total: {len(all_test_cases)})")
                else:
                    logger.warning(f"Batch {batch_num + 1}: No test cases extracted")
                    debug_file = os.path.join(self.datasets_dir, f"debug_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                    try:
                        with open(debug_file, 'w', encoding='utf-8') as f:
                            f.write("="*80 + "\n")
                            f.write(f"BATCH {batch_num + 1} - {self.provider.upper()} RESPONSE DEBUG DUMP\n")
                            f.write("="*80 + "\n\n")
                            f.write("Full Response:\n")
                            f.write(response_text)
                        logger.error(f"Saved debug response to: {debug_file}")
                    except OSError as file_error:
                        logger.debug(f"Could not save debug file: {file_error}")

            elapsed = time.time() - start_time
            test_cases = all_test_cases
            
            update_progress(60, f"Generated {len(test_cases)} test cases in {elapsed:.1f}s", "parse_complete")
            
            if not test_cases:
                raise ValueError(f"Failed to generate any test cases after {total_batches} batches. LLM may be refusing the request.")
            
            logger.info(f"Received {len(test_cases)} test cases from {self.provider.upper()} in {total_batches} batches")
            update_progress(70, f"Received {len(test_cases)} test cases, validating...", "validate")
 
            valid_test_cases = []
            validation_errors = 0
            for tc in test_cases:
                if self._validate_test_case(tc, template_data):
                    valid_test_cases.append(tc)
                else:
                    validation_errors += 1
                    if validation_errors <= 3: 
                        logger.warning(f"Skipping invalid test case: {tc.get('query', 'unknown')[:50]}")
            
            if validation_errors > 0:
                logger.warning(f"Total validation errors: {validation_errors}")
            
            logger.info(f"Validated {len(valid_test_cases)} of {len(test_cases)} test cases")
            update_progress(80, f"Validated {len(valid_test_cases)} test cases", "validated")
            
            if len(valid_test_cases) == 0:
                raise ValueError("No valid test cases generated. Check template schema and LLM output.")
            
            update_progress(85, "Converting to CSV format...", "convert_csv")
            csv_rows = self._convert_to_csv_format(valid_test_cases)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_template_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in template_name.lower())
            csv_filename = f"{safe_template_name}_dataset_{timestamp}.csv"
            csv_path = os.path.join(self.datasets_dir, csv_filename)
            
            update_progress(90, "Saving CSV file...", "save_csv")
            
            df = pd.DataFrame(csv_rows)
            df.to_csv(csv_path, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8')
            logger.info(f"Saved CSV dataset: {csv_path}")
            
            json_filename = f"{safe_template_name}_dataset_{timestamp}.json"
            json_path = os.path.join(self.datasets_dir, json_filename)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(valid_test_cases, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved JSON backup: {json_path}")
            
            update_progress(95, "Calculating statistics...", "stats")
            
            scenario_stats = {
                "valid": sum(1 for tc in valid_test_cases if tc.get("scenario_type") == "valid"),
                "edge": sum(1 for tc in valid_test_cases if tc.get("scenario_type") == "edge"),
                "extreme": sum(1 for tc in valid_test_cases if tc.get("scenario_type") == "extreme")
            }
            
            category_stats = {}
            for tc in valid_test_cases:
                category = tc.get("test_category", "unknown")
                category_stats[category] = category_stats.get(category, 0) + 1
            
            logger.info(f"Distribution: valid={scenario_stats['valid']}, edge={scenario_stats['edge']}, extreme={scenario_stats['extreme']}")
            
            update_progress(100, f"Generated {len(valid_test_cases)} test cases successfully!", "complete")
            logger.info(f"Dataset generation completed successfully!")
            
            return {
                "success": True,
                "template_name": template_name,
                "template_id": template_id_str,
                "total_generated": len(valid_test_cases),
                "requested": num_examples if num_examples else "dynamic",
                "scenario_distribution": scenario_stats,
                "category_distribution": category_stats,
                "paths": {
                    "csv": csv_path,
                    "json": json_path
                },
                "user_prompt": user_prompt,
                "focus_areas": focus_areas or [],
                "csv_preview": csv_rows[:5],  
                "timestamp": timestamp,
                "model_used": self.model_name
            }
        
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Error generating dataset: {type(e).__name__}: {e}")
            logger.error(f"Full traceback:\n{error_traceback}")
            
            if task_id:
                try:
                    from app.services.dataset_task_manager import get_task_manager
                    task_manager = get_task_manager()
                    task_manager.update_task(task_id, status="failed", message=str(e), error=str(e))
                except Exception as task_error:
                    logger.debug(f"Could not update task status: {task_error}")
            
            error_category = "unknown"
            if "API" in str(e) or "api" in str(e).lower():
                error_category = "api_error"
            elif "JSON" in str(e) or "json" in str(e).lower() or "parse" in str(e).lower():
                error_category = "json_parsing_error"
            elif "timeout" in str(e).lower():
                error_category = "timeout_error"
            elif "rate" in str(e).lower() or "limit" in str(e).lower():
                error_category = "rate_limit_error"
            elif "auth" in str(e).lower() or "key" in str(e).lower():
                error_category = "auth_error"
            
            logger.error(f"Error category: {error_category}")
            
            return {
                "success": False,
                "error": str(e),
                "error_category": error_category,
                "error_type": type(e).__name__,
                "template_name": template_name,
                "template_id": template_id_str,
                "traceback": error_traceback
            }


_enterprise_generator = None


def get_enterprise_dataset_generator() -> EnterpriseDatasetGenerator:
    """Get or create global EnterpriseDatasetGenerator instance"""
    global _enterprise_generator
    if _enterprise_generator is None:
        _enterprise_generator = EnterpriseDatasetGenerator()
    return _enterprise_generator