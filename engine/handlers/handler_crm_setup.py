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

# Add both the engine root and shared directory to path
engine_root = os.path.dirname(os.path.dirname(__file__))
shared_path = os.path.join(engine_root, 'shared')
if engine_root not in sys.path:
    sys.path.insert(0, engine_root)
if shared_path not in sys.path:
    sys.path.insert(0, shared_path)

# Import config only - clients will be imported in handler
from config import config


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
        # Import HubSpot client inside handler to avoid initialization issues during testing
        from hubspot_client import hubspot_client
        
        # Handle both API Gateway format (with body) and direct format (for testing)
        if event.get('body'):
            # API Gateway format
            request_data = json.loads(event['body'])
        else:
            # Direct format (for testing)
            request_data = event
        
        # Extract client information
        client_info = request_data.get('client_info', {})
        
        # Validate required parameters
        if not client_info.get('email'):
            return _create_error_response(400, "Missing required parameter: email in client_info")
        
        # Create/update HubSpot contact
        # Get contact name from either 'contact_name' or 'name' field
        full_name = client_info.get('contact_name', client_info.get('name', ''))
        name_parts = full_name.split(' ') if full_name else ['', '']
        
        industry_input = client_info.get('industry', '')  # Capture caller-provided industry value
        normalized_industry = industry_input  # Default to the raw value unless we normalize it
        if isinstance(industry_input, str) and industry_input.strip().lower() == 'consulting':
            normalized_industry = 'MANAGEMENT_CONSULTING'  # HubSpot's allowed enum for "consulting"
        
        contact_data = {
            'email': client_info['email'],
            'firstname': name_parts[0] if name_parts else '',
            'lastname': ' '.join(name_parts[1:]) if len(name_parts) > 1 else '',
            'company': client_info.get('company', ''),
            'phone': client_info.get('phone', ''),
            'industry': normalized_industry,  # Use normalized industry value for HubSpot enum validation
            'lifecyclestage': 'customer',
        }
        
        # Create contact if missing, or update properties if the contact already exists
        existing_contact = hubspot_client.get_contact_by_email(client_info['email'])
        if existing_contact:
            contact = hubspot_client.update_contact(str(existing_contact['id']), contact_data)
        else:
            contact = hubspot_client.create_contact(contact_data)
        
        # Resolve company by domain (preferred) or exact name; create only when missing
        company = None
        company_name = (client_info.get('company') or '').strip()
        if company_name:
            company_data = {
                'name': company_name,
                'industry': normalized_industry,
                'phone': client_info.get('phone', ''),
            }
            domain_val = (client_info.get('domain') or '').strip()
            if domain_val:
                company_data['domain'] = domain_val
            existing_company = None
            if domain_val:
                existing_company = hubspot_client.get_company_by_domain(domain_val)
            if not existing_company:
                existing_company = hubspot_client.get_company_by_name(company_name)
            if existing_company:
                company = hubspot_client.update_company(str(existing_company['id']), company_data)
            else:
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
            # HubSpot expects `closedate` as a long/int (Unix milliseconds), not an ISO string
            'closedate': int((datetime.utcnow() + timedelta(days=14)).timestamp() * 1000),
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
