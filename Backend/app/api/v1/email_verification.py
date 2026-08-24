"""
Email Verification API - OTP-based email verification endpoints

Endpoints:
- POST /api/v1/auth/send-verification-otp - Send OTP to email
- POST /api/v1/auth/verify-otp - Verify OTP code
- POST /api/v1/auth/resend-otp - Resend OTP
"""

import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.core.postgres import get_db
from app.models.database_models import User
from app.models.email_verification_models import EmailVerification
from app.services.email_service import EmailService, get_email_service

router = APIRouter(prefix="/auth", tags=["email-verification"])
limiter = Limiter(key_func=get_remote_address)

# Dev-only endpoints are hidden from the OpenAPI schema in production
_DEV_MODE = os.getenv("ENVIRONMENT", "development").lower() != "production"


# --- Schemas ---

class SendOTPRequest(BaseModel):
    """Request to send OTP"""
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    """Request to verify OTP"""
    email: EmailStr
    otp: str


class OTPResponse(BaseModel):
    """Response for OTP operations"""
    success: bool
    message: str
    email: str
    expires_in_minutes: int | None = None


# --- Endpoints ---

@router.post("/send-verification-otp", response_model=OTPResponse)
@limiter.limit("5/minute")
async def send_verification_otp(
    request_data: SendOTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service)
):
    """
    Send OTP to email for verification
    
    - Generates 6-digit OTP
    - Sends email with OTP
    - OTP expires in 10 minutes
    - Can be called during registration or separately
    """
    try:
        email = request_data.email.lower()
        
        # Check if user exists
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found. Please register first."
            )
        
        # Check if already verified
        if user.email_verified == 1:
            return OTPResponse(
                success=True,
                message="Email already verified",
                email=email,
                expires_in_minutes=None
            )
        
        # Invalidate any existing OTPs for this email
        existing_otps = select(EmailVerification).where(
            and_(
                EmailVerification.email == email,
                EmailVerification.is_verified.is_(False)
            )
        )
        result = await db.execute(existing_otps)
        for old_otp in result.scalars():
            old_otp.is_verified = True  # Mark as used/invalid
        
        # Generate new OTP
        otp = email_service.generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        # Store OTP in database
        verification = EmailVerification(
            email=email,
            otp=otp,
            expires_at=expires_at,
            ip_address=request.client.host if request.client else None
        )
        db.add(verification)
        await db.commit()

        # Send email
        username = user.user_name or email.split('@')[0]
        sent = email_service.send_verification_email(email, otp, username)

        if not sent:
            logger.warning(f"Email not sent, OTP created for {email}")

        logger.info(f"OTP sent to {email} (expires in 10 minutes)")

        return OTPResponse(
            success=True,
            message="OTP sent to your email. Please check your inbox (and spam folder).",
            email=email,
            expires_in_minutes=10
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending OTP: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP: {str(e)}"
        )


@router.post("/verify-otp", response_model=OTPResponse)
@limiter.limit("10/minute")
async def verify_otp(
    request_data: VerifyOTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify OTP code
    
    - Validates OTP
    - Checks expiry
    - Marks user as verified
    - Limits to 5 attempts
    """
    try:
        email = request_data.email.lower()
        otp = request_data.otp.strip()
        
        # Get user
        user_query = select(User).where(User.email == email)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if already verified
        if user.email_verified == 1:
            return OTPResponse(
                success=True,
                message="Email already verified",
                email=email
            )
        
        # Get latest OTP for this email
        otp_query = select(EmailVerification).where(
            and_(
                EmailVerification.email == email,
                EmailVerification.is_verified.is_(False)
            )
        ).order_by(EmailVerification.created_at.desc())
        
        otp_result = await db.execute(otp_query)
        verification = otp_result.scalar_one_or_none()
        
        if not verification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No OTP found. Please request a new OTP."
            )
        
        # Check if OTP expired
        if datetime.utcnow() > verification.expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP expired. Please request a new OTP."
            )
        
        # Check attempts limit
        if verification.attempts >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Please request a new OTP."
            )
        
        # Verify OTP
        if verification.otp != otp:
            verification.attempts += 1
            await db.commit()
            
            remaining = 5 - verification.attempts
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid OTP. {remaining} attempts remaining."
            )
        
        # OTP is valid - mark user as verified
        user.email_verified = 1
        verification.is_verified = True
        await db.commit()
        
        logger.info(f"Email verified for user: {email}")
        
        return OTPResponse(
            success=True,
            message="Email verified successfully! You can now login.",
            email=email
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying OTP: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify OTP: {str(e)}"
        )


@router.post("/resend-otp", response_model=OTPResponse)
@limiter.limit("3/minute")
async def resend_otp(
    request_data: SendOTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    email_service: EmailService = Depends(get_email_service)
):
    """
    Resend OTP to email
    
    - Generates new OTP
    - Invalidates old OTPs
    - Rate limited to prevent abuse
    """
    try:
        email = request_data.email.lower()
        
        # Get user
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.email_verified == 1:
            return OTPResponse(
                success=True,
                message="Email already verified",
                email=email
            )
        
        # Check rate limiting - max 3 OTPs per hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_otps = select(EmailVerification).where(
            and_(
                EmailVerification.email == email,
                EmailVerification.created_at > one_hour_ago
            )
        )
        result = await db.execute(recent_otps)
        count = len(result.scalars().all())
        
        if count >= 3:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many OTP requests. Please try again in 1 hour."
            )
        
        # Invalidate existing OTPs
        existing_otps = select(EmailVerification).where(
            and_(
                EmailVerification.email == email,
                EmailVerification.is_verified.is_(False)
            )
        )
        result = await db.execute(existing_otps)
        for old_otp in result.scalars():
            old_otp.is_verified = True
        
        # Generate new OTP
        otp = email_service.generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        verification = EmailVerification(
            email=email,
            otp=otp,
            expires_at=expires_at,
            ip_address=request.client.host if request.client else None
        )
        db.add(verification)
        await db.commit()
        
        # Send email
        username = user.user_name or email.split('@')[0]
        sent = email_service.send_resend_otp_email(email, otp, username)

        if not sent:
            logger.warning(f"Email not sent, OTP created for {email}")

        logger.info(f"OTP resent to {email}")
        
        return OTPResponse(
            success=True,
            message="New OTP sent to your email",
            email=email,
            expires_in_minutes=10
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resending OTP: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resend OTP: {str(e)}"
        )


@router.get("/verification-status/{email}")
async def check_verification_status(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Check if email is verified
    
    Returns verification status for given email
    """
    try:
        email = email.lower()
        
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "email": email,
            "verified": bool(user.email_verified),
            "user_id": str(user.u_id)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking verification status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check verification status"
        )


# =============================================================================
# DEV-ONLY ENDPOINTS — Blocked in production (ENVIRONMENT=production)
# =============================================================================

@router.get("/dev/otp/{email}", include_in_schema=_DEV_MODE)
async def dev_get_otp(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """
    [DEV ONLY] Retrieve the latest pending OTP for an email directly from the DB.

    Blocked in production. Use this when SMTP is not reachable during local dev.
    """
    import os
    if os.getenv("ENVIRONMENT", "development").lower() == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in development mode."
        )

    email = email.lower()

    otp_query = (
        select(EmailVerification)
        .where(
            and_(
                EmailVerification.email == email,
                EmailVerification.is_verified.is_(False),
            )
        )
        .order_by(EmailVerification.created_at.desc())
    )
    result = await db.execute(otp_query)
    verification = result.scalar_one_or_none()

    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending OTP found. Register or request a new OTP first."
        )

    expired = datetime.utcnow() > verification.expires_at
    return {
        "email": email,
        "otp": verification.otp,
        "expires_at": verification.expires_at.isoformat(),
        "expired": expired,
        "attempts_used": verification.attempts,
        "note": "Use this OTP at POST /api/v1/auth/verify-otp"
    }


@router.post("/dev/verify-direct", include_in_schema=_DEV_MODE)
async def dev_verify_direct(
    request_data: SendOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    [DEV ONLY] Mark an email as verified WITHOUT needing the OTP.

    Blocked in production. Use this to unblock login when SMTP is unavailable.
    """
    import os
    if os.getenv("ENVIRONMENT", "development").lower() == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in development mode."
        )

    email = request_data.email.lower()

    user_query = select(User).where(User.email == email)
    result = await db.execute(user_query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please register first."
        )

    if user.email_verified == 1:
        return {"success": True, "message": "Email was already verified.", "email": email}

    user.email_verified = 1
    await db.commit()

    logger.warning(f"[DEV] Email directly verified (OTP bypassed) for: {email}")
    return {
        "success": True,
        "message": "Email verified (dev bypass). You can now log in.",
        "email": email
    }
