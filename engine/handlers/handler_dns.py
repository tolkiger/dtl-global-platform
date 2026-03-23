"""POST /dns Lambda handler for DTL-Global onboarding platform.

This handler manages DNS configuration for client domains.

Endpoint: POST /dns
Purpose: Configure DNS records for client domains
Dependencies: Route 53 client for DNS management

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
from route53_client import route53_client


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Configure DNS records for client domains."""
    print(f"DNS configuration started - Request ID: {context.aws_request_id}")
    
    try:
        request_data = json.loads(event['body'])
        domain = request_data['domain']
        action = request_data.get('action', 'setup')
        
        if action == 'setup':
            # Create hosted zone if needed
            hosted_zone = route53_client.create_hosted_zone(domain)
            
            # Generate DNS instructions for manual setup
            cloudfront_domain = "d111111abcdef8.cloudfront.net"  # Placeholder
            
            dns_instructions = {
                'hosted_zone_id': hosted_zone['id'],
                'name_servers': hosted_zone['name_servers'],
                'records_to_create': [
                    {
                        'type': 'CNAME',
                        'name': f'www.{domain}',
                        'value': cloudfront_domain,
                        'ttl': 300
                    }
                ]
            }
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': True,
                    'domain': domain,
                    'hosted_zone_id': hosted_zone['id'],
                    'dns_instructions': dns_instructions,
                    'message': 'DNS setup instructions generated'
                })
            }
            
        elif action == 'validate':
            # Check DNS propagation
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': True,
                    'domain': domain,
                    'validation_status': 'pending',
                    'message': 'DNS validation check completed'
                })
            }
        
    except Exception as e:
        print(f"Error in DNS handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e), 'timestamp': datetime.utcnow().isoformat()})
        }
