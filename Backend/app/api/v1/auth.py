"""
Authentication API endpoints — HttpOnly cookie-based JWT architecture
"""

from datetime import timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.postgres import get_db
from app.services.auth_service import get_auth_service, AuthService, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.schemas.auth_schemas import (
    UserCreate, UserLogin, UserResponse, Token, ChangePasswordRequest,
    ForgotPasswordRequest, ResetPasswordRequest, PromoteExpertRequest
)
from app.models.schemas.common_schemas import MessageResponse
from app.models.database_models import User
from app.core.logger import logger
from app.services.audit_service import log_audit_event
from app.core.cookie_config import (
    ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE,
    set_auth_cookies, clear_auth_cookies
)
from app.core.token_denylist import revoke_token, is_token_revoked

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """
    Resolve the authenticated user from the HttpOnly access cookie.
    Falls back to Authorization: Bearer header for API clients / Swagger.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Prefer HttpOnly cookie
    token: Optional[str] = request.cookies.get(ACCESS_TOKEN_COOKIE)

    # 2. Fall back to Authorization header (Swagger UI / API clients)
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise credentials_exception

    payload = auth_service.decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise credentials_exception

    # SECURITY: reject tokens revoked via logout / rotation
    if await is_token_revoked(payload.get("jti")):
        raise credentials_exception

    user_id: str = payload.get("sub")
    if not user_id:
        raise credentials_exception

    import uuid
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token format invalid. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await auth_service.get_user_by_id(db, user_uuid)
    if user is None:
        raise credentials_exception
    return user


async def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dependency: allow only administrators.

    Admin (system privilege) is distinct from expert (domain privilege).
    The admin role can only be granted via scripts/make_admin.py - there is
    deliberately no API path to self-assign it.
    """
    if not bool(getattr(current_user, "is_admin", 0)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )
    return current_user


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user
    
    RATE LIMIT: 5 registrations per minute per IP
    
    - **email**: Valid email address (unique)
    - **username**: Username (min 3 characters, unique)
    - **password**: Password (min 8 characters, must contain uppercase, lowercase, and digit)
    - **confirm_password**: Must match password
    - **full_name**: Optional full name
    
    **Note**: After registration, user must verify their email address before full access.
    An OTP will be sent to the provided email automatically.
    """
    # Check if user already exists
    existing_user = await auth_service.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user (email_verified = 0 by default)
    try:
        user = await auth_service.create_user(
            db=db,
            email=user_data.email,
            password=user_data.password,
            user_name=user_data.username
        )
    except Exception as e:
        # Log detailed error for debugging
        logger.error(f"Failed to create user {user_data.email}: {type(e).__name__}: {e}", exc_info=True)
        # Rollback any partial transaction
        try:
            await db.rollback()
        except Exception as rollback_error:
            logger.error(f"Rollback failed: {rollback_error}")
        
        # Raise appropriate HTTP exception
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again later."
        )
    
    # Send verification OTP automatically (MANDATORY)
    from app.services.email_service import get_email_service
    from app.models.email_verification_models import EmailVerification
    from datetime import datetime, timezone, timedelta
    
    email_service = get_email_service()
    otp = email_service.generate_otp()
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).replace(tzinfo=None)  # TIMESTAMP WITHOUT TIME ZONE
    
    # Store OTP
    verification = EmailVerification(
        email=user.email,
        otp=otp,
        expires_at=expires_at
    )
    try:
        db.add(verification)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to store verification for {user.email}: {type(e).__name__}: {e}", exc_info=True)
        try:
            await db.rollback()
        except Exception as rollback_error:
            logger.error(f"Verification rollback failed: {rollback_error}")
        
        # Don't leak detailed internal error to client
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create verification record. Please try again later."
        )
    
    # Send email
    username = user.user_name or user.email.split('@')[0]
    try:
        email_service.send_verification_email(user.email, otp, username)
    except Exception as e:
        # Email service already logs errors but capture here to provide visibility
        logger.error(f"Email sending error for {user.email}: {e}", exc_info=True)
        # we do not fail registration on email sending; continue but inform client
        # Client can request OTP resend explicitly via API
    
    logger.info(f"User registered: {user.email} (verification OTP sent)")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": str(user.u_id)},
        expires_delta=access_token_expires
    )
    refresh_token = auth_service.create_refresh_token(
        data={"sub": str(user.u_id)}
    )

    response = JSONResponse(
        content={"user": UserResponse.model_validate(user).model_dump(mode="json")}
    )
    set_auth_cookies(response, access_token, refresh_token)
    return response


@router.post("/login")
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Login (OAuth2 form). Tokens are set as HttpOnly cookies — NOT returned in body.
    Response body contains only non-sensitive user info.
    """
    user = await auth_service.authenticate_user(
        db=db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect email or password",
                            headers={"WWW-Authenticate": "Bearer"})
    if not user.email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Email not verified. Please verify your email before logging in.")

    access_token = auth_service.create_access_token(
        data={"sub": str(user.u_id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = auth_service.create_refresh_token(data={"sub": str(user.u_id)})

    logger.info(f"User logged in: {user.email}")
    await log_audit_event(db, action="login", user_id=user.u_id,
                          ip_address=request.client.host if request.client else None,
                          resource_type="user", resource_id=str(user.u_id))

    response = JSONResponse(content={"user": UserResponse.model_validate(user).model_dump(mode="json")})
    set_auth_cookies(response, access_token, refresh_token)
    return response


@router.post("/login/json")
@limiter.limit("10/minute")
async def login_json(
    request: Request,
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Login with JSON body. Tokens set as HttpOnly cookies."""
    user = await auth_service.authenticate_user(
        db=db, email=user_data.email, password=user_data.password
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect email or password")
    if not user.email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Email not verified. Please verify your email before logging in.")

    access_token = auth_service.create_access_token(
        data={"sub": str(user.u_id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = auth_service.create_refresh_token(data={"sub": str(user.u_id)})

    logger.info(f"User logged in: {user.email}")
    await log_audit_event(db, action="login_json", user_id=user.u_id,
                          ip_address=request.client.host if request.client else None,
                          resource_type="user", resource_id=str(user.u_id))

    response = JSONResponse(content={"user": UserResponse.model_validate(user).model_dump(mode="json")})
    set_auth_cookies(response, access_token, refresh_token)
    return response


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Get current user information
    
    Requires authentication token
    """
    return UserResponse.model_validate(current_user)


@router.post("/promote-expert", response_model=UserResponse)
async def promote_to_expert(
    promote_data: PromoteExpertRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Promote a user to expert status (ADMIN ONLY).

    Experts can approve/reject templates. Only administrators may grant
    this role.

    SECURITY: this endpoint previously allowed ANY authenticated user to
    promote themselves (privilege escalation). It is now admin-gated and
    targets a user by email instead of the caller.

    - **email**: Email address of the user to promote
    """
    from sqlalchemy import update

    target = await auth_service.get_user_by_email(db, promote_data.email)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await db.execute(
        update(User).where(User.u_id == target.u_id).values(is_expert=1)
    )
    await db.commit()
    await db.refresh(target)

    logger.info(
        f"User promoted to expert: {target.email} "
        f"(by admin: {current_user.email})"
    )

    await log_audit_event(
        db, action="promote_to_expert", user_id=current_user.u_id,
        resource_type="user",
        resource_id=str(target.u_id),
    )

    return UserResponse.model_validate(target)


@router.post("/change-password", response_model=MessageResponse)
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    password_data: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Change user password
    
    Requires authentication and current password verification
    
    - **current_password**: Your current password
    - **new_password**: New password (min 8 characters, must contain uppercase, lowercase, and digit)
    - **confirm_password**: Must match new password
    """
    # Verify current password
    is_valid = auth_service.verify_password(password_data.current_password, current_user.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Check new password is different from current
    if auth_service.verify_password(password_data.new_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )
    
    # Hash new password and update
    from sqlalchemy import update
    new_password_hash = auth_service.hash_password(password_data.new_password)
    
    await db.execute(
        update(User).where(User.u_id == current_user.u_id).values(password=new_password_hash)
    )
    await db.commit()
    
    logger.info(f"Password changed for user: {current_user.email}")

    await log_audit_event(
        db, action="password_change", user_id=current_user.u_id,
        ip_address=request.client.host if request.client else None,
        resource_type="user", resource_id=str(current_user.u_id),
    )

    return MessageResponse(message="Password changed successfully")


@router.get("/health")
async def auth_health():
    """Check authentication service health"""
    return {
        "status": "healthy",
        "service": "authentication",
        "features": ["registration", "login", "jwt_tokens", "user_profile", "password_reset"]
    }


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,
    forgot_data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Request a password reset link
    
    RATE LIMIT: 3 requests per hour per email
    
    - **email**: Email address of the account
    
    If the email exists, a password reset link will be sent.
    For security, we always return success even if the email doesn't exist.
    """
    import secrets
    from datetime import datetime, timezone, timedelta
    from app.services.email_service import get_email_service
    from app.models.password_reset_models import PasswordReset
    from sqlalchemy import select, and_
    
    # Check if user exists (but don't reveal this to the client)
    user = await auth_service.get_user_by_email(db, forgot_data.email)
    
    if user:
        # Rate limiting: Check if user has requested too many resets in the past hour
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        result = await db.execute(
            select(PasswordReset).where(
                and_(
                    PasswordReset.email == forgot_data.email,
                    PasswordReset.created_at >= one_hour_ago
                )
            )
        )
        recent_requests = result.scalars().all()
        
        if len(recent_requests) >= 3:
            logger.warning(f"Too many password reset requests for {forgot_data.email}")
            # Still return success to not reveal rate limiting
            return MessageResponse(
                message="If an account with that email exists, a password reset link has been sent."
            )
        
        # Generate secure token
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Get client IP
        client_ip = request.client.host if request.client else None
        
        # Store reset token
        password_reset = PasswordReset(
            email=forgot_data.email,
            token=reset_token,
            expires_at=expires_at,
            ip_address=client_ip
        )
        
        try:
            db.add(password_reset)
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to store password reset token: {e}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process password reset request"
            )
        
        # Build reset URL (frontend URL)
        # SECURITY: build the reset URL from server-side config only.
        # Never derive it from Origin/Host request headers — an attacker could
        # inject their own domain and capture a valid reset token (host header injection).
        from app.core.config import settings
        frontend_url = settings.frontend_url.rstrip("/")
        reset_url = f"{frontend_url}/auth/reset-password?token={reset_token}"
        
        # Send email
        email_service = get_email_service()
        username = user.user_name or user.email.split('@')[0]
        
        try:
            email_service.send_password_reset_email(
                to_email=forgot_data.email,
                reset_token=reset_token,
                reset_url=reset_url,
                username=username
            )
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
            # Don't fail the request, user can try again
        
        logger.info(f"Password reset requested for: {forgot_data.email}")
    else:
        # User doesn't exist, but don't reveal this
        logger.info(f"Password reset requested for non-existent email: {forgot_data.email}")
    
    # Always return the same message for security
    return MessageResponse(
        message="If an account with that email exists, a password reset link has been sent."
    )


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit("5/minute")
async def reset_password(
    request: Request,
    reset_data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Reset password using token from email
    
    - **token**: Reset token from the email link
    - **new_password**: New password (min 8 characters, must contain uppercase, lowercase, and digit)
    - **confirm_password**: Must match new password
    """
    from datetime import datetime, timezone
    from app.models.password_reset_models import PasswordReset
    from sqlalchemy import select, update, and_
    
    # Find the reset token
    result = await db.execute(
        select(PasswordReset).where(
            and_(
                PasswordReset.token == reset_data.token,
                PasswordReset.is_used.is_(False)
            )
        )
    )
    reset_record = result.scalar_one_or_none()
    
    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Check if token is expired
    if reset_record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new one."
        )
    
    # Get the user
    user = await auth_service.get_user_by_email(db, reset_record.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    # Validate password strength
    password = reset_data.new_password
    if not any(c.isupper() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one uppercase letter"
        )
    if not any(c.islower() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one lowercase letter"
        )
    if not any(c.isdigit() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one digit"
        )
    
    # Hash new password and update user
    new_password_hash = auth_service.hash_password(reset_data.new_password)
    
    await db.execute(
        update(User).where(User.u_id == user.u_id).values(password=new_password_hash)
    )
    
    # Mark token as used
    await db.execute(
        update(PasswordReset).where(PasswordReset.id == reset_record.id).values(is_used=True)
    )
    
    await db.commit()
    
    logger.info(f"Password reset successful for: {reset_record.email}")
    
    return MessageResponse(message="Password has been reset successfully. You can now log in with your new password.")


@router.get("/verify-reset-token")
async def verify_reset_token(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify if a password reset token is valid
    
    - **token**: Reset token to verify
    
    Returns token validity status
    """
    from datetime import datetime, timezone
    from app.models.password_reset_models import PasswordReset
    from sqlalchemy import select, and_
    
    result = await db.execute(
        select(PasswordReset).where(
            and_(
                PasswordReset.token == token,
                PasswordReset.is_used.is_(False)
            )
        )
    )
    reset_record = result.scalar_one_or_none()
    
    if not reset_record:
        return {"valid": False, "message": "Invalid reset token"}
    
    if reset_record.expires_at < datetime.now(timezone.utc):
        return {"valid": False, "message": "Reset token has expired"}
    
    return {"valid": True, "email": reset_record.email}


@router.post("/refresh")
@limiter.limit("30/minute")
async def refresh_access_token(
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Silent token rotation. Reads refresh_token from HttpOnly cookie.
    Issues a new access_token (and rotated refresh_token) as cookies.
    RATE LIMIT: 30/minute per IP.
    """
    _unauth = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or expired refresh token")

    raw = request.cookies.get(REFRESH_TOKEN_COOKIE)
    if not raw:
        raise _unauth

    payload = auth_service.decode_token(raw)
    if payload is None or payload.get("type") != "refresh":
        raise _unauth

    # SECURITY: reject refresh tokens revoked via logout / prior rotation
    if await is_token_revoked(payload.get("jti")):
        raise _unauth

    user_id = payload.get("sub")
    if not user_id:
        raise _unauth

    import uuid
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise _unauth

    user = await auth_service.get_user_by_id(db, user_uuid)
    if user is None:
        raise _unauth

    new_access  = auth_service.create_access_token(
        data={"sub": str(user.u_id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    new_refresh = auth_service.create_refresh_token(data={"sub": str(user.u_id)})

    # SECURITY: refresh tokens are one-time use - revoke the one just spent
    # so a stolen (already-used) refresh token cannot mint new sessions.
    if payload.get("jti") and payload.get("exp"):
        await revoke_token(payload["jti"], payload["exp"])

    logger.info(f"Token rotated for user: {user.email}")

    response = JSONResponse(content={"user": UserResponse.model_validate(user).model_dump(mode="json")})
    set_auth_cookies(response, new_access, new_refresh)
    return response


@router.post("/logout")
async def logout(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Logout: expires both HttpOnly auth cookies AND revokes the tokens
    server-side via the Redis denylist, so they cannot be replayed even
    if captured before logout.
    """
    # Collect both tokens (cookie first, Bearer fallback for access)
    access_raw = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if not access_raw:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            access_raw = auth_header[7:]
    refresh_raw = request.cookies.get(REFRESH_TOKEN_COOKIE)

    for raw in (access_raw, refresh_raw):
        if not raw:
            continue
        payload = auth_service.decode_token(raw)
        if payload and payload.get("jti") and payload.get("exp"):
            await revoke_token(payload["jti"], payload["exp"])

    logger.info(f"User logged out (tokens revoked): {current_user.email}")
    response = JSONResponse(content={"message": "Logged out successfully."})
    clear_auth_cookies(response)
    return response

