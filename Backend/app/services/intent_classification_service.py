# Backend/app/services/intent_classification_service.py

"""
Intent Classification Service - Automatic intent detection for API queries

This service classifies query intent based on:
1. HTTP Method from template (primary, 100% accurate)
2. Query keywords (fallback for edge cases)

Intent Types:
- create: POST operations (add, submit, generate)
- read: GET single resource (view, show, get)
- update: PUT/PATCH operations (modify, change, update)
- delete: DELETE operations (remove, cancel, delete)
- query: GET list/search (list, search, find, query)

NO LLM NEEDED - Uses simple keyword matching and HTTP method mapping.
"""

from typing import Tuple, Optional


# HTTP Method to Intent mapping
METHOD_INTENT_MAP = {
    "POST": "create",
    "GET": "read",
    "PUT": "update",
    "PATCH": "update",
    "DELETE": "delete",
}

# Keywords that strongly indicate specific intents
INTENT_KEYWORDS = {
    "create": [
        "create", "add", "submit", "place", "generate", "make", "new",
        "register", "signup", "sign up", "initiate", "start", "begin",
        "order", "purchase", "buy", "book", "reserve", "schedule"
    ],
    "read": [
        "get", "show", "view", "display", "fetch", "retrieve", "find",
        "look up", "lookup", "details", "info", "information", "status"
    ],
    "update": [
        "update", "modify", "change", "edit", "alter", "set", "configure",
        "adjust", "revise", "patch", "put", "replace", "rename"
    ],
    "delete": [
        "delete", "remove", "cancel", "terminate", "end", "stop", "close",
        "unsubscribe", "deactivate", "disable", "drop", "clear"
    ],
    "query": [
        "list", "search", "query", "find all", "get all", "show all",
        "browse", "filter", "sort", "explore", "what", "which", "how many"
    ],
}


def get_intent_from_method(method: str) -> str:
    """
    Get intent type directly from HTTP method.
    
    This is the PRIMARY and most accurate method for intent classification.
    
    Args:
        method: HTTP method (POST, GET, PUT, PATCH, DELETE)
        
    Returns:
        Intent type string (create, read, update, delete, query)
    """
    if not method:
        return "unknown"
    
    return METHOD_INTENT_MAP.get(method.upper(), "query")


def classify_intent_from_query(query: str) -> Tuple[str, float]:
    """
    Classify intent from query text using keyword matching.
    
    This is a FALLBACK method when HTTP method is not available.
    
    Args:
        query: Natural language query text
        
    Returns:
        Tuple of (intent_type, confidence_score)
        - intent_type: create, read, update, delete, query, unknown
        - confidence_score: 0.0 to 1.0
    """
    if not query:
        return "unknown", 0.0
    
    query_lower = query.lower().strip()
    
    # Count keyword matches for each intent
    intent_scores = {}
    
    for intent, keywords in INTENT_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in query_lower)
        if matches > 0:
            intent_scores[intent] = matches
    
    if not intent_scores:
        return "unknown", 0.5
    
    # Get the intent with the most keyword matches
    best_intent = max(intent_scores, key=intent_scores.get)
    max_matches = intent_scores[best_intent]
    
    # Calculate confidence based on match count
    # 1 match = 0.7, 2 matches = 0.85, 3+ matches = 0.95
    if max_matches >= 3:
        confidence = 0.95
    elif max_matches == 2:
        confidence = 0.85
    else:
        confidence = 0.70
    
    return best_intent, confidence


def classify_intent(
    query: str,
    method: Optional[str] = None
) -> Tuple[str, float]:
    """
    Classify intent using both method and query.
    
    Priority:
    1. If method is provided, use method-based classification (100% confidence)
    2. Fall back to query-based keyword matching
    
    Args:
        query: Natural language query text
        method: Optional HTTP method from template
        
    Returns:
        Tuple of (intent_type, confidence_score)
    """
    # Primary: Use HTTP method if available
    if method:
        intent = get_intent_from_method(method)
        if intent != "unknown":
            return intent, 1.0  # 100% confidence from method
    
    # Fallback: Use query keywords
    return classify_intent_from_query(query)


def get_intent_for_dataset_row(
    query: str,
    method: str,
    scenario_type: Optional[str] = None
) -> str:
    """
    Get the appropriate intent for a dataset row.
    
    For dataset generation, we primarily use the template's HTTP method
    since all queries in a dataset are for the same API endpoint.
    
    Args:
        query: The query text
        method: HTTP method from template
        scenario_type: Optional scenario type (valid, edge, extreme)
        
    Returns:
        Intent type string
    """
    # For edge/extreme cases, the intent might be "unknown" or "query"
    # to represent malformed or ambiguous inputs
    if scenario_type in ["extreme"]:
        # Some extreme cases might have ambiguous intent
        intent, confidence = classify_intent(query, method)
        if confidence < 0.7:
            return "unknown"
        return intent
    
    # For valid and edge cases, use the method-based intent
    return get_intent_from_method(method)


# Singleton instance (no state needed, but follows project pattern)
class IntentClassificationService:
    """Stateless service for intent classification."""
    
    @staticmethod
    def classify(query: str, method: Optional[str] = None) -> Tuple[str, float]:
        """Classify intent from query and optional method."""
        return classify_intent(query, method)
    
    @staticmethod
    def from_method(method: str) -> str:
        """Get intent directly from HTTP method."""
        return get_intent_from_method(method)
    
    @staticmethod
    def for_dataset_row(
        query: str, 
        method: str, 
        scenario_type: Optional[str] = None
    ) -> str:
        """Get intent for a dataset row."""
        return get_intent_for_dataset_row(query, method, scenario_type)


_service_instance: Optional[IntentClassificationService] = None


def get_intent_classification_service() -> IntentClassificationService:
    """Get singleton intent classification service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = IntentClassificationService()
    return _service_instance
