"""Test script to demonstrate all health endpoints."""

import requests
import json
from datetime import datetime

# Base URL for the API
BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(name, url):
    """Test a specific endpoint and display results."""
    print(f"\n{'='*60}")
    print(f"🔍 Testing: {name}")
    print(f"📡 URL: {url}")
    print('='*60)
    
    try:
        response = requests.get(url, timeout=10)
        print(f"✅ Status Code: {response.status_code}")
        print(f"⏱️  Response Time: {response.elapsed.total_seconds():.3f}s")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            data = response.json()
            print(f"📄 Response Data:")
            print(json.dumps(data, indent=2))
        else:
            print(f"📄 Response Text: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def main():
    """Test all health endpoints."""
    print("🏥 NLPForge Health Endpoints Test")
    print(f"🕒 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test all health endpoints
    endpoints = [
        ("Main Health Check", f"{BASE_URL}/api/v1/health/"),
        ("Readiness Check", f"{BASE_URL}/api/v1/health/ready"),
        ("Liveness Check", f"{BASE_URL}/api/v1/health/live"),
        ("Simple Health Check", f"{BASE_URL}/api/v1/health/simple"),
        ("Health Metrics", f"{BASE_URL}/api/v1/health/metrics"),
        ("Root Endpoint", f"{BASE_URL}/"),
        ("API Documentation", f"{BASE_URL}/docs")
    ]
    
    for name, url in endpoints:
        if url.endswith('/docs'):
            print(f"\n{'='*60}")
            print(f"📚 {name}: {url}")
            print("   (Open this URL in your browser to see the interactive API docs)")
            print('='*60)
        else:
            test_endpoint(name, url)
    
    print(f"\n🎉 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
