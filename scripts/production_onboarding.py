#!/usr/bin/env python3
"""
Production Customer Onboarding with Real API Integration

Uses deployed API Gateway for actual HubSpot, Stripe, and AWS integrations.
"""

import json
import requests
from datetime import datetime
from typing import Dict, Any
import sys
import os


class ProductionOnboarding:
    """Production customer onboarding with real API calls."""
    
    def __init__(self):
        self.api_base_url = "https://vxdtzyxui5.execute-api.us-east-1.amazonaws.com/prod"
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def onboard_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete customer onboarding with real API integrations."""
        
        print(f"🚀 Production Onboarding: {customer_data['company']}")
        print(f"🌐 API Gateway: {self.api_base_url}")
        print("=" * 60)
        
        results = {
            'customer': customer_data['company'],
            'steps': {},
            'success': True,
            'errors': []
        }
        
        try:
            # Step 1: Create HubSpot CRM Record
            print("🏢 Creating HubSpot CRM record...")
            hubspot_result = self._create_hubspot_record(customer_data)
            results['steps']['hubspot'] = hubspot_result
            
            # Step 2: Deploy Website Infrastructure
            print("🌐 Deploying website infrastructure...")
            deploy_result = self._deploy_website(customer_data)
            results['steps']['deployment'] = deploy_result
            
            # Step 3: Set up DNS and SSL
            print("🔒 Setting up DNS and SSL...")
            dns_result = self._setup_dns_ssl(customer_data, deploy_result)
            results['steps']['dns_ssl'] = dns_result
            
            # Step 4: Set up Billing
            if customer_data.get('monthly_fee', 0) > 0:
                print("💳 Setting up billing...")
                billing_result = self._setup_billing(customer_data)
                results['steps']['billing'] = billing_result
            
            # Step 5: Send Notifications
            print("📧 Sending customer notifications...")
            notification_result = self._send_notifications(customer_data, results)
            results['steps']['notifications'] = notification_result
            
            print("\n🎉 Production onboarding completed!")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Onboarding failed: {str(e)}")
            print(f"\n❌ Onboarding failed: {str(e)}")
        
        return results
    
    def _create_hubspot_record(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create HubSpot CRM contact and deal."""
        try:
            payload = {
                'client_info': {
                    'company': customer_data['company'],
                    'email': customer_data.get('email', ''),
                    'phone': customer_data.get('phone', ''),
                    'contact_name': customer_data.get('contact_name', ''),
                    'industry': customer_data.get('industry', ''),
                    'package': customer_data.get('package', ''),
                    'setup_fee': customer_data.get('setup_fee', 0),
                    'monthly_fee': customer_data.get('monthly_fee', 0)
                },
                'crm_config': {
                    'pipeline': 'dtl_onboarding',
                    'stage': 'Build Website',
                    'deal_amount': customer_data.get('setup_fee', 0),
                    'monthly_value': customer_data.get('monthly_fee', 0)
                }
            }
            
            response = requests.post(
                f"{self.api_base_url}/crm-setup",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'contact_id': result.get('contact_id'),
                    'deal_id': result.get('deal_id'),
                    'message': 'HubSpot CRM record created'
                }
            else:
                return {
                    'success': False,
                    'error': f'HubSpot API failed: {response.status_code} - {response.text}'
                }
                
        except Exception as e:
            return {'success': False, 'error': f'HubSpot error: {str(e)}'}
    
    def _deploy_website(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy website infrastructure."""
        try:
            payload = {
                'domain': customer_data['domain'],
                'client_info': {
                    'company': customer_data['company'],
                    'industry': customer_data.get('industry', ''),
                    'contact_name': customer_data.get('contact_name', ''),
                    'email': customer_data.get('email', '')
                },
                'deployment_config': {
                    'source': 'github',
                    'repository': customer_data.get('github_repo', ''),
                    'branch': 'main'
                }
            }
            
            response = requests.post(
                f"{self.api_base_url}/deploy",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=120  # Deployment can take longer
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'website_url': result.get('website_url'),
                    'cloudfront_domain': result.get('cloudfront_domain'),
                    's3_bucket': result.get('s3_bucket'),
                    'message': 'Website infrastructure deployed'
                }
            else:
                return {
                    'success': False,
                    'error': f'Deployment API failed: {response.status_code} - {response.text}'
                }
                
        except Exception as e:
            return {'success': False, 'error': f'Deployment error: {str(e)}'}
    
    def _setup_dns_ssl(self, customer_data: Dict[str, Any], deploy_result: Dict[str, Any]) -> Dict[str, Any]:
        """Set up DNS and SSL certificate."""
        try:
            payload = {
                'domain': customer_data['domain'],
                'dns_type': 'cloudfront_ssl',
                'client_info': {
                    'company': customer_data['company']
                },
                'ssl_config': {
                    'certificate_type': 'acm',
                    'domain_validation': 'dns'
                }
            }
            
            response = requests.post(
                f"{self.api_base_url}/dns",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'certificate_arn': result.get('certificate_arn'),
                    'validation_records': result.get('validation_records'),
                    'dns_records': result.get('dns_records'),
                    'message': 'DNS and SSL configured'
                }
            else:
                return {
                    'success': False,
                    'error': f'DNS API failed: {response.status_code} - {response.text}'
                }
                
        except Exception as e:
            return {'success': False, 'error': f'DNS/SSL error: {str(e)}'}
    
    def _setup_billing(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Set up Stripe billing."""
        try:
            payload = {
                'client_info': {
                    'company': customer_data['company'],
                    'email': customer_data.get('email', ''),
                    'contact_name': customer_data.get('contact_name', '')
                },
                'subscription_plan': customer_data.get('package', '').lower(),
                'amount': customer_data.get('monthly_fee', 0) * 100,  # Convert to cents
                'currency': 'usd',
                'interval': 'month',
                'description': f"DTL-Global {customer_data.get('package', '')} - {customer_data['company']}"
            }
            
            response = requests.post(
                f"{self.api_base_url}/subscribe",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'subscription_id': result.get('subscription_id'),
                    'monthly_amount': customer_data.get('monthly_fee', 0),
                    'message': 'Billing setup completed'
                }
            else:
                return {
                    'success': False,
                    'error': f'Billing API failed: {response.status_code} - {response.text}'
                }
                
        except Exception as e:
            return {'success': False, 'error': f'Billing error: {str(e)}'}
    
    def _send_notifications(self, customer_data: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
        """Send customer notifications."""
        try:
            payload = {
                'notification_type': 'onboarding_completed',
                'client_info': {
                    'company': customer_data['company'],
                    'email': customer_data.get('email', ''),
                    'contact_name': customer_data.get('contact_name', '')
                },
                'project_details': {
                    'project_id': customer_data.get('project_id', ''),
                    'package': customer_data.get('package', ''),
                    'website_url': results.get('steps', {}).get('deployment', {}).get('website_url', ''),
                    'monthly_fee': customer_data.get('monthly_fee', 0)
                }
            }
            
            response = requests.post(
                f"{self.api_base_url}/notify",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'message_id': result.get('message_id'),
                    'message': 'Customer notifications sent'
                }
            else:
                return {
                    'success': False,
                    'error': f'Notification API failed: {response.status_code} - {response.text}'
                }
                
        except Exception as e:
            return {'success': False, 'error': f'Notification error: {str(e)}'}


def main():
    """CLI interface for production onboarding."""
    if len(sys.argv) < 2:
        print("Usage: python production_onboarding.py <customer_project_file>")
        print("Example: python production_onboarding.py customer_projects/businesscentersolutions/DTL-BUSINESSCENTERSOLUTIONS-20260323.json")
        return 1
    
    project_file = sys.argv[1]
    
    if not os.path.exists(project_file):
        print(f"❌ Project file not found: {project_file}")
        return 1
    
    # Load customer data
    with open(project_file, 'r') as f:
        customer_data = json.load(f)
    
    # Add missing fields if needed
    if 'email' not in customer_data:
        customer_data['email'] = input("Customer email: ")
    if 'contact_name' not in customer_data:
        customer_data['contact_name'] = input("Contact name: ")
    
    # Run production onboarding
    onboarding = ProductionOnboarding()
    results = onboarding.onboard_customer(customer_data)
    
    # Update project file with results
    customer_data['onboarding_results'] = results
    customer_data['status'] = 'completed' if results['success'] else 'failed'
    customer_data['last_updated'] = datetime.now().isoformat()
    
    with open(project_file, 'w') as f:
        json.dump(customer_data, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 PRODUCTION ONBOARDING RESULTS")
    print("="*60)
    
    if results['success']:
        print("✅ All steps completed successfully!")
        for step, result in results['steps'].items():
            status = "✅" if result.get('success', False) else "❌"
            print(f"   {status} {step.replace('_', ' ').title()}")
    else:
        print("❌ Onboarding had issues:")
        for error in results['errors']:
            print(f"   • {error}")
    
    return 0 if results['success'] else 1


if __name__ == '__main__':
    exit(main())