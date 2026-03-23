#!/usr/bin/env python3
"""
Start customer onboarding process for DTL-Global platform.

This script guides you through the initial customer onboarding steps
and ensures all prerequisites are met before beginning implementation.

Author: DTL-Global Platform
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, Any


def display_welcome():
    """Display welcome message and process overview."""
    print("🎯 DTL-Global Customer Onboarding Starter")
    print("=" * 50)
    print("\nThis script will guide you through:")
    print("1. Customer information collection")
    print("2. Service package selection")
    print("3. Technical requirements gathering")
    print("4. Project setup and next steps")
    print("\n📋 Before starting, ensure you have:")
    print("✓ Completed customer consultation")
    print("✓ Received signed contract")
    print("✓ Collected 50% deposit")
    print("✓ Switched to production mode (if not done)")


def check_production_mode():
    """Check if system is in production mode."""
    print("\n🔍 Checking system mode...")
    
    try:
        import boto3
        ssm = boto3.client('ssm')
        
        # Check Stripe key
        response = ssm.get_parameter(
            Name='/dtl-global-platform/stripe/secret',
            WithDecryption=True
        )
        stripe_key = response['Parameter']['Value']
        
        if stripe_key.startswith('sk_test_'):
            print("⚠️  WARNING: System is in SANDBOX mode")
            print("   You must switch to production mode before real customers")
            print("   Run: python scripts/switch_to_production.py")
            
            proceed = input("\nContinue in sandbox mode for testing? (y/N): ")
            if proceed.lower() != 'y':
                print("❌ Please switch to production mode first.")
                sys.exit(1)
            return False
        elif stripe_key.startswith('sk_live_'):
            print("✅ System is in PRODUCTION mode")
            return True
        else:
            print("❓ Unknown Stripe key format")
            return False
            
    except Exception as e:
        print(f"⚠️  Could not verify system mode: {str(e)}")
        print("   Assuming sandbox mode for testing")
        return False


def collect_customer_info() -> Dict[str, Any]:
    """Collect customer information interactively."""
    print("\n📝 Customer Information Collection")
    print("-" * 30)
    
    customer_info = {}
    
    # Basic business information
    customer_info['company'] = input("Company Name: ").strip()
    customer_info['domain'] = input("Domain (e.g., company.com): ").strip().lower()
    
    # Industry selection
    industries = [
        'roofing', 'construction', 'consulting', 'technology', 'healthcare',
        'retail', 'manufacturing', 'financial_services', 'food_service',
        'real_estate', 'legal', 'automotive', 'other'
    ]
    
    print("\nIndustry Options:")
    for i, industry in enumerate(industries, 1):
        print(f"{i:2d}. {industry.replace('_', ' ').title()}")
    
    while True:
        try:
            choice = int(input("\nSelect industry (number): "))
            if 1 <= choice <= len(industries):
                customer_info['industry'] = industries[choice - 1]
                break
            else:
                print("Invalid choice. Please select a number from the list.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Contact information
    print("\n📞 Contact Information:")
    customer_info['email'] = input("Primary Email: ").strip().lower()
    customer_info['phone'] = input("Phone Number: ").strip()
    customer_info['contact_name'] = input("Primary Contact Name: ").strip()
    
    return customer_info


def select_service_package() -> Dict[str, Any]:
    """Select service package and client type."""
    print("\n📦 Service Package Selection")
    print("-" * 30)
    
    # Display packages
    packages = {
        'STARTER': {
            'setup_fee': 500,
            'monthly_fee': 49,
            'description': 'Website + SEO + Hosting',
            'client_type': 'website_only',
            'services': ['dns', 'website', 'email_optional', 'notify']
        },
        'GROWTH': {
            'setup_fee': 1250,
            'monthly_fee': 149,
            'description': 'Starter + CRM + Payments + Email',
            'client_type': 'full_package',
            'services': ['dns', 'website', 'crm', 'stripe', 'email', 'notify']
        },
        'PROFESSIONAL': {
            'setup_fee': 2500,
            'monthly_fee': 249,
            'description': 'Growth + AI Chatbot + CRM Import',
            'client_type': 'full_package',
            'services': ['dns', 'website', 'crm', 'stripe', 'email', 'notify', 'chatbot']
        },
        'PREMIUM': {
            'setup_fee': 4000,
            'monthly_fee': 399,
            'description': 'Professional + Custom Automations',
            'client_type': 'full_package',
            'services': ['dns', 'website', 'crm', 'stripe', 'email', 'notify', 'chatbot', 'custom']
        }
    }
    
    print("Available Packages:")
    for name, details in packages.items():
        print(f"\n{name}:")
        print(f"  Setup: ${details['setup_fee']:,}")
        print(f"  Monthly: ${details['monthly_fee']}")
        print(f"  Includes: {details['description']}")
    
    while True:
        package_name = input("\nSelect package (STARTER/GROWTH/PROFESSIONAL/PREMIUM): ").upper().strip()
        if package_name in packages:
            return {
                'package': package_name,
                **packages[package_name]
            }
        print("Invalid package. Please select from the available options.")


def collect_technical_requirements(customer_info: Dict[str, Any], package_info: Dict[str, Any]) -> Dict[str, Any]:
    """Collect technical requirements and preferences."""
    print("\n🔧 Technical Requirements")
    print("-" * 30)
    
    tech_requirements = {}
    
    # Domain management
    print(f"\nDomain: {customer_info['domain']}")
    tech_requirements['manage_dns'] = input("Should we manage DNS for this domain? (y/N): ").lower() == 'y'
    
    if not tech_requirements['manage_dns']:
        print("📝 Note: You'll need to update DNS records manually")
        print("   We'll provide the necessary DNS configuration")
    
    # Existing systems
    print("\nExisting Systems:")
    tech_requirements['existing_website'] = input("Do they have an existing website? (y/N): ").lower() == 'y'
    
    if 'crm' in package_info['services']:
        tech_requirements['existing_crm'] = input("Do they have existing CRM data to import? (y/N): ").lower() == 'y'
    
    if 'stripe' in package_info['services']:
        tech_requirements['existing_stripe'] = input("Do they have an existing Stripe account? (y/N): ").lower() == 'y'
    
    # Timeline
    timelines = ['standard', 'rush', 'flexible']
    print(f"\nTimeline Options:")
    print("1. Standard (2-4 weeks)")
    print("2. Rush (1-2 weeks, +50% fee)")
    print("3. Flexible (4-6 weeks)")
    
    while True:
        try:
            choice = int(input("Select timeline (1-3): "))
            if 1 <= choice <= 3:
                tech_requirements['timeline'] = timelines[choice - 1]
                break
            else:
                print("Invalid choice. Please select 1, 2, or 3.")
        except ValueError:
            print("Please enter a valid number.")
    
    return tech_requirements


def generate_project_summary(customer_info: Dict[str, Any], package_info: Dict[str, Any], 
                           tech_requirements: Dict[str, Any]) -> Dict[str, Any]:
    """Generate complete project summary."""
    project_summary = {
        'customer_info': customer_info,
        'package_info': package_info,
        'tech_requirements': tech_requirements,
        'project_metadata': {
            'created_date': datetime.now().isoformat(),
            'project_id': f"DTL-{customer_info['company'].replace(' ', '').upper()}-{datetime.now().strftime('%Y%m%d')}",
            'estimated_timeline': tech_requirements['timeline'],
            'total_setup_fee': package_info['setup_fee'],
            'monthly_fee': package_info['monthly_fee']
        }
    }
    
    # Adjust pricing for rush timeline
    if tech_requirements['timeline'] == 'rush':
        project_summary['project_metadata']['total_setup_fee'] = int(package_info['setup_fee'] * 1.5)
        project_summary['project_metadata']['rush_fee_applied'] = True
    
    return project_summary


def display_project_summary(project_summary: Dict[str, Any]):
    """Display complete project summary."""
    print("\n" + "="*60)
    print("📋 PROJECT SUMMARY")
    print("="*60)
    
    customer = project_summary['customer_info']
    package = project_summary['package_info']
    tech = project_summary['tech_requirements']
    meta = project_summary['project_metadata']
    
    print(f"\n🏢 CUSTOMER: {customer['company']}")
    print(f"   Domain: {customer['domain']}")
    print(f"   Industry: {customer['industry'].replace('_', ' ').title()}")
    print(f"   Contact: {customer['contact_name']} ({customer['email']})")
    
    print(f"\n📦 PACKAGE: {package['package']}")
    print(f"   Setup Fee: ${meta['total_setup_fee']:,}")
    if meta.get('rush_fee_applied'):
        print(f"   (Includes 50% rush fee)")
    print(f"   Monthly Fee: ${meta['monthly_fee']}")
    print(f"   Services: {', '.join(package['services'])}")
    
    print(f"\n🔧 TECHNICAL:")
    print(f"   Timeline: {tech['timeline'].title()}")
    print(f"   Manage DNS: {'Yes' if tech['manage_dns'] else 'No'}")
    print(f"   Existing Website: {'Yes' if tech['existing_website'] else 'No'}")
    if 'existing_crm' in tech:
        print(f"   CRM Data Import: {'Yes' if tech['existing_crm'] else 'No'}")
    if 'existing_stripe' in tech:
        print(f"   Existing Stripe: {'Yes' if tech['existing_stripe'] else 'No'}")
    
    print(f"\n📊 PROJECT:")
    print(f"   Project ID: {meta['project_id']}")
    print(f"   Client Type: {package['client_type']}")
    print(f"   Created: {meta['created_date'][:10]}")


def save_project_file(project_summary: Dict[str, Any]) -> str:
    """Save project summary to file."""
    project_id = project_summary['project_metadata']['project_id']
    filename = f"customer_projects/{project_id}.json"
    
    # Create directory if it doesn't exist
    os.makedirs('customer_projects', exist_ok=True)
    
    # Save project file
    with open(filename, 'w') as f:
        json.dump(project_summary, f, indent=2)
    
    return filename


def display_next_steps(project_summary: Dict[str, Any], project_file: str):
    """Display next steps for implementation."""
    print("\n" + "="*60)
    print("🚀 NEXT STEPS")
    print("="*60)
    
    project_id = project_summary['project_metadata']['project_id']
    
    print(f"\n1. 📁 Project file saved: {project_file}")
    
    print(f"\n2. 🏢 Create HubSpot record:")
    print(f"   - Add customer to DTL-Global CRM")
    print(f"   - Set pipeline stage to 'Build Website'")
    print(f"   - Add project ID: {project_id}")
    
    print(f"\n3. 🚀 Start technical implementation:")
    print(f"   curl -X POST https://your-api-gateway/prod/onboard \\")
    print(f"     -H \"Content-Type: application/json\" \\")
    print(f"     -d @{project_file}")
    
    print(f"\n4. 📧 Send project kickoff email:")
    print(f"   - Confirm project details with customer")
    print(f"   - Set expectations for timeline")
    print(f"   - Schedule regular check-ins")
    
    print(f"\n5. 📋 Follow customer onboarding workflow:")
    print(f"   - Reference: .cursor/skills/customer-onboarding/SKILL.md")
    print(f"   - Complete all quality assurance gates")
    print(f"   - Monitor progress daily")
    
    print(f"\n⚠️  IMPORTANT REMINDERS:")
    print(f"   - Customer has paid 50% deposit")
    print(f"   - Final 50% due on project completion")
    print(f"   - Timeline: {project_summary['tech_requirements']['timeline'].title()}")
    print(f"   - Support starts after go-live")


def main():
    """Main execution function."""
    display_welcome()
    
    # Check if user wants to proceed
    proceed = input("\nReady to start customer onboarding? (y/N): ")
    if proceed.lower() != 'y':
        print("❌ Customer onboarding cancelled.")
        sys.exit(0)
    
    try:
        # Check production mode
        is_production = check_production_mode()
        
        # Collect information
        customer_info = collect_customer_info()
        package_info = select_service_package()
        tech_requirements = collect_technical_requirements(customer_info, package_info)
        
        # Generate project summary
        project_summary = generate_project_summary(customer_info, package_info, tech_requirements)
        
        # Display summary
        display_project_summary(project_summary)
        
        # Confirm details
        confirm = input("\nIs this information correct? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Please restart the process with correct information.")
            sys.exit(0)
        
        # Save project file
        project_file = save_project_file(project_summary)
        
        # Display next steps
        display_next_steps(project_summary, project_file)
        
        print(f"\n🎉 Customer onboarding setup complete!")
        print(f"   Project ID: {project_summary['project_metadata']['project_id']}")
        
    except KeyboardInterrupt:
        print("\n❌ Customer onboarding interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Customer onboarding failed: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()