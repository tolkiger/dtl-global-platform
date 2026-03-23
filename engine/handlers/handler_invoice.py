"""POST /invoice Lambda handler for DTL-Global onboarding platform.

This handler generates and sends invoices using Stripe (SANDBOX mode).
Handles setup fees, deposits, and one-time charges for client onboarding.

Endpoint: POST /invoice
Purpose: Generate Stripe invoices for client setup fees and deposits
Dependencies: Stripe client (SANDBOX), SES client for notifications

Author: DTL-Global Platform
"""

import json
import boto3
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta

# Import shared modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import config
from stripe_client import stripe_client
from ses_client import ses_client


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Generate and send a Stripe invoice.
    
    This function creates invoices for setup fees, deposits, or one-time charges
    using Stripe's invoicing system in SANDBOX mode.
    
    Args:
        event: API Gateway proxy request event containing invoice data
        context: Lambda runtime context object
        
    Returns:
        API Gateway proxy response with invoice details and payment link
        
    Expected Request Body:
        {
            "customer_info": {
                "email": "client@example.com",
                "name": "Client Name",
                "company": "Company Name"
            },
            "invoice_items": [
                {
                    "description": "DTL Growth Setup",
                    "amount": 125000,  // Amount in cents
                    "quantity": 1
                }
            ],
            "invoice_config": {
                "due_days": 30,  // Payment terms in days
                "auto_advance": true,  // Automatically finalize
                "send_email": true,  // Send via email
                "currency": "usd"
            },
            "metadata": {
                "onboarding_id": "uuid",
                "client_type": "growth",
                "project_name": "Company Website"
            }
        }
    """
    print(f"Invoice generation started - Request ID: {context.aws_request_id}")
    
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
        validation_error = _validate_invoice_request(request_data)
        if validation_error:
            return _create_error_response(400, validation_error)
        
        # Extract invoice data
        customer_info = request_data['customer_info']
        invoice_items = request_data['invoice_items']
        invoice_config = request_data.get('invoice_config', {})
        metadata = request_data.get('metadata', {})
        
        print(f"Generating invoice for {customer_info['email']} - Items: {len(invoice_items)}")
        
        # Create or get Stripe customer
        stripe_customer = _get_or_create_stripe_customer(customer_info, metadata)
        
        # Calculate total amount
        total_amount = sum(item['amount'] * item.get('quantity', 1) for item in invoice_items)
        
        print(f"Invoice total: ${total_amount / 100:.2f} USD")
        
        # Create Stripe invoice
        stripe_invoice = _create_stripe_invoice(
            stripe_customer['id'], 
            invoice_items, 
            invoice_config, 
            metadata
        )
        
        # Send email notification if requested
        if invoice_config.get('send_email', True):
            print("Sending invoice notification email")
            email_result = _send_invoice_notification(
                customer_info, 
                stripe_invoice, 
                metadata
            )
        else:
            email_result = {'success': True, 'message': 'Email notification skipped'}
        
        # Store invoice data for tracking
        invoice_record = _store_invoice_data(
            stripe_invoice, 
            customer_info, 
            metadata
        )
        
        # Prepare response data
        response_data = {
            'invoice_id': stripe_invoice['id'],
            'invoice_number': stripe_invoice['number'],
            'customer_id': stripe_customer['id'],
            'amount_due': stripe_invoice['amount_due'],
            'currency': stripe_invoice['currency'],
            'status': stripe_invoice['status'],
            'payment_link': stripe_invoice['hosted_invoice_url'],
            'pdf_link': stripe_invoice['invoice_pdf'],
            'due_date': _format_due_date(stripe_invoice.get('due_date')),
            'email_sent': email_result['success'],
            'created_at': datetime.utcfromtimestamp(stripe_invoice['created']).isoformat(),
            'metadata': metadata
        }
        
        print(f"Invoice generation completed successfully - ID: {stripe_invoice['id']}")
        
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
        print(f"Error in invoice generation: {str(e)}")
        
        # Return error response
        return _create_error_response(500, f"Internal server error: {str(e)}")


def _validate_invoice_request(request_data: Dict[str, Any]) -> Optional[str]:
    """Validate the invoice request data.
    
    Args:
        request_data: Parsed request body data
        
    Returns:
        Error message if validation fails, None if valid
    """
    # Check required top-level fields
    required_fields = ['customer_info', 'invoice_items']
    for field in required_fields:
        if field not in request_data:
            return f"Missing required field: {field}"
    
    # Validate customer_info fields
    customer_info = request_data['customer_info']
    required_customer_fields = ['email', 'name']
    for field in required_customer_fields:
        if field not in customer_info or not customer_info[field]:
            return f"Missing required customer_info field: {field}"
    
    # Validate email format (basic check)
    email = customer_info['email']
    if '@' not in email or '.' not in email:
        return "Invalid email address format"
    
    # Validate invoice_items
    invoice_items = request_data['invoice_items']
    if not isinstance(invoice_items, list) or len(invoice_items) == 0:
        return "invoice_items must be a non-empty list"
    
    # Validate each invoice item
    for i, item in enumerate(invoice_items):
        if 'description' not in item or not item['description']:
            return f"Invoice item {i} missing description"
        if 'amount' not in item or not isinstance(item['amount'], int) or item['amount'] <= 0:
            return f"Invoice item {i} missing or invalid amount (must be positive integer in cents)"
    
    return None  # Validation passed


def _get_or_create_stripe_customer(customer_info: Dict[str, Any], 
                                  metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Get existing Stripe customer or create a new one.
    
    Args:
        customer_info: Customer information dictionary
        metadata: Additional metadata for the customer
        
    Returns:
        Stripe customer data dictionary
    """
    # Check if customer already exists
    existing_customer = stripe_client.get_customer_by_email(customer_info['email'])
    
    if existing_customer:
        print(f"Found existing Stripe customer: {existing_customer['id']}")
        return existing_customer
    
    # Create new Stripe customer
    customer_data = {
        'email': customer_info['email'],
        'name': customer_info['name'],
        'metadata': {
            'company': customer_info.get('company', ''),
            'created_via': 'dtl_global_invoice_handler',
            **metadata
        }
    }
    
    new_customer = stripe_client.create_customer(customer_data)
    print(f"Created new Stripe customer: {new_customer['id']}")
    
    return new_customer


def _create_stripe_invoice(customer_id: str, invoice_items: List[Dict[str, Any]],
                          invoice_config: Dict[str, Any], 
                          metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Create a Stripe invoice with line items.
    
    Args:
        customer_id: Stripe customer ID
        invoice_items: List of invoice line items
        invoice_config: Invoice configuration options
        metadata: Invoice metadata
        
    Returns:
        Created Stripe invoice data
    """
    # Get DTL service products for pricing
    dtl_products = stripe_client.get_dtl_products()
    
    # Prepare line items for Stripe
    line_items = []
    
    for item in invoice_items:
        # Try to match with DTL products or create custom item
        price_id = _get_or_create_price_for_item(item, dtl_products)
        
        line_items.append({
            'price_id': price_id,
            'quantity': item.get('quantity', 1)
        })
    
    # Create invoice with configuration
    invoice_data = stripe_client.create_invoice(
        customer_id=customer_id,
        line_items=line_items,
        metadata={
            'invoice_type': 'setup_fee',
            'generated_by': 'dtl_global_platform',
            **metadata
        }
    )
    
    return invoice_data


def _get_or_create_price_for_item(item: Dict[str, Any], 
                                 dtl_products: Dict[str, Any]) -> str:
    """Get or create a Stripe price for an invoice item.
    
    Args:
        item: Invoice item dictionary
        dtl_products: DTL service products mapping
        
    Returns:
        Stripe price ID
    """
    # For now, create a custom price for each item
    # In production, this would match against existing DTL products
    
    # This is a placeholder - in real implementation, you'd use Stripe's Price API
    # to create or retrieve prices for your products
    
    description = item['description']
    amount = item['amount']
    
    # Map common descriptions to DTL products
    if 'starter setup' in description.lower():
        return 'price_dtl_starter_setup'  # Would be actual Stripe price ID
    elif 'growth setup' in description.lower():
        return 'price_dtl_growth_setup'
    elif 'professional setup' in description.lower():
        return 'price_dtl_professional_setup'
    elif 'premium setup' in description.lower():
        return 'price_dtl_premium_setup'
    else:
        # Create custom price (placeholder ID)
        return f'price_custom_{abs(hash(description + str(amount))) % 10000}'


def _send_invoice_notification(customer_info: Dict[str, Any], 
                              stripe_invoice: Dict[str, Any],
                              metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Send invoice notification email to customer.
    
    Args:
        customer_info: Customer information
        stripe_invoice: Stripe invoice data
        metadata: Invoice metadata
        
    Returns:
        Email sending result dictionary
    """
    try:
        # Prepare invoice data for email
        invoice_data = {
            'number': stripe_invoice['number'],
            'amount_due': stripe_invoice['amount_due'],
            'currency': stripe_invoice['currency'],
            'hosted_invoice_url': stripe_invoice['hosted_invoice_url'],
            'due_date': _format_due_date(stripe_invoice.get('due_date'))
        }
        
        # Send invoice notification email
        email_result = ses_client.send_invoice_notification(
            client_email=customer_info['email'],
            client_name=customer_info['name'],
            invoice_data=invoice_data
        )
        
        return {
            'success': True,
            'message_id': email_result['MessageId'],
            'message': 'Invoice notification email sent successfully'
        }
        
    except Exception as e:
        print(f"Failed to send invoice notification: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to send invoice notification email'
        }


def _store_invoice_data(stripe_invoice: Dict[str, Any], 
                       customer_info: Dict[str, Any],
                       metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Store invoice data in DynamoDB for tracking.
    
    Args:
        stripe_invoice: Stripe invoice data
        customer_info: Customer information
        metadata: Invoice metadata
        
    Returns:
        Stored invoice record
    """
    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(config.DYNAMODB_TABLES['state'])
        
        # Prepare invoice record
        invoice_record = {
            'pk': f"INVOICE#{stripe_invoice['id']}",
            'sk': 'METADATA',
            'invoice_id': stripe_invoice['id'],
            'invoice_number': stripe_invoice['number'],
            'customer_email': customer_info['email'],
            'customer_name': customer_info['name'],
            'customer_company': customer_info.get('company', ''),
            'amount_due': stripe_invoice['amount_due'],
            'currency': stripe_invoice['currency'],
            'status': stripe_invoice['status'],
            'hosted_invoice_url': stripe_invoice['hosted_invoice_url'],
            'invoice_pdf': stripe_invoice['invoice_pdf'],
            'due_date': stripe_invoice.get('due_date'),
            'created_at': datetime.utcfromtimestamp(stripe_invoice['created']).isoformat(),
            'metadata': metadata,
            'ttl': int((datetime.utcnow() + timedelta(days=365)).timestamp())  # Keep for 1 year
        }
        
        # Store in DynamoDB
        table.put_item(Item=invoice_record)
        print(f"Stored invoice data in DynamoDB: {stripe_invoice['id']}")
        
        return invoice_record
        
    except Exception as e:
        print(f"Failed to store invoice data: {e}")
        return {}


def _format_due_date(due_date_timestamp: Optional[int]) -> Optional[str]:
    """Format due date timestamp to ISO string.
    
    Args:
        due_date_timestamp: Unix timestamp or None
        
    Returns:
        ISO formatted date string or None
    """
    if due_date_timestamp:
        return datetime.utcfromtimestamp(due_date_timestamp).isoformat()
    return None


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
