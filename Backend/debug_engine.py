from app.nlp.enhanced_rule_engine import EnhancedRuleEngine

# Test the engine directly
engine = EnhancedRuleEngine()

test_cases = [
    'Enter john@example.com in the email field',
    'type secret in the password field', 
    'Fill username with testuser',
    'Select India from country dropdown'
]

for text in test_cases:
    print(f"Input: {text}")
    result = engine.parse(text)
    steps = result.get('steps', [])
    print(f"Steps: {len(steps)}")
    for i, step in enumerate(steps):
        func = step.get('function', 'unknown')
        args = step.get('args', {})
        conf = step.get('confidence', 0.0)
        print(f"  {i+1}. function='{func}', args={args}, confidence={conf}")
    print()