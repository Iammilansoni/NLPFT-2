"""
Password Reset Models - Token-based password reset system

Handles:
- Secure token generation
- Token expiry (1 hour)
- Single-use tokens (marked as used after reset)
"""

from sqlalchemy import Column, Text, TIMESTAMP, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

from app.core.postgres import Base


class PasswordReset(Base):
    """
    Password reset token table
    
    Features:
    - Secure random tokens
    - 1-hour expiry
    - Single-use (is_used flag)
    - IP address tracking for security
    """
    __tablename__ = "password_reset"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(Text, nullable=False, index=True)
    token = Column(Text, nullable=False, unique=True, index=True)
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False)
    is_used = Column(Boolean, nullable=False, default=False)
    ip_address = Column(Text, nullable=True)
