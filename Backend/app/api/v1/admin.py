"""
Admin API endpoints - System administration operations
Requires expert (admin) privileges.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user, require_admin
from app.core.encryption import APIKeyEncryption, get_encryption_service
from app.core.logger import logger
from app.core.postgres import get_db
from app.models.database_models import LLMProviderConfig, User

router = APIRouter(prefix="/admin", tags=["Admin"])


class RotateKeyRequest(BaseModel):
    """
    The administrator generates the new Fernet key LOCALLY and provides it
    in the request. SECURITY: the server never returns key material -
    the previous design generated the key server-side and sent it back in
    the HTTP response body, exposing it to logs/proxies/browser history.

    Generate a key with:
        python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    """
    new_key: str = Field(..., min_length=44, max_length=44, description="New Fernet key (generated locally)")


@router.post("/rotate-encryption-key")
async def rotate_encryption_key(
    request: Request,
    payload: RotateKeyRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Rotate the API key encryption key (ADMIN ONLY).

    Re-encrypts ALL stored API keys (all users) with the new key supplied
    by the administrator. The key is generated LOCALLY by the admin and is
    never returned by the server.

    After a successful rotation: update SECRET_KEY_ENCRYPTION in .env to
    the same key you provided, then restart the server.
    """
    old_encryptor = get_encryption_service()
    try:
        new_encryptor = APIKeyEncryption(secret_key=payload.new_key)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid Fernet key. Generate one locally with: "
                "python -c \"from cryptography.fernet import Fernet; "
                "print(Fernet.generate_key().decode())\""
            ),
        )

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

    # SECURITY: never include key material in the response.
    return JSONResponse(content={
        "message": (
            f"Successfully rotated encryption key. "
            f"{rotated_count} API keys re-encrypted. "
            f"IMPORTANT: Update SECRET_KEY_ENCRYPTION in your .env file "
            f"to the key you provided, then restart the server."
        ),
        "success": True,
        "rotated_count": rotated_count,
    })
