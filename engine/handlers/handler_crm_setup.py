"""POST /crm-setup Lambda handler for DTL-Global onboarding platform.

This handler configures HubSpot CRM for new clients including contacts,
companies, deals, and custom properties setup.

Endpoint: POST /crm-setup
Purpose: Configure HubSpot CRM for client onboarding
Dependencies: HubSpot client, DynamoDB for tracking

Author: DTL-Global Platform
"""

import json
import boto3
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

# Import shared modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import config
from hubspot_client import hubspot_client


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Configure HubSpot CRM for client onboarding.
    
    Args:
        event: API Gateway proxy request event
        context: Lambda runtime context object
        
    Returns:
        API Gateway proxy response with CRM setup results
    """
    print(f"CRM setup started - Request ID: {context.aws_request_id}")
    
    try:
        # Parse request body
        if not event.get('body'):
            return _create_error_response(400, "Request body is required")
        
        request_data = json.loads(event['body'])
        
        # Extract client information
        client_info = request_data['client_info']
        
        # Create/update HubSpot contact
        contact_data = {
            'email': client_info['email'],
            'firstname': client_info.get('name', '').split(' ')[0] if client_info.get('name') else '',
            'lastname': ' '.join(client_info.get('name', '').split(' ')[1:]) if client_info.get('name') and len(client_info.get('name', '').split(' ')) > 1 else '',
            'company': client_info.get('company', ''),
            'phone': client_info.get('phone', ''),
            'industry': client_info.get('industry', ''),
            'lifecyclestage': 'customer',
            'lead_source': 'dtl_global_onboarding'
        }
        
        # Check if contact exists
        existing_contact = hubspot_client.get_contact_by_email(client_info['email'])
        if existing_contact:
            contact = existing_contact
        else:
            contact = hubspot_client.create_contact(contact_data)
        
        # Create company if specified
        company = None
        if client_info.get('company'):
            company_data = {
                'name': client_info['company'],
                'industry': client_info.get('industry', ''),
                'phone': client_info.get('phone', ''),
                'domain': client_info.get('domain', '')
            }
            company = hubspot_client.create_company(company_data)
            hubspot_client.associate_contact_to_company(contact['id'], company['id'])
        
        # Create onboarding deal
        pipeline_stages = hubspot_client.get_dtl_pipeline_stages()
        deal_data = {
            'dealname': f"{client_info['company']} - Onboarding",
            'pipeline': 'default',
            'dealstage': pipeline_stages['build'],
            'amount': str(request_data.get('setup_cost', 500)),
            'dealtype': 'newbusiness',
            'closedate': (datetime.utcnow() + timedelta(days=14)).isoformat(),
            'deal_currency_code': 'USD'
        }
        
        deal = hubspot_client.create_deal(deal_data)
        hubspot_client.associate_contact_to_deal(contact['id'], deal['id'])
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'contact_id': contact['id'],
                'company_id': company['id'] if company else None,
                'deal_id': deal['id'],
                'message': 'CRM setup completed successfully'
            })
        }
        
    except Exception as e:
        print(f"Error in CRM setup: {str(e)}")
        return _create_error_response(500, f"Internal server error: {str(e)}")


def _create_error_response(status_code: int, error_message: str) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'error': error_message, 'timestamp': datetime.utcnow().isoformat()})
    }
