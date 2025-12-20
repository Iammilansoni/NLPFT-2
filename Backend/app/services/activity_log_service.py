# Backend\app\services\activity_log_service.py

"""
Activity Log Service - Transform raw system logs into user-friendly messages

This service provides:
- Pattern matching to detect common operations
- Human-readable log message transformation
- Log categorization (Info, Warning, Error, Success)
- Severity levels for highlighting critical warnings

Categories:
- INFO: Normal workflow updates (processing, loading, etc.)
- WARNING: Potential issues (slow operations, rate limits, model mismatches)
- ERROR: Failed operations (generation failed, embedding errors)
- SUCCESS: Completed operations (dataset generated, index built)
"""

import re
from typing import Dict, Any, Optional, Tuple
from enum import Enum


class LogCategory(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class LogSeverity(str, Enum):
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# Pattern definitions: (regex_pattern, human_message_template, category, severity)
# Use {key} placeholders for dynamic values extracted from the log
LOG_PATTERNS: list[Tuple[str, str, LogCategory, LogSeverity]] = [
    # ============= DATASET OPERATIONS =============
    (
        r"Starting dataset generation.*model[=:]?\s*['\"]?(\w[\w\-\.]+)",
        "🚀 Dataset generation started using {model}",
        LogCategory.INFO,
        LogSeverity.NORMAL
    ),
    (
        r"Dataset generation completed.*(\d+)\s*(?:examples?|rows?|items?)",
        "✅ Dataset generated successfully with {count} examples",
        LogCategory.SUCCESS,
        LogSeverity.NORMAL
    ),
    (
        r"Dataset generation failed",
        "❌ Dataset generation failed. Check your configuration.",
        LogCategory.ERROR,
        LogSeverity.HIGH
    ),
    (
        r"Dataset uploaded.*['\"]?([^'\"]+)['\"]?",
        "📤 Dataset uploaded: {filename}",
        LogCategory.SUCCESS,
        LogSeverity.NORMAL
    ),
    
    # ============= EMBEDDING OPERATIONS =============
    (
        r"Embedding.*started.*model[=:]?\s*['\"]?(\w[\w\-\.]+)",
        "🧠 Embedding started with {model}",
        LogCategory.INFO,
        LogSeverity.NORMAL
    ),
    (
        r"Embedding.*completed.*(\d+)\s*vector",
        "✅ Embedding completed: {count} vectors created",
        LogCategory.SUCCESS,
        LogSeverity.NORMAL
    ),
    (
        r"Embedding.*failed|Failed.*embed",
        "❌ Embedding failed. The model may be unavailable.",
        LogCategory.ERROR,
        LogSeverity.HIGH
    ),
    (
        r"(?:Embedding|Model).*(?:changed|switched|updated).*['\"]?(\w[\w\-\.]+)['\"]?",
        "⚠️ Embedding model changed to {model}. Existing vectors may mismatch. Rebuild recommended.",
        LogCategory.WARNING,
        LogSeverity.CRITICAL
    ),
    (
        r"Model mismatch.*embedded.*['\"]?(\w[\w\-\.]+)['\"]?.*current.*['\"]?(\w[\w\-\.]+)['\"]?",
        "⚠️ Model mismatch detected! Data was embedded with {old_model}, but current model is {new_model}",
        LogCategory.WARNING,
        LogSeverity.CRITICAL
    ),
    (
        r"Vector index.*rebuilding|Rebuilding.*index",
        "🔄 Vector index is being rebuilt...",
        LogCategory.INFO,
        LogSeverity.NORMAL
    ),
    (
        r"Vector index.*built|Index.*completed",
        "✅ Vector index built successfully",
        LogCategory.SUCCESS,
        LogSeverity.NORMAL
    ),
    
    # ============= SEARCH OPERATIONS =============
    (
        r"(?:Cross-index|Vector|KNN).*search.*started",
        "🔍 Search started...",
        LogCategory.INFO,
        LogSeverity.NORMAL
    ),
    (
        r"(?:Cross-index|Vector|KNN).*search.*completed.*(\d+)\s*(?:results?|matches?)",
        "✅ Search completed: {count} relevant results found",
        LogCategory.SUCCESS,
        LogSeverity.NORMAL
    ),
    (
        r"(?:Search|Query).*failed",
        "❌ Search failed. Check your query or try again.",
        LogCategory.ERROR,
        LogSeverity.NORMAL
    ),
    (
        r"No.*(?:results?|matches?).*found",
        "ℹ️ No matching results found",
        LogCategory.INFO,
        LogSeverity.NORMAL
    ),
    (
        r"Reranking.*FlashRank.*(\d+)",
        "⚡ Re-ranking {count} results with FlashRank",
        LogCategory.INFO,
        LogSeverity.NORMAL
    ),
    
    # ============= MODEL OPERATIONS =============
    (
        r"(?:Loading|Initializing).*model.*['\"]?(\w[\w\-\.]+)['\"]?",
        "⏳ Loading model: {model}",
        LogCategory.INFO,
        LogSeverity.NORMAL
    ),
    (
        r"Model.*loaded.*['\"]?(\w[\w\-\.]+)['\"]?",
        "✅ Model loaded: {model}",
        LogCategory.SUCCESS,
        LogSeverity.NORMAL
    ),
    (
        r"Model.*unavailable|Cannot.*connect.*(?:Ollama|model)",
        "⚠️ Model unavailable. Ensure Ollama is running.",
        LogCategory.WARNING,
        LogSeverity.HIGH
    ),
    (
        r"Ollama.*not.*(?:running|available|responding)",
        "⚠️ Ollama service is not responding. Start it to use AI features.",
        LogCategory.WARNING,
        LogSeverity.HIGH
    ),
    
    # ============= BACKGROUND TASKS =============
    (
        r"Background.*task.*started.*['\"]?([^'\"]+)['\"]?",
        "🔄 Background task started: {task_name}",
        LogCategory.INFO,
        LogSeverity.NORMAL
    ),
    (
        r"Background.*task.*completed.*['\"]?([^'\"]+)['\"]?",
        "✅ Background task completed: {task_name}",
        LogCategory.SUCCESS,
        LogSeverity.NORMAL
    ),
    (
        r"Background.*task.*failed.*['\"]?([^'\"]+)['\"]?",
        "❌ Background task failed: {task_name}",
        LogCategory.ERROR,
        LogSeverity.HIGH
    ),
    (
        r"(?:Task|Job).*queued|Queued.*(?:task|job)",
        "📋 Task added to queue",
        LogCategory.INFO,
        LogSeverity.NORMAL
    ),
    (
        r"(?:Task|Job).*retry.*(\d+)",
        "🔁 Task retrying (attempt {attempt})",
        LogCategory.WARNING,
        LogSeverity.NORMAL
    ),
    
    # ============= TEMPLATE OPERATIONS =============
    (
        r"Template.*created.*['\"]?([^'\"]+)['\"]?",
        "✅ Template created: {name}",
        LogCategory.SUCCESS,
        LogSeverity.NORMAL
    ),
    (
        r"Template.*updated.*['\"]?([^'\"]+)['\"]?",
        "✏️ Template updated: {name}",
        LogCategory.INFO,
        LogSeverity.NORMAL
    ),
    (
        r"Template.*deleted.*['\"]?([^'\"]+)['\"]?",
        "🗑️ Template deleted: {name}",
        LogCategory.INFO,
        LogSeverity.NORMAL
    ),
    (
        r"Template.*approved.*['\"]?([^'\"]+)['\"]?",
        "✅ Template approved: {name}",
        LogCategory.SUCCESS,
        LogSeverity.NORMAL
    ),
    (
        r"Template.*rejected.*['\"]?([^'\"]+)['\"]?",
        "❌ Template rejected: {name}",
        LogCategory.WARNING,
        LogSeverity.NORMAL
    ),
    (
        r"Template.*submitted.*review",
        "📝 Template submitted for review",
        LogCategory.INFO,
        LogSeverity.NORMAL
    ),
    
    # ============= SYSTEM & PERFORMANCE =============
    (
        r"(?:Rate limit|Throttl).*exceeded",
        "⚠️ Rate limit exceeded. Please wait before trying again.",
        LogCategory.WARNING,
        LogSeverity.HIGH
    ),
    (
        r"(?:High|Slow).*latency.*(\d+)\s*(?:ms|seconds?)",
        "⚠️ Slow response detected ({time}). System may be under load.",
        LogCategory.WARNING,
        LogSeverity.NORMAL
    ),
    (
        r"(?:Storage|Disk).*(?:full|limit|exceeded)",
        "⚠️ Storage limit reached. Clean up old data.",
        LogCategory.WARNING,
        LogSeverity.HIGH
    ),
    (
        r"(?:Token|API).*limit.*(?:exceeded|reached)",
        "⚠️ Token/API limit reached.",
        LogCategory.WARNING,
        LogSeverity.HIGH
    ),
    (
        r"(?:Connected|Connection).*(?:established|successful)",
        "🔗 Connection established",
        LogCategory.SUCCESS,
        LogSeverity.NORMAL
    ),
    (
        r"(?:Disconnected|Connection).*(?:lost|failed|closed)",
        "🔌 Connection lost. Reconnecting...",
        LogCategory.WARNING,
        LogSeverity.NORMAL
    ),
    
    # ============= USER OPERATIONS =============
    (
        r"User.*logged in",
        "👋 Welcome! You are now logged in.",
        LogCategory.SUCCESS,
        LogSeverity.NORMAL
    ),
    (
        r"Settings.*(?:updated|saved)",
        "⚙️ Settings saved",
        LogCategory.SUCCESS,
        LogSeverity.NORMAL
    ),
    (
        r"(?:Export|Download).*completed",
        "📥 Export completed",
        LogCategory.SUCCESS,
        LogSeverity.NORMAL
    ),
]


class ActivityLogService:
    """
    Service to transform raw system logs into user-friendly messages.
    
    Usage:
        service = ActivityLogService()
        result = service.transform_log("Starting dataset generation with model=gemma:2b")
        # Returns: {
        #     "humanMessage": "🚀 Dataset generation started using gemma:2b",
        #     "category": "info",
        #     "severity": "normal",
        #     "matched": True
        # }
    """
    
    def __init__(self):
        # Compile patterns for efficiency
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), template, category, severity)
            for pattern, template, category, severity in LOG_PATTERNS
        ]
    
    def transform_log(self, raw_message: str) -> Dict[str, Any]:
        """
        Transform a raw log message into a user-friendly format.
        
        Args:
            raw_message: The original log message from the system
            
        Returns:
            Dict with transformed log data:
            - humanMessage: User-friendly message (or original if no match)
            - category: Log category (info, warning, error, success)
            - severity: Severity level (normal, high, critical)
            - matched: Whether a pattern was matched
        """
        for compiled_pattern, template, category, severity in self.compiled_patterns:
            match = compiled_pattern.search(raw_message)
            if match:
                # Extract captured groups and create human message
                human_message = self._format_message(template, match)
                return {
                    "humanMessage": human_message,
                    "category": category.value,
                    "severity": severity.value,
                    "matched": True
                }
        
        # No pattern matched - return original with inferred category
        inferred_category = self._infer_category(raw_message)
        return {
            "humanMessage": raw_message,
            "category": inferred_category.value,
            "severity": LogSeverity.NORMAL.value,
            "matched": False
        }
    
    def _format_message(self, template: str, match: re.Match) -> str:
        """Format the template with captured groups from regex match."""
        groups = match.groups()
        
        # Map common placeholder names to group indices
        placeholders = {
            "model": 0, "count": 0, "filename": 0, "name": 0,
            "task_name": 0, "attempt": 0, "time": 0,
            "old_model": 0, "new_model": 1
        }
        
        result = template
        for placeholder, default_idx in placeholders.items():
            key = "{" + placeholder + "}"
            if key in result:
                idx = min(default_idx, len(groups) - 1) if groups else -1
                if idx >= 0 and idx < len(groups):
                    result = result.replace(key, str(groups[idx]))
                else:
                    result = result.replace(key, "")
        
        return result
    
    def _infer_category(self, message: str) -> LogCategory:
        """Infer category from message if no pattern matched."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["error", "failed", "exception", "traceback"]):
            return LogCategory.ERROR
        if any(word in message_lower for word in ["warning", "warn", "caution", "slow"]):
            return LogCategory.WARNING
        if any(word in message_lower for word in ["success", "completed", "done", "✅"]):
            return LogCategory.SUCCESS
        
        return LogCategory.INFO
    
    def enhance_log_entry(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance a full log entry dict with user-friendly fields.
        
        Args:
            log_entry: Original log entry with 'message' field
            
        Returns:
            Enhanced log entry with additional fields
        """
        message = log_entry.get("message", "")
        transformation = self.transform_log(message)
        
        # Merge transformation into log entry
        log_entry.update({
            "humanMessage": transformation["humanMessage"],
            "category": transformation["category"],
            "severity": transformation["severity"],
        })
        
        return log_entry


# Global service instance
activity_log_service = ActivityLogService()