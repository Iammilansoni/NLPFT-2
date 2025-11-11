"""
Test Runs API endpoint - Store and retrieve test run history
Used by dashboard to display recent activity
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from app.core.postgres import get_db, TestRun
from app.core.logger import logger

router = APIRouter()


class TestRunCreate(BaseModel):
    """Request model for creating a test run"""
    query: str = Field(..., description="Natural language query", min_length=1)
    intent: Optional[str] = None
    status: str = Field(..., description="Test run status", pattern="^(passed|failed|running|pending)$")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    tests_count: int = Field(0, ge=0)
    processing_time_ms: Optional[float] = None
    best_match_api: Optional[str] = None
    best_match_score: Optional[float] = None
    search_results_count: int = Field(0, ge=0)
    dataset_generated: bool = False
    error_message: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[dict] = None


class TestRunResponse(BaseModel):
    """Response model for test run"""
    id: int
    query: str
    intent: Optional[str]
    status: str
    confidence: Optional[float]
    tests_count: int
    processing_time_ms: Optional[float]
    best_match_api: Optional[str]
    best_match_score: Optional[float]
    search_results_count: int
    dataset_generated: bool
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    time_ago: str  # Human-readable time like "2m ago"

    class Config:
        from_attributes = True


def format_time_ago(dt: datetime) -> str:
    """Format datetime as human-readable time ago"""
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.total_seconds() < 60:
        seconds = int(diff.total_seconds())
        return f"{seconds}s ago" if seconds > 0 else "just now"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes}m ago"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours}h ago"
    else:
        days = int(diff.total_seconds() / 86400)
        return f"{days}d ago"


@router.post("/runs", response_model=TestRunResponse, status_code=201)
async def create_test_run(
    test_run: TestRunCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new test run record
    
    This endpoint is called after a query is processed to store the test run results.
    """
    try:
        logger.info(f"Creating test run for query: {test_run.query[:50]}...")
        
        # Create new test run
        db_test_run = TestRun(
            query=test_run.query,
            intent=test_run.intent,
            status=test_run.status,
            confidence=test_run.confidence,
            tests_count=test_run.tests_count,
            processing_time_ms=test_run.processing_time_ms,
            best_match_api=test_run.best_match_api,
            best_match_score=test_run.best_match_score,
            search_results_count=test_run.search_results_count,
            dataset_generated=test_run.dataset_generated,
            error_message=test_run.error_message,
            user_id=test_run.user_id,
            session_id=test_run.session_id,
            metadata_=test_run.metadata
        )
        
        db.add(db_test_run)
        await db.commit()
        await db.refresh(db_test_run)
        
        # Format response
        response = TestRunResponse(
            id=db_test_run.id,
            query=db_test_run.query,
            intent=db_test_run.intent,
            status=db_test_run.status,
            confidence=db_test_run.confidence,
            tests_count=db_test_run.tests_count,
            processing_time_ms=db_test_run.processing_time_ms,
            best_match_api=db_test_run.best_match_api,
            best_match_score=db_test_run.best_match_score,
            search_results_count=db_test_run.search_results_count,
            dataset_generated=db_test_run.dataset_generated,
            error_message=db_test_run.error_message,
            created_at=db_test_run.created_at,
            updated_at=db_test_run.updated_at,
            time_ago=format_time_ago(db_test_run.created_at)
        )
        
        logger.info(f"Created test run {db_test_run.id}")
        return response
        
    except Exception as e:
        logger.error(f"Error creating test run: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create test run: {str(e)}")


@router.get("/runs", response_model=List[TestRunResponse])
async def get_recent_runs(
    limit: int = Query(10, ge=1, le=100, description="Number of runs to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent test runs for dashboard
    
    Returns the most recent test runs ordered by creation time.
    """
    try:
        # Build query
        query = select(TestRun).order_by(desc(TestRun.created_at))
        
        # Apply status filter if provided
        if status:
            query = query.where(TestRun.status == status)
        
        # Apply limit
        query = query.limit(limit)
        
        # Execute query
        result = await db.execute(query)
        test_runs = result.scalars().all()
        
        # Format responses
        responses = []
        for run in test_runs:
            responses.append(TestRunResponse(
                id=run.id,
                query=run.query,
                intent=run.intent,
                status=run.status,
                confidence=run.confidence,
                tests_count=run.tests_count,
                processing_time_ms=run.processing_time_ms,
                best_match_api=run.best_match_api,
                best_match_score=run.best_match_score,
                search_results_count=run.search_results_count,
                dataset_generated=run.dataset_generated,
                error_message=run.error_message,
                created_at=run.created_at,
                updated_at=run.updated_at,
                time_ago=format_time_ago(run.created_at)
            ))
        
        logger.info(f"Retrieved {len(responses)} test runs")
        return responses
        
    except Exception as e:
        logger.error(f"Error retrieving test runs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve test runs: {str(e)}")


@router.get("/runs/{run_id}", response_model=TestRunResponse)
async def get_test_run(
    run_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific test run by ID
    """
    try:
        result = await db.execute(
            select(TestRun).where(TestRun.id == run_id)
        )
        test_run = result.scalar_one_or_none()
        
        if not test_run:
            raise HTTPException(status_code=404, detail="Test run not found")
        
        return TestRunResponse(
            id=test_run.id,
            query=test_run.query,
            intent=test_run.intent,
            status=test_run.status,
            confidence=test_run.confidence,
            tests_count=test_run.tests_count,
            processing_time_ms=test_run.processing_time_ms,
            best_match_api=test_run.best_match_api,
            best_match_score=test_run.best_match_score,
            search_results_count=test_run.search_results_count,
            dataset_generated=test_run.dataset_generated,
            error_message=test_run.error_message,
            created_at=test_run.created_at,
            updated_at=test_run.updated_at,
            time_ago=format_time_ago(test_run.created_at)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving test run {run_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve test run: {str(e)}")


class TestRunUpdate(BaseModel):
    """Request model for updating a test run"""
    status: Optional[str] = Field(None, description="Test run status", pattern="^(passed|failed|running|pending)$")
    error_message: Optional[str] = None
    tests_count: Optional[int] = Field(None, ge=0)


@router.patch("/runs/{run_id}", response_model=TestRunResponse)
async def update_test_run(
    run_id: int,
    updates: TestRunUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a test run (e.g., change status from 'running' to 'passed'/'failed')
    """
    try:
        result = await db.execute(
            select(TestRun).where(TestRun.id == run_id)
        )
        test_run = result.scalar_one_or_none()
        
        if not test_run:
            raise HTTPException(status_code=404, detail="Test run not found")
        
        # Update fields if provided
        if updates.status:
            test_run.status = updates.status
        if updates.error_message is not None:
            test_run.error_message = updates.error_message
        if updates.tests_count is not None:
            test_run.tests_count = updates.tests_count
        
        test_run.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(test_run)
        
        return TestRunResponse(
            id=test_run.id,
            query=test_run.query,
            intent=test_run.intent,
            status=test_run.status,
            confidence=test_run.confidence,
            tests_count=test_run.tests_count,
            processing_time_ms=test_run.processing_time_ms,
            best_match_api=test_run.best_match_api,
            best_match_score=test_run.best_match_score,
            search_results_count=test_run.search_results_count,
            dataset_generated=test_run.dataset_generated,
            error_message=test_run.error_message,
            created_at=test_run.created_at,
            updated_at=test_run.updated_at,
            time_ago=format_time_ago(test_run.created_at)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating test run {run_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update test run: {str(e)}")

