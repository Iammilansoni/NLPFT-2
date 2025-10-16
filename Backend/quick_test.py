"""
Quick test of improved entity extraction
"""
from JSONoutput_generator import answer
import json

print("🔧 Testing Improved JSON Output Generator\n")

# Your original problematic query
query = "Please validate confedential avadhi and avdhi@123"

print(f"Query: {query}")
print("\nResult:")
result = answer(query)
print(json.dumps(result, indent=2))

print("\n" + "="*70)
print("Expected Improvements:")
print("="*70)
print("✅ API should be 'login' (not 'register')")
print("✅ Should extract username: 'confedential' or 'avadhi'")
print("✅ Should extract password: 'avdhi@123'")
print("✅ No confusing 'matched_query' field")
print("="*70)
