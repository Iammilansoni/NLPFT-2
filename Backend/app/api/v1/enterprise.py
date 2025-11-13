"""
Enterprise API endpoints for multi-tenant operations
Handles templates, CSV data, embeddings, and test runs
"""

from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.postgres import get_db
from app.services.enterprise_service import get_enterprise_service, EnterpriseService
from app.api.v1.auth import get_current_user
from app.models.schemas import (
    UserResponse, TemplateCreate, TemplateResponse,
    CSVDataCreate, CSVDataResponse, TestRunCreate, TestRunResponse
)
from app.core.logger import logger

router = APIRouter()


@router.post("/templates", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    service: EnterpriseService = Depends(get_enterprise_service)
):
    """
    Create a new API template
    
    Requires authentication
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
    
    Only returns if user owns the template
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


@router.post("/csv-data", response_model=CSVDataResponse, status_code=status.HTTP_201_CREATED)
async def create_csv_data(
    csv_data: CSVDataCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    service: EnterpriseService = Depends(get_enterprise_service)
):
    """
    Create CSV data entry
    
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


@router.post("/test-runs", response_model=TestRunResponse, status_code=status.HTTP_201_CREATED)
async def create_test_run(
    test_run_data: TestRunCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    service: EnterpriseService = Depends(get_enterprise_service)
):
    """
    Create a test run entry
    
    Critical for audit logs and professional SaaS platform
    """
    test_run = await service.create_test_run(
        db=db,
        user_id=current_user.user_id,
        template_id=test_run_data.template_id,
        csv_id=test_run_data.csv_id,
        input_payload=test_run_data.input_payload,
        llm_request=test_run_data.llm_request,
        llm_response=test_run_data.llm_response,
        status=test_run_data.status
    )
    
    return TestRunResponse.model_validate(test_run)


@router.get("/test-runs", response_model=List[TestRunResponse])
async def get_test_runs(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    service: EnterpriseService = Depends(get_enterprise_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get test runs for current user
    
    Returns audit logs and execution history
    """
    test_runs = await service.get_test_runs_by_user(
        db=db,
        user_id=current_user.user_id,
        skip=skip,
        limit=limit
    )
    
    return [TestRunResponse.model_validate(tr) for tr in test_runs]


@router.get("/test-runs/template/{template_id}", response_model=List[TestRunResponse])
async def get_test_runs_by_template(
    template_id: uuid.UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    service: EnterpriseService = Depends(get_enterprise_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get test runs for a specific template
    """
    test_runs = await service.get_test_runs_by_template(
        db=db,
        user_id=current_user.user_id,
        template_id=template_id,
        skip=skip,
        limit=limit
    )
    
    return [TestRunResponse.model_validate(tr) for tr in test_runs]


@router.get("/statistics")
async def get_statistics(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    service: EnterpriseService = Depends(get_enterprise_service)
):
    """
    Get statistics for current user
    
    Returns counts of templates, CSV data, embeddings, and test runs
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
