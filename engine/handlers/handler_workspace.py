"""POST /workspace Lambda handler for DTL-Global onboarding platform.

This handler manages Google Workspace email setup and DNS configuration.

Endpoint: POST /workspace
Purpose: Configure Google Workspace email for client domains
Dependencies: Route53 client for DNS records

Author: DTL-Global Platform
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime

# Import shared modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import config
from route53_client import route53_client


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Configure Google Workspace email setup for client domains.
    
    Args:
        event: API Gateway event containing workspace setup request
        context: Lambda context object
        
    Returns:
        Dict containing workspace setup results and DNS records
    """
    print(f"Workspace handler started - Request ID: {context.aws_request_id}")
    
    try:
        # Parse request body from API Gateway event
        request_data = json.loads(event['body'])
        
        # Extract workspace configuration data
        domain = request_data.get('domain', '')  # Client domain for email setup
        workspace_type = request_data.get('workspace_type', 'google')  # Email provider type
        admin_email = request_data.get('admin_email', '')  # Admin email for setup
        client_info = request_data.get('client_info', {})  # Client information
        
        print(f"Setting up {workspace_type} workspace for domain: {domain}")
        
        # Validate required fields
        if not domain:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Domain is required for workspace setup',
                    'success': False
                })
            }
        
        # Configure workspace based on type
        if workspace_type == 'google':
            # Set up Google Workspace email
            result = _setup_google_workspace(domain, admin_email, client_info)
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': f'Unsupported workspace type: {workspace_type}',
                    'success': False
                })
            }
        
        # Return successful response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'domain': domain,
                'workspace_type': workspace_type,
                'dns_records': result.get('dns_records', []),
                'setup_instructions': result.get('instructions', []),
                'verification_required': result.get('verification_required', True)
            })
        }
        
    except json.JSONDecodeError as e:
        # Handle invalid JSON in request body
        print(f"JSON decode error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Invalid JSON in request body',
                'success': False
            })
        }
        
    except Exception as e:
        # Handle unexpected errors
        print(f"Workspace handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error setting up workspace',
                'success': False
            })
        }


def _setup_google_workspace(domain: str, admin_email: str, 
                          client_info: Dict[str, Any]) -> Dict[str, Any]:
    """Set up Google Workspace email for client domain.
    
    Args:
        domain: Client domain for email setup
        admin_email: Admin email for workspace setup
        client_info: Client information dictionary
        
    Returns:
        Dictionary with setup results and DNS records
    """
    try:
        # Define Google Workspace DNS records
        dns_records = _get_google_workspace_dns_records(domain)
        
        # Create DNS records if domain is managed by Route53
        dns_results = []
        for record in dns_records:
            try:
                # Attempt to create DNS record
                result = route53_client.create_dns_record(
                    domain=domain,
                    record_type=record['type'],
                    name=record['name'],
                    value=record['value'],
                    ttl=record.get('ttl', 300)
                )
                
                dns_results.append({
                    'record': record,
                    'created': result.get('success', False),
                    'message': result.get('message', 'Unknown result')
                })
                
            except Exception as e:
                print(f"Error creating DNS record {record['name']}: {str(e)}")
                dns_results.append({
                    'record': record,
                    'created': False,
                    'message': f'Error: {str(e)}'
                })
        
        # Generate setup instructions
        instructions = _generate_workspace_instructions(domain, admin_email, dns_records)
        
        return {
            'dns_records': dns_records,
            'dns_results': dns_results,
            'instructions': instructions,
            'verification_required': True,
            'setup_complete': False
        }
        
    except Exception as e:
        print(f"Error setting up Google Workspace: {str(e)}")
        return {
            'error': f'Google Workspace setup error: {str(e)}',
            'dns_records': [],
            'instructions': [],
            'verification_required': True
        }


def _get_google_workspace_dns_records(domain: str) -> List[Dict[str, Any]]:
    """Get required DNS records for Google Workspace setup.
    
    Args:
        domain: Client domain for email setup
        
    Returns:
        List of DNS record dictionaries
    """
    # Standard Google Workspace DNS records
    records = [
        # MX Records for email routing
        {
            'type': 'MX',
            'name': domain,
            'value': '1 smtp.google.com.',
            'ttl': 300,
            'priority': 1,
            'description': 'Primary Google Workspace mail server'
        },
        {
            'type': 'MX',
            'name': domain,
            'value': '5 smtp2.google.com.',
            'ttl': 300,
            'priority': 5,
            'description': 'Secondary Google Workspace mail server'
        },
        {
            'type': 'MX',
            'name': domain,
            'value': '5 smtp3.google.com.',
            'ttl': 300,
            'priority': 5,
            'description': 'Tertiary Google Workspace mail server'
        },
        {
            'type': 'MX',
            'name': domain,
            'value': '10 smtp4.google.com.',
            'ttl': 300,
            'priority': 10,
            'description': 'Backup Google Workspace mail server'
        },
        
        # SPF Record for email authentication
        {
            'type': 'TXT',
            'name': domain,
            'value': '"v=spf1 include:_spf.google.com ~all"',
            'ttl': 300,
            'description': 'SPF record for Google Workspace email authentication'
        },
        
        # DKIM Record (placeholder - actual key provided by Google)
        {
            'type': 'TXT',
            'name': f'google._domainkey.{domain}',
            'value': '"v=DKIM1; k=rsa; p=REPLACE_WITH_GOOGLE_DKIM_KEY"',
            'ttl': 300,
            'description': 'DKIM record for Google Workspace (replace with actual key from Google Admin)'
        },
        
        # DMARC Record for email policy
        {
            'type': 'TXT',
            'name': f'_dmarc.{domain}',
            'value': '"v=DMARC1; p=quarantine; rua=mailto:dmarc@dtl-global.org"',
            'ttl': 300,
            'description': 'DMARC policy for email authentication'
        },
        
        # Google Workspace verification record (placeholder)
        {
            'type': 'TXT',
            'name': domain,
            'value': '"google-site-verification=REPLACE_WITH_GOOGLE_VERIFICATION_CODE"',
            'ttl': 300,
            'description': 'Google Workspace domain verification (replace with actual code from Google Admin)'
        }
    ]
    
    return records


def _generate_workspace_instructions(domain: str, admin_email: str, 
                                   dns_records: List[Dict[str, Any]]) -> List[str]:
    """Generate step-by-step Google Workspace setup instructions.
    
    Args:
        domain: Client domain
        admin_email: Admin email for setup
        dns_records: List of DNS records to configure
        
    Returns:
        List of instruction strings
    """
    instructions = [
        "Google Workspace Email Setup Instructions:",
        "",
        "1. Sign up for Google Workspace:",
        f"   - Go to workspace.google.com",
        f"   - Choose a plan (Business Starter recommended)",
        f"   - Enter domain: {domain}",
        f"   - Create admin account with email: {admin_email}",
        "",
        "2. Verify domain ownership:",
        "   - In Google Admin Console, go to Domains",
        "   - Follow verification steps provided by Google",
        "   - Add the verification TXT record to your DNS",
        "",
        "3. Configure DNS records:",
        "   The following DNS records have been configured (or need manual setup):",
        ""
    ]
    
    # Add DNS record details to instructions
    for record in dns_records:
        instructions.append(f"   {record['type']} Record:")
        instructions.append(f"     Name: {record['name']}")
        instructions.append(f"     Value: {record['value']}")
        instructions.append(f"     Description: {record['description']}")
        instructions.append("")
    
    instructions.extend([
        "4. Complete Google Workspace setup:",
        "   - Wait for DNS propagation (up to 24 hours)",
        "   - Verify MX records in Google Admin Console",
        "   - Create user accounts for your team",
        "   - Configure Gmail, Calendar, and Drive access",
        "",
        "5. Test email functionality:",
        f"   - Send test email to admin@{domain}",
        "   - Verify email delivery and reception",
        "   - Check spam folder if emails not received",
        "",
        "Note: Some DNS records contain placeholder values that must be",
        "replaced with actual codes from Google Admin Console.",
        "",
        "For assistance, contact DTL-Global support."
    ])
    
    return instructions