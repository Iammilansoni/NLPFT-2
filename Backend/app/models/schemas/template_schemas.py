"""
Template Schemas - API templates, parameters, expected responses, metadata
Matches: templates, parameters, expected_responses, metadata tables
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from uuid import UUID


# ============= TEMPLATE SCHEMAS =============

class TemplateCreate(BaseModel):
    """Create new API template"""
    api_name: str = Field(..., description="API name")
    description: Optional[str] = Field(None, description="API description")
    base_url: Optional[str] = Field(None, description="Base URL")
    method: Optional[str] = Field(None, description="HTTP method (GET, POST, etc.)")


class TemplateUpdate(BaseModel):
    """Update existing template"""
    api_name: Optional[str] = None
    description: Optional[str] = None
    base_url: Optional[str] = None
    method: Optional[str] = None


class TemplateResponse(BaseModel):
    """Template response"""
    t_id: str = Field(..., alias="template_id")
    user_id: str
    api_name: Optional[str] = None
    description: Optional[str] = None
    base_url: Optional[str] = None
    method: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True


# ============= PARAMETER SCHEMAS =============

class ParameterCreate(BaseModel):
    """Create API parameter"""
    template_id: str = Field(..., alias="t_id")
    name: Optional[str] = Field(None, description="Parameter name")
    type: Optional[str] = Field(None, description="Parameter type")
    description: Optional[str] = Field(None, description="Parameter description")
    
    class Config:
        populate_by_name = True


class ParameterResponse(BaseModel):
    """Parameter response"""
    parameter_id: str
    user_id: str
    template_id: str = Field(..., alias="t_id")
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    
    class Config:
        from_attributes = True
        populate_by_name = True


# ============= EXPECTED RESPONSE SCHEMAS =============

class ExpectedResponseCreate(BaseModel):
    """Create expected response"""
    template_id: str = Field(..., alias="t_id")
    status: Optional[int] = Field(None, description="HTTP status code")
    fields: Optional[Dict[str, Any]] = Field(None, description="Response fields (JSONB)")
    
    class Config:
        populate_by_name = True


class ExpectedResponseResponse(BaseModel):
    """Expected response"""
    response_id: str
    user_id: str
    template_id: str = Field(..., alias="t_id")
    status: Optional[int] = None
    fields: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True
        populate_by_name = True


# ============= METADATA SCHEMAS =============

class MetadataCreate(BaseModel):
    """Create metadata"""
    template_id: str = Field(..., alias="t_id")
    confidence: Optional[float] = Field(None, description="Confidence score")
    remarks: Optional[str] = Field(None, description="Additional remarks")
    
    class Config:
        populate_by_name = True


class MetadataResponse(BaseModel):
    """Metadata response"""
    metadata_id: str
    user_id: str
    template_id: str = Field(..., alias="t_id")
    confidence: Optional[float] = None
    remarks: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True
