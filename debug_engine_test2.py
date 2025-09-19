#!/usr/bin/env python3

import sys
import os
sys.path.append('app')

from nlp.enhanced_rule_engine import EnhancedRuleEngine
from nlp.new_assembler import assemble_steps

def debug_test_case_2():
    # Initialize the Enhanced Rule Engine
    engine = EnhancedRuleEngine()
    
    # Test Case 2: the problematic one
    text = "Fill username with testuser and password with mypass123"
    print(f"=== DEBUGGING TEST CASE 2 ===")
    print(f"Input: {text}")
    
    # Get raw steps from engine
    raw_result = engine.parse(text)
    print(f"\nRaw engine result:")
    print(f"Steps: {raw_result.get('steps', [])}")
    print(f"Unresolved: {raw_result.get('unresolved_tokens', [])}")
    print(f"Overall confidence: {raw_result.get('overall_confidence', 0)}")
    
    # Show each step in detail
    for i, step in enumerate(raw_result.get('steps', []), 1):
        print(f"\nStep {i}:")
        for key, value in step.items():
            print(f"  {key}: {value}")
    
    # Now test the assembler with original text parameter
    print(f"\n=== TESTING ASSEMBLER ===")
    assembled_result = assemble_steps(raw_result.get('steps', []), text)  # Pass original text
    print(f"Assembled steps: {len(assembled_result.get('steps', []))}")
    
    for i, step in enumerate(assembled_result.get('steps', []), 1):
        print(f"\nAssembled Step {i}:")
        for key, value in step.items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    debug_test_case_2()