#!/usr/bin/env python3
"""
Token-Efficient Customer Onboarding Script

Minimal, focused onboarding that reduces Cursor token consumption
while maintaining all essential functionality.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any


class EfficientOnboarding:
    """Streamlined customer onboarding with minimal token usage."""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def quick_onboard(self, company: str, domain: str, package: str, github_repo: str = None) -> str:
        """
        Ultra-fast customer onboarding with minimal steps.
        
        Args:
            company: Company name
            domain: Domain name  
            package: Package type (friends_family, free_website_discounted, etc.)
            github_repo: Actual GitHub repo URL from Rocket.new
            
        Returns:
            Path to customer directory
        """
        # Create clean company directory name
        company_dir = company.lower().replace(' ', '').replace('.', '').replace('-', '')
        customer_path = os.path.join(self.project_root, 'customer_projects', company_dir)
        os.makedirs(customer_path, exist_ok=True)
        
        # Package configurations (minimal data)
        packages = {
            'friends_family': {'setup': 0, 'monthly': 20, 'services': ['dns', 'website', 'support']},
            'free_website_discounted': {'setup': 0, 'monthly': 20, 'services': ['dns', 'website', 'support']},
            'starter': {'setup': 500, 'monthly': 49, 'services': ['dns', 'website', 'support']},
            'growth': {'setup': 1500, 'monthly': 149, 'services': ['dns', 'website', 'crm', 'stripe', 'email']},
            'professional': {'setup': 2500, 'monthly': 249, 'services': ['dns', 'website', 'crm', 'stripe', 'email', 'chatbot']},
            'premium': {'setup': 5000, 'monthly': 499, 'services': ['dns', 'website', 'crm', 'stripe', 'email', 'chatbot', 'automations']}
        }
        
        pkg = packages.get(package, packages['starter'])
        project_id = f"DTL-{company.upper().replace(' ', '')}-{datetime.now().strftime('%Y%m%d')}"
        
        # Create minimal project file
        project_data = {
            'company': company,
            'domain': domain,
            'package': package,
            'setup_fee': pkg['setup'],
            'monthly_fee': pkg['monthly'],
            'services': pkg['services'],
            'project_id': project_id,
            'created': datetime.now().isoformat(),
            'github_repo': github_repo,
            'status': 'ready_for_deployment'
        }
        
        # Save project file
        project_file = os.path.join(customer_path, f"{project_id}.json")
        with open(project_file, 'w') as f:
            json.dump(project_data, f, indent=2)
        
        # Generate essential files only
        self._create_dns_guide(customer_path, domain, company)
        self._create_deployment_checklist(customer_path, project_data)
        
        return customer_path
    
    def _create_dns_guide(self, customer_path: str, domain: str, company: str):
        """Create minimal DNS instructions."""
        dns_content = f"""# DNS Setup: {company}

Domain: {domain}
Provider: Customer Managed

## Required Records
```
CNAME: www → [CloudFront-URL-from-deployment]
A: @ → [IP-from-deployment]
```

## SSL Validation
```
CNAME: _acme-challenge → [AWS-validation-record]
```

Timeline: 2-24 hours after deployment
"""
        with open(os.path.join(customer_path, 'DNS_Setup.md'), 'w') as f:
            f.write(dns_content)
    
    def _create_deployment_checklist(self, customer_path: str, project_data: Dict[str, Any]):
        """Create deployment checklist."""
        checklist_content = f"""# Deployment Checklist: {project_data['company']}

## Pre-Deployment
- [x] Customer data collected
- [x] GitHub repo identified: {project_data.get('github_repo', 'TBD')}
- [ ] Deploy infrastructure: `curl -X POST {{api}}/deploy`
- [ ] Configure DNS records
- [ ] Set up billing: ${project_data['monthly_fee']}/month

## Post-Deployment  
- [ ] Test website functionality
- [ ] Send credentials to customer
- [ ] Schedule training session

Project ID: {project_data['project_id']}
Services: {', '.join(project_data['services'])}
"""
        with open(os.path.join(customer_path, 'Deployment_Checklist.md'), 'w') as f:
            f.write(checklist_content)


def main():
    """CLI interface for efficient onboarding."""
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python efficient_onboarding.py <company> <domain> <package> [github_repo]")
        print("Packages: friends_family, free_website_discounted, starter, growth, professional, premium")
        return 1
    
    company = sys.argv[1]
    domain = sys.argv[2] 
    package = sys.argv[3]
    github_repo = sys.argv[4] if len(sys.argv) > 4 else None
    
    onboarding = EfficientOnboarding()
    customer_path = onboarding.quick_onboard(company, domain, package, github_repo)
    
    print(f"✅ Customer onboarded: {customer_path}")
    print(f"📁 Files: {os.listdir(customer_path)}")
    
    return 0


if __name__ == '__main__':
    exit(main())