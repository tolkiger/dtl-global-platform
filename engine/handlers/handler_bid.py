"""POST /bid Lambda handler for DTL-Global onboarding platform.

This handler generates project bids using AI-powered analysis of client requirements.
Integrates with HubSpot CRM to create deals and track the bidding process.

Endpoint: POST /bid
Purpose: Generate detailed project bids with pricing and timeline
Dependencies: AI client (Claude), HubSpot client, DynamoDB

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
from ai_client import ai_client
from hubspot_client import hubspot_client


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Generate a project bid based on client requirements.
    
    This function processes client requirements and generates a comprehensive
    project bid using AI analysis, then creates a deal in HubSpot CRM.
    
    Args:
        event: API Gateway proxy request event containing client requirements
        context: Lambda runtime context object
        
    Returns:
        API Gateway proxy response with bid details and HubSpot deal ID
        
    Expected Request Body:
        {
            "client_info": {
                "name": "Client Name",
                "email": "client@example.com", 
                "company": "Company Name",
                "phone": "555-1234",
                "industry": "roofing"
            },
            "requirements": {
                "services": ["website", "crm", "stripe"],
                "timeline": "4 weeks",
                "budget_range": "$1000-5000",
                "description": "Need new website and CRM setup"
            },
            "client_type": "growth"  // Optional: full_package, website_only, website_crm, crm_payments
        }
    """
    print(f"Bid generation started - Request ID: {context.aws_request_id}")
    
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
        validation_error = _validate_bid_request(request_data)
        if validation_error:
            return _create_error_response(400, validation_error)
        
        # Extract client and requirement data
        client_info = request_data['client_info']
        requirements = request_data['requirements']
        client_type = request_data.get('client_type', 'growth')  # Default to growth package
        
        print(f"Processing bid for {client_info['name']} - Industry: {client_info['industry']}")
        
        # Generate AI-powered bid
        print("Calling AI client for bid generation")
        bid_data = ai_client.generate_bid(
            client_requirements=requirements,
            industry=client_info['industry']
        )
        
        # Add client information to bid
        bid_data['client_info'] = client_info
        bid_data['client_type'] = client_type
        bid_data['generated_at'] = datetime.utcnow().isoformat()
        
        print(f"AI bid generated - Setup: ${bid_data['setup_cost']}, Monthly: ${bid_data['monthly_cost']}")
        
        # Create or update contact in HubSpot
        print("Creating/updating HubSpot contact")
        hubspot_contact = _create_hubspot_contact(client_info)
        
        # Create deal in HubSpot
        print("Creating HubSpot deal")
        hubspot_deal = _create_hubspot_deal(client_info, bid_data, hubspot_contact['id'])
        
        # Store bid data in DynamoDB
        print("Storing bid data in DynamoDB")
        bid_record = _store_bid_data(bid_data, hubspot_contact['id'], hubspot_deal['id'])
        
        # Prepare response data
        response_data = {
            'bid_id': bid_record['bid_id'],
            'client_info': {
                'name': client_info['name'],
                'company': client_info['company'],
                'industry': client_info['industry']
            },
            'pricing': {
                'setup_cost': bid_data['setup_cost'],
                'monthly_cost': bid_data['monthly_cost'],
                'deposit_amount': bid_data['deposit_amount'],
                'estimated_hours': bid_data['estimated_hours']
            },
            'timeline': {
                'estimated_weeks': bid_data['timeline_weeks'],
                'start_date': (datetime.utcnow() + timedelta(days=3)).isoformat()[:10]  # Start in 3 days
            },
            'services_included': bid_data['services_included'],
            'deliverables': bid_data['deliverables'],
            'hubspot': {
                'contact_id': hubspot_contact['id'],
                'deal_id': hubspot_deal['id']
            },
            'next_steps': bid_data['next_steps'],
            'assumptions': bid_data['assumptions'],
            'risks': bid_data['risks']
        }
        
        print(f"Bid generation completed successfully - Bid ID: {bid_record['bid_id']}")
        
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
        print(f"Error in bid generation: {str(e)}")
        
        # Return error response
        return _create_error_response(500, f"Internal server error: {str(e)}")


def _validate_bid_request(request_data: Dict[str, Any]) -> Optional[str]:
    """Validate the bid request data.
    
    Args:
        request_data: Parsed request body data
        
    Returns:
        Error message if validation fails, None if valid
    """
    # Check required top-level fields
    required_fields = ['client_info', 'requirements']
    for field in required_fields:
        if field not in request_data:
            return f"Missing required field: {field}"
    
    # Validate client_info fields
    client_info = request_data['client_info']
    required_client_fields = ['name', 'email', 'industry']
    for field in required_client_fields:
        if field not in client_info or not client_info[field]:
            return f"Missing required client_info field: {field}"
    
    # Validate email format (basic check)
    email = client_info['email']
    if '@' not in email or '.' not in email:
        return "Invalid email address format"
    
    # Validate requirements fields
    requirements = request_data['requirements']
    required_req_fields = ['services']
    for field in required_req_fields:
        if field not in requirements:
            return f"Missing required requirements field: {field}"
    
    # Validate services list
    services = requirements['services']
    if not isinstance(services, list) or len(services) == 0:
        return "Services must be a non-empty list"
    
    # Validate client_type if provided
    if 'client_type' in request_data:
        valid_types = config.get_all_client_types()
        if request_data['client_type'] not in valid_types:
            return f"Invalid client_type. Must be one of: {', '.join(valid_types)}"
    
    return None  # Validation passed


def _create_hubspot_contact(client_info: Dict[str, Any]) -> Dict[str, Any]:
    """Create or update a contact in HubSpot.
    
    Args:
        client_info: Client information dictionary
        
    Returns:
        HubSpot contact data dictionary
    """
    # Check if contact already exists
    existing_contact = hubspot_client.get_contact_by_email(client_info['email'])
    
    if existing_contact:
        print(f"Found existing HubSpot contact: {existing_contact['id']}")
        return existing_contact
    
    # Prepare contact data for creation
    contact_data = {
        'email': client_info['email'],
        'firstname': client_info.get('name', '').split(' ')[0] if client_info.get('name') else '',
        'lastname': ' '.join(client_info.get('name', '').split(' ')[1:]) if client_info.get('name') and len(client_info.get('name', '').split(' ')) > 1 else '',
        'company': client_info.get('company', ''),
        'phone': client_info.get('phone', ''),
        'industry': client_info.get('industry', ''),
        'lifecyclestage': 'lead',  # New lead stage
        'lead_source': 'dtl_global_website'  # Track source
    }
    
    # Create new contact
    new_contact = hubspot_client.create_contact(contact_data)
    print(f"Created new HubSpot contact: {new_contact['id']}")
    
    return new_contact


def _create_hubspot_deal(client_info: Dict[str, Any], bid_data: Dict[str, Any], 
                        contact_id: str) -> Dict[str, Any]:
    """Create a deal in HubSpot for the bid.
    
    Args:
        client_info: Client information dictionary
        bid_data: Generated bid data
        contact_id: HubSpot contact ID
        
    Returns:
        HubSpot deal data dictionary
    """
    # Get DTL pipeline stages
    pipeline_stages = hubspot_client.get_dtl_pipeline_stages()
    
    # Prepare deal data
    deal_name = f"{client_info['company']} - {client_info['industry'].title()} Project"
    deal_data = {
        'dealname': deal_name,
        'pipeline': 'default',  # Use default pipeline
        'dealstage': pipeline_stages['proposal'],  # Start at proposal stage
        'amount': str(bid_data['setup_cost']),  # Setup cost as deal amount
        'dealtype': 'newbusiness',
        'hubspot_owner_id': '',  # Will be assigned later
        'closedate': (datetime.utcnow() + timedelta(days=30)).isoformat(),  # 30 days to close
        'deal_currency_code': 'USD'
    }
    
    # Create deal
    new_deal = hubspot_client.create_deal(deal_data)
    print(f"Created HubSpot deal: {new_deal['id']} - {deal_name}")
    
    # Associate contact with deal
    hubspot_client.associate_contact_to_deal(contact_id, new_deal['id'])
    print(f"Associated contact {contact_id} with deal {new_deal['id']}")
    
    return new_deal


def _store_bid_data(bid_data: Dict[str, Any], contact_id: str, deal_id: str) -> Dict[str, Any]:
    """Store bid data in DynamoDB.
    
    Args:
        bid_data: Generated bid data
        contact_id: HubSpot contact ID
        deal_id: HubSpot deal ID
        
    Returns:
        Stored bid record with generated ID
    """
    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(config.DYNAMODB_TABLES['state'])  # Use onboarding state table
    
    # Generate unique bid ID
    import uuid
    bid_id = str(uuid.uuid4())
    
    # Prepare bid record
    bid_record = {
        'pk': f'BID#{bid_id}',
        'sk': 'METADATA',
        'bid_id': bid_id,
        'client_email': bid_data['client_info']['email'],
        'client_name': bid_data['client_info']['name'],
        'client_company': bid_data['client_info'].get('company', ''),
        'industry': bid_data['client_info']['industry'],
        'client_type': bid_data['client_type'],
        'setup_cost': bid_data['setup_cost'],
        'monthly_cost': bid_data['monthly_cost'],
        'deposit_amount': bid_data['deposit_amount'],
        'estimated_hours': bid_data['estimated_hours'],
        'timeline_weeks': bid_data['timeline_weeks'],
        'services_included': bid_data['services_included'],
        'deliverables': bid_data['deliverables'],
        'assumptions': bid_data['assumptions'],
        'risks': bid_data['risks'],
        'next_steps': bid_data['next_steps'],
        'hubspot_contact_id': contact_id,
        'hubspot_deal_id': deal_id,
        'status': 'generated',
        'created_at': datetime.utcnow().isoformat(),
        'ttl': int((datetime.utcnow() + timedelta(days=90)).timestamp())  # Expire after 90 days
    }
    
    # Store in DynamoDB
    table.put_item(Item=bid_record)
    print(f"Stored bid data in DynamoDB: {bid_id}")
    
    return bid_record


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
