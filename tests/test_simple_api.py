#!/usr/bin/env python3
"""
Simple API test to verify basic functionality.
"""

import requests
import json

def test_simple_endpoint():
    """Test a simple API endpoint to verify basic connectivity."""
    
    base_url = "https://vxdtzyxui5.execute-api.us-east-1.amazonaws.com/prod"
    
    # Test a minimal CRM setup call
    test_data = {
        "client_info": {
            "company": "Test Company",
            "email": "test@example.com",
            "contact_name": "Test User"
        }
    }
    
    print("🧪 Testing API Gateway connectivity...")
    print(f"🌐 Base URL: {base_url}")
    
    try:
        response = requests.post(
            f"{base_url}/crm-setup",
            json=test_data,
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📝 Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ API is working!")
            return True
        else:
            print("⚠️ API returned an error, but it's responding")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    test_simple_endpoint()