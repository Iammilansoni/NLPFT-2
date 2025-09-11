#!/usr/bin/env python3
"""
Test script for the /convert endpoint.

This script tests the complete NLP pipeline through the FastAPI endpoint.
"""

import requests
import json
from typing import Dict, Any, List


def test_convert_endpoint() -> None:
    """Test the /convert endpoint with various inputs."""
    base_url = "http://localhost:8000"
    convert_url = f"{base_url}/convert/"
    
    print("🧪 Testing /convert endpoint")
    print("=" * 40)
    
    # Test cases with proper type annotation
    test_cases: List[Dict[str, Any]] = [
        {
            "text": "log in as admin with password123",
            "target_format": "nlp_steps",
            "options": {"debug": True}
        },
        {
            "text": "go to https://dashboard.example.com and click the settings button",
            "target_format": "nlp_steps"
        },
        {
            "text": "enter john.doe@email.com in #email and fill password field with secret123",
            "target_format": "nlp_steps"
        },
        {
            "text": "wait until loading spinner disappears and verify Welcome message appears",
            "target_format": "nlp_steps"
        }
    ]
    
    # Test health endpoint first
    try:
        health_response = requests.get(f"{base_url}/health/")
        if health_response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {health_response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on http://localhost:8000")
        return
    
    print(f"\n📝 Testing {len(test_cases)} convert requests:")
    print("-" * 40)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Input: '{test_case['text']}'")
        
        try:
            response = requests.post(
                convert_url,
                json=test_case,  # type: ignore - requests handles Dict[str, Any] properly
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Status: {response.status_code}")
                print(f"   📄 Original: {result.get('original_text', 'N/A')}")
                print(f"   🎯 Target Format: {result.get('target_format', 'N/A')}")
                print(f"   ⏱️  Processing Time: {result.get('processing_time', 0.0):.3f}s")
                
                # Parse the converted text (JSON string)
                try:
                    converted_data = json.loads(result.get('converted_text', '{}'))
                    steps = converted_data.get('steps', [])
                    overall_confidence = converted_data.get('overall_confidence', 0.0)
                    
                    print(f"   🔢 Steps Found: {len(steps)}")
                    print(f"   📊 Overall Confidence: {overall_confidence:.2f}")
                    
                    if steps:
                        print(f"   📋 Parsed Steps:")
                        for j, step in enumerate(steps, 1):
                            function = step.get('function', 'unknown')
                            confidence = step.get('confidence', 0.0)
                            args = step.get('args', {})
                            match_type = step.get('match_type', 'unknown')
                            
                            print(f"      {j}. {function} (confidence: {confidence:.2f}, type: {match_type})")
                            if args:
                                print(f"         Args: {args}")
                            
                            if 'unresolved_tokens' in step:
                                print(f"         Unresolved: {step['unresolved_tokens']}")
                
                except json.JSONDecodeError:
                    print(f"   ⚠️  Could not parse converted text as JSON")
                    print(f"   📄 Raw converted text: {result.get('converted_text', 'N/A')}")
                
            else:
                print(f"   ❌ Status: {response.status_code}")
                print(f"   📄 Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
    
    print(f"\n✅ /convert endpoint testing completed!")


if __name__ == "__main__":
    test_convert_endpoint()
