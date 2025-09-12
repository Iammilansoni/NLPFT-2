#!/usr/bin/env python3
"""
Test script for the enhanced convert endpoint with compound sentence handling.
"""

import requests
import json

# Test the enhanced convert endpoint
def test_convert_endpoint():
    url = "http://localhost:8000/api/v1/convert/"
    
    # Test case: compound sentence that should detect 2 functions
    test_data = {
        "text": "Login with username admin and password secret123, go to www.google.com"
    }
    
    try:
        print(f"Testing convert endpoint with: {test_data['text']}")
        print("-" * 60)
        
        response = requests.post(url, json=test_data, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Count detected functions
            functions = result.get('functions', [])
            print(f"\n✅ SUCCESS: Detected {len(functions)} functions:")
            for i, func in enumerate(functions, 1):
                print(f"  {i}. {func.get('function', 'unknown')} (confidence: {func.get('confidence', 0):.2f})")
                if func.get('args'):
                    print(f"     Args: {func['args']}")
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON Error: {e}")
        print(f"Raw response: {response.text}")

if __name__ == "__main__":
    test_convert_endpoint()