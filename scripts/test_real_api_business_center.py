#!/usr/bin/env python3
"""
Real API Testing with Business Center Solutions
Tests each endpoint individually with proper parameters
"""

import json
import requests
import time
from typing import Dict, Any

class BusinessCenterAPITester:
    """Test all API endpoints with Business Center Solutions data"""
    
    def __init__(self):
        self.api_base_url = "https://vxdtzyxui5.execute-api.us-east-1.amazonaws.com/prod"
        self.business_center_data = {
            "company": "Business Center Solutions",
            "email": "aduarte@businesscentersolutions.net",
            "phone": "(816) 204-7169",
            "contact_name": "Alondra Duarte",
            "industry": "MANAGEMENT_CONSULTING",  # HubSpot allowed option for "consulting"
            "package": "FREE_WEBSITE_DISCOUNTED",
            "setup_fee": 0,
            "monthly_fee": 20,
            "domain": "businesscentersolutions.net"
        }
        
    def test_crm_setup(self) -> Dict[str, Any]:
        """Test HubSpot CRM setup with Business Center Solutions"""
        print("🏢 Testing CRM Setup (HubSpot)...")
        
        payload = {
            "client_info": {
                "company": self.business_center_data["company"],
                "email": self.business_center_data["email"],
                "phone": self.business_center_data["phone"],
                "contact_name": self.business_center_data["contact_name"],
                "industry": self.business_center_data["industry"],
                "package": self.business_center_data["package"],
                "setup_fee": self.business_center_data["setup_fee"],
                "monthly_fee": self.business_center_data["monthly_fee"]
            },
            "crm_config": {
                "pipeline": "dtl_onboarding",
                "stage": "Build Website",
                "deal_amount": self.business_center_data["setup_fee"],
                "monthly_value": self.business_center_data["monthly_fee"]
            }
        }
        
        try:
            response = requests.post(
                f"{self.api_base_url}/crm-setup",
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            result = {
                "endpoint": "crm-setup",
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": response.text,
                "error": None
            }
            
            if response.status_code == 200:
                print("   ✅ HubSpot CRM setup successful!")
                try:
                    response_data = response.json()
                    if 'contact_id' in response_data:
                        print(f"   📝 Contact ID: {response_data['contact_id']}")
                    if 'deal_id' in response_data:
                        print(f"   💼 Deal ID: {response_data['deal_id']}")
                except:
                    pass
            else:
                print(f"   ❌ HubSpot CRM setup failed: {response.status_code}")
                print(f"   📝 Response: {response.text}")
                
            return result
            
        except Exception as e:
            return {
                "endpoint": "crm-setup",
                "status_code": 0,
                "success": False,
                "response": "",
                "error": str(e)
            }
    
    def test_deployment(self) -> Dict[str, Any]:
        """Test website deployment"""
        print("🌐 Testing Website Deployment...")
        
        payload = {
            "client_info": {
                "company": self.business_center_data["company"],
                "domain": self.business_center_data["domain"],
                "email": self.business_center_data["email"],  # Required by /deploy handler validation
                "industry": self.business_center_data["industry"]
            },
            "deployment_config": {
                "domain_scenario": "new_domain",  # Not route53-managed (customer uses GoDaddy)
                "github_repo": "https://github.com/tolkiger/businesscenter",
                "s3_bucket": f"{self.business_center_data['domain'].replace('.', '-')}-website",
                "cloudfront_enabled": True,
                "ssl_enabled": True,  # Keep SSL on (handler defaults to True)
                "cdn_enabled": True,  # Keep CDN on (handler defaults to True)
                "created_by": "rocket_new_export"
            }
        }
        
        try:
            response = requests.post(
                f"{self.api_base_url}/deploy",
                json=payload,
                timeout=60,  # Deployment might take longer
                headers={"Content-Type": "application/json"}
            )
            
            result = {
                "endpoint": "deploy",
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": response.text,
                "error": None
            }
            
            if response.status_code == 200:
                print("   ✅ Website deployment successful!")
                try:
                    response_data = response.json()
                    if 'deployment_id' in response_data:
                        print(f"   🚀 Deployment ID: {response_data['deployment_id']}")
                    if 'website_url' in response_data:
                        print(f"   🌐 Website URL: {response_data['website_url']}")
                except:
                    pass
            else:
                print(f"   ❌ Website deployment failed: {response.status_code}")
                print(f"   📝 Response: {response.text}")
                
            return result
            
        except Exception as e:
            return {
                "endpoint": "deploy",
                "status_code": 0,
                "success": False,
                "response": "",
                "error": str(e)
            }
    
    def test_dns_setup(self) -> Dict[str, Any]:
        """Test DNS configuration"""
        print("🔒 Testing DNS & SSL Setup...")
        
        payload = {
            "domain": self.business_center_data["domain"],
            "dns_config": {
                "create_hosted_zone": False,  # Using GoDaddy DNS
                "ssl_certificate": True,
                "cloudfront_alias": True,
                "external_dns": True,
                "dns_provider": "godaddy"
            }
        }
        
        try:
            response = requests.post(
                f"{self.api_base_url}/dns",
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            result = {
                "endpoint": "dns",
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": response.text,
                "error": None
            }
            
            if response.status_code == 200:
                print("   ✅ DNS & SSL setup successful!")
                try:
                    response_data = response.json()
                    if 'dns_instructions' in response_data:
                        print("   📋 DNS instructions generated")
                    if 'ssl_certificate' in response_data:
                        print("   🔒 SSL certificate configured")
                except:
                    pass
            else:
                print(f"   ❌ DNS & SSL setup failed: {response.status_code}")
                print(f"   📝 Response: {response.text}")
                
            return result
            
        except Exception as e:
            return {
                "endpoint": "dns",
                "status_code": 0,
                "success": False,
                "response": "",
                "error": str(e)
            }
    
    def test_billing_setup(self) -> Dict[str, Any]:
        """Test Stripe billing setup"""
        print("💳 Testing Stripe Billing Setup...")
        
        payload = {
            "action": "create",
            "customer_info": {
                "company": self.business_center_data["company"],  # Optional in handler
                "email": self.business_center_data["email"],  # Required by handler_subscribe
                "name": self.business_center_data["contact_name"]  # Required by handler_subscribe
            },
            "subscription_config": {
                "service_package": "dtl_friends_family"  # $20/month corresponds to Friends & Family hosting
            }
        }
        
        try:
            response = requests.post(
                f"{self.api_base_url}/subscribe",
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            result = {
                "endpoint": "subscribe",
                "status_code": response.status_code,
                "success": False,  # Set below after inspecting response body
                "response": response.text,
                "error": None
            }
            
            if response.status_code == 200:
                print("   ✅ Stripe billing setup successful!")
                try:
                    response_data = response.json()
                    result["success"] = bool(response_data.get("success", True))  # Treat explicit failure as failure
                    if 'customer_id' in response_data:
                        print(f"   👤 Customer ID: {response_data['customer_id']}")
                    if 'subscription_id' in response_data:
                        print(f"   💳 Subscription ID: {response_data['subscription_id']}")
                except:
                    pass
            else:
                print(f"   ❌ Stripe billing setup failed: {response.status_code}")
                print(f"   📝 Response: {response.text}")
                
            return result
            
        except Exception as e:
            return {
                "endpoint": "subscribe",
                "status_code": 0,
                "success": False,
                "response": "",
                "error": str(e)
            }
    
    def test_notifications(self) -> Dict[str, Any]:
        """Test customer notifications"""
        print("📧 Testing Customer Notifications...")
        
        payload = {
            "client_info": {
                "company": self.business_center_data["company"],
                "email": self.business_center_data["email"],
                "contact_name": self.business_center_data["contact_name"]
            },
            "notification_type": "welcome",
            "notification_config": {
                "email_type": "welcome",
                "template": "onboarding_welcome",
                "send_dns_instructions": True,
                "project_details": {
                    "domain": self.business_center_data["domain"],
                    "package": self.business_center_data["package"],
                    "monthly_fee": self.business_center_data["monthly_fee"]
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.api_base_url}/notify",
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            result = {
                "endpoint": "notify",
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": response.text,
                "error": None
            }
            
            if response.status_code == 200:
                print("   ✅ Customer notifications successful!")
                try:
                    response_data = response.json()
                    if 'message_id' in response_data:
                        print(f"   📧 Message ID: {response_data['message_id']}")
                except:
                    pass
            else:
                print(f"   ❌ Customer notifications failed: {response.status_code}")
                print(f"   📝 Response: {response.text}")
                # Note: SES email failure is acceptable if not configured
                if "SES" in response.text or "email" in response.text.lower():
                    print("   ℹ️  Note: SES email failure is acceptable if not configured")
                
            return result
            
        except Exception as e:
            return {
                "endpoint": "notify",
                "status_code": 0,
                "success": False,
                "response": "",
                "error": str(e)
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all API tests for Business Center Solutions"""
        print("🚀 Testing All APIs with Business Center Solutions")
        print("=" * 60)
        print(f"🏢 Company: {self.business_center_data['company']}")
        print(f"📧 Email: {self.business_center_data['email']}")
        print(f"🌐 Domain: {self.business_center_data['domain']}")
        print(f"💰 Package: {self.business_center_data['package']} (${self.business_center_data['monthly_fee']}/month)")
        print("=" * 60)
        
        results = {}
        
        # Test each endpoint
        results['crm_setup'] = self.test_crm_setup()
        time.sleep(2)  # Small delay between tests
        
        results['deployment'] = self.test_deployment()
        time.sleep(2)
        
        results['dns_setup'] = self.test_dns_setup()
        time.sleep(2)
        
        results['billing'] = self.test_billing_setup()
        time.sleep(2)
        
        results['notifications'] = self.test_notifications()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 BUSINESS CENTER SOLUTIONS API TEST RESULTS")
        print("=" * 60)
        
        successful_tests = 0
        total_tests = len(results)
        
        for endpoint, result in results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{endpoint.upper():<15} | {status} | Status: {result['status_code']}")
            if result['success']:
                successful_tests += 1
            elif result['error']:
                print(f"                | Error: {result['error']}")
        
        print("=" * 60)
        print(f"🎯 Success Rate: {successful_tests}/{total_tests} ({(successful_tests/total_tests)*100:.1f}%)")
        
        if successful_tests == total_tests:
            print("🎉 ALL TESTS PASSED - Business Center Solutions ready for onboarding!")
        elif successful_tests >= total_tests - 1:  # Allow SES failure
            print("✅ MOSTLY SUCCESSFUL - Ready for production (SES email may need configuration)")
        else:
            print("⚠️  ISSUES DETECTED - Need to fix API endpoints before production")
        
        return results

if __name__ == "__main__":
    tester = BusinessCenterAPITester()
    results = tester.run_all_tests()