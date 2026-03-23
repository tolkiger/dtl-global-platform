#!/usr/bin/env python3
"""
API Diagnostic Script

Tests API Gateway endpoints and provides recommendations for fixing issues.
"""

import requests
import json


def test_api_endpoint(base_url: str, endpoint: str, payload: dict = None) -> dict:
    """Test a single API endpoint."""
    url = f"{base_url}/{endpoint}"
    
    try:
        if payload:
            response = requests.post(url, json=payload, timeout=10)
        else:
            response = requests.get(url, timeout=10)
        
        return {
            'endpoint': endpoint,
            'status_code': response.status_code,
            'success': response.status_code == 200,
            'response': response.text[:200] if response.text else 'No response body',
            'error': None
        }
    except Exception as e:
        return {
            'endpoint': endpoint,
            'status_code': None,
            'success': False,
            'response': None,
            'error': str(e)
        }


def main():
    """Run API diagnostics."""
    base_url = "https://vxdtzyxui5.execute-api.us-east-1.amazonaws.com/prod"
    
    print("🔍 DTL-Global API Diagnostics")
    print(f"🌐 Base URL: {base_url}")
    print("=" * 60)
    
    # Test endpoints with minimal payloads
    endpoints_to_test = [
        ('crm-setup', {'client_info': {'company': 'Test'}, 'crm_config': {}}),
        ('deploy', {'domain': 'test.com', 'client_info': {}}),
        ('dns', {'domain': 'test.com', 'dns_type': 'test'}),
        ('subscribe', {'client_info': {'email': 'test@test.com'}, 'amount': 100}),
        ('notify', {'notification_type': 'test', 'client_info': {}})
    ]
    
    results = []
    for endpoint, payload in endpoints_to_test:
        print(f"Testing /{endpoint}...")
        result = test_api_endpoint(base_url, endpoint, payload)
        results.append(result)
        
        status = "✅" if result['success'] else "❌"
        print(f"  {status} Status: {result['status_code']}")
        if not result['success']:
            print(f"     Error: {result.get('error') or result.get('response', 'Unknown')}")
    
    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    working_endpoints = [r for r in results if r['success']]
    failing_endpoints = [r for r in results if not r['success']]
    
    print(f"✅ Working endpoints: {len(working_endpoints)}")
    print(f"❌ Failing endpoints: {len(failing_endpoints)}")
    
    if failing_endpoints:
        print("\n🔧 RECOMMENDED FIXES:")
        
        # Check for common error patterns
        server_errors = [r for r in failing_endpoints if r.get('status_code') == 502]
        if server_errors:
            print("\n❌ 502 Internal Server Errors detected:")
            print("   Likely causes:")
            print("   • Missing Lambda dependencies (hubspot-api-client, stripe, anthropic)")
            print("   • Missing environment variables")
            print("   • Missing SSM parameters for API keys")
            print("   • Lambda function import errors")
            
            print("\n🛠️  Recommended actions:")
            print("   1. Check CloudWatch logs for Lambda functions")
            print("   2. Verify SSM parameters are set:")
            print("      - /dtl-global-platform/hubspot/access-token")
            print("      - /dtl-global-platform/stripe/secret-key")
            print("      - /dtl-global-platform/anthropic/api-key")
            print("   3. Ensure Lambda layers include required Python packages")
            print("   4. Check Lambda function environment variables")
        
        timeout_errors = [r for r in failing_endpoints if 'timeout' in str(r.get('error', '')).lower()]
        if timeout_errors:
            print("\n⏱️  Timeout errors detected:")
            print("   • Lambda functions may be cold starting")
            print("   • Increase timeout settings in CDK")
    
    else:
        print("🎉 All endpoints are working correctly!")
    
    return len(failing_endpoints)


if __name__ == '__main__':
    exit(main())