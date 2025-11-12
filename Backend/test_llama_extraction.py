"""
Test script for Llama 3.2 3B slot extraction
Run this to verify your setup is working correctly
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.nlp.llama_slot_extractor import get_llama_extractor
from app.nlp.query_parser import get_query_parser

def test_llama_availability():
    """Test if Llama model is available"""
    print("=" * 60)
    print("Testing Llama 3.2 3B Availability")
    print("=" * 60)
    
    extractor = get_llama_extractor()
    
    if extractor.enabled:
        print("✅ Llama 3.2 3B is available!")
        print(f"   Model: {extractor.model_path}")
        print(f"   llama-cli: {extractor.llama_cpp_path}")
    else:
        print("⚠️  Llama 3.2 3B is NOT available")
        print("   Slot extraction will use fallback methods (spaCy + regex)")
        print("\n   To enable Llama:")
        print("   1. Download model: See LLAMA_SETUP.md")
        print("   2. Set LLAMA_MODEL_PATH in .env")
        print("   3. Install llama.cpp: See LLAMA_SETUP.md")
    
    print()
    return extractor.enabled


def test_direct_extraction():
    """Test direct slot extraction with Llama"""
    print("=" * 60)
    print("Testing Direct Llama Extraction")
    print("=" * 60)
    
    extractor = get_llama_extractor()
    
    if not extractor.enabled:
        print("⚠️  Skipping (Llama not available)")
        return
    
    # Test queries
    test_cases = [
        {
            "query": "Update my profile with the credential as John and July123",
            "intent": "update_profile",
            "slots": [
                {"key": "username", "questions": ["What is the username?"]},
                {"key": "password", "questions": ["What is the password?"]},
                {"key": "name", "questions": ["What is the user's name?"]}
            ],
            "expected": {"username": "John", "password": "July123"}
        },
        {
            "query": "Login with milan.soni and SecurePass2024!",
            "intent": "login",
            "slots": [
                {"key": "username", "questions": ["What is the username?"]},
                {"key": "password", "questions": ["What is the password?"]}
            ],
            "expected": {"username": "milan.soni", "password": "SecurePass2024!"}
        },
        {
            "query": "Sign up with email test@example.com and phone +1-555-0123",
            "intent": "signup",
            "slots": [
                {"key": "email", "questions": ["What is the email?"]},
                {"key": "phone", "questions": ["What is the phone number?"]}
            ],
            "expected": {"email": "test@example.com", "phone": "+1-555-0123"}
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['query']}")
        print(f"Intent: {test['intent']}")
        
        slots = extractor.extract_slots(
            test["query"],
            test["intent"],
            test["slots"]
        )
        
        print(f"Extracted: {slots}")
        print(f"Expected:  {test['expected']}")
        
        # Check if extraction matches expected
        matches = all(
            slots.get(k) == v 
            for k, v in test["expected"].items()
        )
        
        if matches:
            print("✅ PASS")
        else:
            print("❌ FAIL")
    
    print()


def test_full_pipeline():
    """Test full query parsing pipeline with Llama"""
    print("=" * 60)
    print("Testing Full Query Parser Pipeline")
    print("=" * 60)
    
    parser = get_query_parser()
    
    test_queries = [
        "Update my profile with the credential as John and July123",
        "Login with username admin and password SuperSecret!",
        "Sign up with email john@example.com",
        "Change my password to NewPass2024",
        "Authenticate with Milan and MS3ESD"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = parser.parse(query)
        
        print(f"  Intent: {result['intent']} (confidence: {result['confidence']:.2f})")
        print(f"  Slots: {result['slots']}")
        
        # Show extraction sources
        metadata = result.get('metadata', {})
        if metadata.get('slots_llama'):
            print(f"  📊 Llama extracted: {metadata['slots_llama']}")
        if metadata.get('slots_spacy'):
            print(f"  🔍 spaCy found: {metadata['slots_spacy']}")
        if metadata.get('slots_regex'):
            print(f"  🔤 Regex matched: {metadata['slots_regex']}")
        if metadata.get('slots_contextual'):
            print(f"  🎯 Contextual: {metadata['slots_contextual']}")
    
    print()


def test_performance():
    """Test extraction performance"""
    print("=" * 60)
    print("Testing Extraction Performance")
    print("=" * 60)
    
    extractor = get_llama_extractor()
    
    if not extractor.enabled:
        print("⚠️  Skipping (Llama not available)")
        return
    
    import time
    
    query = "Login with username testuser and password TestPass123!"
    intent = "login"
    slots_def = [
        {"key": "username", "questions": ["What is the username?"]},
        {"key": "password", "questions": ["What is the password?"]}
    ]
    
    # Warmup
    print("Warming up...")
    extractor.extract_slots(query, intent, slots_def)
    
    # Benchmark
    print("Running benchmark (5 iterations)...")
    times = []
    
    for i in range(5):
        start = time.time()
        slots = extractor.extract_slots(query, intent, slots_def)
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  Run {i+1}: {elapsed:.2f}s - Extracted: {slots}")
    
    avg_time = sum(times) / len(times)
    print(f"\n📊 Average extraction time: {avg_time:.2f}s")
    
    if avg_time < 1.0:
        print("✅ Excellent performance! (<1s)")
    elif avg_time < 3.0:
        print("✅ Good performance (1-3s)")
    else:
        print("⚠️  Slow performance (>3s) - Consider GPU acceleration")
    
    print()


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Llama 3.2 3B Slot Extraction Test Suite")
    print("=" * 60 + "\n")
    
    # Test 1: Availability
    llama_available = test_llama_availability()
    
    # Test 2: Direct extraction (only if available)
    if llama_available:
        test_direct_extraction()
        test_performance()
    
    # Test 3: Full pipeline (works with or without Llama)
    test_full_pipeline()
    
    print("=" * 60)
    print("Test Suite Complete!")
    print("=" * 60)
    
    if not llama_available:
        print("\n💡 TIP: Install Llama 3.2 3B for better slot extraction")
        print("   See LLAMA_SETUP.md for installation instructions")


if __name__ == "__main__":
    main()
