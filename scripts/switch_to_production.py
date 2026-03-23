#!/usr/bin/env python3
"""
Switch DTL-Global platform from SANDBOX to PRODUCTION mode.

This script safely switches Stripe from test mode to live mode and updates
all necessary system parameters for real customer onboarding.

CRITICAL: Run this script BEFORE onboarding any real customers.

Author: DTL-Global Platform
"""

import boto3
import sys
import os
from typing import Dict, Any
import json


class ProductionSwitcher:
    """Handles switching DTL-Global platform to production mode."""
    
    def __init__(self):
        """Initialize production switcher."""
        self.ssm = boto3.client('ssm')
        self.current_params = {}
        
    def verify_prerequisites(self) -> bool:
        """Verify all prerequisites are met before switching to production.
        
        Returns:
            True if all prerequisites are met, False otherwise
        """
        print("🔍 Verifying prerequisites for production switch...")
        
        # Check if we have AWS credentials
        try:
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            print(f"✓ AWS credentials valid (Account: {identity['Account']})")
        except Exception as e:
            print(f"✗ AWS credentials error: {str(e)}")
            return False
        
        # Check current Stripe mode
        try:
            current_key = self.get_current_stripe_key()
            if current_key.startswith('sk_live_'):
                print("⚠️  Stripe is already in LIVE mode")
                response = input("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    return False
            elif current_key.startswith('sk_test_'):
                print("✓ Stripe currently in TEST mode (ready to switch)")
            else:
                print("✗ Unrecognized Stripe key format")
                return False
        except Exception as e:
            print(f"✗ Could not verify current Stripe mode: {str(e)}")
            return False
        
        # Verify all required parameters exist
        required_params = [
            '/dtl-global-platform/hubspot/token',
            '/dtl-global-platform/stripe/secret',
            '/dtl-global-platform/stripe/connect_client_id',
            '/dtl-global-platform/anthropic/api_key'
        ]
        
        for param in required_params:
            try:
                self.ssm.get_parameter(Name=param, WithDecryption=True)
                print(f"✓ Parameter exists: {param}")
            except Exception as e:
                print(f"✗ Missing parameter: {param}")
                return False
        
        return True
    
    def get_current_stripe_key(self) -> str:
        """Get current Stripe secret key from SSM.
        
        Returns:
            Current Stripe secret key
        """
        try:
            response = self.ssm.get_parameter(
                Name='/dtl-global-platform/stripe/secret',
                WithDecryption=True
            )
            return response['Parameter']['Value']
        except Exception as e:
            raise Exception(f"Could not retrieve current Stripe key: {str(e)}")
    
    def backup_current_config(self) -> Dict[str, Any]:
        """Backup current configuration before making changes.
        
        Returns:
            Dictionary containing current configuration
        """
        print("💾 Backing up current configuration...")
        
        backup = {
            'timestamp': str(boto3.Session().region_name),
            'parameters': {}
        }
        
        # Backup all DTL-Global parameters
        try:
            paginator = self.ssm.get_paginator('get_parameters_by_path')
            pages = paginator.paginate(
                Path='/dtl-global-platform/',
                Recursive=True,
                WithDecryption=True
            )
            
            for page in pages:
                for param in page['Parameters']:
                    backup['parameters'][param['Name']] = {
                        'value': param['Value'],
                        'type': param['Type']
                    }
            
            # Save backup to file
            backup_file = f"production_switch_backup_{backup['timestamp']}.json"
            with open(backup_file, 'w') as f:
                # Don't save actual values in backup file for security
                safe_backup = {
                    'timestamp': backup['timestamp'],
                    'parameters': {k: {'type': v['type'], 'exists': True} 
                                 for k, v in backup['parameters'].items()}
                }
                json.dump(safe_backup, f, indent=2)
            
            print(f"✓ Configuration backed up to {backup_file}")
            return backup
            
        except Exception as e:
            print(f"✗ Backup failed: {str(e)}")
            raise
    
    def get_live_stripe_credentials(self) -> Dict[str, str]:
        """Get live Stripe credentials from user input.
        
        Returns:
            Dictionary containing live Stripe credentials
        """
        print("\n🔑 Enter your LIVE Stripe credentials:")
        print("⚠️  WARNING: These will be stored securely in AWS SSM Parameter Store")
        print("⚠️  Make sure you're entering LIVE (not test) credentials!")
        
        while True:
            secret_key = input("\nStripe Secret Key (sk_live_...): ").strip()
            if secret_key.startswith('sk_live_'):
                break
            print("✗ Invalid format. Live secret keys must start with 'sk_live_'")
        
        while True:
            client_id = input("Stripe Connect Client ID (ca_...): ").strip()
            if client_id.startswith('ca_'):
                break
            print("✗ Invalid format. Client IDs must start with 'ca_'")
        
        # Confirm credentials
        print(f"\nConfirm credentials:")
        print(f"Secret Key: {secret_key[:15]}...{secret_key[-4:]}")
        print(f"Client ID: {client_id[:10]}...{client_id[-4:]}")
        
        confirm = input("\nAre these credentials correct? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Credentials not confirmed. Exiting.")
            sys.exit(1)
        
        return {
            'secret_key': secret_key,
            'client_id': client_id
        }
    
    def update_stripe_parameters(self, credentials: Dict[str, str]) -> bool:
        """Update Stripe parameters with live credentials.
        
        Args:
            credentials: Dictionary containing live Stripe credentials
            
        Returns:
            True if update successful, False otherwise
        """
        print("\n🔄 Updating Stripe parameters to LIVE mode...")
        
        try:
            # Update secret key
            self.ssm.put_parameter(
                Name='/dtl-global-platform/stripe/secret',
                Value=credentials['secret_key'],
                Type='SecureString',
                Overwrite=True,
                Description='Stripe Live Secret Key for DTL-Global Platform'
            )
            print("✓ Updated Stripe secret key")
            
            # Update client ID
            self.ssm.put_parameter(
                Name='/dtl-global-platform/stripe/connect_client_id',
                Value=credentials['client_id'],
                Type='SecureString',
                Overwrite=True,
                Description='Stripe Connect Live Client ID for DTL-Global Platform'
            )
            print("✓ Updated Stripe Connect client ID")
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to update Stripe parameters: {str(e)}")
            return False
    
    def verify_production_mode(self) -> bool:
        """Verify that production mode is working correctly.
        
        Returns:
            True if production mode verified, False otherwise
        """
        print("\n🧪 Verifying production mode...")
        
        try:
            # Check that parameters were updated
            secret_key = self.ssm.get_parameter(
                Name='/dtl-global-platform/stripe/secret',
                WithDecryption=True
            )['Parameter']['Value']
            
            if not secret_key.startswith('sk_live_'):
                print("✗ Stripe secret key is not in live mode")
                return False
            
            print("✓ Stripe secret key confirmed as live")
            
            client_id = self.ssm.get_parameter(
                Name='/dtl-global-platform/stripe/connect_client_id',
                WithDecryption=True
            )['Parameter']['Value']
            
            if not client_id.startswith('ca_'):
                print("✗ Stripe client ID format invalid")
                return False
            
            print("✓ Stripe Connect client ID confirmed")
            
            # TODO: Add API test to verify Stripe is working
            # This would require importing stripe library and making test call
            
            print("✅ Production mode verification complete")
            return True
            
        except Exception as e:
            print(f"✗ Production mode verification failed: {str(e)}")
            return False
    
    def display_next_steps(self):
        """Display next steps after successful production switch."""
        print("\n" + "="*60)
        print("🎉 PRODUCTION MODE SWITCH COMPLETE!")
        print("="*60)
        print("\n📋 NEXT STEPS:")
        print("\n1. Update Stripe Products in Live Mode:")
        print("   python scripts/phase0_stripe_setup.py --live-mode")
        print("\n2. Test Production Setup:")
        print("   python test_phase6_end_to_end.py")
        print("\n3. Verify Customer Onboarding Process:")
        print("   Review .cursor/skills/customer-onboarding/SKILL.md")
        print("\n4. Ready for Real Customer:")
        print("   Follow the customer onboarding workflow")
        print("\n⚠️  IMPORTANT REMINDERS:")
        print("   - All payments will now be REAL money")
        print("   - Test thoroughly before customer onboarding")
        print("   - Monitor system closely during first customer")
        print("   - Have rollback plan ready if needed")
        print("\n🔒 Security Note:")
        print("   Live Stripe credentials are stored securely in AWS SSM")
        print("   Never share or commit these credentials")
        print("\n" + "="*60)


def main():
    """Main execution function."""
    print("🚀 DTL-Global Platform - Production Mode Switch")
    print("=" * 50)
    print("\n⚠️  WARNING: This will switch Stripe from TEST to LIVE mode")
    print("⚠️  All payments after this will be REAL money!")
    print("\nThis script will:")
    print("1. Verify system prerequisites")
    print("2. Backup current configuration")
    print("3. Update Stripe to live credentials")
    print("4. Verify production mode is working")
    
    # Confirm user wants to proceed
    print("\n" + "="*50)
    proceed = input("Do you want to proceed? (y/N): ")
    if proceed.lower() != 'y':
        print("❌ Production switch cancelled.")
        sys.exit(0)
    
    switcher = ProductionSwitcher()
    
    try:
        # Step 1: Verify prerequisites
        if not switcher.verify_prerequisites():
            print("❌ Prerequisites not met. Cannot proceed.")
            sys.exit(1)
        
        # Step 2: Backup current configuration
        backup = switcher.backup_current_config()
        
        # Step 3: Get live Stripe credentials
        credentials = switcher.get_live_stripe_credentials()
        
        # Step 4: Update Stripe parameters
        if not switcher.update_stripe_parameters(credentials):
            print("❌ Failed to update Stripe parameters.")
            sys.exit(1)
        
        # Step 5: Verify production mode
        if not switcher.verify_production_mode():
            print("❌ Production mode verification failed.")
            sys.exit(1)
        
        # Step 6: Display next steps
        switcher.display_next_steps()
        
    except KeyboardInterrupt:
        print("\n❌ Production switch interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Production switch failed: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()