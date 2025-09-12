#!/usr/bin/env python3
"""
Test script for the /api/v1/convert/ endpoint.
"""

import requests
import json
import sys


def test_convert_endpoint():
    """Test the convert endpoint with POST request."""
    url = "http://localhost:8000/api/v1/convert/"
    
    # Test data
    test_requests = [
        {
            "text": "log in as admin with password123",
            "target_format": "nlp_steps"
        },
        {
            "text": "go to https://dashboard.example.com",
            "target_format": "nlp_steps"
        },
        {
            "text": "click the submit button",
            "target_format": "nlp_steps"
        },
        {
            "text": "enter john.doe@email.com in #email field",
            "target_format": "nlp_steps"
        }
    ]
    
    print("🧪 Testing /api/v1/convert/ endpoint")
    print("=" * 50)
    
    for i, test_data in enumerate(test_requests, 1):
        print(f"\n{i}. Testing: '{test_data['text']}'")
        print("-" * 40)
        
        try:
            response = requests.post(
                url,
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ SUCCESS!")
                print(f"Original Text: {result.get('original_text')}")
                print(f"Target Format: {result.get('target_format')}")
                print(f"Processing Time: {result.get('processing_time', 0):.3f}s")
                
                # Parse the converted text (JSON string)
                try:
                    converted_data = json.loads(result.get('converted_text', '{}'))
                    steps = converted_data.get('steps', [])
                    
                    print(f"Steps Found: {len(steps)}")
                    for j, step in enumerate(steps, 1):
                        function = step.get('function', 'unknown')
                        confidence = step.get('confidence', 0.0)
                        args = step.get('args', {})
                        
                        print(f"  {j}. Function: {function}")
                        print(f"     Confidence: {confidence:.2f}")
                        if args:
                            print(f"     Arguments: {args}")
                
                except json.JSONDecodeError:
                    print("⚠️ Could not parse converted_text as JSON")
                    print(f"Raw Output: {result.get('converted_text')}")
                    
            else:
                print("❌ FAILED!")
                print(f"Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Make sure the server is running on http://localhost:8000")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return True


def test_health_endpoint():
    """Test the health endpoint first."""
    try:
        response = requests.get("http://localhost:8000/api/v1/health/")
        if response.status_code == 200:
            print("✅ Health check passed - Server is running")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except:
        print("❌ Cannot connect to server")
        return False


if __name__ == "__main__":
    print("🚀 NLPForge Convert Endpoint Test")
    print("=" * 50)
    
    # First check if server is running
    if not test_health_endpoint():
        print("\n❌ Server is not running. Please start it with:")
        print("C:/Users/milan/PROJECTS/NLPForge-Tester/.venv/Scripts/python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        sys.exit(1)
    
    # Test the convert endpoint
    if test_convert_endpoint():
        print("\n✅ All tests completed!")
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)