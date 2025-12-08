"""
Authentication Service - User management and JWT tokens
"""

from datetime import datetime, timedelta
from typing import Optional
import uuid
import os
import hashlib
import base64

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database_models import User
from app.core.logger import logger
from app.core.config import settings

# Configuration - Use the same secret key as the rest of the application
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours default


class AuthService:
    """Handles authentication, user management, and JWT tokens"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with bcrypt (uses SHA-256 pre-hash for long passwords)"""
        # Pre-hash with SHA-256 and encode to base64 to stay within bcrypt's 72-byte limit
        password_hash = hashlib.sha256(password.encode('utf-8')).digest()
        password_b64 = base64.b64encode(password_hash).decode('utf-8')  # 44 chars, well under 72 bytes
        
        # Hash with bcrypt
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_b64.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash (uses SHA-256 pre-hash for long passwords)"""
        # Pre-hash with SHA-256 and encode to base64 to match the hashing process
        password_hash = hashlib.sha256(plain_password.encode('utf-8')).digest()
        password_b64 = base64.b64encode(password_hash).decode('utf-8')
        
        # Verify with bcrypt
        return bcrypt.checkpw(password_b64.encode('utf-8'), hashed_password.encode('utf-8'))
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """Decode JWT token"""
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError as e:
            logger.error(f"JWT decode error: {e}")
            return None
    
    @staticmethod
    async def create_user(db: AsyncSession, email: str, password: str, user_name: Optional[str] = None) -> User:
        """Create new user with hashed password"""
        user = User(
            u_id=uuid.uuid4(),
            email=email,
            password=AuthService.hash_password(password),
            user_name=user_name,
            created_at=datetime.utcnow()
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"Created user: {email}")
        return user
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID"""
        result = await db.execute(select(User).where(User.u_id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = await AuthService.get_user_by_email(db, email)
        if user and AuthService.verify_password(password, user.password):
            return user
        return None


# Singleton
_auth_service = AuthService()

def get_auth_service() -> AuthService:
    return _auth_service
