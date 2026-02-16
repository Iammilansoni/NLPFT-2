"""
Audit Service - Structured audit logging for sensitive operations

Logs security-relevant events (login, password change, role changes, key rotation)
to both the application logger and the database AuditLog table.
"""

from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger


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
