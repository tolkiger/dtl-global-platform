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


def _setup_google_workspace_dns(domain: str, admin_email: str, client_info: Dict[str, Any]) -> Dict[str, Any]:
    """Set up DNS records for Google Workspace email.
    
    Args:
        domain: Client domain for email setup
        admin_email: Admin email for workspace setup
        client_info: Client information dictionary
        
    Returns:
        Dictionary with setup results and DNS records
    """
    try:
        print(f"Setting up Google Workspace DNS for domain: {domain}")
        
        # Get or create hosted zone for the domain
        zone_info = route53_client.get_or_create_hosted_zone(domain)
        zone_id = zone_info['zone_id']
        
        # Google Workspace MX records (priority, server)
        mx_records = [
            (1, 'smtp.google.com'),
            (5, 'alt1.gmail-smtp-in.l.google.com'),
            (5, 'alt2.gmail-smtp-in.l.google.com'),
            (10, 'alt3.gmail-smtp-in.l.google.com'),
            (10, 'alt4.gmail-smtp-in.l.google.com')
        ]
        
        # Create MX records for Google Workspace
        for priority, server in mx_records:
            route53_client.create_mx_record(zone_id, domain, priority, server)
        
        # Create TXT record for domain verification (placeholder - user must add actual verification code)
        verification_txt = f"google-site-verification=PLACEHOLDER_VERIFICATION_CODE"
        route53_client.create_txt_record(zone_id, domain, verification_txt)
        
        # Create CNAME records for Google services
        cname_records = {
            'mail': 'ghs.googlehosted.com',
            'calendar': 'ghs.googlehosted.com',
            'drive': 'ghs.googlehosted.com'
        }
        
        for subdomain, target in cname_records.items():
            route53_client.create_cname_record(zone_id, f"{subdomain}.{domain}", target)
        
        # Generate setup instructions
        instructions = _generate_google_workspace_instructions(domain, admin_email)
        
        return {
            'success': True,
            'provider': 'google_workspace',
            'domain': domain,
            'zone_id': zone_id,
            'mx_records': mx_records,
            'setup_instructions': instructions,
            'message': 'Google Workspace DNS records created successfully'
        }
        
    except Exception as e:
        print(f"ERROR: Google Workspace setup failed: {e}")
        return {
            'success': False,
            'error': f'Google Workspace setup error: {str(e)}',
            'message': 'Google Workspace DNS setup failed'
        }


def _setup_microsoft365_dns(domain: str, admin_email: str, client_info: Dict[str, Any]) -> Dict[str, Any]:
    """Set up DNS records for Microsoft 365 email.
    
    Args:
        domain: Client domain for email setup
        admin_email: Admin email for workspace setup
        client_info: Client information dictionary
        
    Returns:
        Dictionary with setup results and DNS records
    """
    try:
        print(f"Setting up Microsoft 365 DNS for domain: {domain}")
        
        # Get or create hosted zone for the domain
        zone_info = route53_client.get_or_create_hosted_zone(domain)
        zone_id = zone_info['zone_id']
        
        # Microsoft 365 MX record
        route53_client.create_mx_record(zone_id, domain, 0, f"{domain.replace('.', '-')}.mail.protection.outlook.com")
        
        # Create TXT records for Microsoft 365
        txt_records = [
            f"v=spf1 include:spf.protection.outlook.com -all",  # SPF record
            f"MS=msXXXXXXXX"  # Domain verification (placeholder)
        ]
        
        for txt_record in txt_records:
            route53_client.create_txt_record(zone_id, domain, txt_record)
        
        # Create CNAME records for Microsoft 365 services
        cname_records = {
            'autodiscover': 'autodiscover.outlook.com',
            'sip': 'sipdir.online.lync.com',
            'lyncdiscover': 'webdir.online.lync.com'
        }
        
        for subdomain, target in cname_records.items():
            route53_client.create_cname_record(zone_id, f"{subdomain}.{domain}", target)
        
        # Generate setup instructions
        instructions = _generate_microsoft365_instructions(domain, admin_email)
        
        return {
            'success': True,
            'provider': 'microsoft365',
            'domain': domain,
            'zone_id': zone_id,
            'setup_instructions': instructions,
            'message': 'Microsoft 365 DNS records created successfully'
        }
        
    except Exception as e:
        print(f"ERROR: Microsoft 365 setup failed: {e}")
        return {
            'success': False,
            'error': f'Microsoft 365 setup error: {str(e)}',
            'message': 'Microsoft 365 DNS setup failed'
        }


def _generate_google_workspace_instructions(domain: str, admin_email: str) -> list:
    """Generate step-by-step Google Workspace setup instructions.
    
    Args:
        domain: Client domain for email setup
        admin_email: Admin email for setup
        
    Returns:
        List of setup instruction strings
    """
    return [
        "1. Sign up for Google Workspace at workspace.google.com",
        f"2. Add domain '{domain}' to your Google Workspace account",
        "3. Verify domain ownership using the TXT record we created",
        "4. Create user accounts for your team members",
        f"5. Set up {admin_email} as the primary admin account",
        "6. Configure Gmail, Calendar, and Drive access",
        "7. Test email delivery by sending a test message",
        "Note: DNS records have been configured automatically",
        "For assistance with Google Workspace setup, contact DTL-Global support."
    ]


def _generate_microsoft365_instructions(domain: str, admin_email: str) -> list:
    """Generate step-by-step Microsoft 365 setup instructions.
    
    Args:
        domain: Client domain for email setup
        admin_email: Admin email for setup
        
    Returns:
        List of setup instruction strings
    """
    return [
        "1. Sign up for Microsoft 365 at admin.microsoft.com",
        f"2. Add custom domain '{domain}' in the Microsoft 365 admin center",
        "3. Verify domain ownership using the TXT record we created",
        "4. Create user mailboxes for your team members",
        f"5. Set up {admin_email} as the global administrator",
        "6. Configure Outlook, Teams, and OneDrive access",
        "7. Test email delivery by sending a test message",
        "Note: DNS records have been configured automatically",
        "For assistance with Microsoft 365 setup, contact DTL-Global support."
    ]
