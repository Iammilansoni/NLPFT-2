from pydantic import BaseModel,Field
from typing import Dict, List, Any, Optional, Literal

class BodyParameters(BaseModel):
    type: str = Field(..., desciption="Data type of parameter (string, int, float, bool, etc.)")
    description: str = Field(..., min_length=200, description="Detailed explanation (min 200 words)")

class APITemplate(BaseModel):
    api_name: str = Field(..., description="Name of the API")
    description: str = Field(..., min_length=500, description="Detailed description (min 500 words)")
    base_url: str = Field(..., description="Base URL of the API (without endpoint)")
    method: Literal["get", "post", "update", "delete"] = Field(..., description="HTTP method type")
    body: Dict[str, BodyParameters] = Field(..., description="Body parameters with type and description")
    