"""
Dataset Schemas - Dataset generation and upload
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class DatasetGenerateRequest(BaseModel):
    """Request to generate dataset"""
    api_name: str = Field(..., description="API name")
    description: str = Field(..., description="API description")
    base_url: str = Field(..., description="Base URL")
    method: str = Field(..., description="HTTP method")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="API parameters")
    num_samples: int = Field(default=10, ge=1, le=100, description="Number of samples to generate")


class UploadResponse(BaseModel):
    """Response for file upload"""
    filename: str
    size: int
    rows_processed: Optional[int] = None
    message: str
    success: bool = True
