#!/usr/bin/env python3
"""
Quick Customer Onboarding Wrapper Script

This script provides a simplified interface to onboard customers
using the automated onboarding system.
"""

import json
import os
import sys
from datetime import datetime
from automated_customer_onboarding import AutomatedOnboardingProcessor


def main():
    """Main function for quick customer onboarding."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/onboard_customer.py <company_name>")
        print("Example: python scripts/onboard_customer.py businesscentersolutions")
        return 1
    
    company_name = sys.argv[1].lower().replace(' ', '_').replace('.', '').replace('-', '_')
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    company_dir = os.path.join(project_root, 'customer_projects', company_name)
    
    # Find the most recent project file for this company
    if not os.path.exists(company_dir):
        print(f"❌ No customer project found for: {company_name}")
        print(f"   Expected directory: {company_dir}")
        return 1
    
    # Look for JSON project files
    project_files = [f for f in os.listdir(company_dir) if f.endswith('.json')]
    if not project_files:
        print(f"❌ No project files found in: {company_dir}")
        return 1
    
    # Use the most recent project file
    project_file = os.path.join(company_dir, sorted(project_files)[-1])
    
    print(f"🚀 Starting automated onboarding for: {company_name}")
    print(f"📁 Using project file: {project_file}")
    print("=" * 60)
    
    # Load customer data
    with open(project_file, 'r') as f:
        project_data = json.load(f)
    
    # Extract customer data from project structure
    customer_data = project_data.get('customer_info', {})
    if 'package_info' not in customer_data:
        customer_data['package_info'] = project_data.get('package_info', {})
    if 'tech_requirements' not in customer_data:
        customer_data['tech_requirements'] = project_data.get('tech_requirements', {})
    
    # Initialize processor
    processor = AutomatedOnboardingProcessor()
    
    # Process onboarding
    results = processor.process_customer_onboarding(customer_data)
    
    # Update project file with results
    project_data['onboarding_results'] = results
    project_data['project_metadata']['last_updated'] = datetime.now().isoformat()
    project_data['project_metadata']['status'] = 'completed' if results['success'] else 'failed'
    
    with open(project_file, 'w') as f:
        json.dump(project_data, f, indent=2)
    
    # Output results
    print("\n" + "="*60)
    print("📊 ONBOARDING RESULTS")
    print("="*60)
    
    if results['success']:
        print("✅ Onboarding completed successfully!")
        print(f"📁 Project ID: {results['project_id']}")
        
        print("\n🔧 Completed Steps:")
        for step, result in results['onboarding_steps'].items():
            status = "✅" if result.get('success', False) else "❌"
            print(f"   {status} {step.replace('_', ' ').title()}")
        
        print(f"\n📂 Customer files updated in: {company_dir}")
        
        if results.get('next_steps'):
            print("\n📋 Next Steps:")
            for step in results['next_steps']:
                print(f"   • {step}")
    else:
        print("❌ Onboarding failed!")
        for error in results['errors']:
            print(f"   • {error}")
    
    return 0 if results['success'] else 1


if __name__ == '__main__':
    exit(main())