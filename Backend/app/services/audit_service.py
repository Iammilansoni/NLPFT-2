"""
Audit Service - Enterprise logging for security, compliance, and debugging

🎯 Logs all user actions:
- Template CRUD (create, update, delete, approve, reject)
- Dataset operations (generate, upload, embed)
- Vector searches
- Settings changes
- Authentication events
- Test executions

✅ Multi-tenant isolation: Users can only query their own audit logs
✅ Compliance: Detailed change tracking with before/after values
✅ Security: IP address, user agent, endpoint tracking
✅ Debugging: Success/failure status with error messages
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from fastapi import Request

from app.models.database_models import AuditLog, User
from app.core.logger import logger


class AuditService:
    """
    Enterprise audit logging service
    
    Provides comprehensive tracking of all user actions for:
    - Security auditing
    - Compliance reporting
    - Debugging and troubleshooting
    - User activity monitoring
    """
    
    @staticmethod
    async def log_action(
        db: AsyncSession,
        user_id: UUID,
        action: str,
        resource_type: str,
        resource_id: Optional[UUID] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata_: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        request: Optional[Request] = None
    ) -> AuditLog:
        """
        Log a user action to audit_logs table
        
        Args:
            db: Database session
            user_id: User performing the action
            action: Action name (e.g., "create_template", "approve_template", "generate_dataset")
            resource_type: Type of resource (e.g., "template", "dataset", "settings")
            resource_id: UUID of affected resource (optional)
            changes: Before/after values for updates (optional)
            metadata_: Additional context (optional)
            success: Whether action succeeded
            error_message: Error message if action failed
            request: FastAPI request object for IP/user agent extraction
        
        Returns:
            Created AuditLog entry
        """
        # Extract request context if available
        ip_address = None
        user_agent = None
        endpoint = None
        
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
            endpoint = str(request.url.path)
        
        # Create audit log entry
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            metadata_=metadata_,
            success=1 if success else 0,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        
        db.add(audit_entry)
        await db.commit()
        await db.refresh(audit_entry)
        
        logger.info(
            f"📝 Audit: user={user_id} action={action} resource={resource_type}:{resource_id} "
            f"success={success} ip={ip_address}"
        )
        
        return audit_entry
    
    # ============= TEMPLATE OPERATIONS =============
    
    @staticmethod
    async def log_template_created(
        db: AsyncSession,
        user_id: UUID,
        template_id: UUID,
        template_name: str,
        metadata_: Optional[Dict] = None,
        request: Optional[Request] = None
    ):
        """Log template creation"""
        return await AuditService.log_action(
            db=db,
            user_id=user_id,
            action="create_template",
            resource_type="template",
            resource_id=template_id,
            metadata_={
                "template_name": template_name,
                **(metadata_ or {})
            },
            request=request
        )
    
    @staticmethod
    async def log_template_updated(
        db: AsyncSession,
        user_id: UUID,
        template_id: UUID,
        changes: Dict[str, Any],
        request: Optional[Request] = None
    ):
        """Log template update with before/after values"""
        return await AuditService.log_action(
            db=db,
            user_id=user_id,
            action="update_template",
            resource_type="template",
            resource_id=template_id,
            changes=changes,
            request=request
        )
    
    @staticmethod
    async def log_template_deleted(
        db: AsyncSession,
        user_id: UUID,
        template_id: UUID,
        template_name: str,
        request: Optional[Request] = None
    ):
        """Log template deletion"""
        return await AuditService.log_action(
            db=db,
            user_id=user_id,
            action="delete_template",
            resource_type="template",
            resource_id=template_id,
            metadata_={"template_name": template_name},
            request=request
        )
    
    @staticmethod
    async def log_template_submitted_for_review(
        db: AsyncSession,
        user_id: UUID,
        template_id: UUID,
        template_name: str,
        request: Optional[Request] = None
    ):
        """Log template submission for review"""
        return await AuditService.log_action(
            db=db,
            user_id=user_id,
            action="submit_template_review",
            resource_type="template",
            resource_id=template_id,
            metadata_={"template_name": template_name},
            request=request
        )
    
    @staticmethod
    async def log_template_approved(
        db: AsyncSession,
        user_id: UUID,
        template_id: UUID,
        template_name: str,
        approver_id: UUID,
        request: Optional[Request] = None
    ):
        """Log template approval"""
        return await AuditService.log_action(
            db=db,
            user_id=user_id,
            action="approve_template",
            resource_type="template",
            resource_id=template_id,
            metadata_={
                "template_name": template_name,
                "approver_id": str(approver_id)
            },
            request=request
        )
    
    @staticmethod
    async def log_template_rejected(
        db: AsyncSession,
        user_id: UUID,
        template_id: UUID,
        template_name: str,
        rejector_id: UUID,
        reason: Optional[str] = None,
        request: Optional[Request] = None
    ):
        """Log template rejection"""
        return await AuditService.log_action(
            db=db,
            user_id=user_id,
            action="reject_template",
            resource_type="template",
            resource_id=template_id,
            metadata_={
                "template_name": template_name,
                "rejector_id": str(rejector_id),
                "reason": reason
            },
            request=request
        )
    
    # ============= DATASET OPERATIONS =============
    
    @staticmethod
    async def log_dataset_generated(
        db: AsyncSession,
        user_id: UUID,
        template_id: UUID,
        dataset_path: str,
        num_examples: int,
        metadata_: Optional[Dict] = None,
        request: Optional[Request] = None
    ):
        """Log dataset generation"""
        return await AuditService.log_action(
            db=db,
            user_id=user_id,
            action="generate_dataset",
            resource_type="dataset",
            resource_id=template_id,
            metadata_={
                "dataset_path": dataset_path,
                "num_examples": num_examples,
                **(metadata_ or {})
            },
            request=request
        )
    
    @staticmethod
    async def log_dataset_uploaded(
        db: AsyncSession,
        user_id: UUID,
        filename: str,
        file_size: int,
        request: Optional[Request] = None
    ):
        """Log dataset upload"""
        return await AuditService.log_action(
            db=db,
            user_id=user_id,
            action="upload_dataset",
            resource_type="dataset",
            metadata_={
                "filename": filename,
                "file_size": file_size
            },
            request=request
        )
    
    @staticmethod
    async def log_dataset_embedded(
        db: AsyncSession,
        user_id: UUID,
        template_id: UUID,
        model_name: str,
        dimension: int,
        num_vectors: int,
        request: Optional[Request] = None
    ):
        """Log dataset embedding"""
        return await AuditService.log_action(
            db=db,
            user_id=user_id,
            action="embed_dataset",
            resource_type="embedding",
            resource_id=template_id,
            metadata_={
                "model_name": model_name,
                "dimension": dimension,
                "num_vectors": num_vectors
            },
            request=request
        )
    
    @staticmethod
    async def log_vector_search(
        db: AsyncSession,
        user_id: UUID,
        template_id: Optional[UUID],
        query: str,
        num_results: int,
        model_name: str,
        request: Optional[Request] = None
    ):
        """Log vector similarity search"""
        return await AuditService.log_action(
            db=db,
            user_id=user_id,
            action="search_vectors",
            resource_type="search",
            resource_id=template_id,
            metadata_={
                "query": query[:100],  # Truncate long queries
                "num_results": num_results,
                "model_name": model_name
            },
            request=request
        )
    
    # ============= SETTINGS OPERATIONS =============
    
    @staticmethod
    async def log_settings_updated(
        db: AsyncSession,
        user_id: UUID,
        changes: Dict[str, Any],
        request: Optional[Request] = None
    ):
        """Log user settings update"""
        return await AuditService.log_action(
            db=db,
            user_id=user_id,
            action="update_settings",
            resource_type="settings",
            changes=changes,
            request=request
        )
    
    # ============= TEST EXECUTION =============
    
    @staticmethod
    async def log_test_executed(
        db: AsyncSession,
        user_id: UUID,
        template_id: UUID,
        test_run_id: UUID,
        total_tests: int,
        passed: int,
        failed: int,
        request: Optional[Request] = None
    ):
        """Log test execution"""
        return await AuditService.log_action(
            db=db,
            user_id=user_id,
            action="execute_tests",
            resource_type="test_run",
            resource_id=test_run_id,
            metadata_={
                "template_id": str(template_id),
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed
            },
            request=request
        )
    
    # ============= AUTHENTICATION EVENTS =============
    
    @staticmethod
    async def log_login(
        db: AsyncSession,
        user_id: UUID,
        success: bool = True,
        error_message: Optional[str] = None,
        request: Optional[Request] = None
    ):
        """Log user login attempt"""
        return await AuditService.log_action(
            db=db,
            user_id=user_id,
            action="login",
            resource_type="auth",
            success=success,
            error_message=error_message,
            request=request
        )
    
    @staticmethod
    async def log_logout(
        db: AsyncSession,
        user_id: UUID,
        request: Optional[Request] = None
    ):
        """Log user logout"""
        return await AuditService.log_action(
            db=db,
            user_id=user_id,
            action="logout",
            resource_type="auth",
            request=request
        )
    
    # ============= QUERY AUDIT LOGS =============
    
    @staticmethod
    async def get_user_audit_logs(
        db: AsyncSession,
        user_id: UUID,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        success_only: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Query audit logs for a specific user with filters
        
        Args:
            db: Database session
            user_id: User to query logs for
            action: Filter by action type (optional)
            resource_type: Filter by resource type (optional)
            start_date: Filter logs after this date (optional)
            end_date: Filter logs before this date (optional)
            success_only: Filter by success status (optional)
            limit: Maximum number of results
            offset: Pagination offset
        
        Returns:
            List of AuditLog entries
        """
        query = select(AuditLog).where(AuditLog.user_id == user_id)
        
        if action:
            query = query.where(AuditLog.action == action)
        
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        
        if start_date:
            query = query.where(AuditLog.created_at >= start_date)
        
        if end_date:
            query = query.where(AuditLog.created_at <= end_date)
        
        if success_only is not None:
            query = query.where(AuditLog.success == (1 if success_only else 0))
        
        query = query.order_by(AuditLog.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        return result.scalars().all()


# Global instance
_audit_service = None


def get_audit_service() -> AuditService:
    """Get or create global AuditService instance"""
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service
