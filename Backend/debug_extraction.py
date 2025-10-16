"""Debug entity extraction"""
import re

text = "Please validate confedential avadhi and avdhi@123"

print("Testing extraction patterns:")
print(f"Text: {text}")
print()

# Test email
email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
email_match = re.search(email_pattern, text)
print(f"Email: {email_match.group(0) if email_match else 'Not found'}")

# Test password - improved pattern
password_patterns = [
    r'\b([A-Za-z][A-Za-z0-9@#$%^&*!_-]{5,})\b',  # Start with letter, at least 6 chars
    r'(?:password|pass|pwd|secret)[\s:=]+([^\s]+)',  # After keyword
]

print("\nPassword patterns:")
for i, pattern in enumerate(password_patterns):
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        result = match.group(1) if match.lastindex else match.group(0)
        print(f"  Pattern {i+1}: {result}")

# Test username - look for words before password-like strings
words = text.split()
print(f"\nWords: {words}")

# Find password candidate
for word in words:
    if re.match(r'[A-Za-z0-9@#$%^&*!_-]{6,}', word) and ('@' in word or any(c.isdigit() for c in word)):
        print(f"Password candidate: {word}")
        
        # Get word before it as username
        idx = words.index(word)
        if idx > 0:
            username_candidate = words[idx - 1]
            if len(username_candidate) > 2 and username_candidate.lower() not in ['and', 'the', 'with', 'please', 'validate']:
                print(f"Username candidate: {username_candidate}")
