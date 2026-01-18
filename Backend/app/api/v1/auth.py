"""
Authentication API endpoints
Handles user registration, login, and token management
"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.postgres import get_db
from app.services.auth_service import get_auth_service, AuthService, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.schemas.auth_schemas import (
    UserCreate, UserLogin, UserResponse, Token, ChangePasswordRequest,
    ForgotPasswordRequest, ResetPasswordRequest
)
from app.models.schemas.common_schemas import MessageResponse
from app.models.database_models import User
from app.core.logger import logger

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Get current authenticated user from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = auth_service.decode_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    import uuid
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        # Token has email instead of UUID - old token format
        logger.warning(f"Invalid token format - 'sub' is not a UUID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token format invalid. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await auth_service.get_user_by_id(db, user_uuid)
    if user is None:
        raise credentials_exception
    
    return user


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
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
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    
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
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login with email and password (OAuth2 form)
    
    RATE LIMIT: 10 login attempts per minute per IP
    
    Returns JWT access token for authenticated requests
    
    Note: Email must be verified before login is allowed
    """
    user = await auth_service.authenticate_user(
        db=db,
        email=form_data.username,  # OAuth2 uses 'username' field
        password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if email is verified
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email before logging in.",
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": str(user.u_id)},
        expires_delta=access_token_expires
    )
    
    logger.info(f"User logged in: {user.email}")
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/login/json", response_model=Token)
async def login_json(
    request: Request,
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login with JSON payload (alternative to form data)
    
    RATE LIMIT: 10 login attempts per minute per IP
    
    - **email**: User email
    - **password**: User password
    
    Note: Email must be verified before login is allowed
    """
    user = await auth_service.authenticate_user(
        db=db,
        email=user_data.email,
        password=user_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if email is verified
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email before logging in.",
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": str(user.u_id)},
        expires_delta=access_token_expires
    )
    
    logger.info(f"User logged in: {user.email}")
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


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
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """
    Promote current user to expert status
    
    This is a development/testing endpoint that allows users to
    become experts so they can approve/reject templates.
    
    In production, this would require admin privileges.
    """
    from sqlalchemy import update
    
    await db.execute(
        update(User).where(User.u_id == current_user.u_id).values(is_expert=1)
    )
    await db.commit()
    await db.refresh(current_user)
    
    logger.info(f"User promoted to expert: {current_user.email}")
    
    return UserResponse.model_validate(current_user)


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
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
        frontend_url = request.headers.get("Origin", "http://localhost:3000")
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
                PasswordReset.is_used == False
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
                PasswordReset.is_used == False
            )
        )
    )
    reset_record = result.scalar_one_or_none()
    
    if not reset_record:
        return {"valid": False, "message": "Invalid reset token"}
    
    if reset_record.expires_at < datetime.now(timezone.utc):
        return {"valid": False, "message": "Reset token has expired"}
    
    return {"valid": True, "email": reset_record.email}

