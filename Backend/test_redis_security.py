"""
Test Redis Security - Validate key access control
Run with: python test_redis_security.py
"""

import uuid
from app.core.redis_security import (
    RedisKeyValidator,
    validate_user_access,
    RedisAccessDeniedError
)

def test_redis_key_validation():
    """Test Redis key validation"""
    print("\n=== Testing Redis Key Validation ===\n")
    
    validator = RedisKeyValidator()
    user1_id = uuid.uuid4()
    user2_id = uuid.uuid4()
    
    # Test 1: Valid key for correct user
    print("Test 1: Valid key for correct user")
    key1 = f"embedding:{user1_id}:template-123:csv-456"
    result = validator.validate_embedding_key(key1, user1_id)
    print(f"  Key: {key1}")
    print(f"  User: {user1_id}")
    print(f"  Result: {'✅ PASS' if result else '❌ FAIL'}")
    assert result == True, "Should allow access to own key"
    
    # Test 2: Invalid key for different user
    print("\nTest 2: Invalid key for different user")
    result = validator.validate_embedding_key(key1, user2_id)
    print(f"  Key: {key1}")
    print(f"  User: {user2_id}")
    print(f"  Result: {'✅ PASS (blocked)' if not result else '❌ FAIL (allowed!)'}")
    assert result == False, "Should block access to other user's key"
    
    # Test 3: Invalid key format
    print("\nTest 3: Invalid key format")
    invalid_key = "invalid:key:format"
    result = validator.validate_embedding_key(invalid_key, user1_id)
    print(f"  Key: {invalid_key}")
    print(f"  Result: {'✅ PASS (blocked)' if not result else '❌ FAIL (allowed!)'}")
    assert result == False, "Should reject invalid key format"
    
    # Test 4: Generate safe key
    print("\nTest 4: Generate safe key")
    safe_key = validator.generate_safe_embedding_key(user1_id, uuid.uuid4(), uuid.uuid4())
    print(f"  Generated: {safe_key}")
    result = validator.validate_embedding_key(safe_key, user1_id)
    print(f"  Validation: {'✅ PASS' if result else '❌ FAIL'}")
    assert result == True, "Generated key should be valid"
    
    # Test 5: Extract user_id from key
    print("\nTest 5: Extract user_id from key")
    extracted_id = validator.extract_user_id_from_key(key1)
    print(f"  Key: {key1}")
    print(f"  Extracted: {extracted_id}")
    print(f"  Expected: {user1_id}")
    print(f"  Result: {'✅ PASS' if extracted_id == str(user1_id) else '❌ FAIL'}")
    assert extracted_id == str(user1_id), "Should extract correct user_id"
    
    # Test 6: Exception on access denied
    print("\nTest 6: Exception on access denied")
    try:
        validate_user_access(key1, user2_id, key_type="embedding")
        print("  ❌ FAIL - No exception raised!")
        assert False, "Should raise RedisAccessDeniedError"
    except RedisAccessDeniedError as e:
        print(f"  ✅ PASS - Exception raised: {e}")
    
    # Test 7: No exception on valid access
    print("\nTest 7: No exception on valid access")
    try:
        validate_user_access(key1, user1_id, key_type="embedding")
        print("  ✅ PASS - Access granted")
    except RedisAccessDeniedError as e:
        print(f"  ❌ FAIL - Exception raised: {e}")
        assert False, "Should not raise exception for valid access"
    
    # Test 8: API key validation
    print("\nTest 8: API key validation")
    api_key = "api:abc123hash"
    result = validator.validate_api_key(api_key)
    print(f"  Key: {api_key}")
    print(f"  Result: {'✅ PASS' if result else '❌ FAIL'}")
    assert result == True, "Should validate API key format"
    
    print("\n" + "="*50)
    print("✅ All tests passed!")
    print("="*50 + "\n")


if __name__ == "__main__":
    test_redis_key_validation()
