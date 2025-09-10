#!/usr/bin/env python3
"""
Test script for the Rule Engine component.

This script demonstrates the Rule Engine functionality with various
natural language inputs and shows the structured outputs.
"""

import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.nlp.rule_engine import RuleEngine


def test_rule_engine():
    """Test the Rule Engine with various input examples."""
    print("🚀 Testing NLPForge Rule Engine")
    print("=" * 50)
    
    # Initialize the rule engine
    try:
        engine = RuleEngine()
        print(f"✅ Rule Engine initialized with {len(engine.function_dictionary)} functions")
    except Exception as e:
        print(f"❌ Failed to initialize Rule Engine: {e}")
        return
    
    # Test cases
    test_cases = [
        "log in as admin with password123",
        "go to https://example.com",
        "click the login button",
        "enter email@test.com in #email",
        "wait until spinner appears",
        "verify user is logged in",
        "check success toast says 'Welcome'",
        "upload resume.pdf to #cv-input",
        "refresh the page",
        "invalid command that should not match"
    ]
    
    print(f"\n📝 Testing {len(test_cases)} cases:")
    print("-" * 50)
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n{i}. Input: '{test_input}'")
        try:
            steps = engine.parse(test_input)
            
            if steps:
                print(f"   ✅ Found {len(steps)} step(s):")
                for j, step in enumerate(steps, 1):
                    function = step.get("function", "unknown")
                    confidence = step.get("confidence", 0.0)
                    match_type = step.get("match_type", "unknown")
                    args = step.get("args", {})
                    
                    print(f"      {j}. Function: {function}")
                    print(f"         Confidence: {confidence:.2f}")
                    print(f"         Match Type: {match_type}")
                    if args:
                        print(f"         Arguments: {args}")
                    
                    if "unresolved_tokens" in step:
                        print(f"         Unresolved: {step['unresolved_tokens']}")
            else:
                print("   ❌ No matches found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test function info lookup
    print(f"\n🔍 Testing function lookup:")
    print("-" * 30)
    
    available_functions = engine.list_available_functions()
    print(f"Available functions: {len(available_functions)}")
    
    # Test a specific function
    if "login" in available_functions:
        func_info = engine.get_function_info("login")
        if func_info:
            print(f"\nLogin function info:")
            print(f"  ID: {func_info.get('id')}")
            print(f"  Name: {func_info.get('name')}")
            print(f"  Templates: {func_info.get('templates')}")
            print(f"  Signature: {func_info.get('signature')}")
    
    print(f"\n✅ Rule Engine testing completed!")


if __name__ == "__main__":
    test_rule_engine()
