"""MongoDB models for dictionary entries and function definitions."""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId for Pydantic compatibility."""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any, *args, **kwargs) -> ObjectId:
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema: Dict[str, Any]) -> Dict[str, Any]:
        # Pydantic v2 replacement for __modify_schema__
        schema.update(type="string")
        return schema
    


class FunctionArgument(BaseModel):
    """Function argument definition."""
    name: str = Field(..., description="Argument name")
    type: str = Field(..., description="Argument type (str, int, bool, etc.)")
    required: bool = Field(True, description="Whether the argument is required")
    default: Optional[Any] = Field(None, description="Default value if not required")
    description: Optional[str] = Field(None, description="Argument description")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra: Dict[str, Any] = {
            "example": {
                "name": "username",
                "type": "str",
                "required": True,
                "description": "User login name"
            }
        }


class DictionaryFunction(BaseModel):
    """Function definition in the dictionary."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., description="Function name/identifier")
    display_name: Optional[str] = Field(None, description="Human-readable function name")
    signature: Dict[str, str] = Field(default_factory=dict, description="Function signature")
    templates: List[str] = Field(default_factory=list, description="Natural language templates")
    examples: List[str] = Field(default_factory=list, description="Usage examples")
    arguments: List[FunctionArgument] = Field(default_factory=list, description="Function arguments")
    category: str = Field("general", description="Function category")
    aliases: List[str] = Field(default_factory=list, description="Alternative names")
    description: Optional[str] = Field(None, description="Function description")
    is_active: bool = Field(True, description="Whether function is active")
    tags: List[str] = Field(default_factory=list, description="Function tags")
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = Field(None, description="Creator user ID")
    updated_by: Optional[str] = Field(None, description="Last updater user ID")
    
    # Usage stats
    usage_count: int = Field(0, description="Number of times function has been used")
    last_used: Optional[datetime] = Field(None, description="Last time function was used")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra: Dict[str, Any] = {
            "example": {
                "name": "login",
                "display_name": "User Login",
                "signature": {"username": "str", "password": "str"},
                "templates": [
                    "login with username {username} and password {password}",
                    "log in as {username} with {password}",
                    "sign in with {username}/{password}"
                ],
                "examples": [
                    "Login with username admin and password secret123",
                    "Log in as testuser with Pa$$w0rd"
                ],
                "arguments": [
                    {"name": "username", "type": "str", "required": True},
                    {"name": "password", "type": "str", "required": True}
                ],
                "category": "authentication",
                "description": "Authenticate user with credentials"
            }
        }


class DictionaryStats(BaseModel):
    """Dictionary statistics."""
    total_functions: int = 0
    active_functions: int = 0
    categories: Dict[str, int] = Field(default_factory=dict)
    most_used_functions: List[Dict[str, Any]] = Field(default_factory=list)
    recent_additions: List[Dict[str, Any]] = Field(default_factory=list)
    last_updated: Optional[datetime] = None
    
    class Config:
        json_schema_extra: Dict[str, Any] = {
            "example": {
                "total_functions": 25,
                "active_functions": 23,
                "categories": {
                    "authentication": 3,
                    "navigation": 8,
                    "forms": 7,
                    "assertions": 7
                },
                "most_used_functions": [
                    {"name": "click", "usage_count": 150},
                    {"name": "login", "usage_count": 89}
                ]
            }
        }


class FunctionUsageLog(BaseModel):
    """Log entry for function usage."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    function_id: PyObjectId = Field(..., description="Function ID")
    function_name: str = Field(..., description="Function name")
    user_input: str = Field(..., description="Original user input")
    matched_template: str = Field(..., description="Template that was matched")
    extracted_args: Dict[str, Any] = Field(default_factory=dict, description="Extracted arguments")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    success: bool = Field(True, description="Whether the match was successful")
    confidence_score: Optional[float] = Field(None, description="Matching confidence score")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}