"""POST /notify Lambda handler for DTL-Global onboarding platform.

This handler sends notifications to clients and internal team members.

Endpoint: POST /notify
Purpose: Send email notifications for onboarding events
Dependencies: SES client for email delivery

Author: DTL-Global Platform
"""

import json
from typing import Any, Dict
from datetime import datetime

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
    """Send notifications for onboarding events."""
    print(f"Notification handler started - Request ID: {context.aws_request_id}")
    
    try:
        # Import SES client inside handler to avoid initialization issues during testing
        from ses_client import ses_client
        
        # Handle both API Gateway format (with body) and direct format (for testing)
        if event.get('body'):
            # API Gateway format
            request_data = json.loads(event['body'])
        else:
            # Direct format (for testing)
            request_data = event
            
        notification_type = request_data.get('notification_type')
        client_info = request_data.get('client_info', {})
        
        # Validate required parameters
        if not client_info.get('email'):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required parameter: email in client_info',
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        if notification_type == 'welcome':
            # Send welcome email
            project_details = {
                'project_name': f"{client_info['company']} Digital Transformation",
                'services': request_data.get('services', []),
                'timeline': '2-4 weeks'
            }
            
            result = ses_client.send_onboarding_welcome(
                client_email=client_info['email'],
                client_name=client_info.get('contact_name', client_info.get('name', 'Customer')),
                project_details=project_details
            )
            
        elif notification_type == 'status_update':
            # Send status update email
            status_data = request_data.get('status_data', {})
            result = ses_client.send_status_update(
                client_email=client_info['email'],
                client_name=client_info.get('contact_name', client_info.get('name', 'Customer')),
                status_data=status_data
            )
            
        else:
            # Generic notification
            result = ses_client.send_email(
                to_addresses=client_info['email'],
                subject=request_data.get('subject', 'DTL-Global Notification'),
                body_text=request_data.get('message', 'Thank you for choosing DTL-Global!')
            )
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'message_id': result['MessageId'],
                'notification_type': notification_type,
                'message': 'Notification sent successfully'
            })
        }
        
    except Exception as e:
        print(f"Error in notification handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e), 'timestamp': datetime.utcnow().isoformat()})
        }
