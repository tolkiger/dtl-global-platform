"""POST /webhook/stripe Lambda handler for DTL-Global onboarding platform.

This handler receives Stripe webhook events and advances HubSpot deals through
the onboarding lifecycle. Validates webhook signatures and processes key events
like invoice payments and subscription cancellations.

Endpoint: POST /webhook/stripe
Purpose: Process Stripe webhook events and update CRM accordingly
Dependencies: Stripe client, HubSpot client, DynamoDB client, Slack notifications

Author: DTL-Global Platform
"""

import json
import boto3
from typing import Any, Dict, Optional
import requests

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

# Import config and clients
from config import config
from stripe_client import stripe_client
from hubspot_client import hubspot_client


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Process Stripe webhook events and update HubSpot deals accordingly.
    
    This function validates Stripe webhook signatures and processes key events
    to advance deals through the onboarding lifecycle automatically.
    
    Args:
        event: API Gateway proxy request event containing webhook payload
        context: Lambda runtime context object
        
    Returns:
        API Gateway proxy response with processing status
        
    Expected Webhook Events:
        - invoice.paid: Advance deal from "Contract & Deposit" to "Build Website"
                       or from "Final Payment" to "Live & Monthly"
        - customer.subscription.deleted: Move deal to "Churned" stage
    """
    print(f"Stripe webhook processing started - Request ID: {context.aws_request_id}")
    
    try:
        # Get webhook payload and headers
        payload = event.get('body', '')  # Raw webhook payload from Stripe
        signature = event.get('headers', {}).get('stripe-signature', '')  # Webhook signature header
        
        if not payload or not signature:  # Missing required webhook data
            print("ERROR: Missing webhook payload or signature")
            return _create_error_response(400, "Missing webhook payload or signature")
        
        # Get webhook secret from SSM for signature validation
        webhook_secret = config.get_secret('stripe_webhook_secret')
        
        # Validate webhook signature using Stripe SDK
        try:
            import stripe
            webhook_event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )  # Stripe validates the signature and parses the event
        except stripe.error.SignatureVerificationError as e:
            print(f"ERROR: Invalid webhook signature: {e}")
            return _create_error_response(400, "Invalid webhook signature")
        except Exception as e:
            print(f"ERROR: Webhook validation failed: {e}")
            return _create_error_response(400, f"Webhook validation failed: {e}")
        
        # Extract event type and data
        event_type = webhook_event.get('type')  # Type of Stripe event
        event_data = webhook_event.get('data', {}).get('object', {})  # Event payload data
        
        print(f"Processing Stripe webhook event: {event_type}")
        
        # Route to appropriate event handler
        if event_type == 'invoice.paid':
            result = _handle_invoice_paid(event_data)
        elif event_type == 'customer.subscription.deleted':
            result = _handle_subscription_deleted(event_data)
        else:
            # Unknown event type - log and return success (Stripe expects 200)
            print(f"Unhandled event type: {event_type}")
            return _create_success_response(f"Event type {event_type} not handled")
        
        print(f"Webhook event {event_type} processed successfully")
        
        # Return success response
        return _create_success_response(result.get('message', 'Webhook processed'))
        
    except Exception as e:
        print(f"ERROR: Webhook processing failed: {e}")
        return _create_error_response(500, f"Internal server error: {e}")


def _handle_invoice_paid(invoice_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle invoice.paid webhook event.
    
    When an invoice is paid, advance the corresponding HubSpot deal to the next stage
    based on current stage (deposit payment vs final payment).
    
    Args:
        invoice_data: Stripe invoice object from webhook
        
    Returns:
        Dictionary with processing results
    """
    try:
        # Extract customer ID from invoice
        customer_id = invoice_data.get('customer')  # Stripe customer ID
        if not customer_id:
            print("WARNING: No customer ID in invoice data")
            return {'success': False, 'message': 'No customer ID in invoice'}
        
        print(f"Processing invoice payment for customer: {customer_id}")
        
        # Query DynamoDB to find client by Stripe customer ID
        client_data = _get_client_by_stripe_id(customer_id)
        if not client_data:
            print(f"WARNING: No client found for Stripe customer: {customer_id}")
            return {'success': False, 'message': f'Client not found for customer {customer_id}'}
        
        # Get HubSpot deal ID from client data
        deal_id = client_data.get('hubspot_deal_id')  # HubSpot deal identifier
        if not deal_id:
            print("WARNING: No HubSpot deal ID in client data")
            return {'success': False, 'message': 'No HubSpot deal ID found'}
        
        # Get current deal stage from HubSpot
        current_stage = _get_deal_stage(deal_id)
        if not current_stage:
            print(f"WARNING: Could not get current stage for deal: {deal_id}")
            return {'success': False, 'message': f'Could not get deal stage for {deal_id}'}
        
        print(f"Current deal stage: {current_stage}")
        
        # Determine next stage based on current stage
        next_stage = None
        if current_stage == 'Contract & Deposit':  # First payment (50% deposit)
            next_stage = 'Build Website'  # Move to website building phase
        elif current_stage == 'Final Payment':  # Second payment (remaining 50%)
            next_stage = 'Live & Monthly'  # Move to live and billing phase
        else:
            print(f"INFO: No stage advancement needed for current stage: {current_stage}")
            return {'success': True, 'message': f'No advancement needed from stage: {current_stage}'}
        
        # Update deal stage in HubSpot
        update_result = _update_deal_stage(deal_id, next_stage)
        if not update_result:
            print(f"ERROR: Failed to update deal stage to: {next_stage}")
            return {'success': False, 'message': f'Failed to update deal stage to {next_stage}'}
        
        # Send Slack notification about payment and stage advancement
        company_name = client_data.get('company', 'Unknown Company')  # Client company name
        invoice_amount = invoice_data.get('amount_paid', 0) / 100  # Convert cents to dollars
        slack_message = f"💰 Payment received: ${invoice_amount:.2f} from {company_name}. Deal advanced from '{current_stage}' to '{next_stage}'."
        _send_slack_notification(slack_message)
        
        return {
            'success': True,
            'message': f'Deal {deal_id} advanced from {current_stage} to {next_stage}',
            'deal_id': deal_id,
            'previous_stage': current_stage,
            'new_stage': next_stage
        }
        
    except Exception as e:
        print(f"ERROR: Failed to handle invoice.paid event: {e}")
        return {'success': False, 'message': f'Invoice processing failed: {e}'}


def _handle_subscription_deleted(subscription_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle customer.subscription.deleted webhook event.
    
    When a subscription is cancelled, move the corresponding HubSpot deal to "Churned" stage.
    
    Args:
        subscription_data: Stripe subscription object from webhook
        
    Returns:
        Dictionary with processing results
    """
    try:
        # Extract customer ID from subscription
        customer_id = subscription_data.get('customer')  # Stripe customer ID
        if not customer_id:
            print("WARNING: No customer ID in subscription data")
            return {'success': False, 'message': 'No customer ID in subscription'}
        
        print(f"Processing subscription cancellation for customer: {customer_id}")
        
        # Query DynamoDB to find client by Stripe customer ID
        client_data = _get_client_by_stripe_id(customer_id)
        if not client_data:
            print(f"WARNING: No client found for Stripe customer: {customer_id}")
            return {'success': False, 'message': f'Client not found for customer {customer_id}'}
        
        # Get HubSpot deal ID from client data
        deal_id = client_data.get('hubspot_deal_id')  # HubSpot deal identifier
        if not deal_id:
            print("WARNING: No HubSpot deal ID in client data")
            return {'success': False, 'message': 'No HubSpot deal ID found'}
        
        # Move deal to "Churned" stage
        update_result = _update_deal_stage(deal_id, 'Churned')
        if not update_result:
            print(f"ERROR: Failed to move deal to Churned stage")
            return {'success': False, 'message': 'Failed to move deal to Churned stage'}
        
        # Send Slack notification about churn
        company_name = client_data.get('company', 'Unknown Company')  # Client company name
        slack_message = f"😞 Subscription cancelled: {company_name}. Deal moved to 'Churned' stage."
        _send_slack_notification(slack_message)
        
        return {
            'success': True,
            'message': f'Deal {deal_id} moved to Churned stage due to subscription cancellation',
            'deal_id': deal_id,
            'new_stage': 'Churned'
        }
        
    except Exception as e:
        print(f"ERROR: Failed to handle subscription.deleted event: {e}")
        return {'success': False, 'message': f'Subscription processing failed: {e}'}


def _get_client_by_stripe_id(customer_id: str) -> Optional[Dict[str, Any]]:
    """Query DynamoDB to find client record by Stripe customer ID.
    
    Args:
        customer_id: Stripe customer ID to search for
        
    Returns:
        Client data dictionary or None if not found
    """
    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')  # DynamoDB resource for table operations
        table = dynamodb.Table('dtl-clients')  # Client records table
        
        # Scan table for matching Stripe customer ID (no GSI assumed)
        response = table.scan(
            FilterExpression='stripe_customer_id = :customer_id',
            ExpressionAttributeValues={':customer_id': customer_id}
        )  # Scan with filter for Stripe customer ID
        
        items = response.get('Items', [])  # Get matching items
        if items:
            print(f"Found client record for Stripe customer: {customer_id}")
            return items[0]  # Return first matching client record
        else:
            print(f"No client record found for Stripe customer: {customer_id}")
            return None  # No matching client found
            
    except Exception as e:
        print(f"ERROR: DynamoDB query failed for customer {customer_id}: {e}")
        return None  # Return None on error


def _get_deal_stage(deal_id: str) -> Optional[str]:
    """Get current stage of HubSpot deal.
    
    Args:
        deal_id: HubSpot deal ID
        
    Returns:
        Current deal stage name or None if error
    """
    try:
        # Get deal details from HubSpot
        deal_data = hubspot_client.get_deal(deal_id)  # Fetch deal from HubSpot API
        if deal_data:
            stage = deal_data.get('properties', {}).get('dealstage')  # Extract deal stage property
            print(f"Retrieved deal stage for {deal_id}: {stage}")
            return stage
        else:
            print(f"ERROR: Could not retrieve deal {deal_id} from HubSpot")
            return None
            
    except Exception as e:
        print(f"ERROR: Failed to get deal stage for {deal_id}: {e}")
        return None


def _update_deal_stage(deal_id: str, new_stage: str) -> bool:
    """Update HubSpot deal stage.
    
    Args:
        deal_id: HubSpot deal ID
        new_stage: New stage name to set
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Update deal stage in HubSpot
        result = hubspot_client.update_deal(deal_id, {'dealstage': new_stage})  # Update deal stage property
        if result:
            print(f"Successfully updated deal {deal_id} to stage: {new_stage}")
            return True
        else:
            print(f"ERROR: Failed to update deal {deal_id} to stage: {new_stage}")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to update deal stage for {deal_id}: {e}")
        return False


def _send_slack_notification(message: str) -> None:
    """Send notification to Slack webhook.
    
    Args:
        message: Message text to send to Slack
    """
    try:
        # Get Slack webhook URL from SSM
        slack_url = config.get_secret('slack_webhook_url')  # Slack incoming webhook URL
        
        # Send POST request to Slack webhook
        payload = {'text': message}  # Slack webhook payload format
        response = requests.post(
            slack_url,
            json=payload,
            timeout=10
        )  # POST to Slack webhook with timeout
        
        if response.status_code == 200:
            print(f"Slack notification sent: {message}")
        else:
            print(f"WARNING: Slack notification failed with status {response.status_code}")
            
    except Exception as e:
        print(f"WARNING: Failed to send Slack notification: {e}")
        # Don't fail the webhook processing if Slack fails (non-critical)


def _create_success_response(message: str) -> Dict[str, Any]:
    """Create successful API Gateway response.
    
    Args:
        message: Success message
        
    Returns:
        API Gateway response dictionary
    """
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'success': True,
            'message': message
        })
    }


def _create_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Create error API Gateway response.
    
    Args:
        status_code: HTTP status code
        message: Error message
        
    Returns:
        API Gateway response dictionary
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'success': False,
            'error': message
        })
    }