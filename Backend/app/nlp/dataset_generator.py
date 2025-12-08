# Backend\app\nlp\dataset_generator.py

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

from app.core.config import settings, DATASETS_DIR, OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_FALLBACK_MODEL
from app.core.logger import logger

# ============= OLLAMA (LOCAL CPU INFERENCE) =============
# Uses quantized models for fast CPU inference
_ollama_available = False
_ollama_host = OLLAMA_HOST
_ollama_model = OLLAMA_MODEL
_ollama_fallback = OLLAMA_FALLBACK_MODEL

try:
    import httpx
    # Check if Ollama is running
    response = httpx.get(f"{_ollama_host}/api/tags", timeout=5.0)
    if response.status_code == 200:
        _ollama_available = True
        available_models = [m.get("name", "") for m in response.json().get("models", [])]
        logger.info(f"Ollama running at {_ollama_host}")
        logger.info(f"Available models: {', '.join(available_models[:5])}{'...' if len(available_models) > 5 else ''}")
        
        # Check if preferred models are available
        if any(_ollama_model.split(':')[0] in m for m in available_models):
            logger.info(f"Primary model available: {_ollama_model}")
        else:
            logger.warning(f"⚠ Primary model {_ollama_model} not found. Run: ollama pull {_ollama_model}")
        
        if any(_ollama_fallback.split(':')[0] in m for m in available_models):
            logger.info(f"Fallback model available: {_ollama_fallback}")
        else:
            logger.warning(f"⚠ Fallback model {_ollama_fallback} not found. Run: ollama pull {_ollama_fallback}")
except Exception as e:
    logger.warning(f"⚠ Ollama not available at {_ollama_host}: {e}")
    logger.warning("⚠ Install Ollama: https://ollama.ai/download")
    logger.warning(f"⚠ Then run: ollama pull {_ollama_model}")


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
    
    def _init_(self, datasets_dir: str = str(DATASETS_DIR)):
        """Initialize the enterprise dataset generator"""
        self.datasets_dir = datasets_dir
        os.makedirs(datasets_dir, exist_ok=True)
        
        # Initialize Ollama for local LLM inference
        self.ollama_available = _ollama_available
        self.ollama_host = _ollama_host
        self.ollama_model = _ollama_model  # Llama 3.2 Instruct (quantized)
        self.ollama_fallback = _ollama_fallback  # Gemma 2B (faster, lighter)
        
        # Set provider
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
                "valid": 0.70,  # 70% valid cases
                "edge": 0.20,   # 20% edge cases
                "extreme": 0.10  # 10% extreme scenarios
            }
        
        # Extract template information safely
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
        
        # Safely serialize JSON fields
        def safe_json_dumps(obj, default="[]"):
            try:
                return json.dumps(obj, indent=2, default=str)
            except Exception as e:
                logger.warning(f"⚠ JSON serialization failed: {e}")
                return default
        
        parameters_json = safe_json_dumps(parameters, "[]")
        json_schema_json = safe_json_dumps(json_schema, "{}")
        sample_requests_json = safe_json_dumps(sample_requests, "[]")
        sample_responses_json = safe_json_dumps(sample_responses, "[]")
        domain_tags_str = ', '.join(str(t) for t in domain_tags) if domain_tags else 'general'
        
        # Build comprehensive system prompt with STRICT RULES
        system_prompt = f"""You are an EXPERT DATASET GENERATOR creating HIGH-QUALITY, DIVERSE datasets for EMBEDDING MODELS.

# TEMPLATE (SOURCE OF TRUTH)
- *API*: {name} ({method} {endpoint})
- *Base URL*: {base_url}
- *Security*: {security_classification}
- *Tags*: {domain_tags_str}

## Description
{description}

## Schema & Examples
Parameters: {parameters_json}
JSON Schema: {json_schema_json}
Requests: {sample_requests_json}
Responses: {sample_responses_json}

# OBJECTIVE: EMBEDDING-OPTIMIZED DATASET

## 1. QUERY DIVERSITY (CRITICAL)
Generate queries with varied structures to train robust embeddings:
- *Linguistic (25%)*: Imperative ("Create user"), Interrogative ("How to create?"), Declarative ("I want to..."), Passive, Conditional.
- *Paraphrases (25%)*: Synonyms ("Register" vs "Sign up"), jargon, varying lengths (3-25+ words).
- *Typos/Errors (15%)*: Swaps ("craete"), missing chars ("userr"), phonetic ("receve"), keyboard slips.
- *Shorthand (10%)*: "usr", "pwd", "acct", "cust", acronyms.
- *Contextual (15%)*: "getting error when...", "for Q4 project...", "urgent request".
- *Multi-intent (10%)*: "Create user then update", "List or create".

## 2. SCENARIO DISTRIBUTION
- *70% VALID*: Normal, schema-compliant.
- *20% EDGE*: Boundary values, special chars, min/max.
- *10% EXTREME*: Stress tests, malformed inputs.

## 3. OPTIMIZATION RULES
- *Length Variance*: Mix ultra-short (2-4 words) to very long (26+ words).
- *Style Mix*: Questions, Commands, Statements, Conversational ("hey can u"), Keywords ("user create").
- *Negative Examples*: Include 10% queries that sound similar but match different intents (contrastive learning).

## 4. STRICT CONSTRAINTS
- *ZERO HALLUCINATION*: Use ONLY template data. No invented fields/logic.
- *SEMANTIC CONSISTENCY: Even when generating typos or variations, the *intent of the query must match the API's function. Do not generate queries for unrelated actions (e.g., do not ask to 'create user' if the API is 'create order').
- *VALID JSON*: All request/response fields must be valid JSON.
- *REALISTIC DATA*: No placeholders like "test123". Use domain-appropriate values.
- *NO MARKDOWN*: Output raw JSON array only.

# Security: {security_classification.upper()} (Use synthetic, realistic values)
"""
        
        return system_prompt
    
    def _build_user_prompt(
        self,
        user_prompt: str,
        num_examples: int,
        focus_areas: Optional[List[str]] = None
    ) -> str:
        """
        Build user prompt for STRICT CSV dataset generation
        
        Args:
            user_prompt: User's custom generation instructions
            num_examples: Number of test cases to generate
            focus_areas: Specific areas to focus on
        
        Returns:
            User prompt string
        """
        focus_text = ""
        if focus_areas:
            focus_text = f"\n\n*FOCUS AREAS*: Pay special attention to: {', '.join(focus_areas)}"
        
        # Calculate distribution if num_examples is provided
        distribution_text = ""
        count_instruction = ""
        
        if num_examples:
            valid_count = int(num_examples * 0.70)
            edge_count = int(num_examples * 0.20)
            extreme_count = num_examples - valid_count - edge_count
            
            count_instruction = f"Generate EXACTLY *{num_examples}* high-quality, diverse test cases following ALL system prompt rules."
            distribution_text = f"""## STRICT DISTRIBUTION (Must Match Exactly)
- *{valid_count} VALID cases* (70%): Schema-compliant, realistic values, normal operation
- *{edge_count} EDGE cases* (20%): Boundary conditions, special chars, min/max values
- *{extreme_count} EXTREME cases* (10%): Error-inducing, stress tests, rare conditions"""
        else:
            count_instruction = """*DETERMINE THE NUMBER OF TEST CASES FROM THE USER'S CUSTOM REQUIREMENTS.*
- If the user specifies a number (e.g., "generate 50 cases"), use that number.
- If the user DOES NOT specify a number, *DEFAULT TO 100 TEST CASES*.
- Do not generate more than 1000 cases."""
            distribution_text = """## DISTRIBUTION GUIDELINES
- Maintain roughly: 70% VALID, 20% EDGE, 10% EXTREME cases
- Ensure diversity across all categories."""

        user_prompt_text = f"""# 🎯 GENERATION REQUEST

{count_instruction}

## Requirements
{user_prompt}
{focus_text}
{distribution_text}

## DIVERSITY CHECKLIST (MANDATORY)
1. *Variations*: Typos (15%), Abbreviations (10%), Questions (15%), Commands (20%), Statements (15%), Conversational (10%), Keywords (5%).
2. *Lengths*: Mix Short (3-5 words), Medium (6-12), Long (13+).
3. *Typos*: Transposition ("teh"), Omission ("creat"), Insertion ("userr"), Substitution ("vreate"). MUST PRESERVE INTENT (e.g., "creat order" is OK, "create user" is NOT OK if API is order).

## OUTPUT FORMAT (JSON ARRAY ONLY)
[
  {{
    "query": "Description (Vary length 3-30 words, include typos/variations)",
    "api": "api_name",
    "endpoint": "/path",
    "method": "METHOD",
    "request": {{...}},
    "expected_response": {{...}},
    "scenario_type": "valid|edge|extreme",
    "test_category": "typo|paraphrase|abbreviation|question|command|statement|conversational|keyword|boundary|error_case",
    "query_style": "imperative|interrogative|declarative|conversational|keyword_only",
    "has_typo": true|false,
    "notes": "Purpose"
  }}
]

## RULES
1. *JSON ONLY*: No markdown, no backticks. Start with [, end with ].
2. *UNIQUE*: No duplicate queries or structures.
3. *VALID*: Valid JSON objects for request/response.
4. *SCHEMA*: Follow template exactly.
5. *INTENT*: Queries must match the API function.

*START GENERATION - RETURN JSON ARRAY*
"""
        
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
            
            # Safety check: If response looks like it contains Python code, reject it
            if any(keyword in response_text[:500] for keyword in ['import ', 'def ', 'class ', 'from ', 'print(', 'if _name_']):
                logger.error("Response appears to contain Python code instead of JSON")
                logger.error(f"Response start: {response_text[:300]}")
                return []
            
            # Strategy 1: Remove markdown code blocks (json ... )
            if "" in response_text:
                # Find content between code blocks
                code_block_pattern = r'(?:json)?\s*([\s\S]*?)```'
                matches = re.findall(code_block_pattern, response_text)
                if matches:
                    response_text = matches[0].strip()
                    logger.debug(f"Extracted from code block: {len(response_text)} chars")
            
            # Strategy 2: Remove any remaining backticks
            response_text = response_text.strip('`').strip()
            
            # Strategy 3: Handle "json" prefix (sometimes LLM outputs "json[...]")
            if response_text.lower().startswith("json"):
                response_text = response_text[4:].strip()
            
            # Strategy 4: Find the JSON array bounds
            bracket_start = response_text.find("[")
            bracket_end = response_text.rfind("]")
            
            if bracket_start != -1 and bracket_end != -1 and bracket_end > bracket_start:
                response_text = response_text[bracket_start:bracket_end + 1]
                logger.debug(f"Extracted array bounds: {len(response_text)} chars")
            
            # Strategy 5: Try direct JSON parse
            try:
                data = json.loads(response_text)
                return self._process_parsed_json(data)
            except json.JSONDecodeError as e:
                logger.warning(f"⚠ Initial JSON parse failed: {e}")
            except Exception as e:
                logger.error(f"Unexpected error during JSON parse: {type(e)._name_}: {e}")
                return []
            
            # Strategy 6: Fix common JSON issues
            fixed_text = response_text
            
            # Fix trailing commas before ] or }
            fixed_text = re.sub(r',\s*]', ']', fixed_text)
            fixed_text = re.sub(r',\s*}', '}', fixed_text)
            
            # Fix unescaped newlines in strings
            fixed_text = re.sub(r'(?<!\\)\n(?=[^"]"[^"]$)', '\\n', fixed_text)
            
            try:
                data = json.loads(fixed_text)
                logger.info(f"Fixed trailing commas and parsed JSON")
                return self._process_parsed_json(data)
            except json.JSONDecodeError:
                pass
            except Exception as e:
                logger.error(f"Unexpected error after fixing JSON: {type(e)._name_}: {e}")
            
            # Strategy 7: Try to parse line by line for individual JSON objects
            logger.warning("⚠ Attempting line-by-line JSON object extraction...")
            test_cases = []
            
            # Find all JSON objects that look like test cases (balanced braces)
            try:
                # Use a more sophisticated approach to find balanced JSON objects
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
                            # Check if this looks like a test case
                            if '"query"' in potential_json:
                                try:
                                    obj = json.loads(potential_json)
                                    if isinstance(obj, dict) and "query" in obj:
                                        test_cases.append(obj)
                                except json.JSONDecodeError as e:
                                    logger.debug(f"⚠ Failed to parse potential object: {e}")
                                    continue
                            start = -1
            except Exception as e:
                logger.error(f"Error in balanced brace extraction: {e}")
            
            if test_cases:
                logger.info(f"Extracted {len(test_cases)} test cases via balanced brace extraction")
                return test_cases
            
            # Strategy 8: Last resort - try to fix quotes
            try:
                # Some LLMs use single quotes
                fixed_text = response_text.replace("'", '"')
                data = json.loads(fixed_text)
                logger.info(f"Fixed quotes and parsed JSON")
                return self._process_parsed_json(data)
            except json.JSONDecodeError:
                pass
            except Exception as e:
                logger.error(f"Unexpected error after fixing quotes: {type(e)._name_}: {e}")
            
            logger.error(f"All JSON extraction strategies failed")
            logger.error(f"Response text sample: {original_text[:500]}...")
            return []
            
        except Exception as outer_error:
            logger.error(f"Critical error in extract_json_from_response: {type(outer_error).name_}: {outer_error}")
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
                # Check common wrapper keys
                for key in ["test_cases", "examples", "data", "results", "dataset"]:
                    if key in data and isinstance(data[key], list):
                        logger.info(f"Extracted {len(data[key])} test cases from '{key}' key")
                        return data[key]
                # Single test case
                if "query" in data:
                    logger.info(f"Extracted 1 test case (single object)")
                    return [data]
            
            logger.warning(f"⚠ Unexpected JSON structure: {type(data)}")
            return []
        except Exception as e:
            logger.error(f"Error in process_parsed_json: {type(e).name_}: {e}")
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
        # Safety check: must be a dict
        if not isinstance(test_case, dict):
            logger.warning(f"Test case is not a dict: {type(test_case)}")
            return False
        
        required_fields = ["query", "api", "endpoint", "method", "request", 
                          "expected_response", "scenario_type", "test_category", "notes"]
        
        for field in required_fields:
            if field not in test_case:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate scenario_type
        if test_case.get("scenario_type") not in ["valid", "edge", "extreme"]:
            logger.warning(f"Invalid scenario_type: {test_case.get('scenario_type')}")
            return False
        
        # Validate test_category
        valid_categories = ["typo", "boundary", "rare_combination", "valid_flow", 
                           "error_case", "security", "performance"]
        if test_case.get("test_category") not in valid_categories:
            logger.warning(f"Invalid test_category: {test_case.get('test_category')}")
            return False
        
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
            # Skip if tc is not a dict (malformed data)
            if not isinstance(tc, dict):
                logger.warning(f"⚠ Skipping non-dict test case: {type(tc)}")
                continue
            
            # Ensure request and expected_response are JSON strings
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
                
                # Ollama chat API endpoint
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
                        "num_predict": 8192,  # Max tokens for response
                    }
                }
                
                # Longer timeout for local CPU inference
                timeout = httpx.Timeout(300.0, connect=10.0)  # 5 min for generation, 10s for connect
                
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
                    
                    # Log performance metrics
                    eval_count = result.get("eval_count", 0)
                    eval_duration = result.get("eval_duration", 0)
                    if eval_duration > 0:
                        tokens_per_sec = eval_count / (eval_duration / 1e9)
                        logger.info(f"Ollama: {eval_count} tokens @ {tokens_per_sec:.1f} tok/s")
                    
                    logger.info(f"Ollama response received: {len(response_text)} chars")
                    return response_text
                    
            except httpx.TimeoutException:
                logger.warning(f"⚠ Ollama timeout on {current_model}")
                
                # Try fallback model (Gemma 2B - faster)
                if current_model != self.ollama_fallback and attempt == 0:
                    logger.warning(f"⚠ Switching to faster model: {self.ollama_fallback}")
                    current_model = self.ollama_fallback
                    continue
                    
            except Exception as e:
                error_str = str(e).lower()
                
                # Model not found - try to pull it
                if "model" in error_str and "not found" in error_str:
                    logger.warning(f"⚠ Model {current_model} not found. Try: ollama pull {current_model}")
                    
                    if current_model != self.ollama_fallback:
                        logger.warning(f"⚠ Trying fallback model: {self.ollama_fallback}")
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
        scenario_distribution: Optional[Dict[str, float]] = None
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
        
        Returns:
            Dictionary with generation results and file paths
        """
        if not self.ollama_available:
            raise ValueError("Ollama not available. Install from https://ollama.ai/download")
        
        # Safely extract template info
        template_name = "Unknown"
        template_id = "unknown"
        try:
            template_name = template_data.get("name", "Unknown") if isinstance(template_data, dict) else "Unknown"
            template_id = str(template_data.get("id", "unknown")) if isinstance(template_data, dict) else "unknown"
        except Exception as e:
            logger.error(f"Error extracting template info: {e}")
        
        logger.info(f"Starting FAST dataset generation for: {template_name}")
        logger.info(f"Provider: {self.provider.upper()} | Model: {self.model_name}")
        target_msg = f"{num_examples} test cases" if num_examples else "dynamic count (default 100)"
        logger.info(f"Target: {target_msg} (70% valid, 20% edge, 10% extreme)")
        custom_preview = user_prompt[:100] if user_prompt else "None"
        logger.info(f"User prompt: {custom_preview}...")
        
        try:
            # Build prompts with error handling
            logger.info(f"Building prompts...")
            try:
                system_prompt = self._build_system_prompt(template_data, scenario_distribution)
                user_prompt_msg = self._build_user_prompt(user_prompt, num_examples, focus_areas)
            except Exception as prompt_error:
                logger.error(f"Error building prompts: {type(prompt_error)._name_}: {prompt_error}")
                raise ValueError(f"Failed to build prompts: {prompt_error}")
            
            logger.info(f"📋 Total prompt: ~{(len(system_prompt) + len(user_prompt_msg))//4} tokens")
            
            import time
            start_time = time.time()
            
            # Call Ollama API
            response_text = None
            try:
                response_text = await self._call_ollama_api(system_prompt, user_prompt_msg, num_examples)
            except Exception as api_error:
                logger.error(f"API call failed: {type(api_error)._name_}: {api_error}")
                raise ValueError(f"API call failed: {api_error}")
            
            if not response_text:
                raise ValueError("Empty response from API")
            
            elapsed = time.time() - start_time
            logger.info(f"API call completed in {elapsed:.2f} seconds")
            
            # Save raw response for debugging if extraction fails
            try:
                test_cases = self._extract_json_from_response(response_text)
            except Exception as extract_error:
                logger.error(f"JSON extraction failed: {extract_error}")
                logger.error(f"Full response text:\n{response_text}")
                # Save to file for inspection
                debug_file = os.path.join(self.datasets_dir, f"debug_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                try:
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(f"Error: {extract_error}\n\n")
                        f.write(f"Response text:\n{response_text}")
                    logger.error(f"Saved debug response to: {debug_file}")
                except:
                    pass
                raise ValueError(f"Failed to extract JSON from response: {extract_error}")
            
            if not test_cases:
                # Save problematic response to file for debugging
                debug_file = os.path.join(self.datasets_dir, f"debug_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                try:
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write("="*80 + "\n")
                        f.write(f"{self.provider.upper()} RESPONSE DEBUG DUMP\n")
                        f.write("="*80 + "\n\n")
                        f.write("Full Response:\n")
                        f.write(response_text)
                    logger.error(f"Saved debug response to: {debug_file}")
                except Exception as save_error:
                    logger.error(f"Could not save debug file: {save_error}")
                
                logger.error(f"Failed to extract JSON from response.")
                logger.error(f"Response length: {len(response_text)} chars")
                logger.error(f"Response preview (first 2000 chars): {response_text[:2000]}")
                raise ValueError(f"Failed to extract test cases from LLM response. Response may be malformed. Debug file: {debug_file if 'debug_file' in locals() else 'N/A'}")
            
            logger.info(f"✅ Received {len(test_cases)} test cases from {self.provider.upper()}")
            
            # Validate test cases
            valid_test_cases = []
            validation_errors = 0
            for tc in test_cases:
                if self._validate_test_case(tc, template_data):
                    valid_test_cases.append(tc)
                else:
                    validation_errors += 1
                    if validation_errors <= 3:  # Only log first 3 errors
                        logger.warning(f"⚠ Skipping invalid test case: {tc.get('query', 'unknown')[:50]}")
            
            if validation_errors > 0:
                logger.warning(f"⚠ Total validation errors: {validation_errors}")
            
            logger.info(f"Validated {len(valid_test_cases)} of {len(test_cases)} test cases")
            
            if len(valid_test_cases) == 0:
                raise ValueError("No valid test cases generated. Check template schema and LLM output.")
            
            # Convert to CSV format
            csv_rows = self._convert_to_csv_format(valid_test_cases)
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_template_name = "".join(c if c.isalnum() or c in "-" else "" for c in template_name.lower())
            csv_filename = f"{safe_template_name}dataset{timestamp}.csv"
            csv_path = os.path.join(self.datasets_dir, csv_filename)
            
            # Save to CSV with proper escaping
            df = pd.DataFrame(csv_rows)
            df.to_csv(csv_path, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8')
            logger.info(f"Saved CSV dataset: {csv_path}")
            
            # Save JSON backup
            json_filename = f"{safe_template_name}dataset{timestamp}.json"
            json_path = os.path.join(self.datasets_dir, json_filename)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(valid_test_cases, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved JSON backup: {json_path}")
            
            # Calculate statistics
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
            logger.info(f"Dataset generation completed successfully!")
            
            return {
                "success": True,
                "template_name": template_name,
                "template_id": template_id,
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
                "csv_preview": csv_rows[:5],  # First 5 rows for preview
                "timestamp": timestamp,
                "model_used": self.model_name
            }
        
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Error generating dataset: {type(e)._name_}: {e}")
            logger.error(f"Full traceback:\n{error_traceback}")
            
            # Determine error category for better debugging
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
                "error_type": type(e)._name_,
                "template_name": template_name,
                "template_id": template_id,
                "traceback": error_traceback
            }


# Global instance
_enterprise_generator = None


def get_enterprise_dataset_generator() -> EnterpriseDatasetGenerator:
    """Get or create global EnterpriseDatasetGenerator instance"""
    global _enterprise_generator
    if _enterprise_generator is None:
        _enterprise_generator = EnterpriseDatasetGenerator()
    return _enterprise_generator