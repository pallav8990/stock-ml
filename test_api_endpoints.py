#!/usr/bin/env python3
"""
API Endpoint Test Script for Stock-ML Production
Tests all endpoints with real data
"""

import requests
import json
from datetime import datetime

def test_endpoint(name: str, url: str, expected_keys: list = None) -> bool:
    """Test an endpoint and validate response"""
    try:
        print(f"\n🔍 Testing {name}")
        print(f"📍 URL: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success - Response keys: {list(data.keys())}")
            
            if expected_keys:
                missing_keys = [key for key in expected_keys if key not in data]
                if missing_keys:
                    print(f"⚠️  Missing expected keys: {missing_keys}")
                else:
                    print(f"✅ All expected keys present")
            
            # Show sample data
            if isinstance(data, dict) and len(data) > 0:
                first_key = list(data.keys())[0]
                sample_value = data[first_key]
                if isinstance(sample_value, list) and len(sample_value) > 0:
                    print(f"📋 Sample item count: {len(sample_value)}")
                    print(f"📋 First item: {sample_value[0] if sample_value else 'Empty'}")
                else:
                    print(f"📋 Sample value: {sample_value}")
            
            return True
            
        else:
            print(f"❌ Failed - Status: {response.status_code}")
            print(f"📋 Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"💥 Error: {e}")
        return False

def main():
    print("🚀 STOCK-ML API ENDPOINT TESTING")
    print("=" * 50)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    base_url = "http://localhost:8000"
    
    # Test endpoints
    endpoints = [
        {
            "name": "Health Check",
            "url": f"{base_url}/health",
            "expected_keys": ["status", "timestamp", "data_status"]
        },
        {
            "name": "Today's Predictions",
            "url": f"{base_url}/predict_today",
            "expected_keys": ["predictions"]
        },
        {
            "name": "Gap Explanations", 
            "url": f"{base_url}/explain_gap",
            "expected_keys": ["explanations"]
        },
        {
            "name": "60-day Accuracy",
            "url": f"{base_url}/accuracy_by_stock?window=60",
            "expected_keys": ["accuracy_metrics"]
        }
    ]
    
    results = []
    for endpoint in endpoints:
        success = test_endpoint(
            endpoint["name"],
            endpoint["url"], 
            endpoint["expected_keys"]
        )
        results.append((endpoint["name"], success))
    
    # Summary
    print(f"\n{'='*50}")
    print("🏁 TESTING COMPLETE")
    print(f"{'='*50}")
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {name}")
    
    print(f"\n📊 Results: {success_count}/{total_count} endpoints working")
    
    if success_count == total_count:
        print("🎉 ALL ENDPOINTS WORKING - PRODUCTION READY!")
    else:
        print("⚠️  Some endpoints failed - check logs above")

if __name__ == "__main__":
    main()