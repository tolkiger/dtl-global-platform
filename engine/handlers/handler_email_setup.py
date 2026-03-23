"""POST /email-setup Lambda handler for DTL-Global onboarding platform.

This handler configures email services for client domains.

Endpoint: POST /email-setup
Purpose: Configure email verification and setup
Dependencies: SES client for email configuration

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


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Configure email services for client domains."""
    print(f"Email setup started - Request ID: {context.aws_request_id}")
    
    try:
        request_data = json.loads(event['body'])
        client_info = request_data['client_info']
        email_config = request_data.get('email_config', {})
        
        # Verify client email address
        verification_result = ses_client.verify_email_address(client_info['email'])
        
        # Send welcome email
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
