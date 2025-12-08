"""
Redis Security - Key validation for multi-tenant isolation
"""

import uuid
from typing import Optional
from app.core.logger import logger


class RedisAccessDeniedError(Exception):
    """Raised when user tries to access Redis key they don't own"""
    pass


class RedisKeyValidator:
    """Validates Redis key access for multi-tenant security"""
    
    @staticmethod
    def validate_embedding_key(redis_key: str, user_id: uuid.UUID) -> bool:
        """
        Validate that Redis embedding key belongs to user
        Format: embedding:{user_id}:{t_id}:{csv_id}
        """
        if not redis_key or not user_id:
            return False
        
        if not redis_key.startswith("embedding:"):
            logger.warning(f"Invalid key format: {redis_key}")
            return False
        
        try:
            parts = redis_key.split(":")
            if len(parts) < 2:
                return False
            
            key_user_id = parts[1]
            if key_user_id == str(user_id):
                return True
            
            logger.warning(f"Access denied: User {user_id} tried to access {redis_key}")
            return False
        except Exception as e:
            logger.error(f"Error validating key: {e}")
            return False
    
    @staticmethod
    def generate_safe_embedding_key(user_id: uuid.UUID, t_id: Optional[uuid.UUID] = None,
                                    csv_id: Optional[uuid.UUID] = None) -> str:
        """Generate safe Redis key: embedding:{user_id}:{t_id}:{csv_id}"""
        return f"embedding:{user_id}:{t_id or 'none'}:{csv_id or 'none'}"


def validate_embedding_access(redis_key: str, user_id: uuid.UUID) -> None:
    """
    Validate user access to embedding key, raise exception if denied
    
    Raises:
        RedisAccessDeniedError: If user doesn't own the key
    """
    validator = RedisKeyValidator()
    if not validator.validate_embedding_key(redis_key, user_id):
        raise RedisAccessDeniedError(
            f"Access denied: User {user_id} cannot access {redis_key}"
        )
