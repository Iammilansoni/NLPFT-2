"""
Template Builder API - Enterprise-Grade Template Management
Postman-Style Interface with Strict Validation & Approval Workflow

Features:
- Minimum 500 words description (comprehensive technical documentation)
- 3+ sample requests (valid, edge, error cases)
- JSON Schema validation
- Parameters table (name, type, required, example, description)
- Domain tags (telecom, fft, mimo, encryption, drone, defence)
- Approval workflow: draft > review > approved
- Dataset generation ONLY for approved templates
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.logger import logger
from app.core.postgres import get_db
from app.models.database_models import ExpectedResponse, Metadata, Parameter, Template, User
from app.models.schemas.template_schemas import EnterpriseTemplateCreate as TemplateCreate
from app.models.schemas.template_schemas import EnterpriseTemplateResponse as TemplateResponse
from app.models.schemas.template_schemas import EnterpriseTemplateUpdate as TemplateUpdate
from app.models.schemas.template_schemas import (
    TemplateApprovalResponse,
    TemplateApprove,
    TemplateApproveBody,
    TemplateDraftCreate,
    TemplateDraftUpdate,
    TemplateReject,
    TemplateRejectBody,
    TemplateStatus,
    TemplateSubmitForReview,
    TemplateValidationError,
    TemplateValidationResponse,
)
from app.services.audit_service import get_audit_service

# Initialize rate limiter for template operations
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/templates", tags=["Template Builder"])


# --- Helper Functions ---

def validate_uuid(template_id: str) -> UUID:
    """
    Validate and convert string to UUID.
    Raises HTTPException if invalid.
    """
    try:
        return UUID(template_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid template ID format: '{template_id}'. Expected UUID format (e.g., '123e4567-e89b-12d3-a456-426614174000')"
        )


# --- Template CRUD ---

@router.post("/", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")  # Rate limit: 20 template creations per minute per IP
async def create_template(
    template_data: TemplateCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new API template with strict validation
    
    RATE LIMIT: 20 creations per minute per IP
    
    **Requirements:**
    - API name: 3-200 characters
    - Description: 100-5000 characters, MINIMUM 500 words
    - 3+ sample requests (at least 1 valid scenario)
    - 3+ sample responses
    - 1+ parameters with full specifications
    - 1+ domain tags
    - JSON Schema with proper structure
    
    **Template Status:**
    - Starts as 'draft'
    - Can be submitted for 'review'
    - Requires 'approved' status for dataset generation
    
    **Example:** See schema documentation for full FFT API example
    """
    try:
        # Create template in database
        new_template = Template(
            t_id=uuid4(),
            u_id=current_user.u_id,
            api_name=template_data.api_name,
            description=template_data.description,
            base_url=template_data.base_url,
            method=template_data.method.value,
            Field=template_data.endpoint,
            json_schema=template_data.json_schema,
            response_schema=template_data.response_schema,
            sample_requests=template_data.sample_requests,  # Already List[Dict]
            sample_responses=template_data.sample_responses,  # Already List[Dict]
            domain_tags=template_data.domain_tags,  # Already List[str]
            auth_config=template_data.auth_config,
            headers=template_data.headers,
            rate_limit=template_data.rate_limit,
            assertions=template_data.assertions
        )
        
        db.add(new_template)
        
        # Create parameters
        for param in template_data.parameters:
            new_param = Parameter(
                p_id=uuid4(),
                u_id=current_user.u_id,
                t_id=new_template.t_id,
                name=param.name,
                type=param.type,
                required=1 if param.required else 0,
                example=param.example,
                description=param.description
            )
            db.add(new_param)
        
        # Create sample responses as expected_responses
        for idx, sample_resp in enumerate(template_data.sample_responses):
            expected_resp = ExpectedResponse(
                r_id=uuid4(),
                u_id=current_user.u_id,
                t_id=new_template.t_id,
                status=sample_resp.get('status_code', 200),
                fields=sample_resp.get('response_body', sample_resp)
            )
            db.add(expected_resp)
        
        # Create metadata with draft status
        metadata = Metadata(
            m_id=uuid4(),
            u_id=current_user.u_id,
            t_id=new_template.t_id,
            status=TemplateStatus.DRAFT.value,
            expert_notes=None
        )
        
        db.add(metadata)
        
        await db.commit()
        await db.refresh(new_template)
        
        logger.info(f"Template created: {new_template.api_name} (ID: {new_template.t_id}) by user {current_user.u_id}")
        
        # Build response
        response = TemplateResponse(
            template_id=str(new_template.t_id),
            user_id=str(new_template.u_id),
            api_name=new_template.api_name,
            description=new_template.description,
            base_url=new_template.base_url,
            method=new_template.method,
            endpoint=new_template.Field,
            json_schema=new_template.json_schema,
            response_schema=new_template.response_schema,
            sample_requests=new_template.sample_requests,
            sample_responses=new_template.sample_responses,
            parameters=[param.model_dump() for param in template_data.parameters],
            domain_tags=template_data.domain_tags,  # Already List[str]
            expert_notes=None,
            status=TemplateStatus.DRAFT.value,
            auth_config=new_template.auth_config,
            headers=new_template.headers,
            rate_limit=new_template.rate_limit,
            assertions=new_template.assertions,
            created_at=new_template.created_at,
            updated_at=new_template.updated_at
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}"
        )


@router.post("/draft", response_model=TemplateResponse)
async def create_draft_template(
    template_data: TemplateDraftCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a draft template with relaxed validation
    
    This endpoint allows saving incomplete templates as drafts.
    All fields except api_name are optional.
    The template can be completed and submitted for review later.
    
    **Required:** Only `api_name` is required
    **Optional:** All other fields can be empty or partial
    """
    try:
        # Create template with defaults for missing fields
        new_template = Template(
            t_id=uuid4(),
            u_id=current_user.u_id,
            api_name=template_data.api_name,
            description=template_data.description or "",
            base_url=template_data.base_url or "",
            endpoint=template_data.endpoint or "/api",
            method=template_data.method.value if template_data.method else "POST",
            json_schema=template_data.json_schema or {},
            response_schema=template_data.response_schema,
            sample_requests=template_data.sample_requests or [],
            sample_responses=template_data.sample_responses or [],
            domain_tags=template_data.domain_tags or [],
            auth_config=template_data.auth_config,
            headers=template_data.headers,
            rate_limit=template_data.rate_limit,
            assertions=template_data.assertions
        )
        
        db.add(new_template)
        
        # Create parameters if provided
        for param in (template_data.parameters or []):
            new_param = Parameter(
                p_id=uuid4(),
                u_id=current_user.u_id,
                t_id=new_template.t_id,
                name=param.name,
                type=param.type,
                required=1 if param.required else 0,
                example=param.example,
                description=param.description
            )
            db.add(new_param)
        
        # Create sample responses as expected_responses
        for idx, sample_resp in enumerate(template_data.sample_responses or []):
            expected_resp = ExpectedResponse(
                r_id=uuid4(),
                u_id=current_user.u_id,
                t_id=new_template.t_id,
                status=sample_resp.get('status_code', 200),
                fields=sample_resp.get('response_body', sample_resp)
            )
            db.add(expected_resp)
        
        # Create metadata with draft status
        metadata = Metadata(
            m_id=uuid4(),
            u_id=current_user.u_id,
            t_id=new_template.t_id,
            status=TemplateStatus.DRAFT.value,
            expert_notes=None
        )
        
        db.add(metadata)
        
        await db.commit()
        await db.refresh(new_template)
        
        logger.info(f"Draft template created: {new_template.api_name} (ID: {new_template.t_id}) by user {current_user.u_id}")
        
        # Build response
        response = TemplateResponse(
            template_id=str(new_template.t_id),
            user_id=str(new_template.u_id),
            api_name=new_template.api_name,
            description=new_template.description,
            base_url=new_template.base_url,
            method=new_template.method,
            endpoint=new_template.endpoint,
            json_schema=new_template.json_schema,
            response_schema=new_template.response_schema,
            sample_requests=new_template.sample_requests,
            sample_responses=new_template.sample_responses,
            parameters=[p.model_dump() if hasattr(p, 'model_dump') else {'name': p.name, 'type': p.type, 'required': p.required, 'example': p.example, 'description': p.description} for p in (template_data.parameters or [])],
            domain_tags=template_data.domain_tags or [],
            expert_notes=None,
            status=TemplateStatus.DRAFT.value,
            auth_config=new_template.auth_config,
            headers=new_template.headers,
            rate_limit=new_template.rate_limit,
            assertions=new_template.assertions,
            created_at=new_template.created_at,
            updated_at=new_template.updated_at
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error creating draft template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create draft template: {str(e)}"
        )


@router.put("/draft/{template_id}", response_model=TemplateResponse)
async def update_draft_template(
    template_id: str,
    template_data: TemplateDraftUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a draft template with relaxed validation
    
    This endpoint allows updating incomplete templates.
    All fields are optional and there's no strict validation.
    Only works for templates in 'draft' or 'rejected' status.
    """
    try:
        # Get template
        result = await db.execute(
            select(Template).where(
                Template.t_id == UUID(template_id),
                Template.u_id == current_user.u_id
            )
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Check status
        metadata_result = await db.execute(
            select(Metadata).where(Metadata.t_id == template.t_id)
        )
        metadata = metadata_result.scalar_one_or_none()
        
        editable_statuses = [TemplateStatus.DRAFT.value, TemplateStatus.REJECTED.value]
        if metadata and metadata.status not in editable_statuses:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot edit template with status '{metadata.status}'. Only 'draft' or 'rejected' templates can be edited."
            )
        
        # Update fields (all optional)
        if template_data.api_name is not None:
            template.api_name = template_data.api_name
        if template_data.description is not None:
            template.description = template_data.description
        if template_data.base_url is not None:
            template.base_url = template_data.base_url
        if template_data.method is not None:
            template.method = template_data.method.value
        if template_data.endpoint is not None:
            template.endpoint = template_data.endpoint
        if template_data.json_schema is not None:
            template.json_schema = template_data.json_schema
        if template_data.response_schema is not None:
            template.response_schema = template_data.response_schema
        if template_data.sample_requests is not None:
            template.sample_requests = template_data.sample_requests
        if template_data.sample_responses is not None:
            template.sample_responses = template_data.sample_responses
        if template_data.domain_tags is not None:
            template.domain_tags = template_data.domain_tags
        if template_data.auth_config is not None:
            template.auth_config = template_data.auth_config
        if template_data.headers is not None:
            template.headers = template_data.headers
        if template_data.rate_limit is not None:
            template.rate_limit = template_data.rate_limit
        if template_data.assertions is not None:
            template.assertions = template_data.assertions
        
        template.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Update parameters if provided
        if template_data.parameters is not None:
            # Delete existing parameters
            await db.execute(
                delete(Parameter).where(Parameter.t_id == template.t_id)
            )
            
            # Create new parameters
            for param in template_data.parameters:
                new_param = Parameter(
                    p_id=uuid4(),
                    u_id=current_user.u_id,
                    t_id=template.t_id,
                    name=param.name,
                    type=param.type,
                    required=1 if param.required else 0,
                    example=param.example,
                    description=param.description
                )
                db.add(new_param)
        
        await db.commit()
        await db.refresh(template)
        
        logger.info(f"Draft template updated: {template.api_name} (ID: {template.t_id}) by user {current_user.u_id}")
        
        # Get updated parameters
        params_result = await db.execute(
            select(Parameter).where(Parameter.t_id == template.t_id)
        )
        params = params_result.scalars().all()
        
        # Build response
        response = TemplateResponse(
            template_id=str(template.t_id),
            user_id=str(template.u_id),
            api_name=template.api_name,
            description=template.description,
            base_url=template.base_url,
            method=template.method,
            endpoint=template.endpoint,
            json_schema=template.json_schema,
            response_schema=template.response_schema,
            sample_requests=template.sample_requests,
            sample_responses=template.sample_responses,
            parameters=[{
                "name": p.name,
                "type": p.type,
                "required": bool(p.required),
                "example": p.example,
                "description": p.description
            } for p in params],
            domain_tags=template.domain_tags or [],
            expert_notes=metadata.expert_notes if metadata else None,
            status=metadata.status if metadata else "draft",
            auth_config=template.auth_config,
            headers=template.headers,
            rate_limit=template.rate_limit,
            assertions=template.assertions,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating draft template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update draft template: {str(e)}"
        )


@router.get("/", response_model=List[TemplateResponse])
async def list_templates(
    status_filter: Optional[str] = None,
    domain_tag: Optional[str] = None,
    security_level: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all templates for current user with optional filters
    
    **Filters:**
    - `status_filter`: draft, review, approved, rejected
    - `domain_tag`: telecom, fft, encryption, drone, etc.
    - `security_level`: public, internal, secret, highly-restricted
    - `skip`: Pagination offset
    - `limit`: Max results (default 100)
    """
    try:
        # Multi-tenant isolation: every query is scoped strictly to the
        # authenticated user — users can NEVER see another user's templates.
        if status_filter:
            # INNER JOIN with explicit condition (matches pattern used in stats endpoint)
            # Only return templates whose Metadata.status matches the filter
            query = (
                select(Template)
                .join(Metadata, Template.t_id == Metadata.t_id)
                .where(
                    Template.u_id == current_user.u_id,
                    Metadata.status == status_filter
                )
            )
        else:
            # No status filter — return all of the user's templates
            query = select(Template).where(Template.u_id == current_user.u_id)

        # Add pagination
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        templates = result.scalars().all()
        
        # Build responses
        responses = []
        for template in templates:
            # Get metadata
            metadata_result = await db.execute(
                select(Metadata).where(Metadata.t_id == template.t_id)
            )
            metadata = metadata_result.scalar_one_or_none()
            
            # Get parameters
            params_result = await db.execute(
                select(Parameter).where(Parameter.t_id == template.t_id)
            )
            params = params_result.scalars().all()
            
            # Apply domain_tag filter
            if domain_tag and domain_tag not in (template.domain_tags or []):
                continue
            
            response = TemplateResponse(
                template_id=str(template.t_id),
                user_id=str(template.u_id),
                api_name=template.api_name,
                description=template.description,
                base_url=template.base_url,
                method=template.method,
                endpoint=template.Field,
                json_schema=template.json_schema,
                response_schema=template.response_schema,
                sample_requests=template.sample_requests or [],
                sample_responses=template.sample_responses or [],
                parameters=[{
                    "name": p.name,
                    "type": p.type,
                    "required": bool(p.required),
                    "example": p.example,
                    "description": p.description
                } for p in params],
                domain_tags=template.domain_tags or [],
                expert_notes=metadata.expert_notes if metadata else None,
                status=metadata.status if metadata else "draft",
                auth_config=template.auth_config,
                headers=template.headers,
                rate_limit=template.rate_limit,
                assertions=template.assertions,
                created_at=template.created_at,
                updated_at=template.updated_at
            )
            responses.append(response)
        
        return responses
        
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list templates: {str(e)}"
        )


@router.get("/stats")
async def get_template_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics about templates
    
    Returns:
        Template statistics including counts by status and domain tags
    """
    try:
        # Get total count - use UUID directly
        user_id = current_user.u_id
        total_result = await db.execute(
            select(Template).where(Template.u_id == user_id)
        )
        total = len(total_result.scalars().all())
        
        # Get counts by status - join with Metadata since status is stored there
        draft_result = await db.execute(
            select(Template).join(Metadata, Template.t_id == Metadata.t_id).where(
                Template.u_id == user_id,
                Metadata.status == TemplateStatus.DRAFT.value
            )
        )
        draft_count = len(draft_result.scalars().all())
        
        review_result = await db.execute(
            select(Template).join(Metadata, Template.t_id == Metadata.t_id).where(
                Template.u_id == user_id,
                Metadata.status == TemplateStatus.REVIEW.value
            )
        )
        review_count = len(review_result.scalars().all())
        
        approved_result = await db.execute(
            select(Template).join(Metadata, Template.t_id == Metadata.t_id).where(
                Template.u_id == user_id,
                Metadata.status == TemplateStatus.APPROVED.value
            )
        )
        approved_count = len(approved_result.scalars().all())
        
        rejected_result = await db.execute(
            select(Template).join(Metadata, Template.t_id == Metadata.t_id).where(
                Template.u_id == user_id,
                Metadata.status == TemplateStatus.REJECTED.value
            )
        )
        rejected_count = len(rejected_result.scalars().all())
        
        return {
            "total_templates": total,
            "by_status": {
                "draft": draft_count,
                "review": review_count,
                "approved": approved_count,
                "rejected": rejected_count
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting template stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template stats: {str(e)}"
        )


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get template by ID"""
    try:
        # Validate UUID format
        validated_id = validate_uuid(template_id)
        
        result = await db.execute(
            select(Template).where(
                Template.t_id == validated_id,
                Template.u_id == current_user.u_id
            )
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Get metadata
        metadata_result = await db.execute(
            select(Metadata).where(Metadata.t_id == template.t_id)
        )
        metadata = metadata_result.scalar_one_or_none()
        
        # Get parameters
        params_result = await db.execute(
            select(Parameter).where(Parameter.t_id == template.t_id)
        )
        params = params_result.scalars().all()
        
        response = TemplateResponse(
            template_id=str(template.t_id),
            user_id=str(template.u_id),
            api_name=template.api_name,
            description=template.description,
            base_url=template.base_url,
            method=template.method,
            endpoint=template.Field,
            json_schema=template.json_schema,
            response_schema=template.response_schema,
            sample_requests=template.sample_requests or [],
            sample_responses=template.sample_responses or [],
            parameters=[{
                "name": p.name,
                "type": p.type,
                "required": bool(p.required),
                "example": p.example,
                "description": p.description
            } for p in params],
            domain_tags=template.domain_tags or [],
            expert_notes=metadata.expert_notes if metadata else None,
            status=metadata.status if metadata else "draft",
            auth_config=template.auth_config,
            headers=template.headers,
            rate_limit=template.rate_limit,
            assertions=template.assertions,
            created_at=template.created_at,
            updated_at=template.updated_at
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template: {str(e)}"
        )


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    template_data: TemplateUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update existing template (draft or rejected status only)
    
    Templates can only be edited while in 'draft' or 'rejected' status.
    Once submitted for review or approved, create a new version instead.
    """
    try:
        # Get template
        result = await db.execute(
            select(Template).where(
                Template.t_id == UUID(template_id),
                Template.u_id == current_user.u_id
            )
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Check status - allow editing for both draft and rejected templates
        metadata_result = await db.execute(
            select(Metadata).where(Metadata.t_id == template.t_id)
        )
        metadata = metadata_result.scalar_one_or_none()
        
        editable_statuses = [TemplateStatus.DRAFT.value, TemplateStatus.REJECTED.value]
        if metadata and metadata.status not in editable_statuses:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot edit template with status '{metadata.status}'. Only 'draft' or 'rejected' templates can be edited."
            )
        
        # Update fields
        if template_data.api_name:
            template.api_name = template_data.api_name
        if template_data.description:
            template.description = template_data.description
        if template_data.base_url:
            template.base_url = template_data.base_url
        if template_data.method:
            template.method = template_data.method.value
        if template_data.endpoint:
            template.endpoint = template_data.endpoint
        if template_data.json_schema:
            template.json_schema = template_data.json_schema
        if template_data.response_schema is not None:
            template.response_schema = template_data.response_schema
        if template_data.sample_requests:
            # sample_requests is already List[Dict], no need for model_dump
            template.sample_requests = template_data.sample_requests
        if template_data.sample_responses:
            # sample_responses is already List[Dict], no need for model_dump
            template.sample_responses = template_data.sample_responses
        if template_data.domain_tags:
            # domain_tags is already List[str], no enum conversion needed
            template.domain_tags = template_data.domain_tags
        if template_data.auth_config is not None:
            template.auth_config = template_data.auth_config
        if template_data.headers is not None:
            template.headers = template_data.headers
        if template_data.rate_limit is not None:
            template.rate_limit = template_data.rate_limit
        if template_data.assertions is not None:
            template.assertions = template_data.assertions
        
        template.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Update parameters if provided
        if template_data.parameters:
            # Delete old parameters
            await db.execute(delete(Parameter).where(Parameter.t_id == template.t_id))
            
            # Create new parameters
            for param in template_data.parameters:
                new_param = Parameter(
                    p_id=uuid4(),
                    u_id=current_user.u_id,
                    t_id=template.t_id,
                    name=param.name,
                    type=param.type,
                    required=1 if param.required else 0,
                    example=param.example,
                    description=param.description
                )
                db.add(new_param)
        
        await db.commit()
        await db.refresh(template)
        
        logger.info(f"Template updated: {template.api_name} (ID: {template.t_id})")
        
        # Audit log
        audit_service = get_audit_service()
        changes = {}
        if template_data.api_name:
            changes["api_name"] = {"new": template_data.api_name}
        if template_data.description:
            changes["description"] = {"updated": True}
        if template_data.domain_tags:
            changes["domain_tags"] = {"new": template_data.domain_tags}
        
        await audit_service.log_template_updated(
            db=db,
            user_id=current_user.u_id,
            template_id=template.t_id,
            changes=changes,
            request=request
        )
        
        # Return updated template
        return await get_template(template_id, db, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update template: {str(e)}"
        )


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete template (draft status only)
    
    Only templates in 'draft' status can be deleted.
    Approved templates are archived instead.
    """
    try:
        # Get template
        result = await db.execute(
            select(Template).where(
                Template.t_id == UUID(template_id),
                Template.u_id == current_user.u_id
            )
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Check status
        metadata_result = await db.execute(
            select(Metadata).where(Metadata.t_id == template.t_id)
        )
        metadata = metadata_result.scalar_one_or_none()
        
        if metadata and metadata.status != TemplateStatus.DRAFT.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot delete template with status '{metadata.status}'. Only 'draft' templates can be deleted."
            )
        
        # Audit log before deletion
        audit_service = get_audit_service()
        template_name = template.api_name
        template_id_for_log = template.t_id
        
        # Delete template (cascade will delete related records)
        await db.delete(template)
        await db.commit()
        
        logger.info(f"Template deleted: {template_name} (ID: {template_id_for_log})")
        
        # Audit log after successful deletion
        await audit_service.log_template_deleted(
            db=db,
            user_id=current_user.u_id,
            template_id=template_id_for_log,
            template_name=template_name,
            request=request
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete template: {str(e)}"
        )


# --- Internal Validation Helper ---

async def _validate_template_internal(template_id: str, db: AsyncSession, current_user: User) -> TemplateValidationResponse:
    """
    Internal validation function for template submission.
    Checks all strict requirements before allowing submission for review.
    """
    # Get template
    template = await get_template(template_id, db, current_user)
    
    errors = []
    warnings = []
    
    # Check description word count (500+ words requirement)
    word_count = len(template.description.split()) if template.description else 0
    if word_count < 500:
        errors.append(TemplateValidationError(
            field="description",
            error=f"Description has only {word_count} words (minimum 500 required)",
            suggestion="Add comprehensive details about the API"
        ))
    
    # Check sample requests
    sample_requests = template.sample_requests or []
    if len(sample_requests) < 3:
        errors.append(TemplateValidationError(
            field="sample_requests",
            error=f"Only {len(sample_requests)} sample requests (minimum 3 required)",
            suggestion="Add at least 3 samples: 1 valid, 1 edge case, 1 error case"
        ))
    
    # Check sample responses
    sample_responses = template.sample_responses or []
    if len(sample_responses) < 3:
        errors.append(TemplateValidationError(
            field="sample_responses",
            error=f"Only {len(sample_responses)} sample responses (minimum 3 required)",
            suggestion="Add expected responses matching your sample requests"
        ))
    
    # Check parameters
    parameters = template.parameters or []
    if len(parameters) < 1:
        errors.append(TemplateValidationError(
            field="parameters",
            error="No parameters defined (minimum 1 required)",
            suggestion="Add parameter table with: name, type, required, example, description"
        ))
    
    # Check domain tags
    domain_tags = template.domain_tags or []
    if len(domain_tags) < 1:
        errors.append(TemplateValidationError(
            field="domain_tags",
            error="No domain tags specified (minimum 1 required)",
            suggestion="Add relevant tags: telecom, fft, encryption, drone, etc."
        ))
    
    # Check JSON Schema
    json_schema = template.json_schema or {}
    if not json_schema.get("type"):
        errors.append(TemplateValidationError(
            field="json_schema",
            error="JSON Schema missing 'type' field",
            suggestion="Add 'type' field (e.g., 'object', 'array')"
        ))
    
    is_valid = len(errors) == 0
    
    return TemplateValidationResponse(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        can_generate_dataset=False  # Can't generate until approved
    )


# ============= APPROVAL WORKFLOW =============

@router.post("/{template_id}/submit", response_model=TemplateApprovalResponse)
@limiter.limit("30/minute")  # Rate limit: 30 submissions per minute per IP
async def submit_template_for_review(
    template_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit template for expert review (simplified endpoint)
    
    RATE LIMIT: 30 submissions per minute per IP
    
    Changes status from 'draft' or 'rejected' to 'review'.
    Template cannot be edited while in review.
    """
    try:
        # Get template to verify ownership
        template_result = await db.execute(
            select(Template).where(
                Template.t_id == UUID(template_id),
                Template.u_id == current_user.u_id
            )
        )
        template = template_result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or access denied"
            )
        
        # Validate template with strict requirements
        validation = await _validate_template_internal(template_id, db, current_user)
        
        if not validation.is_valid:
            # Build readable error message
            error_messages = [f"• {err.field}: {err.error}" for err in validation.errors]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Template validation failed. Please fix the following issues:",
                    "errors": error_messages,
                    "warnings": validation.warnings
                }
            )
        
        # Get metadata
        metadata_result = await db.execute(
            select(Metadata).where(Metadata.t_id == UUID(template_id))
        )
        metadata = metadata_result.scalar_one_or_none()
        
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template metadata not found"
            )
        
        if metadata.status not in [TemplateStatus.DRAFT.value, TemplateStatus.REJECTED.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot submit template with status '{metadata.status}'. Only 'draft' or 'rejected' templates can be submitted."
            )
        
        # Update status
        metadata.status = TemplateStatus.REVIEW.value
        metadata.submitted_at = datetime.now(timezone.utc)
        metadata.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        
        logger.info(f"Template submitted for review: {template_id} by user {current_user.u_id}")
        
        # Audit log
        audit_service = get_audit_service()
        await audit_service.log_template_submitted_for_review(
            db=db,
            user_id=current_user.u_id,
            template_id=UUID(template_id),
            template_name=template.api_name,
            request=request
        )
        
        return TemplateApprovalResponse(
            template_id=template_id,
            status=TemplateStatus.REVIEW.value,
            message="Template submitted for expert review",
            timestamp=datetime.now(timezone.utc)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting template for review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit template: {str(e)}"
        )


@router.post("/{template_id}/submit-review", response_model=TemplateApprovalResponse)
async def submit_for_review(
    template_id: str,
    submission_data: TemplateSubmitForReview,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit template for expert review
    
    Changes status from 'draft' to 'review'.
    Template cannot be edited while in review.
    """
    try:
        # Validate template
        validation = await validate_template(template_id, db, current_user)
        
        if not validation.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Template validation failed",
                    "errors": [err.model_dump() for err in validation.errors],
                    "warnings": validation.warnings
                }
            )
        
        # Get metadata
        metadata_result = await db.execute(
            select(Metadata).where(Metadata.t_id == UUID(template_id))
        )
        metadata = metadata_result.scalar_one_or_none()
        
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template metadata not found"
            )
        
        if metadata.status != TemplateStatus.DRAFT.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template already in '{metadata.status}' status. Only 'draft' templates can be submitted."
            )
        
        # Update status
        metadata.status = TemplateStatus.REVIEW.value
        metadata.submitted_at = datetime.now(timezone.utc)
        metadata.updated_at = datetime.now(timezone.utc)
        
        if submission_data.comments:
            metadata.remarks = submission_data.comments
        
        await db.commit()
        
        logger.info(f"Template submitted for review: {template_id} by user {current_user.u_id}")
        
        # Audit log
        audit_service = get_audit_service()
        template_result = await db.execute(select(Template).where(Template.t_id == UUID(template_id)))
        template = template_result.scalar_one_or_none()
        await audit_service.log_template_submitted_for_review(
            db=db,
            user_id=current_user.u_id,
            template_id=UUID(template_id),
            template_name=template.api_name if template else "Unknown",
            request=request
        )
        
        return TemplateApprovalResponse(
            template_id=template_id,
            status=TemplateStatus.REVIEW.value,
            message="Template submitted for expert review",
            timestamp=datetime.now(timezone.utc)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting template for review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit template: {str(e)}"
        )


@router.post("/{template_id}/approve", response_model=TemplateApprovalResponse)
@limiter.limit("50/minute")  # Rate limit: 50 approvals per minute per IP
async def approve_template_by_id(
    template_id: str,
    request: Request,
    approval_body: Optional[TemplateApproveBody] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve template (Expert users only - simplified endpoint)
    
    RATE LIMIT: 50 approvals per minute per IP
    
    Changes status from 'review' to 'approved'.
    Only approved templates can generate datasets.
    
    **Requires:** User must have `is_expert=True`
    """
    try:
        # Check if user is expert
        if not current_user.is_expert:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only expert users can approve templates"
            )
        
        # Get metadata
        metadata_result = await db.execute(
            select(Metadata).where(Metadata.t_id == UUID(template_id))
        )
        metadata = metadata_result.scalar_one_or_none()
        
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        if metadata.status != TemplateStatus.REVIEW.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template must be in 'review' status. Current status: '{metadata.status}'"
            )
        
        # Approve template
        metadata.status = TemplateStatus.APPROVED.value
        metadata.approved_by = current_user.u_id
        metadata.approved_at = datetime.now(timezone.utc)
        metadata.updated_at = datetime.now(timezone.utc)

        await db.commit()

        logger.info(f"Template approved: {template_id} by expert {current_user.u_id}")

        # Audit log
        audit_service = get_audit_service()
        template_result = await db.execute(select(Template).where(Template.t_id == UUID(template_id)))
        template = template_result.scalar_one_or_none()
        await audit_service.log_template_approved(
            db=db,
            user_id=metadata.u_id,
            template_id=UUID(template_id),
            template_name=template.api_name if template else "Unknown",
            approver_id=current_user.u_id,
            request=request
        )

        return TemplateApprovalResponse(
            template_id=template_id,
            status=TemplateStatus.APPROVED.value,
            message="Template approved for dataset generation",
            approved_by=str(current_user.u_id),
            timestamp=datetime.now(timezone.utc)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve template: {str(e)}"
        )


@router.post("/approve", response_model=TemplateApprovalResponse)
async def approve_template(
    approval_data: TemplateApprove,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve template (Expert users only - legacy endpoint with body)
    
    Changes status from 'review' to 'approved'.
    Only approved templates can generate datasets.
    
    **Requires:** User must have `is_expert=True`
    **Deprecated:** Use POST /{template_id}/approve instead
    """
    try:
        # Check if user is expert
        if not current_user.is_expert:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only expert users can approve templates"
            )
        
        # Get metadata
        metadata_result = await db.execute(
            select(Metadata).where(Metadata.t_id == UUID(approval_data.template_id))
        )
        metadata = metadata_result.scalar_one_or_none()
        
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        if metadata.status != TemplateStatus.REVIEW.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template must be in 'review' status. Current status: '{metadata.status}'"
            )
        
        # Approve template
        metadata.status = TemplateStatus.APPROVED.value
        metadata.confidence = approval_data.confidence
        metadata.expert_notes = approval_data.expert_notes
        metadata.approved_by = current_user.u_id
        metadata.approved_at = datetime.now(timezone.utc)
        metadata.updated_at = datetime.now(timezone.utc)

        await db.commit()

        logger.info(f"Template approved: {approval_data.template_id} by expert {current_user.u_id}")
        
        # Audit log
        audit_service = get_audit_service()
        template_result = await db.execute(select(Template).where(Template.t_id == UUID(approval_data.template_id)))
        template = template_result.scalar_one_or_none()
        await audit_service.log_template_approved(
            db=db,
            user_id=metadata.u_id,
            template_id=UUID(approval_data.template_id),
            template_name=template.api_name if template else "Unknown",
            approver_id=current_user.u_id,
            request=request
        )
        
        return TemplateApprovalResponse(
            template_id=approval_data.template_id,
            status=TemplateStatus.APPROVED.value,
            message="Template approved for dataset generation",
            approved_by=str(current_user.u_id),
            timestamp=datetime.now(timezone.utc)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve template: {str(e)}"
        )


@router.post("/{template_id}/reject", response_model=TemplateApprovalResponse)
async def reject_template_by_id(
    template_id: str,
    request: Request,
    rejection_body: Optional[TemplateRejectBody] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reject template (Expert users only - simplified endpoint)
    
    Changes status from 'review' to 'rejected'.
    Template can be revised and re-submitted.
    
    **Requires:** User must have `is_expert=True`
    """
    try:
        # Check if user is expert
        if not current_user.is_expert:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only expert users can reject templates"
            )
        
        # Get metadata
        metadata_result = await db.execute(
            select(Metadata).where(Metadata.t_id == UUID(template_id))
        )
        metadata = metadata_result.scalar_one_or_none()
        
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        if metadata.status != TemplateStatus.REVIEW.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template must be in 'review' status. Current status: '{metadata.status}'"
            )
        
        # Get rejection reason from body if provided
        rejection_reason = "Template requires revision"
        if rejection_body and rejection_body.rejection_reason:
            rejection_reason = rejection_body.rejection_reason
        
        # Reject template
        metadata.status = TemplateStatus.REJECTED.value
        metadata.remarks = f"REJECTED: {rejection_reason}"
        metadata.rejected_by = current_user.u_id
        metadata.rejected_at = datetime.now(timezone.utc)
        metadata.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        
        logger.info(f"Template rejected: {template_id} by expert {current_user.u_id}")
        
        # Audit log
        audit_service = get_audit_service()
        template_result = await db.execute(select(Template).where(Template.t_id == UUID(template_id)))
        template = template_result.scalar_one_or_none()
        await audit_service.log_template_rejected(
            db=db,
            user_id=metadata.u_id,
            template_id=UUID(template_id),
            template_name=template.api_name if template else "Unknown",
            rejector_id=current_user.u_id,
            reason=rejection_reason,
            request=request
        )
        
        return TemplateApprovalResponse(
            template_id=template_id,
            status=TemplateStatus.REJECTED.value,
            message=f"Template rejected - {rejection_reason}",
            rejected_by=str(current_user.u_id),
            timestamp=datetime.now(timezone.utc)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject template: {str(e)}"
        )


@router.post("/reject", response_model=TemplateApprovalResponse)
async def reject_template(
    rejection_data: TemplateReject,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reject template with reasons (Expert users only - legacy endpoint with body)
    
    Changes status from 'review' to 'rejected'.
    Template can be revised and re-submitted.
    
    **Requires:** User must have `is_expert=True`
    **Deprecated:** Use POST /{template_id}/reject instead
    """
    try:
        # Check if user is expert
        if not current_user.is_expert:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only expert users can reject templates"
            )
        
        # Get metadata
        metadata_result = await db.execute(
            select(Metadata).where(Metadata.t_id == UUID(rejection_data.template_id))
        )
        metadata = metadata_result.scalar_one_or_none()
        
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        if metadata.status != TemplateStatus.REVIEW.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template must be in 'review' status. Current status: '{metadata.status}'"
            )
        
        # Reject template
        metadata.status = TemplateStatus.REJECTED.value
        metadata.remarks = f"REJECTED: {rejection_data.rejection_reason}"
        if rejection_data.improvement_suggestions:
            metadata.expert_notes = rejection_data.improvement_suggestions
        metadata.rejected_by = current_user.u_id
        metadata.rejected_at = datetime.now(timezone.utc)
        metadata.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        
        logger.info(f"Template rejected: {rejection_data.template_id} by expert {current_user.u_id}")
        
        # Audit log
        audit_service = get_audit_service()
        template_result = await db.execute(select(Template).where(Template.t_id == UUID(rejection_data.template_id)))
        template = template_result.scalar_one_or_none()
        await audit_service.log_template_rejected(
            db=db,
            user_id=metadata.u_id,
            template_id=UUID(rejection_data.template_id),
            template_name=template.api_name if template else "Unknown",
            rejector_id=current_user.u_id,
            reason=rejection_data.rejection_reason,
            request=request
        )
        
        return TemplateApprovalResponse(
            template_id=rejection_data.template_id,
            status=TemplateStatus.REJECTED.value,
            message=f"Template rejected: {rejection_data.rejection_reason}",
            rejected_by=str(current_user.u_id),
            timestamp=datetime.now(timezone.utc)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject template: {str(e)}"
        )


@router.post("/{template_id}/disable", response_model=TemplateApprovalResponse)
async def disable_template(
    template_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Disable an approved template (Expert users only)
    
    Changes status from 'approved' to 'draft', making it unavailable 
    for dataset generation until re-approved.
    
    **Requires:** User must have `is_expert=True`
    """
    try:
        # Check if user is expert
        if not current_user.is_expert:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only expert users can disable templates"
            )
        
        # Get metadata
        metadata_result = await db.execute(
            select(Metadata).where(Metadata.t_id == UUID(template_id))
        )
        metadata = metadata_result.scalar_one_or_none()
        
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        if metadata.status != TemplateStatus.APPROVED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template must be in 'approved' status to disable. Current status: '{metadata.status}'"
            )
        
        # Disable template (revert to draft)
        metadata.status = TemplateStatus.DRAFT.value
        metadata.remarks = f"DISABLED: Template disabled by expert on {datetime.now(timezone.utc).isoformat()}"
        metadata.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        
        logger.info(f"Template disabled: {template_id} by expert {current_user.u_id}")
        
        # Audit log
        audit_service = get_audit_service()
        template_result = await db.execute(select(Template).where(Template.t_id == UUID(template_id)))
        template = template_result.scalar_one_or_none()
        await audit_service.log_action(
            db=db,
            action="template_disabled",
            user_id=current_user.u_id,
            resource_type="template",
            resource_id=template_id,
            details=f"Template '{template.api_name if template else 'Unknown'}' disabled by expert",
            request=request
        )
        
        return TemplateApprovalResponse(
            template_id=template_id,
            status=TemplateStatus.DRAFT.value,
            message="Template disabled - reverted to draft status",
            rejected_by=str(current_user.u_id),
            timestamp=datetime.now(timezone.utc)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable template: {str(e)}"
        )


@router.post("/{template_id}/enable", response_model=TemplateApprovalResponse)
async def enable_template(
    template_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Re-enable a disabled template (sets status back to approved)
    
    This allows templates that were previously approved and then disabled
    to be re-enabled without going through the full review process again.
    
    **Requires:** User must have `is_expert=True`
    """
    try:
        # Check if user is expert
        if not current_user.is_expert:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only expert users can enable templates"
            )
        
        # Get metadata
        metadata_result = await db.execute(
            select(Metadata).where(Metadata.t_id == UUID(template_id))
        )
        metadata = metadata_result.scalar_one_or_none()
        
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Check if template was previously approved (look for DISABLED in remarks)
        if metadata.status != TemplateStatus.DRAFT.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template must be in 'draft' status to enable. Current status: '{metadata.status}'"
            )
        
        # Enable template (set back to approved)
        metadata.status = TemplateStatus.APPROVED.value
        metadata.remarks = f"ENABLED: Template re-enabled by expert on {datetime.now(timezone.utc).isoformat()}"
        metadata.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        
        logger.info(f"Template enabled: {template_id} by expert {current_user.u_id}")
        
        # Audit log
        audit_service = get_audit_service()
        template_result = await db.execute(select(Template).where(Template.t_id == UUID(template_id)))
        template = template_result.scalar_one_or_none()
        await audit_service.log_action(
            db=db,
            action="template_enabled",
            user_id=current_user.u_id,
            resource_type="template",
            resource_id=template_id,
            details=f"Template '{template.api_name if template else 'Unknown'}' re-enabled by expert",
            request=request
        )
        
        return TemplateApprovalResponse(
            template_id=template_id,
            status=TemplateStatus.APPROVED.value,
            message="Template enabled - now available for dataset generation",
            approved_by=str(current_user.u_id),
            timestamp=datetime.now(timezone.utc)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable template: {str(e)}"
        )


@router.post("/{template_id}/toggle-visibility", response_model=TemplateApprovalResponse)
async def toggle_template_visibility(
    template_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Toggle template visibility for dataset generation (Simple ON/OFF)
    
    - ON (approved): Template visible in dataset page, can generate datasets
    - OFF (draft): Template hidden from dataset page, cannot generate datasets
    
    This is a simplified workflow that replaces the submit/review/approve process.
    User can directly toggle their own templates without expert approval.
    """
    try:
        # Validate UUID format
        validated_id = validate_uuid(template_id)
        
        # Get template to verify ownership
        template_result = await db.execute(
            select(Template).where(
                Template.t_id == validated_id,
                Template.u_id == current_user.u_id
            )
        )
        template = template_result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or access denied"
            )
        
        # Get metadata
        metadata_result = await db.execute(
            select(Metadata).where(Metadata.t_id == validated_id)
        )
        metadata = metadata_result.scalar_one_or_none()
        
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template metadata not found"
            )
        
        # Toggle status: draft <-> approved
        if metadata.status == TemplateStatus.APPROVED.value:
            # Turn OFF - hide from dataset page
            metadata.status = TemplateStatus.DRAFT.value
            new_status = TemplateStatus.DRAFT.value
            message = "Template hidden from dataset page"
            action = "template_visibility_off"
        else:
            # Turn ON - show in dataset page (from draft, rejected, or review)
            metadata.status = TemplateStatus.APPROVED.value
            metadata.approved_by = current_user.u_id
            metadata.approved_at = datetime.now(timezone.utc).replace(tzinfo=None)
            new_status = TemplateStatus.APPROVED.value
            message = "Template now visible in dataset page"
            action = "template_visibility_on"
        
        metadata.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await db.commit()
        
        logger.info(f"Template visibility toggled: {template_id} -> {new_status} by user {current_user.u_id}")
        
        # Audit log
        audit_service = get_audit_service()
        await audit_service.log_action(
            db=db,
            action=action,
            user_id=current_user.u_id,
            resource_type="template",
            resource_id=validated_id,
            metadata_={"details": f"Template '{template.api_name}' visibility set to {'ON' if new_status == 'approved' else 'OFF'}"},
            request=request
        )
        
        return TemplateApprovalResponse(
            template_id=template_id,
            status=new_status,
            message=message,
            approved_by=str(current_user.u_id) if new_status == TemplateStatus.APPROVED.value else None,
            timestamp=datetime.now(timezone.utc)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling template visibility: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle template visibility: {str(e)}"
        )


# ============= VALIDATION =============

@router.get("/{template_id}/validate", response_model=TemplateValidationResponse)
async def validate_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate template against all requirements
    
    Checks:
    - Description word count (500+ words for comprehensive documentation)
    - Sample requests count (3+ required)
    - Sample responses count (3+ required)
    - Parameters count (1+ required)
    - Domain tags count (1+ required)
    - JSON Schema structure
    - Scenario coverage (valid + edge/error cases)
    """
    try:
        # Get template
        template = await get_template(template_id, db, current_user)
        
        errors = []
        warnings = []
        
        # Check description word count (500+ words requirement)
        word_count = len(template.description.split())
        if word_count < 500:
            errors.append(TemplateValidationError(
                field="description",
                error=f"Description has only {word_count} words (minimum 500 required for comprehensive documentation)",
                suggestion="Add comprehensive details: purpose, use cases, technical architecture, integration patterns, security considerations, error handling, performance characteristics, versioning, rate limiting, and monitoring"
            ))
        
        # Check sample requests
        if len(template.sample_requests) < 3:
            errors.append(TemplateValidationError(
                field="sample_requests",
                error=f"Only {len(template.sample_requests)} sample requests (minimum 3 required)",
                suggestion="Add at least 3 samples: 1 valid, 1 edge case, 1 error case"
            ))
        else:
            scenarios = [req.get("scenario", "valid") for req in template.sample_requests]
            if "valid" not in scenarios:
                warnings.append("No sample request marked as 'valid' scenario")
            if "edge_case" not in scenarios and "error_case" not in scenarios:
                warnings.append("Consider adding edge case or error case samples")
        
        # Check sample responses
        if len(template.sample_responses) < 3:
            errors.append(TemplateValidationError(
                field="sample_responses",
                error=f"Only {len(template.sample_responses)} sample responses (minimum 3 required)",
                suggestion="Add expected responses matching your sample requests"
            ))
        
        # Check parameters
        if len(template.parameters) < 1:
            errors.append(TemplateValidationError(
                field="parameters",
                error="No parameters defined (minimum 1 required)",
                suggestion="Add parameter table with: name, type, required, example, description"
            ))
        
        # Check domain tags
        if len(template.domain_tags) < 1:
            errors.append(TemplateValidationError(
                field="domain_tags",
                error="No domain tags specified (minimum 1 required)",
                suggestion="Add relevant tags: telecom, fft, encryption, drone, etc."
            ))
        
        # Check JSON Schema
        if not template.json_schema.get("type"):
            errors.append(TemplateValidationError(
                field="json_schema",
                error="JSON Schema missing 'type' field",
                suggestion="Add 'type' field (e.g., 'object', 'array')"
            ))
        
        # Check if template can generate datasets (requires 'approved' status)
        can_generate = template.status == TemplateStatus.APPROVED.value
        
        if template.status == TemplateStatus.DRAFT.value:
            warnings.append("Template is in 'draft' status. Submit for review to enable dataset generation.")
        elif template.status == TemplateStatus.REVIEW.value:
            warnings.append("Template is under expert review. Waiting for approval.")
        elif template.status == TemplateStatus.REJECTED.value:
            warnings.append("Template was rejected. Please revise and re-submit.")
        
        is_valid = len(errors) == 0
        
        return TemplateValidationResponse(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            can_generate_dataset=can_generate
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate template: {str(e)}"
        )
