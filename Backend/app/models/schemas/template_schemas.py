"""
Template Schemas - API templates, parameters, expected responses, metadata
Matches: templates, parameters, expected_responses, metadata tables

✅ ENTERPRISE TEMPLATE BUILDER:
- Strict validation (500+ word descriptions, 3+ samples)
- Approval workflow (draft → review → approved/rejected)
- Security classification (public/internal/secret/highly-restricted)
- Domain tags (telecom, 5g, fft, mimo, encryption, drone, defence, etc.)
- Expert-only approve/reject operations
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, model_validator
from uuid import UUID
from enum import Enum


# ============= ENUMS FOR ENTERPRISE TEMPLATE BUILDER =============

class HTTPMethod(str, Enum):
    """Supported HTTP methods"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class SecurityClassification(str, Enum):
    """Security classification levels for templates"""
    PUBLIC = "public"                      # No restrictions, publicly documented APIs
    INTERNAL = "internal"                  # Internal use only, company-wide
    SECRET = "secret"                      # Restricted access, security clearance required
    HIGHLY_RESTRICTED = "highly-restricted"  # Top secret, highest clearance


class TemplateStatus(str, Enum):
    """Template approval workflow states"""
    DRAFT = "draft"          # Created, editable
    REVIEW = "review"        # Submitted for expert approval, locked
    APPROVED = "approved"    # Expert-approved, can generate datasets
    REJECTED = "rejected"    # Expert-rejected, reverted to draft


class DomainTag(str, Enum):
    """Predefined domain tags for complex APIs"""
    # Telecom & Wireless
    TELECOM = "telecom"
    FIVE_G = "5g"
    FOUR_G = "4g"
    FFT = "fft"
    RF = "rf"
    MIMO = "mimo"
    NETWORK_MANAGEMENT = "network-management"
    SIGNAL_PROCESSING = "signal-processing"
    
    # Defence & Aerospace
    DEFENCE = "defence"
    MILITARY = "military"
    AEROSPACE = "aerospace"
    DRONE = "drone"
    SATELLITE = "satellite"
    RADAR = "radar"
    SONAR = "sonar"
    NAVIGATION = "navigation"
    
    # Security & Encryption
    ENCRYPTION = "encryption"
    CRYPTOGRAPHY = "cryptography"
    AUTHENTICATION = "authentication"
    SECURE_COMMUNICATION = "secure-communication"
    
    # General
    IOT = "iot"
    INDUSTRIAL = "industrial"
    AUTOMOTIVE = "automotive"


# ============= TEMPLATE SCHEMAS (LEGACY - BACKWARD COMPATIBLE) =============

class SampleRequest(BaseModel):
    """Sample request example"""
    query: str = Field(..., description="Sample query text")
    request: Optional[Dict[str, Any]] = Field(None, description="Sample request payload")
    description: Optional[str] = Field(None, description="Description of this sample")
    is_annotated: bool = Field(False, description="Whether this is an annotated mock or real sample")


class TemplateCreate(BaseModel):
    """Create new API template"""
    api_name: str = Field(..., description="API name")
    description: Optional[str] = Field(None, description="API description")
    base_url: Optional[str] = Field(None, description="Base URL")
    method: Optional[str] = Field(None, description="HTTP method (GET, POST, etc.)")
    sample_requests: List[SampleRequest] = Field(
        ..., 
        min_length=1,
        description="Sample requests (minimum 1 required, 3+ recommended)"
    )
    domain_tags: List[str] = Field(
        default_factory=list,
        description="Domain/context tags (e.g., telecom, fft, encryption, internal-only)"
    )


class TemplateUpdate(BaseModel):
    """Update existing template"""
    api_name: Optional[str] = None
    description: Optional[str] = None
    base_url: Optional[str] = None
    method: Optional[str] = None
    sample_requests: Optional[List[SampleRequest]] = Field(
        None,
        min_length=1,
        description="Sample requests (minimum 1 required if provided)"
    )
    domain_tags: Optional[List[str]] = Field(
        None,
        description="Domain/context tags"
    )


class TemplateResponse(BaseModel):
    """Template response"""
    t_id: str = Field(..., alias="template_id")
    user_id: str
    api_name: Optional[str] = None
    description: Optional[str] = None
    base_url: Optional[str] = None
    method: Optional[str] = None
    sample_requests: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Sample requests with examples"
    )
    domain_tags: Optional[List[str]] = Field(
        None,
        description="Domain/context tags"
    )
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


# ============= ENTERPRISE TEMPLATE BUILDER SCHEMAS =============

class ParameterSchema(BaseModel):
    """Parameter schema with strict validation for Template Builder"""
    name: str = Field(..., description="Parameter name (e.g., 'slice_id', 'latency_ms')")
    type: str = Field(..., description="Parameter type (string, integer, float, boolean, array, object)")
    required: bool = Field(..., description="Whether parameter is required")
    example: Any = Field(..., description="Example value for the parameter")
    description: str = Field(..., description="Detailed parameter description")
    
    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Ensure parameter description is meaningful (min 10 chars)"""
        if len(v.strip()) < 10:
            raise ValueError("Parameter description must be at least 10 characters")
        return v.strip()


class EnterpriseTemplateCreate(BaseModel):
    """
    Enterprise Template Builder - Create new template with strict validation
    
    Requirements:
    - Description: 500 words minimum (comprehensive technical documentation)
    - Sample requests: 3+ samples (valid, edge, error scenarios)
    - Parameters: Complete table with examples
    - Domain tags: At least 1 tag
    - Security classification: Required
    - JSON schema: Structured request/response validation
    """
    api_name: str = Field(..., description="API/Template name (e.g., '5G Network Slice Management API')")
    description: str = Field(
        ..., 
        description="Detailed API description (MINIMUM 500 words). Must include: purpose, use cases, technical context, integration details, security considerations, architecture overview, error handling, performance characteristics."
    )
    base_url: str = Field(..., description="Base URL for the API (e.g., 'https://api.telecom.example.com')")
    endpoint: str = Field(..., description="API endpoint path (e.g., '/v1/network-slices')")
    method: HTTPMethod = Field(..., description="HTTP method")
    
    # Structured parameters
    parameters: List[ParameterSchema] = Field(
        ...,
        min_length=1,
        description="Complete parameters table with examples (minimum 1 parameter)"
    )
    
    # Enhanced sample requests with scenarios
    sample_requests: List[Dict[str, Any]] = Field(
        ...,
        min_length=3,
        description="Sample requests (MINIMUM 3: valid, edge, error scenarios)"
    )
    
    sample_responses: List[Dict[str, Any]] = Field(
        ...,
        min_length=3,
        description="Sample responses matching the requests (MINIMUM 3)"
    )
    
    # JSON Schema validation
    json_schema: Optional[Dict[str, Any]] = Field(
        None,
        description="JSON Schema for request validation (optional but recommended)"
    )
    
    response_schema: Optional[Dict[str, Any]] = Field(
        None,
        description="JSON Schema for response validation (optional but recommended)"
    )
    
    # Domain & Security
    domain_tags: List[str] = Field(
        ...,
        min_length=1,
        description="Domain tags (minimum 1 tag: telecom, 5g, fft, mimo, encryption, drone, defence, etc.)"
    )
    
    security_classification: SecurityClassification = Field(
        ...,
        description="Security classification level"
    )
    
    # Additional configurations
    auth_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Authentication configuration (API key, OAuth2, JWT, etc.)"
    )
    
    headers: Optional[Dict[str, str]] = Field(
        None,
        description="Default headers for API requests"
    )
    
    rate_limit: Optional[Dict[str, Any]] = Field(
        None,
        description="Rate limiting configuration"
    )
    
    assertions: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Test assertions to validate responses"
    )
    
    @field_validator("description")
    @classmethod
    def validate_description_length(cls, v: str) -> str:
        """Ensure description is comprehensive (500+ words)"""
        word_count = len(v.split())
        if word_count < 500:
            raise ValueError(
                f"Description must be at least 500 words for comprehensive API documentation. "
                f"Current: {word_count} words. Please provide detailed information including: "
                f"purpose and business context, detailed use cases and scenarios, technical architecture and design, "
                f"integration patterns and dependencies, security considerations and authentication, "
                f"error handling and edge cases, performance characteristics and scalability, "
                f"API versioning and backward compatibility, rate limiting and quotas, monitoring and observability."
            )
        return v
    
    @field_validator("sample_requests")
    @classmethod
    def validate_sample_requests(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure at least 3 sample requests with scenario coverage"""
        if len(v) < 3:
            raise ValueError(
                f"Minimum 3 sample requests required (got {len(v)}). "
                f"Must include: valid scenario, edge case, error case."
            )
        
        # Check for scenario diversity
        scenarios = []
        for sample in v:
            if "scenario" in sample:
                scenarios.append(sample["scenario"])
        
        if scenarios and "valid" not in scenarios:
            raise ValueError(
                "At least one sample request must have scenario='valid' for normal operation testing"
            )
        
        return v
    
    @field_validator("json_schema")
    @classmethod
    def validate_json_schema(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate JSON Schema structure if provided"""
        if v:
            if "type" not in v:
                raise ValueError("JSON Schema must include 'type' field")
            if v.get("type") == "object" and "properties" not in v:
                raise ValueError("JSON Schema with type='object' must include 'properties'")
        return v


class EnterpriseTemplateUpdate(BaseModel):
    """
    Enterprise Template Builder - Update existing template
    Only allowed for templates in 'draft' status
    """
    api_name: Optional[str] = None
    description: Optional[str] = Field(
        None,
        description="Detailed API description (MINIMUM 500 words if provided)"
    )
    base_url: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[HTTPMethod] = None
    parameters: Optional[List[ParameterSchema]] = None
    sample_requests: Optional[List[Dict[str, Any]]] = Field(
        None,
        min_length=3,
        description="Sample requests (MINIMUM 3 if provided)"
    )
    sample_responses: Optional[List[Dict[str, Any]]] = None
    json_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    domain_tags: Optional[List[str]] = Field(
        None,
        min_length=1,
        description="Domain tags (minimum 1 if provided)"
    )
    security_classification: Optional[SecurityClassification] = None
    auth_config: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    rate_limit: Optional[Dict[str, Any]] = None
    assertions: Optional[List[Dict[str, Any]]] = None
    
    @field_validator("description")
    @classmethod
    def validate_description_length(cls, v: Optional[str]) -> Optional[str]:
        """Ensure description is comprehensive if provided"""
        if v:
            word_count = len(v.split())
            if word_count < 500:
                raise ValueError(
                    f"Description must be at least 500 words for comprehensive documentation (got {word_count} words). "
                    f"Please include: purpose, use cases, technical context, integration details, security considerations, "
                    f"architecture overview, error handling, performance characteristics, versioning, and monitoring."
                )
        return v


class EnterpriseTemplateResponse(BaseModel):
    """Enterprise Template Builder - Full template response with all metadata"""
    template_id: str = Field(..., description="Template ID as string")
    user_id: str = Field(..., description="User ID as string")
    api_name: str = Field(..., description="API/Template name")
    description: Optional[str] = None
    base_url: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    parameters: Optional[List[Dict[str, Any]]] = None
    sample_requests: Optional[List[Dict[str, Any]]] = None
    sample_responses: Optional[List[Dict[str, Any]]] = None
    json_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    domain_tags: Optional[List[str]] = None
    security_classification: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    rate_limit: Optional[Dict[str, Any]] = None
    assertions: Optional[List[Dict[str, Any]]] = None
    
    # Metadata fields
    status: Optional[str] = None
    submitted_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[datetime] = None
    expert_notes: Optional[str] = None
    confidence: Optional[float] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TemplateSubmitForReview(BaseModel):
    """Submit template for expert review"""
    template_id: Optional[str] = Field(None, description="Template ID to submit (optional - can be passed in URL)")
    comments: Optional[str] = Field(None, description="Comments for the reviewer")


class TemplateApproveBody(BaseModel):
    """Optional body for approve endpoint"""
    approver_notes: Optional[str] = Field(None, description="Optional notes from approver")
    confidence: Optional[float] = Field(None, ge=0.0, le=100.0, description="Confidence score (0-100)")


class TemplateRejectBody(BaseModel):
    """Optional body for reject endpoint"""
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection")


class TemplateApprove(BaseModel):
    """Approve template (expert only)"""
    template_id: str = Field(..., description="Template ID to approve")
    confidence: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0,
        description="Confidence score (0-100)"
    )
    expert_notes: Optional[str] = Field(
        None,
        description="Expert notes/recommendations"
    )


class TemplateReject(BaseModel):
    """Reject template (expert only)"""
    template_id: str = Field(..., description="Template ID to reject")
    rejection_reason: str = Field(
        ...,
        min_length=20,
        description="Detailed reason for rejection (minimum 20 characters)"
    )
    improvement_suggestions: Optional[str] = Field(
        None,
        description="Suggestions for improvement"
    )


class TemplateApprovalResponse(BaseModel):
    """Response after approval/rejection"""
    template_id: str
    status: str
    message: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[datetime] = None
    timestamp: Optional[datetime] = None
    expert_notes: Optional[str] = None


class TemplateValidationError(BaseModel):
    """Individual validation error"""
    field: str
    error: str
    suggestion: Optional[str] = None


class TemplateValidationResponse(BaseModel):
    """Template validation result"""
    is_valid: bool
    can_generate_dataset: bool = False  # Only true if status='approved'
    errors: List[TemplateValidationError] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class TemplateDraftCreate(BaseModel):
    """
    Draft Template - Relaxed validation for saving work in progress
    
    All fields are optional except api_name.
    Templates saved as drafts can be completed later.
    """
    api_name: str = Field(..., description="API/Template name (required)")
    description: Optional[str] = Field(None, description="API description (can be incomplete)")
    base_url: Optional[str] = Field(None, description="Base URL for the API")
    endpoint: Optional[str] = Field(default="/api", description="API endpoint path")
    method: Optional[HTTPMethod] = Field(default=HTTPMethod.POST, description="HTTP method")
    
    # Parameters - optional for drafts
    parameters: Optional[List[ParameterSchema]] = Field(
        default_factory=list,
        description="Parameters (can be empty for drafts)"
    )
    
    # Sample requests - optional for drafts
    sample_requests: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="Sample requests (can be empty for drafts)"
    )
    
    sample_responses: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="Sample responses (can be empty for drafts)"
    )
    
    # JSON Schema validation - optional
    json_schema: Optional[Dict[str, Any]] = Field(None, description="JSON Schema for request validation")
    response_schema: Optional[Dict[str, Any]] = Field(None, description="JSON Schema for response validation")
    
    # Domain & Security - defaults provided
    domain_tags: Optional[List[str]] = Field(
        default_factory=list,
        description="Domain tags (can be empty for drafts)"
    )
    
    security_classification: Optional[SecurityClassification] = Field(
        default=SecurityClassification.PUBLIC,
        description="Security classification level"
    )
    
    # Additional configurations
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration")
    headers: Optional[Dict[str, str]] = Field(None, description="Default headers")
    rate_limit: Optional[Dict[str, Any]] = Field(None, description="Rate limiting configuration")
    assertions: Optional[List[Dict[str, Any]]] = Field(None, description="Assertions")


class TemplateDraftUpdate(BaseModel):
    """
    Draft Template Update - Relaxed validation for updating work in progress
    
    All fields are optional. No strict validation.
    Templates saved as drafts can be completed later.
    """
    api_name: Optional[str] = Field(None, description="API/Template name")
    description: Optional[str] = Field(None, description="API description (can be incomplete)")
    base_url: Optional[str] = Field(None, description="Base URL for the API")
    endpoint: Optional[str] = Field(None, description="API endpoint path")
    method: Optional[HTTPMethod] = Field(None, description="HTTP method")
    
    # Parameters - no minimum
    parameters: Optional[List[ParameterSchema]] = Field(
        None,
        description="Parameters (can be empty for drafts)"
    )
    
    # Sample requests - no minimum
    sample_requests: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Sample requests (can be empty for drafts)"
    )
    
    sample_responses: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Sample responses (can be empty for drafts)"
    )
    
    # JSON Schema validation - optional
    json_schema: Optional[Dict[str, Any]] = Field(None, description="JSON Schema for request validation")
    response_schema: Optional[Dict[str, Any]] = Field(None, description="JSON Schema for response validation")
    
    # Domain & Security - no minimums
    domain_tags: Optional[List[str]] = Field(
        None,
        description="Domain tags (can be empty for drafts)"
    )
    
    security_classification: Optional[SecurityClassification] = Field(
        None,
        description="Security classification level"
    )
    
    # Additional configurations
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration")
    headers: Optional[Dict[str, str]] = Field(None, description="Default headers")
    rate_limit: Optional[Dict[str, Any]] = Field(None, description="Rate limiting configuration")
    assertions: Optional[List[Dict[str, Any]]] = Field(None, description="Assertions")
