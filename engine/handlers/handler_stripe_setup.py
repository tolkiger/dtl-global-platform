"""POST /stripe-setup Lambda handler for DTL-Global onboarding platform.

This handler configures Stripe Connect accounts for clients (SANDBOX mode).

Endpoint: POST /stripe-setup
Purpose: Set up Stripe Connect accounts for client payment processing
Dependencies: Stripe client (SANDBOX mode)

Author: DTL-Global Platform
"""

import json
from typing import Any, Dict
from datetime import datetime

# Import shared modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import config
from stripe_client import stripe_client


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Set up Stripe Connect account for client."""
    print(f"Stripe Connect setup started - Request ID: {context.aws_request_id}")
    
    try:
        request_data = json.loads(event['body'])
        client_info = request_data['client_info']
        business_info = request_data.get('business_info', {})
        
        # Create Stripe Connect account
        account_data = {
            'email': client_info['email'],
            'business_type': business_info.get('business_type', 'individual'),
            'country': business_info.get('country', 'US'),
            'business_profile': {
                'name': client_info.get('company', ''),
                'url': business_info.get('website', ''),
                'mcc': '7372'  # Business services MCC code
            },
            'metadata': {
                'dtl_global_client': 'true',
                'onboarding_id': request_data.get('onboarding_id', '')
            }
        }
        
        connect_account = stripe_client.create_connect_account(account_data)
        
        # Create onboarding link
        return_url = request_data.get('return_url', 'https://dtl-global.org/stripe-complete')
        refresh_url = request_data.get('refresh_url', 'https://dtl-global.org/stripe-refresh')
        
        onboarding_link = stripe_client.create_connect_onboarding_link(
            account_id=connect_account['id'],
            return_url=return_url,
            refresh_url=refresh_url
        )
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'account_id': connect_account['id'],
                'onboarding_url': onboarding_link,
                'charges_enabled': connect_account['charges_enabled'],
                'payouts_enabled': connect_account['payouts_enabled'],
                'message': 'Stripe Connect account created successfully (SANDBOX mode)'
            })
        }
        
    except Exception as e:
        print(f"Error in Stripe Connect setup: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e), 'timestamp': datetime.utcnow().isoformat()})
        }
