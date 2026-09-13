"""
Audit Logs API - Query audit logs for security and compliance

Endpoints:
- GET /api/v1/audit/logs - Get user's audit logs with filters
- GET /api/v1/audit/logs/{log_id} - Get specific audit log entry
- GET /api/v1/audit/stats - Get audit statistics

Multi-tenant isolation: Users can only access their own audit logs
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.logger import logger
from app.core.postgres import get_db
from app.models.database_models import AuditLog, User

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


# ============= SCHEMAS =============

class AuditLogResponse(BaseModel):
    """Single audit log entry"""
    log_id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    endpoint: Optional[str]
    changes: Optional[dict]
    metadata: Optional[dict]
    success: bool
    error_message: Optional[str]
    created_at: datetime
    
    model_config = {"from_attributes": True}


class AuditLogsListResponse(BaseModel):
    """Paginated list of audit logs"""
    total: int
    page: int
    page_size: int
    logs: List[AuditLogResponse]


class AuditStatsResponse(BaseModel):
    """Audit statistics for user"""
    total_actions: int
    successful_actions: int
    failed_actions: int
    actions_by_type: dict
    resources_by_type: dict
    recent_activity: List[AuditLogResponse]


class AuditLogCreate(BaseModel):
    """Create audit log entry from frontend"""
    action: str = Field(..., description="Action performed (e.g., 'submit_template_review', 'approve_template')")
    # SECURITY: user_id is NOT accepted from client - always uses authenticated user
    template_id: Optional[str] = Field(None, description="Related template ID")
    resource_type: Optional[str] = Field(default="template", description="Type of resource")
    payload: Optional[dict] = Field(default=None, description="Additional payload data")


# ============= ENDPOINTS =============

@router.post("/logs", response_model=dict)
async def create_audit_log(
    data: AuditLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create audit log entry from frontend
    
    SECURITY: user_id is always taken from the authenticated user, never from request body.
    This prevents audit log injection attacks.
    
    Note: Most audit logs are created automatically by backend operations.
    This endpoint is for supplementary client-side logging.
    """
    try:
        from uuid import uuid4
        
        new_log = AuditLog(
            log_id=uuid4(),
            user_id=current_user.u_id,  # ALWAYS use authenticated user, never from request
            action=data.action,
            resource_type=data.resource_type or "template",
            resource_id=UUID(data.template_id) if data.template_id else None,
            changes=data.payload,
            success=1,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        
        db.add(new_log)
        await db.commit()
        
        logger.info(f"Audit log created: {data.action} by user {current_user.u_id}")
        
        return {"success": True, "log_id": str(new_log.log_id)}
        
    except Exception as e:
        logger.error(f"Error creating audit log: {e}", exc_info=True)
        # Don't fail the request - audit logging should be non-blocking
        return {"success": False, "error": str(e)}


@router.get("/logs", response_model=AuditLogsListResponse)
async def get_audit_logs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    action: Optional[str] = Query(None, description="Filter by action type (e.g., 'create_template', 'approve_template')"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type (e.g., 'template', 'dataset', 'settings')"),
    start_date: Optional[datetime] = Query(None, description="Filter logs after this date (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="Filter logs before this date (ISO 8601)"),
    success_only: Optional[bool] = Query(None, description="Filter by success status (true=success only, false=failures only)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Results per page")
):
    """
    Get audit logs for current user with filters
    
    Multi-tenant isolation: Users can only see their own logs
    
    Filters:
    - action: Specific action type (create_template, generate_dataset, etc.)
    - resource_type: Type of resource (template, dataset, settings, etc.)
    - start_date: Start date for time range
    - end_date: End date for time range
    - success_only: Filter by success/failure status
    - page: Page number (starts at 1)
    - page_size: Results per page (1-200)
    """
    try:
        # Build base query with multi-tenant isolation
        query = select(AuditLog).where(AuditLog.user_id == current_user.u_id)
        count_query = select(func.count()).select_from(AuditLog).where(AuditLog.user_id == current_user.u_id)
        
        # Apply filters
        if action:
            query = query.where(AuditLog.action == action)
            count_query = count_query.where(AuditLog.action == action)
        
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
            count_query = count_query.where(AuditLog.resource_type == resource_type)
        
        # Normalize timezone-aware dates to timezone-naive UTC for PostgreSQL
        if start_date:
            if start_date.tzinfo is not None:
                start_date = start_date.astimezone(timezone.utc).replace(tzinfo=None)
            query = query.where(AuditLog.created_at >= start_date)
            count_query = count_query.where(AuditLog.created_at >= start_date)
        
        if end_date:
            if end_date.tzinfo is not None:
                end_date = end_date.astimezone(timezone.utc).replace(tzinfo=None)
            query = query.where(AuditLog.created_at <= end_date)
            count_query = count_query.where(AuditLog.created_at <= end_date)
        
        if success_only is not None:
            success_value = 1 if success_only else 0
            query = query.where(AuditLog.success == success_value)
            count_query = count_query.where(AuditLog.success == success_value)
        
        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        offset = (page - 1) * page_size
        query = query.order_by(AuditLog.created_at.desc())
        query = query.limit(page_size).offset(offset)
        
        # Execute query
        result = await db.execute(query)
        logs = result.scalars().all()
        
        # Convert to response format
        log_responses = [
            AuditLogResponse(
                log_id=str(log.log_id),
                user_id=str(log.user_id),
                action=log.action,
                resource_type=log.resource_type,
                resource_id=str(log.resource_id) if log.resource_id else None,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                endpoint=log.endpoint,
                changes=log.changes,
                metadata=log.metadata_,
                success=bool(log.success),
                error_message=log.error_message,
                created_at=log.created_at
            )
            for log in logs
        ]
        
        logger.info(f"Retrieved {len(log_responses)}/{total} audit logs for user {current_user.u_id}")
        
        return AuditLogsListResponse(
            total=total,
            page=page,
            page_size=page_size,
            logs=log_responses
        )
    
    except Exception as e:
        logger.error(f"Error retrieving audit logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit logs: {str(e)}"
        )


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get specific audit log entry by ID
    
    Multi-tenant isolation: Users can only access their own logs
    """
    try:
        # Query with multi-tenant isolation
        query = select(AuditLog).where(
            AuditLog.log_id == UUID(log_id),
            AuditLog.user_id == current_user.u_id
        )
        result = await db.execute(query)
        log = result.scalar_one_or_none()
        
        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit log not found"
            )
        
        return AuditLogResponse(
            log_id=str(log.log_id),
            user_id=str(log.user_id),
            action=log.action,
            resource_type=log.resource_type,
            resource_id=str(log.resource_id) if log.resource_id else None,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            endpoint=log.endpoint,
            changes=log.changes,
            metadata=log.metadata_,
            success=bool(log.success),
            error_message=log.error_message,
            created_at=log.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving audit log: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit log: {str(e)}"
        )


@router.get("/stats", response_model=AuditStatsResponse)
async def get_audit_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get audit statistics for current user
    
    Returns:
    - Total actions count
    - Success/failure breakdown
    - Actions by type
    - Resources by type
    - Recent activity (last 10 actions)
    """
    try:
        # Calculate date range - use timezone-naive datetime for TIMESTAMP WITHOUT TIME ZONE column
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).replace(tzinfo=None)
        
        # Get all logs for period
        query = select(AuditLog).where(
            AuditLog.user_id == current_user.u_id,
            AuditLog.created_at >= start_date
        )
        result = await db.execute(query)
        logs = result.scalars().all()
        
        # Calculate statistics
        total_actions = len(logs)
        successful_actions = sum(1 for log in logs if log.success == 1)
        failed_actions = total_actions - successful_actions
        
        # Actions by type
        actions_by_type = {}
        for log in logs:
            actions_by_type[log.action] = actions_by_type.get(log.action, 0) + 1
        
        # Resources by type
        resources_by_type = {}
        for log in logs:
            resources_by_type[log.resource_type] = resources_by_type.get(log.resource_type, 0) + 1
        
        # Recent activity (last 10)
        recent_query = select(AuditLog).where(
            AuditLog.user_id == current_user.u_id
        ).order_by(AuditLog.created_at.desc()).limit(10)
        recent_result = await db.execute(recent_query)
        recent_logs = recent_result.scalars().all()
        
        recent_activity = [
            AuditLogResponse(
                log_id=str(log.log_id),
                user_id=str(log.user_id),
                action=log.action,
                resource_type=log.resource_type,
                resource_id=str(log.resource_id) if log.resource_id else None,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                endpoint=log.endpoint,
                changes=log.changes,
                metadata=log.metadata_,
                success=bool(log.success),
                error_message=log.error_message,
                created_at=log.created_at
            )
            for log in recent_logs
        ]
        
        logger.info(f"Retrieved audit stats for user {current_user.u_id}: {total_actions} actions in last {days} days")
        
        return AuditStatsResponse(
            total_actions=total_actions,
            successful_actions=successful_actions,
            failed_actions=failed_actions,
            actions_by_type=actions_by_type,
            resources_by_type=resources_by_type,
            recent_activity=recent_activity
        )
    
    except Exception as e:
        logger.error(f"Error retrieving audit stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit statistics: {str(e)}"
        )
