"""
LLaMA Slot Extractor - Using Llama 3.2 3B Instruct with llama.cpp
Provides structured JSON slot extraction with grammar constraints
"""

import os
import json
from typing import Dict, List, Optional
from pathlib import Path
import subprocess
import tempfile
from app.core.logger import logger
from app.core.config import settings
from app.services.template_service import get_template_service


class LlamaSlotExtractor:
    """
    Extract slots using Llama 3.2 3B Instruct with llama.cpp JSON schema grammar
    Provides strict, reliable JSON extraction with strong instruction adherence
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        llama_cpp_path: Optional[str] = None,
        context_size: int = 2048,
        temperature: float = 0.1,  # Low temp for consistent extraction
        top_p: float = 0.95,
    ):
        """
        Initialize Llama slot extractor
        
        Args:
            model_path: Path to Llama 3.2 3B GGUF model file
            llama_cpp_path: Path to llama-cli executable
            context_size: Context window size
            temperature: Sampling temperature (lower = more deterministic)
            top_p: Nucleus sampling parameter
        """
        self.model_path = model_path or os.getenv(
            "LLAMA_MODEL_PATH",
            str(Path.home() / "models" / "llama-3.2-3b-instruct-q4_k_m.gguf")
        )
        self.llama_cpp_path = llama_cpp_path or os.getenv(
            "LLAMA_CPP_PATH",
            "llama-cli"  # Assumes llama.cpp in PATH
        )
        self.context_size = context_size
        self.temperature = temperature
        self.top_p = top_p
        
        # Check if model exists
        self.enabled = self._check_availability()
        
        if self.enabled:
            logger.info(f"✅ Llama 3.2 3B slot extractor initialized: {self.model_path}")
        else:
            logger.warning("⚠️ Llama 3.2 3B model not found. Slot extraction will use fallback methods.")
    
    def _check_availability(self) -> bool:
        """Check if Llama model and llama.cpp are available"""
        try:
            # Check if model file exists
            if not os.path.exists(self.model_path):
                logger.warning(f"Llama model not found at: {self.model_path}")
                return False
            
            # Check if llama-cli is available
            result = subprocess.run(
                [self.llama_cpp_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                logger.warning(f"llama-cli not available: {self.llama_cpp_path}")
                return False
            
            return True
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.warning(f"Llama availability check failed: {e}")
            return False
    
    def _create_json_schema(self, intent: str, slot_definitions: List[Dict]) -> Dict:
        """
        Create JSON schema for structured output based on slot definitions
        
        Args:
            intent: API intent name
            slot_definitions: List of slot definitions from template
            
        Returns:
            JSON schema dictionary
        """
        properties = {}
        required = []
        
        for slot_def in slot_definitions:
            slot_key = slot_def.get("key", "")
            if not slot_key:
                continue
            
            # Build property definition
            prop = {
                "type": "string",
                "description": f"Extract {slot_key} from the query"
            }
            
            # Add to schema
            properties[slot_key] = prop
            
            # Mark as required if specified
            if slot_def.get("required", False):
                required.append(slot_key)
        
        schema = {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False
        }
        
        return schema
    
    def _build_prompt(self, query: str, intent: str, slot_definitions: List[Dict]) -> str:
        """
        Build instruction prompt for Llama 3.2 3B
        
        Args:
            query: User's natural language query
            intent: Detected API intent
            slot_definitions: Slot definitions from template
            
        Returns:
            Formatted prompt string
        """
        # Build slot descriptions
        slot_descriptions = []
        for slot_def in slot_definitions:
            key = slot_def.get("key", "")
            questions = slot_def.get("questions", [])
            default = slot_def.get("default", "")
            
            if key:
                desc = f"- **{key}**: "
                if questions:
                    desc += f"{questions[0]}"
                if default:
                    desc += f" (default: {default})"
                slot_descriptions.append(desc)
        
        slots_text = "\n".join(slot_descriptions)
        
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a precise slot extraction system. Extract structured information from user queries.
Extract ONLY the information that is explicitly present in the query.
If a field is not mentioned, use null or empty string.
Return valid JSON only.<|eot_id|>

<|start_header_id|>user<|end_header_id|>

Task: Extract slots from the following query for the "{intent}" API.

Query: "{query}"

Required fields to extract:
{slots_text}

Instructions:
1. Carefully read the query
2. Extract each field value if present
3. Return a JSON object with extracted values
4. Use null for missing values
5. Preserve exact values (case-sensitive for passwords, usernames)

Return only the JSON object, no additional text.<|eot_id|>

<|start_header_id|>assistant<|end_header_id|>

"""
        return prompt
    
    def _run_llama_inference(
        self,
        prompt: str,
        json_schema: Optional[Dict] = None,
        max_tokens: int = 512
    ) -> str:
        """
        Run llama.cpp inference with optional JSON schema grammar
        
        Args:
            prompt: Formatted prompt
            json_schema: Optional JSON schema for constrained generation
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text (JSON string)
        """
        # Build llama-cli command
        cmd = [
            self.llama_cpp_path,
            "-m", self.model_path,
            "-p", prompt,
            "-n", str(max_tokens),
            "-c", str(self.context_size),
            "--temp", str(self.temperature),
            "--top-p", str(self.top_p),
            "--no-display-prompt",
            "-ngl", "0",  # CPU inference (set higher for GPU)
        ]
        
        # Add JSON schema grammar if provided
        if json_schema:
            # Write schema to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(json_schema, f)
                schema_file = f.name
            
            try:
                cmd.extend(["--json-schema", schema_file])
                
                # Run inference
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30  # 30 second timeout
                )
                
                if result.returncode != 0:
                    logger.error(f"Llama inference failed: {result.stderr}")
                    return "{}"
                
                return result.stdout.strip()
            
            finally:
                # Clean up temp file
                try:
                    os.unlink(schema_file)
                except:
                    pass
        else:
            # Run without schema
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Llama inference failed: {result.stderr}")
                return "{}"
            
            return result.stdout.strip()
    
    def extract_slots(
        self,
        query: str,
        intent: str,
        slot_definitions: List[Dict]
    ) -> Dict[str, str]:
        """
        Extract slots from query using Llama 3.2 3B with JSON schema
        
        Args:
            query: Natural language query
            intent: Detected API intent
            slot_definitions: Slot definitions from template
            
        Returns:
            Dictionary of extracted slot values
        """
        if not self.enabled:
            logger.debug("Llama extractor not enabled, returning empty slots")
            return {}
        
        try:
            logger.info(f"🤖 Extracting slots with Llama 3.2 3B for intent: {intent}")
            
            # Build JSON schema
            json_schema = self._create_json_schema(intent, slot_definitions)
            
            # Build prompt
            prompt = self._build_prompt(query, intent, slot_definitions)
            
            # Run inference
            output = self._run_llama_inference(prompt, json_schema, max_tokens=256)
            
            # Parse JSON output
            try:
                # Extract JSON from output (sometimes model adds extra text)
                json_start = output.find('{')
                json_end = output.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = output[json_start:json_end]
                    slots = json.loads(json_str)
                    
                    # Filter out null/empty values
                    slots = {k: v for k, v in slots.items() if v and v != "null"}
                    
                    logger.info(f"✅ Llama extracted slots: {slots}")
                    return slots
                else:
                    logger.warning("No JSON found in Llama output")
                    return {}
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Llama JSON output: {e}")
                logger.debug(f"Raw output: {output}")
                return {}
        
        except subprocess.TimeoutExpired:
            logger.error("Llama inference timed out")
            return {}
        except Exception as e:
            logger.error(f"Llama slot extraction error: {e}", exc_info=True)
            return {}
    
    def extract_slots_for_intent(self, query: str, intent: str) -> Dict[str, str]:
        """
        Extract slots for a specific intent using template definitions
        
        Args:
            query: Natural language query
            intent: Detected API intent
            
        Returns:
            Dictionary of extracted slot values
        """
        try:
            # Get template for intent
            template_service = get_template_service()
            template = template_service.get_template(intent)
            
            if not template:
                logger.warning(f"No template found for intent: {intent}")
                return {}
            
            # Get slot definitions
            slot_definitions = template.get("slots", [])
            
            if not slot_definitions:
                logger.debug(f"No slot definitions for intent: {intent}")
                return {}
            
            # Extract slots
            return self.extract_slots(query, intent, slot_definitions)
            
        except Exception as e:
            logger.error(f"Error in extract_slots_for_intent: {e}")
            return {}


# Global extractor instance
_llama_extractor = None


def get_llama_extractor() -> LlamaSlotExtractor:
    """Get or create global LlamaSlotExtractor instance"""
    global _llama_extractor
    if _llama_extractor is None:
        _llama_extractor = LlamaSlotExtractor()
    return _llama_extractor
