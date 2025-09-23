#!/usr/bin/env python3
"""
Test the extractors to see why they're not working.
"""
import re

# Current extractors
extractors = {
    'username': re.compile(r'\b(?:username|user)\s+([A-Za-z0-9_.-]+)', re.IGNORECASE),
    'password': re.compile(r'\b(?:password|pass|pwd)\s+([^\s,;]+)', re.IGNORECASE),
}

test_text = "Login with username admin and password admin@12"

print(f"Testing: {test_text}")
print()

for name, pattern in extractors.items():
    match = pattern.search(test_text)
    if match:
        print(f"✅ {name}: {match.group(1)}")
    else:
        print(f"❌ {name}: No match")
        
print()
print("Debugging the patterns:")
print("Username pattern:", extractors['username'].pattern)
print("Password pattern:", extractors['password'].pattern)

# Let's test what the patterns actually match
print()
print("Test with different inputs:")
test_cases = [
    "username admin",
    "username: admin", 
    "with username admin",
    "password admin@12",
    "password: admin@12",
    "and password admin@12"
]

for test in test_cases:
    print(f"Input: '{test}'")
    u_match = extractors['username'].search(test)
    p_match = extractors['password'].search(test)
    if u_match:
        print(f"  Username: {u_match.group(1)}")
    if p_match:
        print(f"  Password: {p_match.group(1)}")
    print()