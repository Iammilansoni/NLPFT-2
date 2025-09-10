"""
Rule Engine for NLPForge Tester - converts natural language to structured test steps.

This module provides the core functionality to parse plain-English test descriptions
and convert them into structured JSON test steps using template matching and fuzzy
string matching algorithms.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Pattern
try:
    from rapidfuzz import fuzz, process  # type: ignore
except ImportError:
    # Fallback if rapidfuzz is not installed
    fuzz = None  # type: ignore
    process = None  # type: ignore
from app.core.logger import logger


class RuleEngine:
    """
    Rule Engine that converts natural language input to structured test steps.
    
    Uses template-based regex matching with fuzzy string matching as fallback
    to extract function calls and arguments from natural language descriptions.
    """
    
    def __init__(self, dictionary_path: Optional[str] = None):
        """
        Initialize the Rule Engine with function dictionary.
        
        Args:
            dictionary_path: Path to function_dictionary.json file.
                           If None, uses default storage location.
        """
        if dictionary_path is None:
            # Use storage path from project structure
            dictionary_path = str(Path(__file__).parent.parent.parent / "storage" / "function_dictionary.json")
        
        self.dictionary_path = dictionary_path
        self.function_dictionary: List[Dict[str, Any]] = []
        self.template_patterns: List[Dict[str, Any]] = []
        
        self._load_dictionary()
        self._compile_patterns()
        
        logger.info(f"RuleEngine initialized with {len(self.function_dictionary)} functions")
    
    def _load_dictionary(self) -> None:
        """Load the function dictionary from JSON file."""
        try:
            with open(self.dictionary_path, 'r', encoding='utf-8') as file:
                self.function_dictionary = json.load(file)
            logger.debug(f"Loaded {len(self.function_dictionary)} function definitions")
        except FileNotFoundError:
            logger.error(f"Function dictionary not found at {self.dictionary_path}")
            self.function_dictionary = []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in function dictionary: {e}")
            self.function_dictionary = []
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns from templates for efficient matching."""
        self.template_patterns = []
        
        for func_def in self.function_dictionary:
            function_name = func_def.get("name", "")
            templates = func_def.get("templates", [])
            signature = func_def.get("signature", {})
            
            for template in templates:
                # Convert template to regex pattern
                # e.g., "log in as {username} with {password}" -> r"log in as (?P<username>\S+) with (?P<password>\S+)"
                pattern = self._template_to_regex(template, signature)
                if pattern:
                    self.template_patterns.append({
                        "function": function_name,
                        "template": template,
                        "pattern": pattern,
                        "signature": signature,
                        "func_id": func_def.get("id", "")
                    })
        
        logger.debug(f"Compiled {len(self.template_patterns)} template patterns")
    
    def _template_to_regex(self, template: str, signature: Dict[str, str]) -> Optional[Pattern[str]]:
        """
        Convert a template string to a compiled regex pattern.
        
        Args:
            template: Template string with placeholders like "log in as {username}"
            signature: Function signature defining argument types
            
        Returns:
            Compiled regex pattern or None if invalid
        """
        try:
            # Escape special regex characters except our placeholders
            escaped = re.escape(template)
            
            # Replace escaped placeholders with named groups
            # {username} -> (?P<username>\S+) for basic matching
            # More sophisticated patterns based on type
            for arg_name, arg_type in signature.items():
                placeholder = re.escape("{" + arg_name + "}")
                
                if arg_type == "str":
                    # Match non-whitespace or quoted strings
                    group_pattern = f"(?P<{arg_name}>\\S+|'[^']*'|\"[^\"]*\")"
                elif arg_type == "int":
                    # Match integers
                    group_pattern = f"(?P<{arg_name}>\\d+)"
                elif arg_type == "any":
                    # Match anything non-whitespace
                    group_pattern = f"(?P<{arg_name}>\\S+)"
                else:
                    # Default to non-whitespace
                    group_pattern = f"(?P<{arg_name}>\\S+)"
                
                escaped = escaped.replace(placeholder, group_pattern)
            
            # Make the pattern case-insensitive and allow for variations
            pattern = re.compile(escaped, re.IGNORECASE)
            return pattern
            
        except re.error as e:
            logger.warning(f"Failed to compile regex for template '{template}': {e}")
            return None
    
    def _extract_arguments(self, text: str, pattern_info: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
        """
        Extract arguments from text using compiled regex pattern.
        
        Args:
            text: Input text to match against
            pattern_info: Pattern information including compiled regex
            
        Returns:
            Tuple of (extracted_args, confidence_score)
        """
        try:
            match = pattern_info["pattern"].search(text)
            if match:
                args = match.groupdict()
                
                # Clean up extracted arguments
                cleaned_args: Dict[str, Any] = {}
                for key, value in args.items():
                    if value:
                        # Remove quotes if present
                        cleaned_value = value.strip("'\"")
                        cleaned_args[key] = cleaned_value
                
                # High confidence for exact regex match
                confidence = 0.95
                return cleaned_args, confidence
            
        except Exception as e:
            logger.warning(f"Error extracting arguments: {e}")
        
        return {}, 0.0
    
    def _fuzzy_match_templates(self, text: str, threshold: float = 80.0) -> List[Dict[str, Any]]:
        """
        Use fuzzy string matching to find similar templates.
        
        Args:
            text: Input text to match
            threshold: Minimum similarity score (0-100)
            
        Returns:
            List of fuzzy matches with confidence scores
        """
        matches: List[Dict[str, Any]] = []
        
        # Check if rapidfuzz is available
        if process is None or fuzz is None:
            logger.warning("RapidFuzz not available, skipping fuzzy matching")
            return matches
        
        # Prepare templates for fuzzy matching
        templates = [(pattern["template"], pattern) for pattern in self.template_patterns]
        
        if not templates:
            return matches
        
        # Find fuzzy matches
        fuzzy_results = process.extract(  # type: ignore
            text, 
            [t[0] for t in templates], 
            scorer=fuzz.ratio,  # type: ignore
            limit=5
        )
        
        for template_text, score, _ in fuzzy_results:  # type: ignore
            if score >= threshold:  # type: ignore
                # Find the corresponding pattern info
                pattern_info = next(
                    (pattern for template, pattern in templates if template == template_text),
                    None
                )
                
                if pattern_info:
                    # Try to extract arguments even with fuzzy match
                    args, _ = self._extract_arguments(text, pattern_info)
                    
                    # Lower confidence for fuzzy matches
                    confidence = min(0.85, float(score) / 100.0 * 0.85)  # type: ignore
                    
                    matches.append({
                        "function": pattern_info["function"],
                        "args": args,
                        "confidence": confidence,
                        "source": "rule",
                        "match_type": "fuzzy",
                        "template": template_text,
                        "fuzzy_score": score
                    })
        
        return matches
    
    def _identify_unresolved_tokens(self, text: str, matched_spans: List[Tuple[int, int]]) -> List[str]:
        """
        Identify parts of input text that weren't matched by any pattern.
        
        Args:
            text: Original input text
            matched_spans: List of (start, end) positions that were matched
            
        Returns:
            List of unresolved token strings
        """
        if not matched_spans:
            return [text.strip()]
        
        # Sort spans by start position
        sorted_spans = sorted(matched_spans)
        unresolved: List[str] = []
        
        last_end = 0
        for start, end in sorted_spans:
            if start > last_end:
                # Gap between matches
                gap_text = text[last_end:start].strip()
                if gap_text:
                    unresolved.append(gap_text)
            last_end = max(last_end, end)
        
        # Check for text after last match
        if last_end < len(text):
            remaining = text[last_end:].strip()
            if remaining:
                unresolved.append(remaining)
        
        return unresolved
    
    def parse(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse natural language text into structured test steps.
        
        Args:
            text: Natural language input describing test actions
            
        Returns:
            List of structured test steps with function names, arguments, and confidence scores
        """
        if not text or not text.strip():
            logger.warning("Empty input text provided to rule engine")
            return []
        
        text = text.strip()
        logger.info(f"Parsing text: '{text}'")
        
        steps: List[Dict[str, Any]] = []
        matched_spans: List[Tuple[int, int]] = []
        
        # Phase 1: Try exact template matching
        for pattern_info in self.template_patterns:
            args, confidence = self._extract_arguments(text, pattern_info)
            
            if confidence > 0:
                # Find the span that was matched
                match = pattern_info["pattern"].search(text)
                if match:
                    matched_spans.append((match.start(), match.end()))
                
                step: Dict[str, Any] = {
                    "function": pattern_info["function"],
                    "args": args,
                    "confidence": confidence,
                    "source": "rule",
                    "match_type": "exact",
                    "template": pattern_info["template"]
                }
                steps.append(step)
                logger.debug(f"Exact match: {pattern_info['function']} with confidence {confidence}")
        
        # Phase 2: If no exact matches, try fuzzy matching
        if not steps:
            fuzzy_matches = self._fuzzy_match_templates(text, threshold=70.0)
            steps.extend(fuzzy_matches)
            
            if fuzzy_matches:
                logger.debug(f"Found {len(fuzzy_matches)} fuzzy matches")
        
        # Phase 3: Handle unresolved tokens
        unresolved_tokens = self._identify_unresolved_tokens(text, matched_spans)
        if unresolved_tokens and not steps:
            # If nothing was matched, create an unresolved step
            steps.append({
                "function": "unresolved",
                "args": {"text": text, "tokens": unresolved_tokens},
                "confidence": 0.0,
                "source": "rule",
                "match_type": "unresolved"
            })
            logger.warning(f"No matches found for input: '{text}'")
        elif unresolved_tokens:
            # Add unresolved tokens as metadata to existing steps
            for step in steps:
                step["unresolved_tokens"] = unresolved_tokens
        
        # Sort by confidence (highest first)
        steps.sort(key=lambda x: x["confidence"], reverse=True)  # type: ignore
        
        logger.info(f"Parsed '{text}' into {len(steps)} steps")
        return steps
    
    def get_function_info(self, function_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific function.
        
        Args:
            function_name: Name of the function to look up
            
        Returns:
            Function definition dict or None if not found
        """
        for func_def in self.function_dictionary:
            if func_def.get("name") == function_name:
                return func_def
        return None
    
    def list_available_functions(self) -> List[str]:
        """
        Get list of all available function names.
        
        Returns:
            List of function names
        """
        return [func_def.get("name", "") for func_def in self.function_dictionary]
    
    def get_templates_for_function(self, function_name: str) -> List[str]:
        """
        Get all templates for a specific function.
        
        Args:
            function_name: Name of the function
            
        Returns:
            List of template strings
        """
        func_info = self.get_function_info(function_name)
        if func_info:
            return func_info.get("templates", [])
        return []