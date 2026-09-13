"""
User Data API - Authenticated CRUD operations for user's templates and CSV data
Handles multi-tenant data management with proper user isolation
"""

import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.postgres import get_db
from app.models.schemas import (
    CSVDataCreate,
    CSVDataResponse,
    TemplateCreate,
    TemplateResponse,
    UserResponse,
)
from app.services.enterprise_service import EnterpriseService, get_enterprise_service

router = APIRouter()


# ============= TEMPLATE ENDPOINTS =============

@router.post("/templates", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    service: EnterpriseService = Depends(get_enterprise_service)
):
    """
    Create a new API template
    
    Requires authentication. Template will be owned by current user.
    """
    template = await service.create_template(
        db=db,
        user_id=current_user.user_id,
        api_name=template_data.api_name,
        description=template_data.description,
        base_url=template_data.base_url,
        method=template_data.method
    )
    
    return TemplateResponse.model_validate(template)


@router.get("/templates", response_model=List[TemplateResponse])
async def get_templates(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    service: EnterpriseService = Depends(get_enterprise_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get all templates for current user
    
    Supports pagination for large datasets
    """
    templates = await service.get_user_templates(
        db=db,
        user_id=current_user.user_id,
        skip=skip,
        limit=limit
    )
    
    return [TemplateResponse.model_validate(t) for t in templates]


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    service: EnterpriseService = Depends(get_enterprise_service)
):
    """
    Get a specific template by ID
    
    Only returns if user owns the template (multi-tenant isolation)
    """
    template = await service.get_template_by_id(
        db=db,
        template_id=template_id,
        user_id=current_user.user_id
    )
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return TemplateResponse.model_validate(template)


# ============= CSV DATA ENDPOINTS =============

@router.post("/csv-data", response_model=CSVDataResponse, status_code=status.HTTP_201_CREATED)
async def create_csv_data(
    csv_data: CSVDataCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    service: EnterpriseService = Depends(get_enterprise_service)
):
    """
    Create CSV data entry (test data)
    
    Optimized for millions of rows with proper indexing
    """
    # Verify template ownership
    template = await service.get_template_by_id(
        db=db,
        template_id=csv_data.template_id,
        user_id=current_user.user_id
    )
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    data = await service.create_csv_data(
        db=db,
        user_id=current_user.user_id,
        template_id=csv_data.template_id,
        query=csv_data.query,
        api_name=csv_data.api_name,
        endpoint=csv_data.endpoint,
        request=csv_data.request,
        response=csv_data.response,
        description=csv_data.description
    )
    
    return CSVDataResponse.model_validate(data)


@router.get("/csv-data/template/{template_id}", response_model=List[CSVDataResponse])
async def get_csv_data_by_template(
    template_id: uuid.UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    service: EnterpriseService = Depends(get_enterprise_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=10000)
):
    """
    Get CSV data for a template
    
    Supports pagination for large datasets (millions of rows)
    """
    csv_data = await service.get_csv_data_by_template(
        db=db,
        user_id=current_user.user_id,
        template_id=template_id,
        skip=skip,
        limit=limit
    )
    
    return [CSVDataResponse.model_validate(d) for d in csv_data]


@router.get("/csv-data/template/{template_id}/count")
async def count_csv_data(
    template_id: uuid.UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    service: EnterpriseService = Depends(get_enterprise_service)
):
    """
    Count CSV data entries for a template
    
    Useful for pagination
    """
    count = await service.count_csv_data_by_template(
        db=db,
        user_id=current_user.user_id,
        template_id=template_id
    )
    
    return {"template_id": template_id, "count": count}


# ============= STATISTICS ENDPOINT =============

@router.get("/statistics")
async def get_statistics(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    service: EnterpriseService = Depends(get_enterprise_service)
):
    """
    Get statistics for current user
    
    Returns counts of templates, CSV data, and embeddings
    """
    stats = await service.get_user_statistics(
        db=db,
        user_id=current_user.user_id
    )
    
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "statistics": stats
    }
