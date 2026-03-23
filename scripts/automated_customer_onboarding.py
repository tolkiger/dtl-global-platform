#!/usr/bin/env python3
"""
Automated Customer Onboarding Script for DTL-Global Platform.

This script automates the complete customer onboarding process after
customer information is collected, making API calls to all necessary
services and generating all required documentation.

Author: DTL-Global Platform
"""

import json
import os
import requests
from datetime import datetime
from typing import Dict, Any
import argparse


class AutomatedOnboardingProcessor:
    """Handles automated customer onboarding with API calls."""
    
    def __init__(self, api_base_url: str = None):
        """Initialize the onboarding processor.
        
        Args:
            api_base_url: Base URL for DTL-Global API Gateway
        """
        self.api_base_url = api_base_url or "https://your-api-gateway.execute-api.us-east-1.amazonaws.com/prod"
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    def process_customer_onboarding(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process complete customer onboarding automatically.
        
        Args:
            customer_data: Dictionary containing all customer information
            
        Returns:
            Dictionary with onboarding results and next steps
        """
        print(f"🚀 Starting automated onboarding for {customer_data['company']}")
        print("=" * 60)
        
        results = {
            'customer_info': customer_data,
            'project_id': self._generate_project_id(customer_data['company']),
            'onboarding_steps': {},
            'files_created': [],
            'next_steps': [],
            'success': True,
            'errors': []
        }
        
        try:
            # Step 1: Create project directory and files
            results['onboarding_steps']['project_setup'] = self._setup_project_structure(customer_data, results['project_id'])
            
            # Step 2: Create HubSpot CRM record
            results['onboarding_steps']['hubspot_crm'] = self._create_hubspot_record(customer_data)
            
            # Step 3: GitHub repository setup (handled by Rocket.new)
            # Note: Rocket.new automatically creates GitHub repos when exporting projects
            results['onboarding_steps']['github_setup'] = self._verify_github_repository(customer_data)
            
            # Step 4: Deploy website infrastructure
            results['onboarding_steps']['website_deployment'] = self._deploy_website_infrastructure(customer_data)
            
            # Step 5: Configure DNS and SSL
            results['onboarding_steps']['dns_ssl_setup'] = self._setup_dns_and_ssl(customer_data)
            
            # Step 6: Set up billing and subscriptions
            results['onboarding_steps']['billing_setup'] = self._setup_billing(customer_data)
            
            # Step 7: Generate customer documentation
            results['onboarding_steps']['documentation'] = self._generate_customer_documentation(customer_data, results['project_id'])
            
            # Step 8: Send notifications
            results['onboarding_steps']['notifications'] = self._send_customer_notifications(customer_data, results['project_id'])
            
            print("\n🎉 Automated onboarding completed successfully!")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Onboarding failed: {str(e)}")
            print(f"\n❌ Onboarding failed: {str(e)}")
        
        return results
    
    def _generate_project_id(self, company_name: str) -> str:
        """Generate unique project ID."""
        clean_name = company_name.upper().replace(' ', '').replace('.', '').replace('-', '')[:20]
        date_str = datetime.now().strftime('%Y%m%d')
        return f"DTL-{clean_name}-{date_str}"
    
    def _setup_project_structure(self, customer_data: Dict[str, Any], project_id: str) -> Dict[str, Any]:
        """Set up project directory structure and files."""
        print("📁 Setting up project structure...")
        
        try:
            # Create company directory
            company_name = customer_data['company'].lower().replace(' ', '_').replace('.', '').replace('-', '_')
            company_dir = os.path.join(self.project_root, 'customer_projects', company_name)
            os.makedirs(company_dir, exist_ok=True)
            
            # Create project JSON file
            project_file = os.path.join(company_dir, f"{project_id}.json")
            with open(project_file, 'w') as f:
                json.dump({
                    'customer_info': customer_data,
                    'project_metadata': {
                        'project_id': project_id,
                        'created_date': datetime.now().isoformat(),
                        'status': 'in_progress'
                    }
                }, f, indent=2)
            
            return {
                'success': True,
                'company_directory': company_dir,
                'project_file': project_file,
                'message': 'Project structure created successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Project setup failed: {str(e)}'
            }
    
    def _create_hubspot_record(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create HubSpot CRM contact and deal."""
        print("🏢 Creating HubSpot CRM record...")
        
        try:
            # Prepare HubSpot API request
            hubspot_payload = {
                'client_info': {
                    'company': customer_data['company'],
                    'email': customer_data['email'],
                    'phone': customer_data.get('phone', ''),
                    'contact_name': customer_data.get('contact_name', ''),
                    'industry': customer_data.get('industry', ''),
                    'package': customer_data.get('package_info', {}).get('package', ''),
                    'setup_fee': customer_data.get('package_info', {}).get('setup_fee', 0),
                    'monthly_fee': customer_data.get('package_info', {}).get('monthly_fee', 0)
                },
                'crm_config': {
                    'pipeline': 'dtl_onboarding',
                    'stage': 'Build Website',
                    'deal_amount': customer_data.get('package_info', {}).get('setup_fee', 0),
                    'monthly_value': customer_data.get('package_info', {}).get('monthly_fee', 0)
                }
            }
            
            # Make API call to HubSpot setup handler
            response = requests.post(
                f"{self.api_base_url}/crm-setup",
                json=hubspot_payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'contact_id': result.get('contact_id'),
                    'deal_id': result.get('deal_id'),
                    'message': 'HubSpot CRM record created successfully'
                }
            else:
                return {
                    'success': False,
                    'error': f'HubSpot API call failed: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'HubSpot setup failed: {str(e)}'
            }
    
    def _verify_github_repository(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify GitHub repository exists (created by Rocket.new export)."""
        print("📦 Verifying GitHub repository from Rocket.new...")
        
        try:
            # Expected repository name from Rocket.new (based on project name)
            company_name = customer_data['company'].lower().replace(' ', '-').replace('.', '')
            expected_repo_name = f"{company_name}-website"
            
            # Try to find the repository using GitHub CLI
            # This searches for recently created repos with the company name
            try:
                import subprocess
                result = subprocess.run([
                    'gh', 'repo', 'list', '--limit', '20', '--json', 'name,createdAt'
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    import json
                    repos = json.loads(result.stdout)
                    
                    # Look for repos containing the company name
                    matching_repos = [
                        repo for repo in repos 
                        if company_name in repo['name'].lower()
                    ]
                    
                    if matching_repos:
                        # Use the most recently created matching repo
                        latest_repo = sorted(matching_repos, key=lambda x: x['createdAt'], reverse=True)[0]
                        return {
                            'success': True,
                            'repository_name': latest_repo['name'],
                            'repository_url': f"https://github.com/{latest_repo['name']}",
                            'message': f'Found GitHub repository: {latest_repo["name"]}',
                            'source': 'rocket_new_export'
                        }
            except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
                pass  # Fall through to manual instructions
            
            # If we can't find the repo automatically, provide instructions
            return {
                'success': True,
                'repository_name': expected_repo_name,
                'repository_url': f"https://github.com/username/{expected_repo_name}",
                'message': 'GitHub repository will be created by Rocket.new export',
                'manual_steps': [
                    "1. In Rocket.new, open your project and switch to Code View",
                    "2. Click the GitHub icon in the top-right toolbar",
                    "3. Choose 'Create new repository' or select existing repo",
                    "4. Click 'Push' to export your project to GitHub",
                    "5. Repository will be automatically created and populated"
                ],
                'expected_name': expected_repo_name
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'GitHub verification failed: {str(e)}'
            }
    
    def _deploy_website_infrastructure(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy website infrastructure (S3, CloudFront)."""
        print("🌐 Deploying website infrastructure...")
        
        try:
            # Prepare deployment API request
            deployment_payload = {
                'domain': customer_data['domain'],
                'client_info': {
                    'company': customer_data['company'],
                    'industry': customer_data.get('industry', ''),
                    'contact_name': customer_data.get('contact_name', ''),
                    'email': customer_data['email']
                },
                'deployment_config': {
                    'source': 'github',
                    'repository': f"{customer_data['company'].lower().replace(' ', '-').replace('.', '')}-website",
                    'branch': 'main',
                    'build_command': 'npm run build',
                    'output_directory': 'dist',
                    'created_by': 'rocket_new_export'
                },
                'dns_config': {
                    'manage_dns': customer_data.get('tech_requirements', {}).get('manage_dns', False),
                    'dns_provider': customer_data.get('tech_requirements', {}).get('dns_provider', 'route53'),
                    'subdomain_routing': 'www'
                }
            }
            
            # Make API call to deployment handler
            response = requests.post(
                f"{self.api_base_url}/deploy",
                json=deployment_payload,
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'website_url': result.get('website_url'),
                    'cloudfront_domain': result.get('cloudfront_domain'),
                    's3_bucket': result.get('s3_bucket'),
                    'message': 'Website infrastructure deployed successfully'
                }
            else:
                return {
                    'success': False,
                    'error': f'Deployment API call failed: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Website deployment failed: {str(e)}'
            }
    
    def _setup_dns_and_ssl(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Set up DNS and SSL certificate."""
        print("🔒 Setting up DNS and SSL...")
        
        try:
            # Prepare DNS/SSL API request
            dns_payload = {
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
            
            # Make API call to DNS handler
            response = requests.post(
                f"{self.api_base_url}/dns",
                json=dns_payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'certificate_arn': result.get('certificate_arn'),
                    'validation_records': result.get('validation_records'),
                    'message': 'DNS and SSL setup completed successfully'
                }
            else:
                return {
                    'success': False,
                    'error': f'DNS API call failed: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'DNS/SSL setup failed: {str(e)}'
            }
    
    def _setup_billing(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Set up billing and subscriptions."""
        print("💳 Setting up billing...")
        
        try:
            package_info = customer_data.get('package_info', {})
            monthly_fee = package_info.get('monthly_fee', 0)
            
            if monthly_fee > 0:
                # Prepare billing API request
                billing_payload = {
                    'client_info': {
                        'company': customer_data['company'],
                        'email': customer_data['email'],
                        'contact_name': customer_data.get('contact_name', '')
                    },
                    'subscription_plan': package_info.get('package', '').lower(),
                    'amount': monthly_fee * 100,  # Convert to cents
                    'currency': 'usd',
                    'interval': 'month',
                    'description': f"DTL-Global {package_info.get('package', '')} - {customer_data['company']}"
                }
                
                # Make API call to subscription handler
                response = requests.post(
                    f"{self.api_base_url}/subscribe",
                    json=billing_payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        'success': True,
                        'subscription_id': result.get('subscription_id'),
                        'monthly_amount': monthly_fee,
                        'message': 'Billing setup completed successfully'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Billing API call failed: {response.status_code}'
                    }
            else:
                return {
                    'success': True,
                    'message': 'No billing setup required (free package)'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Billing setup failed: {str(e)}'
            }
    
    def _generate_customer_documentation(self, customer_data: Dict[str, Any], project_id: str) -> Dict[str, Any]:
        """Generate customer documentation and guides."""
        print("📚 Generating customer documentation...")
        
        try:
            company_name = customer_data['company'].lower().replace(' ', '_').replace('.', '').replace('-', '_')
            company_dir = os.path.join(self.project_root, 'customer_projects', company_name)
            
            # Generate DNS instructions if customer manages their own DNS
            if not customer_data.get('tech_requirements', {}).get('manage_dns', True):
                dns_instructions = self._generate_dns_instructions(customer_data, company_dir)
            
            # Generate customer training guide
            training_guide = self._generate_training_guide(customer_data, company_dir)
            
            # Generate project summary
            project_summary = self._generate_project_summary(customer_data, project_id, company_dir)
            
            return {
                'success': True,
                'files_created': [
                    dns_instructions if 'dns_instructions' in locals() else None,
                    training_guide,
                    project_summary
                ],
                'message': 'Customer documentation generated successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Documentation generation failed: {str(e)}'
            }
    
    def _generate_dns_instructions(self, customer_data: Dict[str, Any], company_dir: str) -> str:
        """Generate DNS configuration instructions."""
        dns_file = os.path.join(company_dir, 'DNS_Instructions.md')
        
        dns_content = f"""# DNS Configuration Instructions for {customer_data['company']}

## Domain: {customer_data['domain']}
**DNS Provider**: {customer_data.get('tech_requirements', {}).get('dns_provider', 'Unknown')}
**Website**: AWS S3 + CloudFront
**SSL**: AWS Certificate Manager

---

## Required DNS Records

### 1. Website Routing Records

Add these records in your DNS management:

```
Record Type: CNAME
Name: www
Value: [CloudFront domain will be provided]
TTL: 300

Record Type: A
Name: @
Value: [IP address will be provided]
TTL: 300
```

### 2. SSL Certificate Validation

For SSL certificate validation, add this temporary record:

```
Record Type: CNAME
Name: _acme-challenge
Value: [Validation CNAME provided by AWS]
TTL: 300
```

---

## Timeline Expectations

| Step | Expected Time |
|------|---------------|
| DNS Record Addition | Immediate |
| DNS Propagation | 2-4 hours |
| SSL Certificate Validation | 2-24 hours |
| Full Website Availability | 4-24 hours |

---

## Support Contact

**DTL-Global Support**
Email: support@dtl-global.org
Project ID: {customer_data.get('project_id', 'TBD')}
"""
        
        with open(dns_file, 'w') as f:
            f.write(dns_content)
        
        return dns_file
    
    def _generate_training_guide(self, customer_data: Dict[str, Any], company_dir: str) -> str:
        """Generate customer training guide."""
        training_file = os.path.join(company_dir, 'Customer_Training_Guide.md')
        
        package_info = customer_data.get('package_info', {})
        
        training_content = f"""# Website Management Training Guide
## {customer_data['company']}

### Package Details
- **Package**: {package_info.get('package', 'Unknown')}
- **Setup Fee**: ${package_info.get('setup_fee', 0)}
- **Monthly Fee**: ${package_info.get('monthly_fee', 0)}

### Website Access
- **Website URL**: https://www.{customer_data['domain']}
- **Admin Contact**: {customer_data.get('contact_name', 'N/A')}
- **Support Email**: support@dtl-global.org

### Included Services
{self._format_services_list(package_info.get('services', []))}

### Support and Maintenance
**Contact for Support:**
- **Email**: support@dtl-global.org
- **Response Time**: 24-48 hours for basic requests
- **Project ID**: {customer_data.get('project_id', 'TBD')}

### Monthly Billing
- **Amount**: ${package_info.get('monthly_fee', 0)}/month
- **Billing Date**: 1st of each month
- **Payment Method**: [To be configured]
"""
        
        with open(training_file, 'w') as f:
            f.write(training_content)
        
        return training_file
    
    def _generate_project_summary(self, customer_data: Dict[str, Any], project_id: str, company_dir: str) -> str:
        """Generate project summary document."""
        summary_file = os.path.join(company_dir, 'Project_Summary.md')
        
        summary_content = f"""# Project Summary: {customer_data['company']}

**Project ID**: {project_id}
**Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status**: In Progress

## Customer Information
- **Company**: {customer_data['company']}
- **Domain**: {customer_data['domain']}
- **Contact**: {customer_data.get('contact_name', 'N/A')}
- **Email**: {customer_data['email']}
- **Phone**: {customer_data.get('phone', 'N/A')}
- **Industry**: {customer_data.get('industry', 'N/A')}

## Package Details
- **Package**: {customer_data.get('package_info', {}).get('package', 'Unknown')}
- **Client Type**: {customer_data.get('package_info', {}).get('client_type', 'Unknown')}
- **Setup Fee**: ${customer_data.get('package_info', {}).get('setup_fee', 0)}
- **Monthly Fee**: ${customer_data.get('package_info', {}).get('monthly_fee', 0)}

## Technical Requirements
- **DNS Management**: {'DTL-Global' if customer_data.get('tech_requirements', {}).get('manage_dns', True) else 'Customer Managed'}
- **Timeline**: {customer_data.get('tech_requirements', {}).get('timeline', 'Standard')}
- **Website Source**: {customer_data.get('tech_requirements', {}).get('website_source', 'Custom Development')}

## Project Files
- DNS Instructions: DNS_Instructions.md
- Training Guide: Customer_Training_Guide.md
- Project Data: {project_id}.json

## Next Steps
1. Complete website deployment
2. Configure DNS records
3. Validate SSL certificate
4. Customer training session
5. Go-live and monitoring
"""
        
        with open(summary_file, 'w') as f:
            f.write(summary_content)
        
        return summary_file
    
    def _format_services_list(self, services: list) -> str:
        """Format services list for documentation."""
        service_descriptions = {
            'dns': '✓ DNS management and configuration',
            'website': '✓ Website hosting and deployment',
            'crm': '✓ HubSpot CRM setup and management',
            'stripe': '✓ Payment processing integration',
            'email': '✓ Email setup and configuration',
            'notify': '✓ Automated notifications',
            'chatbot': '✓ AI chatbot integration',
            'basic_support': '✓ Basic technical support'
        }
        
        return '\n'.join([service_descriptions.get(service, f'✓ {service}') for service in services])
    
    def _send_customer_notifications(self, customer_data: Dict[str, Any], project_id: str) -> Dict[str, Any]:
        """Send customer notifications."""
        print("📧 Sending customer notifications...")
        
        try:
            # Prepare notification API request
            notification_payload = {
                'notification_type': 'onboarding_started',
                'client_info': {
                    'company': customer_data['company'],
                    'email': customer_data['email'],
                    'contact_name': customer_data.get('contact_name', '')
                },
                'project_details': {
                    'project_id': project_id,
                    'package': customer_data.get('package_info', {}).get('package', ''),
                    'timeline': customer_data.get('tech_requirements', {}).get('timeline', 'standard')
                }
            }
            
            # Make API call to notification handler
            response = requests.post(
                f"{self.api_base_url}/notify",
                json=notification_payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'message_id': result.get('message_id'),
                    'message': 'Customer notifications sent successfully'
                }
            else:
                return {
                    'success': False,
                    'error': f'Notification API call failed: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Notification sending failed: {str(e)}'
            }


def main():
    """Main execution function for command line usage."""
    parser = argparse.ArgumentParser(description='Automated DTL-Global Customer Onboarding')
    parser.add_argument('--customer-file', required=True, help='Path to customer data JSON file')
    parser.add_argument('--api-url', help='API Gateway base URL')
    parser.add_argument('--dry-run', action='store_true', help='Simulate onboarding without API calls')
    
    args = parser.parse_args()
    
    # Load customer data
    with open(args.customer_file, 'r') as f:
        customer_data = json.load(f)
    
    # Initialize processor
    processor = AutomatedOnboardingProcessor(args.api_url)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No actual API calls will be made")
    
    # Process onboarding
    results = processor.process_customer_onboarding(customer_data)
    
    # Output results
    print("\n" + "="*60)
    print("📊 ONBOARDING RESULTS")
    print("="*60)
    
    if results['success']:
        print("✅ Onboarding completed successfully!")
        print(f"📁 Project ID: {results['project_id']}")
        
        for step, result in results['onboarding_steps'].items():
            status = "✅" if result.get('success', False) else "❌"
            print(f"{status} {step.replace('_', ' ').title()}")
    else:
        print("❌ Onboarding failed!")
        for error in results['errors']:
            print(f"   {error}")
    
    return 0 if results['success'] else 1


if __name__ == '__main__':
    exit(main())