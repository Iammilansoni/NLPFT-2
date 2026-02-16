"""
Unit Tests for Authentication Service
======================================
Tests password hashing, JWT generation, and user authentication logic.
"""

import pytest
from datetime import datetime, timedelta
from jose import jwt

from app.services.auth_service import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)
from app.core.config import settings


@pytest.mark.unit
class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password(self):
        """Test password hashing produces different hash each time."""
        password = "SecurePassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2  # Hashes should differ due to salt
        assert len(hash1) > 50  # bcrypt hashes are long
    
    def test_verify_correct_password(self):
        """Test correct password verification."""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_wrong_password(self):
        """Test wrong password verification fails."""
        password = "SecurePassword123!"
        wrong_password = "WrongPassword456!"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_empty_password(self):
        """Test empty password verification fails."""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        
        assert verify_password("", hashed) is False


@pytest.mark.unit
class TestJWTTokens:
    """Test JWT token creation and decoding."""
    
    def test_create_access_token(self):
        """Test JWT token creation."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(user_id)
        
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are long
        assert "." in token  # JWT format: header.payload.signature
    
    def test_decode_valid_token(self):
        """Test decoding valid JWT token."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(user_id)
        
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert "exp" in payload
    
    def test_decode_expired_token(self):
        """Test decoding expired JWT token fails."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        
        # Create token with past expiration
        expires_delta = timedelta(minutes=-30)
        expire = datetime.utcnow() + expires_delta
        to_encode = {"sub": user_id, "exp": expire}
        token = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
        
        payload = decode_access_token(token)
        assert payload is None  # Expired tokens return None
    
    def test_decode_invalid_token(self):
        """Test decoding invalid JWT token fails."""
        invalid_token = "invalid.token.string"
        
        payload = decode_access_token(invalid_token)
        assert payload is None
    
    def test_decode_token_wrong_signature(self):
        """Test decoding token with wrong signature fails."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        
        # Create token with different secret
        wrong_secret = "wrong_secret_key_12345"
        to_encode = {"sub": user_id, "exp": datetime.utcnow() + timedelta(hours=1)}
        token = jwt.encode(to_encode, wrong_secret, algorithm="HS256")
        
        payload = decode_access_token(token)
        assert payload is None
    
    def test_token_expiration_time(self):
        """Test token has correct expiration time."""
        import os
        configured_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(user_id)
        
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        
        # Token should expire ~configured_minutes from now
        expected_expiry = datetime.utcnow() + timedelta(minutes=configured_minutes)
        time_diff = abs((exp_datetime - expected_expiry).total_seconds())
        
        assert time_diff < 10  # Within 10 seconds tolerance
