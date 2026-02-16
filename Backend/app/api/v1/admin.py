"""
Admin API endpoints - System administration operations
Requires expert (admin) privileges.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.postgres import get_db
from app.api.v1.auth import get_current_user
from app.models.database_models import User, LLMProviderConfig
from app.models.schemas.common_schemas import MessageResponse
from app.core.encryption import get_encryption_service, APIKeyEncryption
from app.core.logger import logger

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/rotate-encryption-key")
async def rotate_encryption_key(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Rotate the API key encryption key (expert-only).

    Re-encrypts ALL stored API keys (all users) with a new encryption key.
    The response includes the new key which must be saved to SECRET_KEY_ENCRYPTION
    in the environment, then the server must be restarted.

    WARNING: After rotation, update SECRET_KEY_ENCRYPTION in .env
    to the returned new_key value, then restart the server.
    """
    if not getattr(current_user, "is_expert", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only expert users can rotate encryption keys",
        )

    old_encryptor = get_encryption_service()
    new_key = APIKeyEncryption.generate_key()
    new_encryptor = APIKeyEncryption(secret_key=new_key)

    # Find ALL LLM configs with encrypted API keys (all users, not just current)
    result = await db.execute(
        select(LLMProviderConfig)
    )
    configs = result.scalars().all()

    rotated_count = 0
    for config in configs:
        if config.api_key_encrypted:
            try:
                config.api_key_encrypted = old_encryptor.rotate_key(
                    config.api_key_encrypted, new_encryptor
                )
                rotated_count += 1
            except Exception as e:
                logger.error(
                    f"Failed to rotate key for config {config.config_id}: {e}"
                )
                # Explicitly rollback so partial re-encryptions are reverted
                await db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Key rotation failed for config {config.config_id}. "
                    "No keys were changed. Check logs for details.",
                )

    await db.commit()

    # Log the audit event
    try:
        from app.services.audit_service import log_audit_event

        await log_audit_event(
            db,
            action="rotate_encryption_key",
            user_id=current_user.u_id,
            ip_address=request.client.host if request.client else None,
            success=True,
            detail=f"Rotated {rotated_count} API keys",
            resource_type="encryption_key",
        )
    except Exception:
        pass  # Audit failure should not block the operation

    logger.info(
        f"Encryption key rotated by user_id={current_user.u_id}: "
        f"{rotated_count} keys re-encrypted"
    )

    return JSONResponse(content={
        "message": (
            f"Successfully rotated encryption key. "
            f"{rotated_count} API keys re-encrypted. "
            f"IMPORTANT: Update SECRET_KEY_ENCRYPTION in your .env file "
            f"with the new_key value below and restart the server."
        ),
        "success": True,
        "new_key": new_key,
    })
