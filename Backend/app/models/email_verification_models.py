"""
Email Verification Models - OTP-based email verification system

Handles:
- OTP generation and storage
- Email verification tracking
- Attempt limiting (max 5 attempts)
- Rate limiting (max 3 OTPs per hour)
- IP address tracking for security
"""

from sqlalchemy import Column, Text, TIMESTAMP, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.core.postgres import Base


class EmailVerification(Base):
    """
    Email verification table for OTP-based email verification
    
    Features:
    - 6-digit OTP codes
    - 10-minute expiry
    - Max 5 verification attempts per OTP
    - Rate limiting: max 3 OTPs per hour per email
    - IP address tracking for security audit
    """
    __tablename__ = "email_verification"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(Text, nullable=False, index=True)
    otp = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False)
    is_verified = Column(Boolean, nullable=False, default=False)
    attempts = Column(Integer, nullable=False, default=0)
    ip_address = Column(Text, nullable=True)
