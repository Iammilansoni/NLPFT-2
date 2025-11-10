"""
Test Llama 3.2 3B model for slot extraction
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.nlp.llama_slot_extractor import get_llama_extractor


def test_llama_extraction():
    """Test Llama slot extraction with sample queries"""
    
    print("\n" + "="*60)
    print("Testing Llama 3.2 3B Slot Extraction")
    print("="*60 + "\n")
    
    # Initialize extractor
    extractor = get_llama_extractor()
    
    if not extractor.enabled:
        print("❌ Llama model not available!")
        print("\nPlease ensure:")
        print("1. Model is downloaded (run: python scripts/download_llama_model.py)")
        print("2. llama.cpp is installed")
        print("3. Environment variables are set in .env:")
        print("   LLAMA_MODEL_PATH=/path/to/llama-3.2-3b-instruct-q4_k_m.gguf")
        print("   LLAMA_CPP_PATH=/path/to/llama-cli")
        return
    
    print(f"✅ Llama model loaded: {extractor.model_path}\n")
    
    # Test cases
    test_cases = [
        {
            "query": "login with username john_doe and password SecureP@ss123",
            "intent": "login",
            "slot_definitions": [
                {"key": "username", "questions": ["What is the username?"], "required": True},
                {"key": "password", "questions": ["What is the password?"], "required": True}
            ]
        },
        {
            "query": "send password reset link to ali@gmail.com",
            "intent": "reset_password",
            "slot_definitions": [
                {"key": "email", "questions": ["What is the email address?"], "required": True}
            ]
        },
        {
            "query": "register new user with email test@example.com, name John Smith, and phone +1234567890",
            "intent": "register",
            "slot_definitions": [
                {"key": "email", "questions": ["What is the email?"], "required": True},
                {"key": "name", "questions": ["What is the name?"], "required": True},
                {"key": "phone", "questions": ["What is the phone number?"], "required": False}
            ]
        },
        {
            "query": "update my profile name to Milan Kumar",
            "intent": "update_profile",
            "slot_definitions": [
                {"key": "name", "questions": ["What is the new name?"], "required": True}
            ]
        }
    ]
    
    # Run tests
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['intent']}")
        print(f"Query: \"{test['query']}\"")
        print("Expected slots:", [s["key"] for s in test["slot_definitions"]])
        
        # Extract slots
        slots = extractor.extract_slots(
            query=test["query"],
            intent=test["intent"],
            slot_definitions=test["slot_definitions"]
        )
        
        print(f"Extracted: {slots}")
        
        # Validate
        required_keys = [s["key"] for s in test["slot_definitions"] if s.get("required")]
        missing = [k for k in required_keys if k not in slots]
        
        if missing:
            print(f"⚠️  Missing required slots: {missing}")
        else:
            print("✅ All required slots extracted")
        
        print("-" * 60 + "\n")
    
    print("="*60)
    print("Testing complete!")
    print("="*60)


if __name__ == "__main__":
    test_llama_extraction()
