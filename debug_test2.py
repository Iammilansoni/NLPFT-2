#!/usr/bin/env python3

import re

# Current regex patterns from new_assembler.py - UPDATED
_MULTI_FILL_RE = re.compile(
    r'(?:enter|type|insert|input|write)\s+(?P<value>["\']?[^,"\']+["\']?)\s+(?:in|into|at)\s+(?P<selector>[^,;]+)',
    flags=re.IGNORECASE
)

_MULTI_FILL_REPEATED = re.compile(
    r'(?:^|and\s+)(?P<field>[\w\s\-_#\.\'"]+?)\s+with\s+(?P<value>[^\s,;]+)(?=\s+and\s+|$)',
    flags=re.IGNORECASE
)

def debug_extract_multi_fill(matched_text: str):
    """Debug version of _extract_multi_fill"""
    print(f"=== DEBUGGING: '{matched_text}' ===")
    
    found = []
    if not matched_text:
        return found

    # Primary pass: patterns like "enter value in selector"
    print("\n1. Testing primary pattern (_MULTI_FILL_RE)...")
    for m in _MULTI_FILL_RE.finditer(matched_text):
        val = m.group("value").strip().strip('\'"')
        sel = m.group("selector").strip()
        print(f"   Found: selector='{sel}', value='{val}'")
        found.append((sel, val))
    if found:
        print(f"   PRIMARY PATTERN SUCCESS - returning {len(found)} pairs")
        return found

    # Fallback pass: repeated 'field with value' constructs
    print("\n2. Testing fallback pattern (_MULTI_FILL_REPEATED)...")
    for m in _MULTI_FILL_REPEATED.finditer(matched_text):
        field = m.group("field").strip()
        val = m.group("value").strip().strip('\'"')
        print(f"   Raw match: field='{field}', value='{val}'")
        # Clean field: remove action words and connectors
        field_clean = re.sub(r'^(fill|enter|type|input|write|insert|and)\s+', '', field, flags=re.IGNORECASE).strip()
        field_clean = re.sub(r'\b(with|and)\b.*$', '', field_clean, flags=re.IGNORECASE).strip()
        print(f"   Cleaned:   field='{field_clean}', value='{val}'")
        if field_clean:  # Only add if we have a valid field name
            found.append((field_clean, val))
    
    print(f"   FALLBACK PATTERN: returning {len(found)} pairs")
    return found

if __name__ == "__main__":
    # Test the specific failing case
    test_text = "Fill username with testuser and password with mypass123"
    result = debug_extract_multi_fill(test_text)
    print(f"\nFINAL RESULT: {result}")