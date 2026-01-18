"""
Common Schemas - Shared response models
"""

from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    status_code: int = 400


class MessageResponse(BaseModel):
    """Standard message response"""
    message: str
    success: bool = True


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    features: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
