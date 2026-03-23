"""POST /chatbot Lambda handler for DTL-Global onboarding platform.

This handler provides AI chatbot functionality that captures leads to HubSpot.

Endpoint: POST /chatbot
Purpose: Handle chatbot conversations and capture leads
Dependencies: AI client for responses, HubSpot client for lead capture

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
from ai_client import ai_client
from hubspot_client import hubspot_client


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle chatbot conversations and capture leads to HubSpot.
    
    Args:
        event: API Gateway event containing chatbot request
        context: Lambda context object
        
    Returns:
        Dict containing chatbot response and lead capture status
    """
    print(f"Chatbot handler started - Request ID: {context.aws_request_id}")
    
    try:
        # Parse request body from API Gateway event
        request_data = json.loads(event['body'])
        
        # Extract chatbot conversation data
        message = request_data.get('message', '')  # User's message to chatbot
        conversation_id = request_data.get('conversation_id')  # Optional conversation tracking
        user_context = request_data.get('user_context', {})  # User info if available
        website_context = request_data.get('website_context', {})  # Website/company context
        
        print(f"Processing chatbot message: {message[:100]}...")  # Log first 100 chars for debugging
        
        # Validate required fields
        if not message.strip():
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Message is required',
                    'success': False
                })
            }
        
        # Generate AI chatbot response using Claude
        chatbot_response = _generate_chatbot_response(
            message=message,
            conversation_id=conversation_id,
            website_context=website_context
        )
        
        # Check if this conversation indicates a potential lead
        lead_captured = False
        lead_data = None
        
        if _is_potential_lead(message, chatbot_response):
            # Extract lead information and capture to HubSpot
            lead_data = _extract_lead_info(message, user_context, website_context)
            
            if lead_data:
                # Create lead in HubSpot CRM
                hubspot_result = _capture_lead_to_hubspot(lead_data)
                lead_captured = hubspot_result.get('success', False)
                print(f"Lead capture result: {lead_captured}")
        
        # Return successful response with chatbot reply
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'response': chatbot_response,
                'conversation_id': conversation_id,
                'lead_captured': lead_captured,
                'lead_data': lead_data if lead_captured else None
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
        print(f"Chatbot handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error processing chatbot request',
                'success': False
            })
        }


def _generate_chatbot_response(message: str, conversation_id: Optional[str], 
                             website_context: Dict[str, Any]) -> str:
    """Generate AI-powered chatbot response using Claude.
    
    Args:
        message: User's message to the chatbot
        conversation_id: Optional conversation tracking ID
        website_context: Context about the website/company
        
    Returns:
        AI-generated chatbot response string
    """
    try:
        # Build system prompt for DTL-Global chatbot
        system_prompt = _build_chatbot_system_prompt(website_context)
        
        # Generate response using AI client
        response = ai_client.generate_chatbot_response(
            user_message=message,
            system_prompt=system_prompt,
            conversation_context=conversation_id
        )
        
        return response
        
    except Exception as e:
        print(f"Error generating chatbot response: {str(e)}")
        # Return fallback response if AI fails
        return ("I'm sorry, I'm having trouble processing your message right now. "
                "Please feel free to contact us directly for assistance with your digital transformation needs.")


def _build_chatbot_system_prompt(website_context: Dict[str, Any]) -> str:
    """Build system prompt for DTL-Global chatbot based on context.
    
    Args:
        website_context: Context about the website/company
        
    Returns:
        System prompt string for the chatbot
    """
    company_name = website_context.get('company_name', 'this business')
    industry = website_context.get('industry', 'your industry')
    
    return f"""You are a helpful AI assistant for DTL-Global, a digital transformation consultancy. 
You are currently helping visitors on {company_name}'s website.

Your role:
- Help visitors understand DTL-Global's services: website development, CRM setup, payment processing, email automation
- Qualify potential leads by asking about their business needs
- Be professional, helpful, and focused on digital transformation solutions
- If someone shows interest in services, gather: company name, contact info, specific needs
- Guide conversations toward scheduling a consultation or getting a quote

Company context:
- Company: {company_name}
- Industry: {industry}

DTL-Global Services:
- Custom website development with SEO optimization
- HubSpot CRM setup and automation
- Stripe payment processing integration
- Email marketing and automation
- Google Workspace setup
- Full digital transformation packages

Keep responses concise (2-3 sentences max) and always try to be helpful while identifying potential business opportunities."""


def _is_potential_lead(message: str, response: str) -> bool:
    """Determine if conversation indicates a potential lead.
    
    Args:
        message: User's message
        response: Chatbot's response
        
    Returns:
        True if this appears to be a potential lead
    """
    # Keywords that indicate business interest
    lead_keywords = [
        'website', 'business', 'company', 'service', 'help', 'need', 'looking for',
        'quote', 'price', 'cost', 'consultation', 'contact', 'email', 'phone',
        'crm', 'payment', 'stripe', 'hubspot', 'automation', 'digital', 'online'
    ]
    
    # Check if message contains lead indicators
    message_lower = message.lower()
    for keyword in lead_keywords:
        if keyword in message_lower:
            return True
    
    return False


def _extract_lead_info(message: str, user_context: Dict[str, Any], 
                      website_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract lead information from conversation context.
    
    Args:
        message: User's message
        user_context: Available user context data
        website_context: Website/company context
        
    Returns:
        Dictionary with lead data or None if insufficient info
    """
    try:
        # Extract available information
        lead_data = {
            'source': 'AI Chatbot',
            'website': website_context.get('domain', 'Unknown'),
            'industry': website_context.get('industry', 'Unknown'),
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            'lead_status': 'New'
        }
        
        # Add user context if available
        if user_context.get('email'):
            lead_data['email'] = user_context['email']
        if user_context.get('name'):
            lead_data['name'] = user_context['name']
        if user_context.get('company'):
            lead_data['company'] = user_context['company']
        if user_context.get('phone'):
            lead_data['phone'] = user_context['phone']
        
        # Use AI to extract additional info from message
        extracted_info = ai_client.extract_lead_information(message)
        if extracted_info:
            lead_data.update(extracted_info)
        
        return lead_data
        
    except Exception as e:
        print(f"Error extracting lead info: {str(e)}")
        return None


def _capture_lead_to_hubspot(lead_data: Dict[str, Any]) -> Dict[str, Any]:
    """Capture lead to HubSpot CRM.
    
    Args:
        lead_data: Dictionary containing lead information
        
    Returns:
        Dictionary with capture result and HubSpot contact ID
    """
    try:
        # Create contact in HubSpot
        contact_result = hubspot_client.create_contact(
            email=lead_data.get('email', ''),
            first_name=lead_data.get('first_name', ''),
            last_name=lead_data.get('last_name', ''),
            company=lead_data.get('company', ''),
            phone=lead_data.get('phone', ''),
            website=lead_data.get('website', ''),
            lead_source='AI Chatbot',
            notes=f"Chatbot conversation: {lead_data.get('message', '')}"
        )
        
        if contact_result.get('success'):
            print(f"Lead captured to HubSpot: {contact_result.get('contact_id')}")
            return {
                'success': True,
                'contact_id': contact_result.get('contact_id'),
                'message': 'Lead successfully captured to HubSpot'
            }
        else:
            print(f"Failed to capture lead to HubSpot: {contact_result.get('error')}")
            return {
                'success': False,
                'error': contact_result.get('error', 'Unknown HubSpot error')
            }
            
    except Exception as e:
        print(f"Error capturing lead to HubSpot: {str(e)}")
        return {
            'success': False,
            'error': f'HubSpot integration error: {str(e)}'
        }