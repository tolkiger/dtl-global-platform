"""POST /whatsapp Lambda handler for DTL-Global onboarding platform.

This handler manages WhatsApp Business API integration setup.

Endpoint: POST /whatsapp
Purpose: Configure WhatsApp Business messaging for client communications
Dependencies: Configuration management for webhook setup

Author: DTL-Global Platform
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime
import hashlib
import hmac

# Import shared modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import config
from hubspot_client import hubspot_client


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle WhatsApp Business API integration setup and webhooks.
    
    Args:
        event: API Gateway event containing WhatsApp request
        context: Lambda context object
        
    Returns:
        Dict containing WhatsApp integration results
    """
    print(f"WhatsApp handler started - Request ID: {context.aws_request_id}")
    
    try:
        # Parse request body from API Gateway event
        request_data = json.loads(event['body'])
        
        # Extract WhatsApp operation type
        operation = request_data.get('operation', 'setup')  # setup, webhook, send_message
        
        if operation == 'setup':
            # Set up WhatsApp Business integration
            return _handle_whatsapp_setup(request_data)
            
        elif operation == 'webhook':
            # Handle WhatsApp webhook verification or message
            return _handle_whatsapp_webhook(event, request_data)
            
        elif operation == 'send_message':
            # Send WhatsApp message to client
            return _handle_send_message(request_data)
            
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': f'Unsupported WhatsApp operation: {operation}',
                    'success': False
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
        print(f"WhatsApp handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error processing WhatsApp request',
                'success': False
            })
        }


def _handle_whatsapp_setup(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle WhatsApp Business API setup configuration.
    
    Args:
        request_data: Request data containing setup parameters
        
    Returns:
        Dictionary with setup results and configuration
    """
    try:
        # Extract setup parameters
        client_info = request_data.get('client_info', {})
        business_name = client_info.get('company', 'Business')
        phone_number = request_data.get('phone_number', '')
        webhook_url = request_data.get('webhook_url', '')
        
        print(f"Setting up WhatsApp for {business_name}")
        
        # Validate required fields
        if not phone_number:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Phone number is required for WhatsApp setup',
                    'success': False
                })
            }
        
        # Generate WhatsApp Business setup configuration
        setup_config = _generate_whatsapp_config(business_name, phone_number, webhook_url)
        
        # Generate setup instructions
        instructions = _generate_whatsapp_instructions(setup_config)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'business_name': business_name,
                'phone_number': phone_number,
                'setup_config': setup_config,
                'instructions': instructions,
                'webhook_url': webhook_url or 'To be configured'
            })
        }
        
    except Exception as e:
        print(f"Error in WhatsApp setup: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'WhatsApp setup error: {str(e)}',
                'success': False
            })
        }


def _handle_whatsapp_webhook(event: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle WhatsApp webhook verification and incoming messages.
    
    Args:
        event: API Gateway event
        request_data: Parsed request data
        
    Returns:
        Dictionary with webhook handling results
    """
    try:
        # Check if this is a webhook verification request
        query_params = event.get('queryStringParameters', {}) or {}
        
        if 'hub.mode' in query_params and query_params['hub.mode'] == 'subscribe':
            # Handle webhook verification
            return _verify_whatsapp_webhook(query_params)
        
        # Handle incoming WhatsApp message
        if 'messages' in request_data:
            return _process_whatsapp_message(request_data)
        
        # Handle status updates
        if 'statuses' in request_data:
            return _process_whatsapp_status(request_data)
        
        # Default response for webhook
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'success': True})
        }
        
    except Exception as e:
        print(f"Error handling WhatsApp webhook: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': f'Webhook processing error: {str(e)}',
                'success': False
            })
        }


def _handle_send_message(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle sending WhatsApp message to client.
    
    Args:
        request_data: Request data containing message parameters
        
    Returns:
        Dictionary with message sending results
    """
    try:
        # Extract message parameters
        to_number = request_data.get('to_number', '')
        message_text = request_data.get('message', '')
        message_type = request_data.get('message_type', 'text')
        
        print(f"Sending WhatsApp message to {to_number}")
        
        # Validate required fields
        if not to_number or not message_text:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Phone number and message are required',
                    'success': False
                })
            }
        
        # For now, simulate message sending (actual WhatsApp API integration would go here)
        message_result = {
            'message_id': f"wamid_{datetime.utcnow().timestamp()}",
            'status': 'sent',
            'to': to_number,
            'message': message_text,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        print(f"WhatsApp message simulated: {message_result['message_id']}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'message_result': message_result,
                'note': 'Message sending simulated - actual WhatsApp API integration required'
            })
        }
        
    except Exception as e:
        print(f"Error sending WhatsApp message: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Message sending error: {str(e)}',
                'success': False
            })
        }


def _generate_whatsapp_config(business_name: str, phone_number: str, 
                            webhook_url: str) -> Dict[str, Any]:
    """Generate WhatsApp Business API configuration.
    
    Args:
        business_name: Name of the business
        phone_number: Business phone number
        webhook_url: Webhook URL for receiving messages
        
    Returns:
        Dictionary with WhatsApp configuration
    """
    config = {
        'business_profile': {
            'name': business_name,
            'phone_number': phone_number,
            'description': f'Digital transformation services by {business_name}',
            'category': 'Business Services',
            'website': f'https://{business_name.lower().replace(" ", "")}.com'
        },
        'webhook_config': {
            'url': webhook_url,
            'verify_token': f'dtl_whatsapp_{hashlib.md5(business_name.encode()).hexdigest()[:8]}',
            'events': ['messages', 'message_deliveries', 'message_reads']
        },
        'message_templates': [
            {
                'name': 'welcome_message',
                'language': 'en_US',
                'category': 'UTILITY',
                'components': [
                    {
                        'type': 'BODY',
                        'text': f'Welcome to {business_name}! We\'re excited to help with your digital transformation. How can we assist you today?'
                    }
                ]
            },
            {
                'name': 'appointment_reminder',
                'language': 'en_US',
                'category': 'UTILITY',
                'components': [
                    {
                        'type': 'BODY',
                        'text': f'Hi! This is a reminder about your consultation with {business_name} scheduled for {{1}}. Looking forward to speaking with you!'
                    }
                ]
            }
        ],
        'integration_settings': {
            'hubspot_sync': True,
            'auto_responses': True,
            'business_hours': {
                'enabled': True,
                'timezone': 'America/New_York',
                'monday': {'start': '09:00', 'end': '17:00'},
                'tuesday': {'start': '09:00', 'end': '17:00'},
                'wednesday': {'start': '09:00', 'end': '17:00'},
                'thursday': {'start': '09:00', 'end': '17:00'},
                'friday': {'start': '09:00', 'end': '17:00'},
                'saturday': {'start': '10:00', 'end': '14:00'},
                'sunday': {'closed': True}
            }
        }
    }
    
    return config


def _generate_whatsapp_instructions(config: Dict[str, Any]) -> List[str]:
    """Generate WhatsApp Business API setup instructions.
    
    Args:
        config: WhatsApp configuration dictionary
        
    Returns:
        List of instruction strings
    """
    business_name = config['business_profile']['name']
    verify_token = config['webhook_config']['verify_token']
    
    instructions = [
        "WhatsApp Business API Setup Instructions:",
        "",
        "1. WhatsApp Business Account Setup:",
        "   - Go to business.whatsapp.com",
        "   - Create a WhatsApp Business account",
        f"   - Verify your business phone number: {config['business_profile']['phone_number']}",
        "   - Complete business verification process",
        "",
        "2. Facebook Developer Account:",
        "   - Go to developers.facebook.com",
        "   - Create a developer account if you don't have one",
        "   - Create a new app for WhatsApp Business API",
        "   - Add WhatsApp product to your app",
        "",
        "3. Configure Webhook:",
        f"   - Webhook URL: {config['webhook_config']['url']}",
        f"   - Verify Token: {verify_token}",
        "   - Subscribe to webhook fields: messages, message_deliveries, message_reads",
        "",
        "4. Business Profile Setup:",
        f"   - Business Name: {business_name}",
        f"   - Description: {config['business_profile']['description']}",
        f"   - Category: {config['business_profile']['category']}",
        f"   - Website: {config['business_profile']['website']}",
        "",
        "5. Message Templates:",
        "   Create the following message templates in Facebook Business Manager:",
        ""
    ]
    
    # Add template details
    for template in config['message_templates']:
        instructions.append(f"   Template: {template['name']}")
        instructions.append(f"   Language: {template['language']}")
        instructions.append(f"   Category: {template['category']}")
        instructions.append(f"   Text: {template['components'][0]['text']}")
        instructions.append("")
    
    instructions.extend([
        "6. Integration Settings:",
        "   - Enable HubSpot synchronization for lead tracking",
        "   - Configure auto-responses for common inquiries",
        "   - Set business hours for automated responses",
        "",
        "7. Testing:",
        "   - Send test messages to verify webhook functionality",
        "   - Test message templates and auto-responses",
        "   - Verify HubSpot lead capture integration",
        "",
        "Note: WhatsApp Business API requires approval from Meta.",
        "The approval process can take several days to weeks.",
        "",
        "For assistance with WhatsApp setup, contact DTL-Global support."
    ])
    
    return instructions


def _verify_whatsapp_webhook(query_params: Dict[str, str]) -> Dict[str, Any]:
    """Verify WhatsApp webhook subscription.
    
    Args:
        query_params: Query parameters from webhook verification request
        
    Returns:
        Dictionary with verification response
    """
    try:
        # Extract verification parameters
        mode = query_params.get('hub.mode')
        token = query_params.get('hub.verify_token')
        challenge = query_params.get('hub.challenge')
        
        # For demo purposes, accept any verification token
        # In production, verify against stored token
        if mode == 'subscribe' and token and challenge:
            print(f"WhatsApp webhook verified with token: {token}")
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'text/plain'
                },
                'body': challenge
            }
        
        return {
            'statusCode': 403,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': 'Webhook verification failed',
                'success': False
            })
        }
        
    except Exception as e:
        print(f"Error verifying WhatsApp webhook: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': f'Verification error: {str(e)}',
                'success': False
            })
        }


def _process_whatsapp_message(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process incoming WhatsApp message and sync to HubSpot.
    
    Args:
        message_data: WhatsApp message data
        
    Returns:
        Dictionary with processing results
    """
    try:
        messages = message_data.get('messages', [])
        
        for message in messages:
            # Extract message details
            from_number = message.get('from', '')
            message_text = message.get('text', {}).get('body', '')
            message_id = message.get('id', '')
            timestamp = message.get('timestamp', '')
            
            print(f"Processing WhatsApp message from {from_number}: {message_text[:50]}...")
            
            # Create lead/contact in HubSpot
            try:
                contact_result = hubspot_client.create_contact(
                    phone=from_number,
                    lead_source='WhatsApp',
                    notes=f'WhatsApp message: {message_text}'
                )
                
                print(f"WhatsApp lead synced to HubSpot: {contact_result.get('contact_id')}")
                
            except Exception as e:
                print(f"Error syncing WhatsApp lead to HubSpot: {str(e)}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': True,
                'processed_messages': len(messages)
            })
        }
        
    except Exception as e:
        print(f"Error processing WhatsApp message: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': f'Message processing error: {str(e)}',
                'success': False
            })
        }


def _process_whatsapp_status(status_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process WhatsApp message status updates.
    
    Args:
        status_data: WhatsApp status update data
        
    Returns:
        Dictionary with processing results
    """
    try:
        statuses = status_data.get('statuses', [])
        
        for status in statuses:
            message_id = status.get('id', '')
            status_type = status.get('status', '')
            timestamp = status.get('timestamp', '')
            
            print(f"WhatsApp message {message_id} status: {status_type}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': True,
                'processed_statuses': len(statuses)
            })
        }
        
    except Exception as e:
        print(f"Error processing WhatsApp status: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': f'Status processing error: {str(e)}',
                'success': False
            })
        }