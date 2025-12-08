"""
CSV Data Schemas - Test data storage (handles millions of rows)
Matches: csv_data table
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class CSVDataCreate(BaseModel):
    """Create CSV data entry"""
    template_id: str = Field(..., alias="t_id")
    query: Optional[str] = Field(None, description="Query text")
    api_name: Optional[str] = Field(None, description="API name")
    endpoint: Optional[str] = Field(None, description="API endpoint")
    request: Optional[Dict[str, Any]] = Field(None, description="Request data (JSONB)")
    response: Optional[Dict[str, Any]] = Field(None, description="Response data (JSONB)")
    description: Optional[str] = Field(None, description="Description")
    
    class Config:
        populate_by_name = True


class CSVDataUpdate(BaseModel):
    """Update CSV data entry"""
    query: Optional[str] = None
    api_name: Optional[str] = None
    endpoint: Optional[str] = None
    request: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class CSVDataResponse(BaseModel):
    """CSV data response"""
    csv_id: str
    user_id: str
    template_id: str = Field(..., alias="t_id")
    query: Optional[str] = None
    api_name: Optional[str] = None
    endpoint: Optional[str] = None
    request: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True


class CSVDataBulkCreate(BaseModel):
    """Bulk create CSV data entries"""
    template_id: str = Field(..., alias="t_id")
    entries: List[Dict[str, Any]] = Field(..., description="List of CSV data entries")
    
    class Config:
        populate_by_name = True
