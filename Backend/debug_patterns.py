import re

# Test the fill pattern
pattern = r'\b(?:enter|type|fill|input|write|insert)\s+(?P<value>["\']?[^,"\']+["\']?)\s+(?:in|into|into the|in the|at|with)\s+(?P<selector>.+)$'
alt_pattern = r'\b(?:fill)\s+(?P<selector>[^,]+?)\s+(?:with)\s+(?P<value>["\']?[^,"\']+["\']?)$'
test_cases = [
    'Enter john@example.com in the email field',
    'type secret in the password field', 
    'Fill username with testuser',
    'Type Hello World in the search box'
]

print("Testing fill pattern:")
for text in test_cases:
    m = re.search(pattern, text, flags=re.IGNORECASE)
    if not m:
        m = re.search(alt_pattern, text, flags=re.IGNORECASE)
    print(f"Text: {text}")
    print(f"Match: {m.groupdict() if m else 'No match'}")
    print()

# Test click pattern  
click_pattern = r'\b(?:click|press|tap|choose|select|hit)\s+(?:on\s+)?(?:the\s+)?(?P<selector>.+)'
click_tests = [
    'click on the profile link',
    'click search button',
    'click #submit'
]

print("Testing click pattern:")
for text in click_tests:
    m = re.search(click_pattern, text, flags=re.IGNORECASE)
    print(f"Text: {text}")
    print(f"Match: {m.groupdict() if m else 'No match'}")
    print()

# Test select pattern
select_pattern = r'\b(?:select|choose)\s+(?P<value>[^,]+?)\s+(?:from|in|in the|from the)\s+(?P<selector>.+)'
select_tests = [
    'Select India from country dropdown',
    'choose India in country'
]

print("Testing select pattern:")
for text in select_tests:
    m = re.search(select_pattern, text, flags=re.IGNORECASE)
    print(f"Text: {text}")
    print(f"Match: {m.groupdict() if m else 'No match'}")
    print()