from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class ParameterSchema(BaseModel):
    name: str = Field(..., description="Name of the parameter")
    type_hint: str = Field(..., description="Data type of the parameter (e.g., str, int, bool)")
    description: str = Field(..., min_length=200, description="Detailed description of the parameter (~200 words)")

class APITemplateCreate(BaseModel):
    api_name: str = Field(..., description="Name of the API")
    description: str = Field(..., min_length=500, description="Detailed description of the API (~500 words)")
    base_url: str = Field(..., description="Base URL or endpoint of the API")
    method: str = Field(..., description="HTTP method, e.g., GET, POST, PUT, DELETE")
    body: List[ParameterSchema] = Field(..., description="List of request body parameters")
    expected_response: str = Field(..., description="Expected JSON or text response format")
    metadata: Optional[Dict[str, str]] = Field(None, description="Optional metadata such as tags, notes, etc.")
