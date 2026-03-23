"""POST /subscribe Lambda handler for DTL-Global onboarding platform.

This handler manages Stripe subscriptions for monthly recurring services (SANDBOX mode).
Handles subscription creation, updates, cancellations, and payment method management.

Endpoint: POST /subscribe
Purpose: Manage Stripe subscriptions for DTL monthly service packages
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
# Add both the engine root and shared directory to path
engine_root = os.path.dirname(os.path.dirname(__file__))
shared_path = os.path.join(engine_root, 'shared')
if engine_root not in sys.path:
    sys.path.insert(0, engine_root)
if shared_path not in sys.path:
    sys.path.insert(0, shared_path)

# Import shared modules directly
from config import config
from stripe_client import stripe_client
from ses_client import ses_client


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Manage Stripe subscriptions for monthly services.
    
    This function handles subscription operations including creation, updates,
    cancellation, and payment method management in Stripe SANDBOX mode.
    
    Args:
        event: API Gateway proxy request event containing subscription data
        context: Lambda runtime context object
        
    Returns:
        API Gateway proxy response with subscription details and status
        
    Expected Request Body:
        {
            "action": "create",  // create, update, cancel, get_status
            "customer_info": {
                "email": "client@example.com",
                "name": "Client Name",
                "company": "Company Name"
            },
            "subscription_config": {
                "service_package": "dtl_growth_monthly",  // DTL service package
                "payment_method_id": "pm_xxx",  // Optional for create
                "trial_days": 0,  // Optional trial period
                "prorate": true  // Prorate changes
            },
            "metadata": {
                "onboarding_id": "uuid",
                "client_type": "growth",
                "project_name": "Company Website"
            }
        }
    """
    print(f"Subscription management started - Request ID: {context.aws_request_id}")
    
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
        validation_error = _validate_subscription_request(request_data)
        if validation_error:
            return _create_error_response(400, validation_error)
        
        # Extract subscription data
        action = request_data['action']
        customer_info = request_data.get('customer_info', {})
        subscription_config = request_data.get('subscription_config', {})
        metadata = request_data.get('metadata', {})
        
        print(f"Processing subscription action: {action}")
        
        # Route to appropriate action handler
        if action == 'create':
            result = _handle_create_subscription(customer_info, subscription_config, metadata)
        elif action == 'update':
            result = _handle_update_subscription(subscription_config, metadata)
        elif action == 'cancel':
            result = _handle_cancel_subscription(subscription_config, metadata)
        elif action == 'get_status':
            result = _handle_get_subscription_status(subscription_config, metadata)
        else:
            return _create_error_response(400, f"Invalid action: {action}")
        
        print(f"Subscription {action} completed successfully")
        
        # Return successful response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  # Enable CORS
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        # Log error for debugging
        print(f"Error in subscription management: {str(e)}")
        
        # Return error response
        return _create_error_response(500, f"Internal server error: {str(e)}")


def _validate_subscription_request(request_data: Dict[str, Any]) -> Optional[str]:
    """Validate the subscription request data.
    
    Args:
        request_data: Parsed request body data
        
    Returns:
        Error message if validation fails, None if valid
    """
    # Check required action field
    if 'action' not in request_data:
        return "Missing required field: action"
    
    action = request_data['action']
    valid_actions = ['create', 'update', 'cancel', 'get_status']
    if action not in valid_actions:
        return f"Invalid action. Must be one of: {', '.join(valid_actions)}"
    
    # Validate customer_info for create action
    if action == 'create':
        if 'customer_info' not in request_data:
            return "customer_info is required for create action"
        
        customer_info = request_data['customer_info']
        required_fields = ['email', 'name']
        for field in required_fields:
            if field not in customer_info or not customer_info[field]:
                return f"Missing required customer_info field: {field}"
        
        # Validate email format
        email = customer_info['email']
        if '@' not in email or '.' not in email:
            return "Invalid email address format"
    
    # Validate subscription_config
    if 'subscription_config' not in request_data:
        return "subscription_config is required"
    
    subscription_config = request_data['subscription_config']
    
    # For create action, validate service package
    if action == 'create':
        if 'service_package' not in subscription_config:
            return "service_package is required for create action"
        
        # Validate against DTL service packages
        dtl_products = stripe_client.get_dtl_products()
        valid_packages = [key for key in dtl_products.keys() if 'monthly' in key]
        
        if subscription_config['service_package'] not in valid_packages:
            return f"Invalid service_package. Must be one of: {', '.join(valid_packages)}"
    
    # For update/cancel actions, validate subscription_id
    if action in ['update', 'cancel', 'get_status']:
        if 'subscription_id' not in subscription_config:
            return f"subscription_id is required for {action} action"
    
    return None  # Validation passed


def _handle_create_subscription(customer_info: Dict[str, Any], 
                               subscription_config: Dict[str, Any],
                               metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Handle subscription creation.
    
    Args:
        customer_info: Customer information
        subscription_config: Subscription configuration
        metadata: Additional metadata
        
    Returns:
        Subscription creation result dictionary
    """
    try:
        # Get or create Stripe customer
        stripe_customer = _get_or_create_stripe_customer(customer_info, metadata)
        
        # Get DTL service package details
        service_package = subscription_config['service_package']
        dtl_products = stripe_client.get_dtl_products()
        
        if service_package not in dtl_products:
            raise ValueError(f"Invalid service package: {service_package}")
        
        package_info = dtl_products[service_package]
        
        # Create subscription price (placeholder - would use actual Stripe Price IDs)
        price_id = _get_price_id_for_package(service_package, package_info)
        
        # Create subscription
        subscription_data = stripe_client.create_subscription(
            customer_id=stripe_customer['id'],
            price_id=price_id,
            metadata={
                'service_package': service_package,
                'created_via': 'dtl_global_platform',
                **metadata
            }
        )
        
        # Store subscription data
        subscription_record = _store_subscription_data(
            subscription_data, 
            customer_info, 
            service_package, 
            metadata
        )
        
        # Send confirmation email
        if customer_info.get('email'):
            _send_subscription_confirmation_email(
                customer_info, 
                subscription_data, 
                package_info
            )
        
        return {
            'success': True,
            'subscription_id': subscription_data['id'],
            'customer_id': stripe_customer['id'],
            'service_package': service_package,
            'amount': package_info['amount'],
            'currency': package_info['currency'],
            'interval': package_info['interval'],
            'status': subscription_data['status'],
            'current_period_start': subscription_data['current_period_start'],
            'current_period_end': subscription_data['current_period_end'],
            'next_payment_attempt': subscription_data.get('next_payment_attempt'),
            'message': 'Subscription created successfully'
        }
        
    except Exception as e:
        print(f"Failed to create subscription: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to create subscription'
        }


def _handle_update_subscription(subscription_config: Dict[str, Any],
                               metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Handle subscription updates.
    
    Args:
        subscription_config: Subscription configuration
        metadata: Additional metadata
        
    Returns:
        Subscription update result dictionary
    """
    try:
        subscription_id = subscription_config['subscription_id']
        
        # For now, return a placeholder result
        # In production, this would update the subscription via Stripe API
        
        return {
            'success': True,
            'subscription_id': subscription_id,
            'message': 'Subscription update functionality not yet implemented',
            'note': 'This is a placeholder for subscription updates'
        }
        
    except Exception as e:
        print(f"Failed to update subscription: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to update subscription'
        }


def _handle_cancel_subscription(subscription_config: Dict[str, Any],
                               metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Handle subscription cancellation.
    
    Args:
        subscription_config: Subscription configuration
        metadata: Additional metadata
        
    Returns:
        Subscription cancellation result dictionary
    """
    try:
        subscription_id = subscription_config['subscription_id']
        cancel_at_period_end = subscription_config.get('cancel_at_period_end', True)
        
        # Cancel subscription via Stripe
        cancellation_result = stripe_client.cancel_subscription(
            subscription_id=subscription_id,
            cancel_at_period_end=cancel_at_period_end
        )
        
        # Update stored subscription data
        _update_subscription_status(subscription_id, 'cancelled', metadata)
        
        return {
            'success': True,
            'subscription_id': subscription_id,
            'status': cancellation_result['status'],
            'cancel_at_period_end': cancellation_result['cancel_at_period_end'],
            'canceled_at': cancellation_result.get('canceled_at'),
            'current_period_end': cancellation_result['current_period_end'],
            'message': 'Subscription cancelled successfully'
        }
        
    except Exception as e:
        print(f"Failed to cancel subscription: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to cancel subscription'
        }


def _handle_get_subscription_status(subscription_config: Dict[str, Any],
                                   metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Handle subscription status retrieval.
    
    Args:
        subscription_config: Subscription configuration
        metadata: Additional metadata
        
    Returns:
        Subscription status result dictionary
    """
    try:
        subscription_id = subscription_config['subscription_id']
        
        # Get subscription from stored data
        subscription_record = _get_subscription_data(subscription_id)
        
        if not subscription_record:
            return {
                'success': False,
                'error': 'Subscription not found',
                'message': 'Subscription not found in our records'
            }
        
        return {
            'success': True,
            'subscription_id': subscription_id,
            'customer_email': subscription_record.get('customer_email'),
            'service_package': subscription_record.get('service_package'),
            'status': subscription_record.get('status'),
            'created_at': subscription_record.get('created_at'),
            'current_period_start': subscription_record.get('current_period_start'),
            'current_period_end': subscription_record.get('current_period_end'),
            'message': 'Subscription status retrieved successfully'
        }
        
    except Exception as e:
        print(f"Failed to get subscription status: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to get subscription status'
        }


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
            'created_via': 'dtl_global_subscription_handler',
            **metadata
        }
    }
    
    new_customer = stripe_client.create_customer(customer_data)
    print(f"Created new Stripe customer: {new_customer['id']}")
    
    return new_customer


def _get_price_id_for_package(service_package: str, package_info: Dict[str, Any]) -> str:
    """Get Stripe price ID for a DTL service package.
    
    Args:
        service_package: Service package identifier
        package_info: Package information from DTL products
        
    Returns:
        Stripe price ID (placeholder for now)
    """
    # Map DTL packages to Stripe price IDs
    # In production, these would be actual Stripe Price IDs created in your account
    
    price_mapping = {
        'dtl_friends_family': 'price_dtl_friends_family_monthly',
        'dtl_starter_monthly': 'price_dtl_starter_monthly',
        'dtl_growth_monthly': 'price_dtl_growth_monthly',
        'dtl_professional_monthly': 'price_dtl_professional_monthly',
        'dtl_premium_monthly': 'price_dtl_premium_monthly'
    }
    
    return price_mapping.get(service_package, f'price_{service_package}')


def _store_subscription_data(subscription_data: Dict[str, Any], 
                            customer_info: Dict[str, Any],
                            service_package: str,
                            metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Store subscription data in DynamoDB for tracking.
    
    Args:
        subscription_data: Stripe subscription data
        customer_info: Customer information
        service_package: DTL service package name
        metadata: Additional metadata
        
    Returns:
        Stored subscription record
    """
    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(config.DYNAMODB_TABLES['state'])
        
        # Prepare subscription record
        subscription_record = {
            'pk': f"SUBSCRIPTION#{subscription_data['id']}",
            'sk': 'METADATA',
            'subscription_id': subscription_data['id'],
            'customer_email': customer_info['email'],
            'customer_name': customer_info['name'],
            'customer_company': customer_info.get('company', ''),
            'service_package': service_package,
            'status': subscription_data['status'],
            'current_period_start': subscription_data['current_period_start'],
            'current_period_end': subscription_data['current_period_end'],
            'cancel_at_period_end': subscription_data['cancel_at_period_end'],
            'created_at': datetime.utcfromtimestamp(subscription_data['created']).isoformat(),
            'metadata': metadata,
            'ttl': int((datetime.utcnow() + timedelta(days=365)).timestamp())  # Keep for 1 year
        }
        
        # Store in DynamoDB
        table.put_item(Item=subscription_record)
        print(f"Stored subscription data in DynamoDB: {subscription_data['id']}")
        
        return subscription_record
        
    except Exception as e:
        print(f"Failed to store subscription data: {e}")
        return {}


def _get_subscription_data(subscription_id: str) -> Optional[Dict[str, Any]]:
    """Get subscription data from DynamoDB.
    
    Args:
        subscription_id: Stripe subscription ID
        
    Returns:
        Subscription record or None if not found
    """
    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(config.DYNAMODB_TABLES['state'])
        
        # Get subscription record
        response = table.get_item(
            Key={
                'pk': f"SUBSCRIPTION#{subscription_id}",
                'sk': 'METADATA'
            }
        )
        
        return response.get('Item')
        
    except Exception as e:
        print(f"Failed to get subscription data: {e}")
        return None


def _update_subscription_status(subscription_id: str, status: str, 
                               metadata: Dict[str, Any]) -> None:
    """Update subscription status in DynamoDB.
    
    Args:
        subscription_id: Stripe subscription ID
        status: New status
        metadata: Additional metadata
    """
    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(config.DYNAMODB_TABLES['state'])
        
        # Update subscription status
        table.update_item(
            Key={
                'pk': f"SUBSCRIPTION#{subscription_id}",
                'sk': 'METADATA'
            },
            UpdateExpression='SET #status = :status, updated_at = :updated_at',
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':status': status,
                ':updated_at': datetime.utcnow().isoformat()
            }
        )
        
        print(f"Updated subscription status: {subscription_id} -> {status}")
        
    except Exception as e:
        print(f"Failed to update subscription status: {e}")


def _send_subscription_confirmation_email(customer_info: Dict[str, Any],
                                         subscription_data: Dict[str, Any],
                                         package_info: Dict[str, Any]) -> None:
    """Send subscription confirmation email to customer.
    
    Args:
        customer_info: Customer information
        subscription_data: Stripe subscription data
        package_info: DTL package information
    """
    try:
        # Prepare email content
        subject = f"Subscription Confirmation - {package_info['name']}"
        
        # Build plain text body
        text_body = f"""
Dear {customer_info['name']},

Thank you for subscribing to {package_info['name']}!

SUBSCRIPTION DETAILS:
- Service: {package_info['name']}
- Amount: ${package_info['amount'] / 100:.2f} USD per {package_info['interval']}
- Status: {subscription_data['status'].title()}
- Next billing date: {datetime.utcfromtimestamp(subscription_data['current_period_end']).strftime('%B %d, %Y')}

Your subscription is now active and you'll receive ongoing support and maintenance for your digital services.

If you have any questions, please don't hesitate to contact us.

Best regards,
The DTL-Global Team
"""
        
        # Send email
        ses_client.send_email(
            to_addresses=customer_info['email'],
            subject=subject,
            body_text=text_body.strip()
        )
        
        print(f"Sent subscription confirmation email to {customer_info['email']}")
        
    except Exception as e:
        print(f"Failed to send subscription confirmation email: {e}")


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
