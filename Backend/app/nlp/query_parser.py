"""
Query Parser - Extract intent and slots from natural language queries
Uses hybrid approach: spaCy NER + QA model + pattern matching
Now dynamically loads patterns from template service
"""

import spacy
from typing import Dict, List, Optional, Tuple
import re
from app.core.logger import logger
from app.services.template_service import get_template_service

# Slot patterns for extracting specific fields
SLOT_PATTERNS = {
    "username": [
        r"username[:\s]+([a-zA-Z0-9_-]+)",
        r"user[:\s]+([a-zA-Z0-9_-]+)",
        r"for\s+([a-zA-Z0-9_-]+)",
        r"name[:\s]+([a-zA-Z0-9_-]+)"
    ],
    "password": [
        r"password[:\s]+([a-zA-Z0-9@#$%^&*!_-]+)",
        r"pwd[:\s]+([a-zA-Z0-9@#$%^&*!_-]+)",
        r"pass[:\s]+([a-zA-Z0-9@#$%^&*!_-]+)"
    ],
    "email": [
        r"email[:\s]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
        r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
    ],
    "phone": [
        r"phone[:\s]+([\+]?[\d\s\-\(\)]+)",
        r"mobile[:\s]+([\+]?[\d\s\-\(\)]+)",
        r"(\+?\d{1,3}[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4})"
    ],
    "name": [
        r"name[:\s]+([A-Z][a-zA-Z\s]+)",
        r"full\s+name[:\s]+([A-Z][a-zA-Z\s]+)"
    ]
}


class QueryParser:
    """
    Parse natural language queries to extract:
    1. Intent (which API: login, signup, update, etc.)
    2. Slots (fields: username, password, email, etc.)
    
    Dynamically loads intent patterns from template service
    """
    
    def __init__(self, spacy_model: str = "en_core_web_md"):
        """
        Initialize the query parser
        
        Args:
            spacy_model: spaCy model to load (default: en_core_web_md)
        """
        try:
            self.nlp = spacy.load(spacy_model)
            logger.info(f"Loaded spaCy model: {spacy_model}")
        except OSError:
            logger.warning(f"spaCy model {spacy_model} not found. Using en_core_web_sm as fallback.")
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.error("No spaCy model available. Run: python -m spacy download en_core_web_sm")
                self.nlp = None
        
        # Load intent patterns dynamically from template service
        self.intent_patterns = self._load_intent_patterns()
        logger.info(f"Loaded {len(self.intent_patterns)} intent patterns from template service")
    
    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """
        Load intent patterns dynamically from template service
        
        Returns:
            Dictionary mapping intent to list of regex patterns
        """
        try:
            template_service = get_template_service()
            templates = template_service.get_all_templates()
            
            patterns = {}
            for intent, template in templates.items():
                keywords = template.get("intent_keywords", [])
                if keywords:
                    # Convert keywords to regex patterns
                    patterns[intent] = self._keywords_to_patterns(keywords)
            
            if not patterns:
                logger.warning("No templates loaded, intent detection may fail")
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error loading intent patterns from templates: {e}")
            return {}
    
    def _keywords_to_patterns(self, keywords: List[str]) -> List[str]:
        """
        Convert intent keywords to regex patterns
        
        Args:
            keywords: List of intent keywords
            
        Returns:
            List of regex patterns
        """
        patterns = []
        for keyword in keywords:
            # Escape special regex characters
            escaped = re.escape(keyword)
            # Create word boundary pattern
            pattern = rf"\b{escaped}\b"
            patterns.append(pattern)
        
        return patterns
    
    def reload_patterns(self):
        """
        Reload intent patterns from template service (hot reload)
        """
        logger.info("Reloading intent patterns...")
        self.intent_patterns = self._load_intent_patterns()
        logger.info(f"Reloaded {len(self.intent_patterns)} intent patterns")
    
    def detect_intent(self, query: str) -> Tuple[str, float]:
        """
        Detect the API intent from the query
        
        Args:
            query: Natural language query
            
        Returns:
            Tuple of (intent_name, confidence_score)
        """
        query_lower = query.lower()
        
        # Score each intent based on pattern matches
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0.0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    matches += 1
                    score += 0.5
            
            if matches > 0:
                intent_scores[intent] = min(score, 1.0)
        
        # If no patterns matched, return unknown
        if not intent_scores:
            return "unknown", 0.0
        
        # Return the intent with highest score
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        return best_intent[0], best_intent[1]
    
    def extract_slots_regex(self, query: str) -> Dict[str, str]:
        """
        Extract slots using regex patterns
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary of slot_name: slot_value
        """
        slots = {}
        
        for slot_name, patterns in SLOT_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    slots[slot_name] = match.group(1).strip()
                    break  # Use first match
        
        return slots
    
    def extract_slots_spacy(self, query: str) -> Dict[str, str]:
        """
        Extract slots using spaCy NER
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary of slot_name: slot_value
        """
        if not self.nlp:
            return {}
        
        doc = self.nlp(query)
        slots = {}
        
        # Map spaCy entity types to slot names
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                if "name" not in slots:
                    slots["name"] = ent.text
            elif ent.label_ == "EMAIL":
                slots["email"] = ent.text
            elif ent.label_ == "PHONE":
                slots["phone"] = ent.text
            elif ent.label_ == "ORG":
                slots["organization"] = ent.text
        
        return slots
    
    def extract_slots_contextual(self, query: str) -> Dict[str, str]:
        """
        Extract slots using contextual analysis
        Looks for common patterns like "for X and Y"
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary of slot_name: slot_value
        """
        slots = {}
        
        # Pattern: "for X and Y" often means username and password
        pattern = r"for\s+([a-zA-Z0-9_-]+)\s+and\s+([a-zA-Z0-9@#$%^&*!_-]+)"
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            slots["username"] = match.group(1)
            slots["password"] = match.group(2)
        
        # Pattern: "credentials for X and Y"
        pattern = r"credentials\s+for\s+([a-zA-Z0-9_-]+)\s+and\s+([a-zA-Z0-9@#$%^&*!_-]+)"
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            slots["username"] = match.group(1)
            slots["password"] = match.group(2)
        
        return slots
    
    def parse(self, query: str) -> Dict:
        """
        Main parsing function - combines all extraction methods
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary with:
            - intent: detected API intent
            - confidence: confidence score (0-1)
            - slots: extracted field values
            - raw_query: original query
        """
        logger.info(f"Parsing query: {query}")
        
        # Detect intent
        intent, confidence = self.detect_intent(query)
        logger.info(f"Detected intent: {intent} (confidence: {confidence:.2f})")
        
        # Extract slots using multiple methods
        slots_regex = self.extract_slots_regex(query)
        slots_spacy = self.extract_slots_spacy(query)
        slots_contextual = self.extract_slots_contextual(query)
        
        # Merge all slots (priority: contextual > regex > spacy)
        slots = {}
        slots.update(slots_spacy)
        slots.update(slots_regex)
        slots.update(slots_contextual)
        
        logger.info(f"Extracted slots: {slots}")
        
        return {
            "intent": intent,
            "confidence": confidence,
            "slots": slots,
            "raw_query": query,
            "metadata": {
                "slots_regex": slots_regex,
                "slots_spacy": slots_spacy,
                "slots_contextual": slots_contextual
            }
        }


# Global parser instance
_parser_instance = None


def get_query_parser() -> QueryParser:
    """Get or create global QueryParser instance"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = QueryParser()
    return _parser_instance


def parse_query(query: str) -> Dict:
    """
    Convenience function to parse a query
    
    Args:
        query: Natural language query
        
    Returns:
        Parsed result with intent and slots
    """
    parser = get_query_parser()
    return parser.parse(query)
