"""POST /email-setup Lambda handler for DTL-Global onboarding platform.

This handler configures email services for client domains including both
SES verification and workspace email setup (Google Workspace, Microsoft 365).

Endpoint: POST /email-setup
Purpose: Configure email verification, SES setup, and workspace email DNS records
Dependencies: SES client for email configuration, Route 53 for DNS records

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
from ses_client import ses_client
from route53_client import route53_client


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Configure email services for client domains including workspace setup.
    
    This function handles:
    1. SES email verification and welcome emails
    2. Google Workspace DNS record creation (MX, TXT, CNAME)
    3. Microsoft 365 DNS record creation (MX, TXT, CNAME)
    
    Args:
        event: API Gateway proxy request event containing email setup data
        context: Lambda runtime context object
        
    Returns:
        API Gateway proxy response with email setup results
        
    Expected Request Body:
        {
            "client_info": {
                "email": "client@example.com",
                "name": "Client Name",
                "company": "Company Name"
            },
            "email_config": {
                "domain": "clientdomain.com",
                "workspace_type": "google|microsoft|ses_only",
                "admin_email": "admin@clientdomain.com"
            }
        }
    """
    print(f"Email setup started - Request ID: {context.aws_request_id}")
    
    try:
        request_data = json.loads(event['body'])
        client_info = request_data['client_info']
        email_config = request_data.get('email_config', {})
        
        # Extract email configuration
        domain = email_config.get('domain', '')  # Client domain for email setup
        workspace_type = email_config.get('workspace_type', 'ses_only')  # Email provider type
        admin_email = email_config.get('admin_email', client_info['email'])  # Admin email for workspace
        
        print(f"Setting up email for domain: {domain}, type: {workspace_type}")
        
        # Step 1: Verify client email address with SES
        verification_result = ses_client.verify_email_address(client_info['email'])
        
        # Step 2: Send welcome email
        project_details = {
            'project_name': f"{client_info['company']} Digital Transformation",
            'services': email_config.get('services', []),
            'timeline': '2-4 weeks'
        }
        
        welcome_result = ses_client.send_onboarding_welcome(
            client_email=client_info['email'],
            client_name=client_info['name'],
            project_details=project_details
        )
        
        # Step 3: Set up workspace email DNS records if requested
        workspace_result = {'success': True, 'message': 'No workspace setup requested'}
        if workspace_type == 'google' and domain:
            workspace_result = _setup_google_workspace_dns(domain, admin_email, client_info)
        elif workspace_type == 'microsoft' and domain:
            workspace_result = _setup_microsoft365_dns(domain, admin_email, client_info)
        elif workspace_type == 'ses_only':
            print("SES-only email setup - no workspace DNS records needed")
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'email_verified': verification_result['verification_sent'],
                'welcome_email_sent': True,
                'welcome_message_id': welcome_result['MessageId'],
                'message': 'Email setup completed successfully'
            })
        }
        
    except Exception as e:
        print(f"Error in email setup: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e), 'timestamp': datetime.utcnow().isoformat()})
        }
