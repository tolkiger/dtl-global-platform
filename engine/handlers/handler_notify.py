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
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import config
from ses_client import ses_client


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Send notifications for onboarding events."""
    print(f"Notification handler started - Request ID: {context.aws_request_id}")
    
    try:
        request_data = json.loads(event['body'])
        notification_type = request_data['notification_type']
        client_info = request_data['client_info']
        
        if notification_type == 'welcome':
            # Send welcome email
            project_details = {
                'project_name': f"{client_info['company']} Digital Transformation",
                'services': request_data.get('services', []),
                'timeline': '2-4 weeks'
            }
            
            result = ses_client.send_onboarding_welcome(
                client_email=client_info['email'],
                client_name=client_info['name'],
                project_details=project_details
            )
            
        elif notification_type == 'status_update':
            # Send status update email
            status_data = request_data.get('status_data', {})
            result = ses_client.send_status_update(
                client_email=client_info['email'],
                client_name=client_info['name'],
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
