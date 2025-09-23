"""
Pydantic models for Rule Engine components according to PRD specifications.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Pattern
from pydantic import BaseModel, Field, validator
from enum import Enum


class MatchType(str, Enum):
    """Types of matches the Rule Engine can produce."""
    EXACT = "exact"
    FUZZY = "fuzzy"
    HEURISTIC = "heuristic" 
    UNRESOLVED = "unresolved"


class Provenance(str, Enum):
    """Source of the candidate match."""
    RULE = "rule"
    SEMANTIC = "semantic"
    FALLBACK = "fallback"


class RuleEngineConfig(BaseModel):
    """Configuration for Rule Engine behavior."""
    fuzzy_threshold: float = Field(
        default=0.90,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score for fuzzy matching (0.0-1.0)"
    )
    exact_confidence: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Confidence score assigned to exact regex matches"
    )
    partial_confidence: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Confidence score for partial/incomplete matches"
    )
    fuzzy_confidence_base: float = Field(
        default=0.80,
        ge=0.0,
        le=1.0,
        description="Base confidence for fuzzy matches (adjusted by similarity)"
    )
    min_fuzzy_confidence: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for accepting fuzzy matches"
    )
    clause_split_regex: str = Field(
        default=r'\s*(?:,\s*)?(?:and\s+|then\s+|after\s+|when\s+|once\s+|;\s*)',
        description="Regex pattern for splitting text into clauses"
    )
    max_clause_length: int = Field(
        default=1000,
        ge=10,
        description="Maximum length of a single clause to process"
    )
    max_fuzzy_candidates: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of fuzzy match candidates to return"
    )
    enable_heuristics: bool = Field(
        default=True,
        description="Enable heuristic matching for URLs, emails, dates, etc."
    )
    compile_timeout_seconds: float = Field(
        default=2.0,
        ge=0.1,
        description="Maximum time allowed for template compilation"
    )

    class Config:
        json_schema_extra = {  # type: ignore
            "example": {
                "fuzzy_threshold": 0.85,
                "exact_confidence": 0.95,
                "partial_confidence": 0.70,
                "fuzzy_confidence_base": 0.80,
                "max_clause_length": 500,
                "max_fuzzy_candidates": 5
            }
        }


class PatternEntry(BaseModel):
    """
    Compiled pattern entry for efficient matching.
    Represents a single template converted to a regex pattern.
    """
    func_name: str = Field(..., description="Function name this pattern maps to")
    template: str = Field(..., description="Original template string")
    template_id: str = Field(..., description="Unique identifier for this template")
    compiled_pattern: Optional[Pattern[str]] = Field(
        None, 
        description="Compiled regex pattern (excluded from JSON serialization)"
    )
    args: List[str] = Field(default_factory=list, description="Expected argument names")
    priority: int = Field(default=0, description="Template priority for tie-breaking")
    category: str = Field(default="general", description="Function category")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        arbitrary_types_allowed = True  # Allow Pattern type
        json_encoders = {  # type: ignore
            Pattern: lambda v: v.pattern if v else None  # type: ignore  # Serialize pattern as string
        }
        exclude = {"compiled_pattern"}  # Don't include compiled pattern in JSON output

    @validator('template_id', pre=True, always=True)
    def generate_template_id(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        """Generate template ID if not provided."""
        if v:
            return v
        func_name = values.get('func_name', 'unknown')
        template = values.get('template', '')
        # Create a simple hash-like ID
        import hashlib
        content = f"{func_name}:{template}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def is_valid(self) -> bool:
        """Check if the pattern entry is valid and ready for matching."""
        return (
            bool(self.func_name) and 
            bool(self.template) and 
            self.compiled_pattern is not None
        )


class TextSpan(BaseModel):
    """Represents a span of text that was matched."""
    start: int = Field(..., ge=0, description="Start position in original text")
    end: int = Field(..., gt=0, description="End position in original text")
    matched_text: Optional[str] = Field(None, description="The actual matched substring")

    @validator('end')
    def end_greater_than_start(cls, v: int, values: Dict[str, Any]) -> int:
        """Ensure end is greater than start."""
        if 'start' in values and v <= values['start']:
            raise ValueError('end must be greater than start')
        return v


class Candidate(BaseModel):
    """
    A candidate structured test step produced by the Rule Engine.
    This is the primary output format specified in the PRD.
    """
    function: str = Field(..., description="Function name to execute")
    args: Dict[str, Any] = Field(default_factory=dict, description="Extracted arguments")
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Confidence score (0.0-1.0)"
    )
    provenance: Provenance = Field(
        default=Provenance.RULE, 
        description="Source of this candidate"
    )
    match_type: MatchType = Field(
        default=MatchType.EXACT,
        description="Type of match that produced this candidate"
    )
    template: Optional[str] = Field(None, description="Template that was matched")
    template_id: Optional[str] = Field(None, description="ID of matched template")
    explanation: str = Field(
        ..., 
        description="Human-readable explanation of the match"
    )
    span: Optional[TextSpan] = Field(None, description="Location in original text")
    order: int = Field(default=1, description="Order/position in overall sentence")
    
    # Additional metadata for debugging and analysis
    unresolved_keys: List[str] = Field(
        default_factory=list, 
        description="Arguments that could not be extracted"
    )
    fuzzy_score: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=100.0, 
        description="Fuzzy matching score (0-100) if applicable"
    )
    processing_time_ms: Optional[float] = Field(
        None, 
        description="Time taken to generate this candidate"
    )

    class Config:
        json_schema_extra = {  # type: ignore
            "example": {
                "function": "login",
                "args": {"username": "admin", "password": "secret123"},
                "confidence": 0.95,
                "provenance": "rule",
                "match_type": "exact",
                "template": "log in as {username} with {password}",
                "explanation": "Exact regex match on login template",
                "span": {"start": 0, "end": 28, "matched_text": "log in as admin with secret123"},
                "order": 1
            }
        }

    @validator('explanation', pre=True, always=True)
    def generate_explanation(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        """Generate explanation if not provided."""
        if v:
            return v
        
        match_type = values.get('match_type', MatchType.EXACT)
        template = values.get('template', 'unknown template')
        function = values.get('function', 'unknown function')
        
        if match_type == MatchType.EXACT:
            return f"Exact regex match on '{function}' template: {template}"
        elif match_type == MatchType.FUZZY:
            fuzzy_score = values.get('fuzzy_score', 0)
            return f"Fuzzy match ({fuzzy_score:.1f}%) on '{function}' template: {template}"
        elif match_type == MatchType.HEURISTIC:
            return f"Heuristic match for '{function}' function"
        else:
            return f"Match for '{function}' function"


class ParseResult(BaseModel):
    """
    Complete result from Rule Engine parse operation.
    Contains all candidates plus metadata about unresolved tokens.
    """
    candidates: List[Candidate] = Field(
        default_factory=list, 
        description="List of candidate matches found"
    )
    overall_confidence: float = Field(
        0.0, 
        ge=0.0, 
        le=1.0, 
        description="Overall confidence across all candidates"
    )
    unresolved_tokens: List[str] = Field(
        default_factory=list,
        description="Text fragments that couldn't be resolved"
    )
    processing_time_ms: float = Field(
        0.0, 
        ge=0.0, 
        description="Total processing time in milliseconds"
    )
    clauses_processed: int = Field(
        0, 
        ge=0, 
        description="Number of text clauses processed"
    )
    patterns_tried: int = Field(
        0, 
        ge=0, 
        description="Total number of patterns attempted"
    )
    
    # Metrics for observability
    exact_matches: int = Field(default=0, description="Count of exact matches")
    fuzzy_matches: int = Field(default=0, description="Count of fuzzy matches")
    heuristic_matches: int = Field(default=0, description="Count of heuristic matches")
    
    class Config:
        json_schema_extra = {  # type: ignore
            "example": {
                "candidates": [
                    {
                        "function": "login",
                        "args": {"username": "admin", "password": "secret"},
                        "confidence": 0.95,
                        "provenance": "rule",
                        "match_type": "exact",
                        "explanation": "Exact match on login template",
                        "order": 1
                    }
                ],
                "overall_confidence": 0.95,
                "unresolved_tokens": [],
                "processing_time_ms": 15.5,
                "clauses_processed": 1,
                "patterns_tried": 12,
                "exact_matches": 1,
                "fuzzy_matches": 0,
                "heuristic_matches": 0
            }
        }

    def add_candidate(self, candidate: Candidate) -> None:
        """Add a candidate and update metrics."""
        self.candidates.append(candidate)
        
        # Update match type counters
        if candidate.match_type == MatchType.EXACT:
            self.exact_matches += 1
        elif candidate.match_type == MatchType.FUZZY:
            self.fuzzy_matches += 1
        elif candidate.match_type == MatchType.HEURISTIC:
            self.heuristic_matches += 1

    def calculate_overall_confidence(self) -> float:
        """Calculate overall confidence as weighted average."""
        if not self.candidates:
            return 0.0
        
        # Weight by confidence scores
        total_weighted = sum(c.confidence for c in self.candidates)
        self.overall_confidence = total_weighted / len(self.candidates)
        return self.overall_confidence

    def sort_candidates(self) -> None:
        """Sort candidates by confidence (descending) then order (ascending)."""
        self.candidates.sort(key=lambda c: (-c.confidence, c.order))


class HotReloadResult(BaseModel):
    """Result from hot-reload operations."""
    success: bool = Field(..., description="Whether reload was successful")
    functions_loaded: int = Field(0, description="Number of functions loaded")
    patterns_compiled: int = Field(0, description="Number of patterns compiled")
    compilation_errors: List[str] = Field(
        default_factory=list, 
        description="Template compilation errors"
    )
    reload_time_ms: float = Field(0.0, description="Time taken for reload")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_schema_extra = {  # type: ignore
            "example": {
                "success": True,
                "functions_loaded": 65,
                "patterns_compiled": 185,
                "compilation_errors": [],
                "reload_time_ms": 156.3,
                "timestamp": "2024-01-15T10:30:45Z"
            }
        }


class RuleEngineMetrics(BaseModel):
    """Metrics for monitoring Rule Engine performance."""
    total_parses: int = Field(0, description="Total parse requests processed")
    successful_parses: int = Field(0, description="Successful parse operations")
    failed_parses: int = Field(0, description="Failed parse operations")
    average_parse_time_ms: float = Field(0.0, description="Average parse time")
    average_candidates_per_parse: float = Field(0.0, description="Average candidates returned")
    
    # Pattern compilation metrics
    active_patterns: int = Field(0, description="Number of active patterns")
    patterns_tried: int = Field(0, description="Number of patterns attempted")
    compilation_failures: int = Field(0, description="Pattern compilation failures")
    last_hot_reload: Optional[datetime] = Field(None, description="Last hot-reload timestamp")
    
    # Match type distribution
    exact_match_rate: float = Field(0.0, description="Percentage of exact matches")
    fuzzy_match_rate: float = Field(0.0, description="Percentage of fuzzy matches") 
    heuristic_match_rate: float = Field(0.0, description="Percentage of heuristic matches")
    unresolved_rate: float = Field(0.0, description="Percentage of unresolved inputs")

    class Config:
        json_schema_extra = {  # type: ignore
            "example": {
                "total_parses": 1250,
                "successful_parses": 1190,
                "failed_parses": 60,
                "average_parse_time_ms": 42.5,
                "average_candidates_per_parse": 2.1,
                "active_patterns": 185,
                "compilation_failures": 3,
                "exact_match_rate": 0.78,
                "fuzzy_match_rate": 0.15,
                "heuristic_match_rate": 0.04,
                "unresolved_rate": 0.03
            }
        }