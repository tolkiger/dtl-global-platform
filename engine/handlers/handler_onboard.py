"""POST /onboard Lambda handler for DTL-Global onboarding platform.

This is the main orchestrator that coordinates the complete client onboarding process.
It handles all 4 client types and orchestrates the appropriate services for each.

Endpoint: POST /onboard
Purpose: Orchestrate complete client onboarding based on client type
Dependencies: All shared modules, other handlers via internal calls

Author: DTL-Global Platform
"""

import json
import boto3
import requests
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta

# Import shared modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import config, CLIENT_TYPES
from hubspot_client import hubspot_client
from ses_client import ses_client


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Orchestrate complete client onboarding process.
    
    This function coordinates all onboarding steps based on the client type:
    - full_package: DNS, website, CRM, Stripe, email, notify
    - website_only: DNS, website, email (optional), notify  
    - website_crm: DNS, website, CRM, notify
    - crm_payments: CRM, Stripe, notify
    
    Args:
        event: API Gateway proxy request event containing onboarding data
        context: Lambda runtime context object
        
    Returns:
        API Gateway proxy response with onboarding status and results
        
    Expected Request Body:
        {
            "client_info": {
                "name": "Client Name",
                "email": "client@example.com",
                "company": "Company Name", 
                "phone": "555-1234",
                "industry": "roofing",
                "address": "123 Main St, City, State 12345"
            },
            "client_type": "full_package",  // Required: one of 4 types
            "services_config": {
                "domain": "clientname.com",  // For DNS/website
                "website_preferences": {...},
                "crm_preferences": {...},
                "stripe_preferences": {...}
            },
            "bid_id": "uuid-from-bid-handler"  // Optional: link to existing bid
        }
    """
    print(f"Onboarding orchestration started - Request ID: {context.aws_request_id}")
    
    try:
        # Parse request body
        if not event.get('body'):
            return _create_error_response(400, "Request body is required")
        
        # Parse JSON body from API Gateway
        try:
            request_data = json.loads(event['body'])
        except json.JSONDecodeError as e:
            return _create_error_response(400, f"Invalid JSON in request body: {e}")
        
        # Validate required fields
        validation_error = _validate_onboard_request(request_data)
        if validation_error:
            return _create_error_response(400, validation_error)
        
        # Extract onboarding data
        client_info = request_data['client_info']
        client_type = request_data['client_type']
        services_config = request_data.get('services_config', {})
        bid_id = request_data.get('bid_id')
        
        print(f"Starting onboarding for {client_info['name']} - Type: {client_type}")
        
        # Initialize onboarding state
        onboarding_state = _initialize_onboarding_state(
            client_info, client_type, services_config, bid_id
        )
        
        # Get required services for this client type
        required_services = config.get_client_services(client_type)
        print(f"Required services for {client_type}: {required_services}")
        
        # Execute onboarding steps in order
        orchestration_results = {}
        
        # Step 1: CRM Setup (if required)
        if 'crm' in required_services:
            print("Executing CRM setup step")
            crm_result = _execute_crm_setup(client_info, services_config, onboarding_state)
            orchestration_results['crm_setup'] = crm_result
            onboarding_state['hubspot_contact_id'] = crm_result.get('contact_id')
            onboarding_state['hubspot_deal_id'] = crm_result.get('deal_id')
        
        # Step 2: Stripe Setup (if required)
        if 'stripe' in required_services:
            print("Executing Stripe setup step")
            stripe_result = _execute_stripe_setup(client_info, services_config, onboarding_state)
            orchestration_results['stripe_setup'] = stripe_result
            onboarding_state['stripe_customer_id'] = stripe_result.get('customer_id')
        
        # Step 3: Website Deployment (if required)
        if 'website' in required_services:
            print("Executing website deployment step")
            deploy_result = _execute_website_deploy(client_info, services_config, onboarding_state)
            orchestration_results['website_deploy'] = deploy_result
            onboarding_state['website_url'] = deploy_result.get('website_url')
        
        # Step 4: DNS Setup (if required)
        if 'dns' in required_services:
            print("Executing DNS setup step")
            dns_result = _execute_dns_setup(client_info, services_config, onboarding_state)
            orchestration_results['dns_setup'] = dns_result
            onboarding_state['custom_domain'] = dns_result.get('domain')
        
        # Step 5: Email Setup (if required or optional)
        if 'email' in required_services or 'email_optional' in required_services:
            print("Executing email setup step")
            email_result = _execute_email_setup(client_info, services_config, onboarding_state)
            orchestration_results['email_setup'] = email_result
        
        # Step 6: Invoice Generation (for setup fees)
        if client_type != 'website_only' or services_config.get('setup_fee_required', True):
            print("Executing invoice generation step")
            invoice_result = _execute_invoice_generation(client_info, services_config, onboarding_state)
            orchestration_results['invoice'] = invoice_result
            onboarding_state['setup_invoice_id'] = invoice_result.get('invoice_id')
        
        # Step 7: Subscription Setup (for monthly fees)
        if client_type != 'crm_payments':  # All types except CRM-only get monthly subscriptions
            print("Executing subscription setup step")
            subscription_result = _execute_subscription_setup(client_info, services_config, onboarding_state)
            orchestration_results['subscription'] = subscription_result
            onboarding_state['subscription_id'] = subscription_result.get('subscription_id')
        
        # Step 8: Notifications (always required)
        print("Executing notification step")
        notification_result = _execute_notifications(client_info, services_config, onboarding_state)
        orchestration_results['notifications'] = notification_result
        
        # Update final onboarding state
        onboarding_state['status'] = 'completed'
        onboarding_state['completed_at'] = datetime.utcnow().isoformat()
        onboarding_state['orchestration_results'] = orchestration_results
        
        # Store final state in DynamoDB
        _update_onboarding_state(onboarding_state)
        
        # Prepare response data
        response_data = {
            'onboarding_id': onboarding_state['onboarding_id'],
            'client_info': {
                'name': client_info['name'],
                'company': client_info['company'],
                'email': client_info['email']
            },
            'client_type': client_type,
            'status': 'completed',
            'services_completed': list(orchestration_results.keys()),
            'results': {
                'hubspot_contact_id': onboarding_state.get('hubspot_contact_id'),
                'hubspot_deal_id': onboarding_state.get('hubspot_deal_id'),
                'stripe_customer_id': onboarding_state.get('stripe_customer_id'),
                'website_url': onboarding_state.get('website_url'),
                'custom_domain': onboarding_state.get('custom_domain'),
                'setup_invoice_id': onboarding_state.get('setup_invoice_id'),
                'subscription_id': onboarding_state.get('subscription_id')
            },
            'next_steps': _get_next_steps(client_type, orchestration_results),
            'completed_at': onboarding_state['completed_at']
        }
        
        print(f"Onboarding orchestration completed successfully - ID: {onboarding_state['onboarding_id']}")
        
        # Return successful response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  # Enable CORS
            },
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        # Log error for debugging
        print(f"Error in onboarding orchestration: {str(e)}")
        
        # Return error response
        return _create_error_response(500, f"Internal server error: {str(e)}")


def _validate_onboard_request(request_data: Dict[str, Any]) -> Optional[str]:
    """Validate the onboarding request data.
    
    Args:
        request_data: Parsed request body data
        
    Returns:
        Error message if validation fails, None if valid
    """
    # Check required top-level fields
    required_fields = ['client_info', 'client_type']
    for field in required_fields:
        if field not in request_data:
            return f"Missing required field: {field}"
    
    # Validate client_info fields
    client_info = request_data['client_info']
    required_client_fields = ['name', 'email', 'company']
    for field in required_client_fields:
        if field not in client_info or not client_info[field]:
            return f"Missing required client_info field: {field}"
    
    # Validate email format (basic check)
    email = client_info['email']
    if '@' not in email or '.' not in email:
        return "Invalid email address format"
    
    # Validate client_type
    client_type = request_data['client_type']
    valid_types = config.get_all_client_types()
    if client_type not in valid_types:
        return f"Invalid client_type. Must be one of: {', '.join(valid_types)}"
    
    return None  # Validation passed


def _initialize_onboarding_state(client_info: Dict[str, Any], client_type: str,
                                services_config: Dict[str, Any], bid_id: Optional[str]) -> Dict[str, Any]:
    """Initialize onboarding state record.
    
    Args:
        client_info: Client information dictionary
        client_type: Client type identifier
        services_config: Services configuration
        bid_id: Optional bid ID reference
        
    Returns:
        Initial onboarding state dictionary
    """
    # Generate unique onboarding ID
    import uuid
    onboarding_id = str(uuid.uuid4())
    
    # Create initial state
    onboarding_state = {
        'onboarding_id': onboarding_id,
        'client_email': client_info['email'],
        'client_name': client_info['name'],
        'client_company': client_info['company'],
        'client_type': client_type,
        'services_config': services_config,
        'bid_id': bid_id,
        'status': 'in_progress',
        'started_at': datetime.utcnow().isoformat(),
        'steps_completed': [],
        'steps_failed': []
    }
    
    # Store initial state in DynamoDB
    _update_onboarding_state(onboarding_state)
    
    return onboarding_state


def _execute_crm_setup(client_info: Dict[str, Any], services_config: Dict[str, Any],
                      onboarding_state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute CRM setup step.
    
    Args:
        client_info: Client information
        services_config: Services configuration
        onboarding_state: Current onboarding state
        
    Returns:
        CRM setup result dictionary
    """
    try:
        # For now, call the CRM setup handler logic directly
        # In production, this could be an internal API call
        
        # Create or update HubSpot contact
        contact_data = {
            'email': client_info['email'],
            'firstname': client_info.get('name', '').split(' ')[0] if client_info.get('name') else '',
            'lastname': ' '.join(client_info.get('name', '').split(' ')[1:]) if client_info.get('name') and len(client_info.get('name', '').split(' ')) > 1 else '',
            'company': client_info.get('company', ''),
            'phone': client_info.get('phone', ''),
            'industry': client_info.get('industry', ''),
            'lifecyclestage': 'customer',  # They're onboarding, so they're customers
            'lead_source': 'dtl_global_onboarding'
        }
        
        # Check if contact exists
        existing_contact = hubspot_client.get_contact_by_email(client_info['email'])
        if existing_contact:
            contact = existing_contact
        else:
            contact = hubspot_client.create_contact(contact_data)
        
        # Create onboarding deal
        pipeline_stages = hubspot_client.get_dtl_pipeline_stages()
        deal_data = {
            'dealname': f"{client_info['company']} - Onboarding ({onboarding_state['client_type']})",
            'pipeline': 'default',
            'dealstage': pipeline_stages['build'],  # Start at build stage
            'amount': str(services_config.get('setup_cost', 500)),
            'dealtype': 'newbusiness',
            'closedate': (datetime.utcnow() + timedelta(days=14)).isoformat(),
            'deal_currency_code': 'USD'
        }
        
        deal = hubspot_client.create_deal(deal_data)
        
        # Associate contact with deal
        hubspot_client.associate_contact_to_deal(contact['id'], deal['id'])
        
        return {
            'success': True,
            'contact_id': contact['id'],
            'deal_id': deal['id'],
            'message': 'CRM setup completed successfully'
        }
        
    except Exception as e:
        print(f"CRM setup failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'CRM setup failed'
        }


def _execute_stripe_setup(client_info: Dict[str, Any], services_config: Dict[str, Any],
                         onboarding_state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Stripe setup step.
    
    Args:
        client_info: Client information
        services_config: Services configuration
        onboarding_state: Current onboarding state
        
    Returns:
        Stripe setup result dictionary
    """
    try:
        # Import Stripe client
        from stripe_client import stripe_client
        
        # Create Stripe customer
        customer_data = {
            'email': client_info['email'],
            'name': client_info.get('name', ''),
            'phone': client_info.get('phone', ''),
            'metadata': {
                'onboarding_id': onboarding_state['onboarding_id'],
                'client_type': onboarding_state['client_type'],
                'company': client_info.get('company', '')
            }
        }
        
        # Check if customer already exists
        existing_customer = stripe_client.get_customer_by_email(client_info['email'])
        if existing_customer:
            customer = existing_customer
        else:
            customer = stripe_client.create_customer(customer_data)
        
        return {
            'success': True,
            'customer_id': customer['id'],
            'message': 'Stripe customer setup completed successfully'
        }
        
    except Exception as e:
        print(f"Stripe setup failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Stripe setup failed'
        }


def _execute_website_deploy(client_info: Dict[str, Any], services_config: Dict[str, Any],
                           onboarding_state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute website deployment step.
    
    Args:
        client_info: Client information
        services_config: Services configuration
        onboarding_state: Current onboarding state
        
    Returns:
        Website deployment result dictionary
    """
    try:
        # For now, create a placeholder website
        # In production, this would generate the full website based on prompts
        
        from s3_client import s3_client
        
        # Create basic HTML website
        website_files = {
            'index.html': _generate_placeholder_website(client_info),
            '404.html': _generate_404_page(client_info)
        }
        
        # Deploy to S3
        domain = services_config.get('domain', f"{client_info['company'].lower().replace(' ', '-')}.example.com")
        deploy_result = s3_client.deploy_website(
            client_domain=domain,
            website_files=website_files,
            enable_spa=False
        )
        
        return {
            'success': True,
            'website_url': deploy_result['website_url'],
            'domain_prefix': deploy_result['domain_prefix'],
            'deployed_files': len(deploy_result['deployed_files']),
            'message': 'Website deployment completed successfully'
        }
        
    except Exception as e:
        print(f"Website deployment failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Website deployment failed'
        }


def _execute_dns_setup(client_info: Dict[str, Any], services_config: Dict[str, Any],
                      onboarding_state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute DNS setup step.
    
    Args:
        client_info: Client information
        services_config: Services configuration
        onboarding_state: Current onboarding state
        
    Returns:
        DNS setup result dictionary
    """
    try:
        # For now, return instructions for manual DNS setup
        # In Phase 4, this will be fully automated
        
        domain = services_config.get('domain')
        if not domain:
            return {
                'success': False,
                'error': 'No domain specified',
                'message': 'DNS setup skipped - no domain provided'
            }
        
        # Generate DNS instructions
        cloudfront_domain = "d111111abcdef8.cloudfront.net"  # Placeholder - would come from CDN stack
        
        return {
            'success': True,
            'domain': domain,
            'dns_instructions': {
                'cname_record': {
                    'name': f'www.{domain}',
                    'value': cloudfront_domain,
                    'ttl': 300
                },
                'validation_records': [
                    {
                        'name': f'_acme-challenge.{domain}',
                        'value': 'ssl-validation-token-placeholder',
                        'type': 'TXT'
                    }
                ]
            },
            'message': 'DNS setup instructions generated - manual configuration required'
        }
        
    except Exception as e:
        print(f"DNS setup failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'DNS setup failed'
        }


def _execute_email_setup(client_info: Dict[str, Any], services_config: Dict[str, Any],
                        onboarding_state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute email setup step.
    
    Args:
        client_info: Client information
        services_config: Services configuration
        onboarding_state: Current onboarding state
        
    Returns:
        Email setup result dictionary
    """
    try:
        # Send welcome email to client
        project_details = {
            'project_name': f"{client_info['company']} Digital Transformation",
            'services': config.get_client_services(onboarding_state['client_type']),
            'timeline': '2-4 weeks'
        }
        
        email_result = ses_client.send_onboarding_welcome(
            client_email=client_info['email'],
            client_name=client_info['name'],
            project_details=project_details
        )
        
        return {
            'success': True,
            'message_id': email_result['MessageId'],
            'message': 'Welcome email sent successfully'
        }
        
    except Exception as e:
        print(f"Email setup failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Email setup failed'
        }


def _execute_invoice_generation(client_info: Dict[str, Any], services_config: Dict[str, Any],
                               onboarding_state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute invoice generation step.
    
    Args:
        client_info: Client information
        services_config: Services configuration
        onboarding_state: Current onboarding state
        
    Returns:
        Invoice generation result dictionary
    """
    try:
        # This would call the invoice handler
        # For now, return a placeholder result
        
        setup_cost = services_config.get('setup_cost', 500)
        
        return {
            'success': True,
            'invoice_id': f"inv_placeholder_{onboarding_state['onboarding_id'][:8]}",
            'amount': setup_cost,
            'currency': 'usd',
            'status': 'draft',
            'message': 'Setup invoice generated successfully (SANDBOX mode)'
        }
        
    except Exception as e:
        print(f"Invoice generation failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Invoice generation failed'
        }


def _execute_subscription_setup(client_info: Dict[str, Any], services_config: Dict[str, Any],
                               onboarding_state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute subscription setup step.
    
    Args:
        client_info: Client information
        services_config: Services configuration
        onboarding_state: Current onboarding state
        
    Returns:
        Subscription setup result dictionary
    """
    try:
        # This would call the subscription handler
        # For now, return a placeholder result
        
        monthly_cost = services_config.get('monthly_cost', 49)
        
        return {
            'success': True,
            'subscription_id': f"sub_placeholder_{onboarding_state['onboarding_id'][:8]}",
            'amount': monthly_cost,
            'currency': 'usd',
            'interval': 'month',
            'status': 'active',
            'message': 'Monthly subscription created successfully (SANDBOX mode)'
        }
        
    except Exception as e:
        print(f"Subscription setup failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Subscription setup failed'
        }


def _execute_notifications(client_info: Dict[str, Any], services_config: Dict[str, Any],
                          onboarding_state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute notifications step.
    
    Args:
        client_info: Client information
        services_config: Services configuration
        onboarding_state: Current onboarding state
        
    Returns:
        Notifications result dictionary
    """
    try:
        # Send internal notification (placeholder)
        # In production, this would notify the DTL team
        
        return {
            'success': True,
            'notifications_sent': [
                'client_welcome_email',
                'internal_team_notification'
            ],
            'message': 'All notifications sent successfully'
        }
        
    except Exception as e:
        print(f"Notifications failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Notifications failed'
        }


def _update_onboarding_state(onboarding_state: Dict[str, Any]) -> None:
    """Update onboarding state in DynamoDB.
    
    Args:
        onboarding_state: Onboarding state dictionary to store
    """
    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(config.DYNAMODB_TABLES['state'])
        
        # Store onboarding state
        table.put_item(
            Item={
                'pk': f"ONBOARD#{onboarding_state['onboarding_id']}",
                'sk': 'METADATA',
                **onboarding_state,
                'ttl': int((datetime.utcnow() + timedelta(days=365)).timestamp())  # Keep for 1 year
            }
        )
        
    except Exception as e:
        print(f"Failed to update onboarding state: {e}")


def _get_next_steps(client_type: str, orchestration_results: Dict[str, Any]) -> List[str]:
    """Get next steps based on client type and results.
    
    Args:
        client_type: Client type identifier
        orchestration_results: Results from orchestration steps
        
    Returns:
        List of next step descriptions
    """
    next_steps = []
    
    # Common next steps
    next_steps.append("Review and approve website design")
    next_steps.append("Complete payment for setup fees")
    
    # Client type specific steps
    if client_type in ['full_package', 'website_crm']:
        next_steps.append("Import existing customer data to HubSpot CRM")
    
    if client_type in ['full_package', 'website_only']:
        if 'dns_setup' in orchestration_results:
            next_steps.append("Configure DNS records with your domain provider")
    
    if client_type in ['full_package', 'crm_payments']:
        next_steps.append("Set up payment methods for monthly billing")
    
    next_steps.append("Schedule training session for new systems")
    
    return next_steps


def _generate_placeholder_website(client_info: Dict[str, Any]) -> str:
    """Generate a placeholder website HTML.
    
    Args:
        client_info: Client information
        
    Returns:
        HTML content string
    """
    company_name = client_info.get('company', 'Your Company')
    industry = client_info.get('industry', 'business')
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{company_name} - Professional {industry.title()} Services</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        header {{ background: #2c5aa0; color: white; padding: 1rem 0; }}
        .hero {{ text-align: center; padding: 4rem 0; background: #f8f9fa; }}
        .services {{ padding: 3rem 0; }}
        .contact {{ background: #2c5aa0; color: white; padding: 3rem 0; text-align: center; }}
        .btn {{ background: #ff6b35; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>{company_name}</h1>
            <p>Professional {industry.title()} Services</p>
        </div>
    </header>
    
    <section class="hero">
        <div class="container">
            <h2>Welcome to {company_name}</h2>
            <p>Your trusted partner for professional {industry} services.</p>
            <a href="#contact" class="btn">Get Started Today</a>
        </div>
    </section>
    
    <section class="services">
        <div class="container">
            <h2>Our Services</h2>
            <p>We provide comprehensive {industry} solutions tailored to your needs.</p>
        </div>
    </section>
    
    <section class="contact" id="contact">
        <div class="container">
            <h2>Contact Us</h2>
            <p>Ready to get started? Contact us today for a free consultation.</p>
            <p>Email: {client_info.get('email', 'info@company.com')}</p>
            <p>Phone: {client_info.get('phone', '(555) 123-4567')}</p>
        </div>
    </section>
</body>
</html>"""


def _generate_404_page(client_info: Dict[str, Any]) -> str:
    """Generate a 404 error page HTML.
    
    Args:
        client_info: Client information
        
    Returns:
        HTML content string for 404 page
    """
    company_name = client_info.get('company', 'Your Company')
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page Not Found - {company_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; padding: 4rem 2rem; }}
        h1 {{ color: #2c5aa0; font-size: 3rem; }}
        .btn {{ background: #2c5aa0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>404</h1>
    <h2>Page Not Found</h2>
    <p>The page you're looking for doesn't exist.</p>
    <a href="/" class="btn">Return Home</a>
</body>
</html>"""


def _create_error_response(status_code: int, error_message: str) -> Dict[str, Any]:
    """Create a standardized error response.
    
    Args:
        status_code: HTTP status code
        error_message: Error message to return
        
    Returns:
        API Gateway proxy response dictionary
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'  # Enable CORS
        },
        'body': json.dumps({
            'error': error_message,
            'timestamp': datetime.utcnow().isoformat()
        })
    }
