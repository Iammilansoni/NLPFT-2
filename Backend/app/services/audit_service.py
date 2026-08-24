"""
Audit Service - Structured audit logging for sensitive operations

Logs security-relevant events (login, password change, role changes, key rotation)
to both the application logger and the database AuditLog table.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger


def _extract_ip(request: Optional[Request] = None) -> Optional[str]:
    """Extract client IP from a FastAPI Request."""
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


async def log_audit_event(
    db: AsyncSession,
    *,
    action: str,
    user_id: Optional[uuid.UUID] = None,
    user_email: Optional[str] = None,
    ip_address: Optional[str] = None,
    success: bool = True,
    detail: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
) -> None:
    """
    Log an audit event for sensitive operations.

    Args:
        db: Database session
        action: Action type (e.g., "login", "password_change", "promote_to_expert")
        user_id: UUID of the user performing or affected by the action
        user_email: DEPRECATED - ignored; kept for backward-compat signatures
        ip_address: Client IP address
        success: Whether the action succeeded
        detail: Additional detail or reason
        resource_type: Type of resource affected (e.g., "user", "encryption_key")
        resource_id: ID of the affected resource
    """
    # Log message intentionally omits PII (user_email)
    status_str = "success" if success else "failure"
    log_msg = (
        f"[AUDIT] action={action} user_id={user_id} "
        f"status={status_str} ip={ip_address} "
        f"resource={resource_type}:{resource_id} detail={detail}"
    )

    if success:
        logger.info(log_msg)
    else:
        logger.warning(log_msg)

    # Persist to AuditLog table
    try:
        from app.models.database_models import AuditLog

        resource_uuid = None
        resource_id_str = None
        if resource_id:
            try:
                resource_uuid = uuid.UUID(resource_id)
            except ValueError:
                # Preserve the original string when it's not a valid UUID
                resource_id_str = resource_id
                logger.warning(
                    f"[AUDIT] resource_id '{resource_id}' is not a valid UUID; "
                    f"stored in metadata instead"
                )

        # Build metadata — never persist user_email
        metadata = {}
        if detail:
            metadata["detail"] = detail
        if resource_id_str:
            metadata["resource_id_str"] = resource_id_str
        
        log_entry = AuditLog(
            log_id=uuid.uuid4(),
            user_id=user_id,
            action=action,
            resource_type=resource_type or "system",
            resource_id=resource_uuid,
            ip_address=ip_address,
            metadata_=metadata if metadata else None,
            success=1 if success else 0,
            error_message=detail if not success else None,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.add(log_entry)
        # Use flush (not commit) so we don't prematurely close the caller's transaction
        await db.flush()
    except Exception as e:
        # Rollback the failed flush, then log — audit logging should never break the main flow
        try:
            await db.rollback()
        except Exception:
            pass
        logger.exception(f"Failed to persist audit log: {e}")


# ---------------------------------------------------------------------------
# High-level AuditService class used by API routes
# ---------------------------------------------------------------------------

class AuditService:
    """Thin facade around log_audit_event with domain-specific helper methods."""

    # -- dataset ----------------------------------------------------------

    async def log_dataset_generated(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        template_id: uuid.UUID,
        dataset_path: str,
        num_examples: int,
        metadata_: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> None:
        detail_parts = [f"path={dataset_path}", f"rows={num_examples}"]
        await log_audit_event(
            db,
            action="dataset_generated",
            user_id=user_id,
            ip_address=_extract_ip(request),
            resource_type="dataset",
            resource_id=str(template_id),
            detail=", ".join(detail_parts),
        )

    # -- settings ---------------------------------------------------------

    async def log_settings_updated(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        request: Optional[Request] = None,
        changes: Optional[dict] = None,
    ) -> None:
        await log_audit_event(
            db,
            action="settings_updated",
            user_id=user_id,
            ip_address=_extract_ip(request),
            resource_type="user_settings",
            resource_id=str(user_id),
            detail=str(changes) if changes else None,
        )

    # -- template CRUD ----------------------------------------------------

    async def log_template_updated(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        template_id: uuid.UUID,
        changes: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> None:
        await log_audit_event(
            db,
            action="template_updated",
            user_id=user_id,
            ip_address=_extract_ip(request),
            resource_type="template",
            resource_id=str(template_id),
            detail=str(changes) if changes else None,
        )

    async def log_template_deleted(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        template_id: uuid.UUID,
        template_name: Optional[str] = None,
        request: Optional[Request] = None,
    ) -> None:
        await log_audit_event(
            db,
            action="template_deleted",
            user_id=user_id,
            ip_address=_extract_ip(request),
            resource_type="template",
            resource_id=str(template_id),
            detail=f"name={template_name}" if template_name else None,
        )

    # -- template workflow ------------------------------------------------

    async def log_template_submitted_for_review(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        template_id: uuid.UUID,
        template_name: Optional[str] = None,
        request: Optional[Request] = None,
    ) -> None:
        await log_audit_event(
            db,
            action="template_submitted_for_review",
            user_id=user_id,
            ip_address=_extract_ip(request),
            resource_type="template",
            resource_id=str(template_id),
            detail=f"name={template_name}" if template_name else None,
        )

    async def log_template_approved(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        template_id: uuid.UUID,
        template_name: Optional[str] = None,
        approver_id: Optional[uuid.UUID] = None,
        request: Optional[Request] = None,
    ) -> None:
        await log_audit_event(
            db,
            action="template_approved",
            user_id=user_id,
            ip_address=_extract_ip(request),
            resource_type="template",
            resource_id=str(template_id),
            detail=f"name={template_name}, approver={approver_id}",
        )

    async def log_template_rejected(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        template_id: uuid.UUID,
        template_name: Optional[str] = None,
        rejector_id: Optional[uuid.UUID] = None,
        reason: Optional[str] = None,
        request: Optional[Request] = None,
    ) -> None:
        await log_audit_event(
            db,
            action="template_rejected",
            user_id=user_id,
            ip_address=_extract_ip(request),
            resource_type="template",
            resource_id=str(template_id),
            detail=f"name={template_name}, rejector={rejector_id}, reason={reason}",
        )

    # -- generic action ---------------------------------------------------

    async def log_action(
        self,
        db: AsyncSession,
        action: str,
        user_id: uuid.UUID,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[str] = None,
        metadata_: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> None:
        detail = details or (str(metadata_) if metadata_ else None)
        await log_audit_event(
            db,
            action=action,
            user_id=user_id,
            ip_address=_extract_ip(request),
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail,
        )


# Singleton instance
_audit_service = AuditService()


def get_audit_service() -> AuditService:
    """Factory / FastAPI dependency that returns the AuditService singleton."""
    return _audit_service
