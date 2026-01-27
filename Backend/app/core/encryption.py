"""
API Key Encryption Service - Secure storage for sensitive credentials

Uses Fernet symmetric encryption for API keys stored in the database.
The encryption key should be stored as SECRET_KEY_ENCRYPTION in .env.

Security Features:
- Fernet symmetric encryption (AES-128-CBC)
- URL-safe base64 encoding
- Timestamp-based key rotation support
- Key never logged or exposed

Usage:
    from app.core.encryption import get_encryption_service
    
    encryptor = get_encryption_service()
    
    # Encrypt before storage
    encrypted = encryptor.encrypt("sk-secret-api-key")
    
    # Decrypt when needed
    decrypted = encryptor.decrypt(encrypted)
"""

import os
import base64
from typing import Optional
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.logger import logger


# =============================================================================
# EXCEPTIONS
# =============================================================================

class EncryptionError(Exception):
    """Base encryption error"""
    pass


class DecryptionError(EncryptionError):
    """Failed to decrypt (invalid key or corrupted data)"""
    pass


class EncryptionKeyError(EncryptionError):
    """Encryption key not configured or invalid"""
    pass


# =============================================================================
# ENCRYPTION SERVICE
# =============================================================================

class APIKeyEncryption:
    """
    Secure encryption service for API keys and secrets.
    
    Uses Fernet symmetric encryption which provides:
    - AES-128 in CBC mode
    - HMAC using SHA256 for authentication
    - Timestamp for optional TTL
    
    The encryption key is derived from SECRET_KEY_ENCRYPTION env var
    using PBKDF2 for additional security.
    """
    
    # Salt for key derivation (can be app-specific)
    _SALT = b"nlpforge_api_key_encryption_v1"
    _ITERATIONS = 100_000
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize encryption service.
        
        Args:
            secret_key: Encryption key. If not provided, reads from
                       SECRET_KEY_ENCRYPTION environment variable.
        """
        self._secret_key = secret_key or os.getenv("SECRET_KEY_ENCRYPTION")
        self._fernet: Optional[Fernet] = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Initialize Fernet cipher on first use"""
        if self._initialized:
            return
        
        if not self._secret_key:
            raise EncryptionKeyError(
                "SECRET_KEY_ENCRYPTION not set. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        
        try:
            # Derive a proper Fernet key from the secret
            fernet_key = self._derive_key(self._secret_key)
            self._fernet = Fernet(fernet_key)
            self._initialized = True
            logger.info("✅ API key encryption service initialized")
        except Exception as e:
            raise EncryptionKeyError(f"Invalid encryption key: {e}")
    
    def _derive_key(self, secret: str) -> bytes:
        """
        Derive a Fernet-compatible key from the secret.
        
        Uses PBKDF2 to create a 32-byte key, then base64 encodes
        to create a valid Fernet key.
        
        Args:
            secret: Raw secret string
            
        Returns:
            Base64-encoded Fernet key
        """
        # If it's already a valid Fernet key, use it directly
        try:
            if len(secret) == 44 and secret.endswith("="):
                # Looks like a Fernet key, validate it
                Fernet(secret.encode())
                return secret.encode()
        except Exception:
            pass
        
        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._SALT,
            iterations=self._ITERATIONS,
        )
        
        key = kdf.derive(secret.encode())
        return base64.urlsafe_b64encode(key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.
        
        Args:
            plaintext: String to encrypt (e.g., API key)
            
        Returns:
            Encrypted string (base64 encoded)
        """
        if not plaintext:
            return ""
        
        self._ensure_initialized()
        
        try:
            encrypted_bytes = self._fernet.encrypt(plaintext.encode("utf-8"))
            return encrypted_bytes.decode("utf-8")
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {e}")
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string.
        
        Args:
            ciphertext: Encrypted string from encrypt()
            
        Returns:
            Original plaintext string
        """
        if not ciphertext:
            return ""
        
        self._ensure_initialized()
        
        try:
            decrypted_bytes = self._fernet.decrypt(ciphertext.encode("utf-8"))
            return decrypted_bytes.decode("utf-8")
        except InvalidToken:
            raise DecryptionError(
                "Failed to decrypt. Key may have changed or data is corrupted."
            )
        except Exception as e:
            raise DecryptionError(f"Decryption failed: {e}")
    
    def rotate_key(self, old_ciphertext: str, new_encryptor: "APIKeyEncryption") -> str:
        """
        Re-encrypt data with a new key.
        
        Args:
            old_ciphertext: Data encrypted with current key
            new_encryptor: Encryptor with new key
            
        Returns:
            Data encrypted with new key
        """
        plaintext = self.decrypt(old_ciphertext)
        return new_encryptor.encrypt(plaintext)
    
    def mask_key(self, api_key: str, visible_chars: int = 4) -> str:
        """
        Create a masked version of an API key for display.
        
        Args:
            api_key: Full API key
            visible_chars: Characters to show at start and end
            
        Returns:
            Masked string like "sk-ab...xy"
        """
        if not api_key:
            return ""
        
        if len(api_key) <= visible_chars * 2:
            return "*" * len(api_key)
        
        return f"{api_key[:visible_chars]}...{api_key[-visible_chars:]}"
    
    @classmethod
    def generate_key(cls) -> str:
        """
        Generate a new Fernet encryption key.
        
        Returns:
            Base64-encoded key suitable for SECRET_KEY_ENCRYPTION
        """
        return Fernet.generate_key().decode()
    
    def is_configured(self) -> bool:
        """Check if encryption is properly configured"""
        try:
            self._ensure_initialized()
            return True
        except EncryptionKeyError:
            return False


# =============================================================================
# SINGLETON ACCESSOR
# =============================================================================

@lru_cache(maxsize=1)
def get_encryption_service() -> APIKeyEncryption:
    """
    Get the singleton encryption service.
    
    Returns:
        Configured APIKeyEncryption instance
    """
    return APIKeyEncryption()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key for storage"""
    return get_encryption_service().encrypt(api_key)


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt a stored API key"""
    return get_encryption_service().decrypt(encrypted_key)


def mask_api_key(api_key: str) -> str:
    """Create masked display version of key"""
    return get_encryption_service().mask_key(api_key)


def is_encryption_configured() -> bool:
    """Check if encryption is configured"""
    return get_encryption_service().is_configured()


def generate_encryption_key() -> str:
    """Generate a new encryption key"""
    return APIKeyEncryption.generate_key()
