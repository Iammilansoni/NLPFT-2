#!/usr/bin/env python3

import re

# Current regex patterns
_MULTI_FILL_RE = re.compile(
    r'(?:enter|type|fill|input|write|insert)\s+(?P<value>["\']?[^,"\']+["\']?)\s+(?:in|into|in the|into the|at|with)\s+(?P<selector>[^,;]+)',
    flags=re.IGNORECASE
)

_MULTI_FILL_ALT_RE = re.compile(
    r'(?P<selector>\b[\w\-\#\.\'"]+\b)\s+with\s+(?P<value>[^,;]+?)(?:\s+and\s+|$)',
    flags=re.IGNORECASE
)

def _split_multi_fill_from_text(matched_text: str):
    """
    Return list of (selector, value) pairs found in matched_text.
    Try the explicit pattern first, then the repeated 'X with Y and Z with W' pattern.
    """
    found = []
    if not matched_text:
        return found

    print(f"\n=== DEBUG: Testing '{matched_text}' ===")
    
    # First try the explicit "enter X in Y" style pattern
    print("Testing primary pattern...")
    for m in _MULTI_FILL_RE.finditer(matched_text):
        val = m.group("value").strip().strip('\'"')
        sel = m.group("selector").strip()
        print(f"  Found: selector='{sel}', value='{val}'")
        found.append((sel, val))

    if found:
        print(f"Primary pattern found {len(found)} matches, returning...")
        return found

    # Fallback: repeated "<selector> with <value>" occurrences separated by 'and'
    print("Testing fallback pattern...")
    for m in _MULTI_FILL_ALT_RE.finditer(matched_text):
        sel = m.group("selector").strip()
        val = m.group("value").strip().strip('\'"')
        print(f"  Raw match: selector='{sel}', value='{val}'")
        # Avoid picking up trailing connectors like 'and password' as part of selector
        # If selector contains known stopwords, trim them
        sel = re.sub(r'\b(with|and)\b.*$', '', sel, flags=re.IGNORECASE).strip()
        print(f"  Cleaned: selector='{sel}', value='{val}'")
        found.append((sel, val))

    print(f"Fallback pattern found {len(found)} matches")
    return found

if __name__ == "__main__":
    test_cases = [
        "Fill username with testuser and password with mypass123",
        "Enter john@example.com in the email field and type secret in the password field",
        "type user123 in username and pass456 in password"
    ]
    
    for case in test_cases:
        result = _split_multi_fill_from_text(case)
        print(f"Result: {result}")