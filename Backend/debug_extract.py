#!/usr/bin/env python3

import sys
import os
sys.path.append('app')

from nlp.new_assembler import _extract_multi_fill

def test_extract_multi_fill():
    original_text = "Fill username with testuser and password with mypass123"
    matched_text = "heuristic_fill"
    
    print(f"Original text: '{original_text}'")
    print(f"Matched text: '{matched_text}'")
    
    # Test what _extract_multi_fill returns
    result1 = _extract_multi_fill(matched_text)
    print(f"\n_extract_multi_fill(matched_text) = {result1}")
    
    result2 = _extract_multi_fill(original_text)
    print(f"_extract_multi_fill(original_text) = {result2}")
    
    result3 = _extract_multi_fill(matched_text or original_text)
    print(f"_extract_multi_fill(matched_text or original_text) = {result3}")

if __name__ == "__main__":
    test_extract_multi_fill()