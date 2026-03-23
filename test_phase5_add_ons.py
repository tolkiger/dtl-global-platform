"""Comprehensive tests for Phase 5: Add-On Modules.

Tests all add-on module functionality including:
- AI Chatbot integration with HubSpot lead capture
- Google Workspace email DNS configuration
- WhatsApp Business API integration
- Slack and Microsoft Teams collaboration setup

Author: DTL-Global Platform
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Test the chatbot handler
def test_chatbot_handler_basic_conversation():
    """Test basic chatbot conversation functionality."""
    from engine.handlers.handler_chatbot import lambda_handler
    
    # Mock event with chatbot message
    event = {
        'body': json.dumps({
            'message': 'Hello, I need help with my website',
            'conversation_id': 'conv_123',
            'user_context': {},
            'website_context': {
                'company_name': 'Test Company',
                'industry': 'Technology'
            }
        })
    }
    
    # Mock context
    context = Mock()
    context.aws_request_id = 'test-request-123'
    
    # Mock AI client response
    with patch('engine.handlers.handler_chatbot.ai_client') as mock_ai:
        mock_ai.generate_chatbot_response.return_value = "Hello! I'd be happy to help you with your website needs. What specific features are you looking for?"
        
        # Call handler
        response = lambda_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert 'response' in body
        assert body['conversation_id'] == 'conv_123'


def test_chatbot_lead_capture():
    """Test chatbot lead capture to HubSpot."""
    from engine.handlers.handler_chatbot import lambda_handler
    
    # Mock event with lead-indicating message
    event = {
        'body': json.dumps({
            'message': 'I need a quote for website development for my company ABC Corp',
            'user_context': {
                'email': 'john@abccorp.com',
                'name': 'John Smith'
            },
            'website_context': {
                'company_name': 'Test Company',
                'industry': 'Technology'
            }
        })
    }
    
    context = Mock()
    context.aws_request_id = 'test-request-123'
    
    # Mock AI and HubSpot clients
    with patch('engine.handlers.handler_chatbot.ai_client') as mock_ai, \
         patch('engine.handlers.handler_chatbot.hubspot_client') as mock_hubspot:
        
        mock_ai.generate_chatbot_response.return_value = "I'd be happy to help you with a website quote!"
        mock_ai.extract_lead_information.return_value = {
            'company': 'ABC Corp',
            'needs': 'website development'
        }
        mock_hubspot.create_contact.return_value = {
            'success': True,
            'contact_id': 'contact_123'
        }
        
        # Call handler
        response = lambda_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['lead_captured'] is True
        assert body['lead_data'] is not None


def test_workspace_google_setup():
    """Test Google Workspace email setup."""
    from engine.handlers.handler_workspace import lambda_handler
    
    # Mock event with Google Workspace setup request
    event = {
        'body': json.dumps({
            'domain': 'testcompany.com',
            'workspace_type': 'google',
            'admin_email': 'admin@testcompany.com',
            'client_info': {
                'company': 'Test Company'
            }
        })
    }
    
    context = Mock()
    context.aws_request_id = 'test-request-123'
    
    # Mock Route53 client
    with patch('engine.handlers.handler_workspace.route53_client') as mock_route53:
        mock_route53.create_dns_record.return_value = {
            'success': True,
            'message': 'DNS record created successfully'
        }
        
        # Call handler
        response = lambda_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['domain'] == 'testcompany.com'
        assert body['workspace_type'] == 'google'
        assert 'dns_records' in body
        assert 'setup_instructions' in body
        
        # Verify DNS records include required Google Workspace records
        dns_records = body['dns_records']
        record_types = [record['type'] for record in dns_records]
        assert 'MX' in record_types
        assert 'TXT' in record_types


def test_workspace_dns_records_structure():
    """Test Google Workspace DNS records structure."""
    from engine.handlers.handler_workspace import _get_google_workspace_dns_records
    
    domain = 'example.com'
    records = _get_google_workspace_dns_records(domain)
    
    # Verify required record types exist
    record_types = [record['type'] for record in records]
    assert 'MX' in record_types
    assert 'TXT' in record_types
    
    # Verify MX records for Google Workspace
    mx_records = [record for record in records if record['type'] == 'MX']
    assert len(mx_records) >= 4  # Google requires multiple MX records
    
    # Verify SPF record exists
    spf_records = [record for record in records if record['type'] == 'TXT' and 'spf1' in record['value']]
    assert len(spf_records) >= 1
    
    # Verify all records have required fields
    for record in records:
        assert 'type' in record
        assert 'name' in record
        assert 'value' in record
        assert 'description' in record


def test_whatsapp_setup():
    """Test WhatsApp Business API setup."""
    from engine.handlers.handler_whatsapp import lambda_handler
    
    # Mock event with WhatsApp setup request
    event = {
        'body': json.dumps({
            'operation': 'setup',
            'phone_number': '+1234567890',
            'client_info': {
                'company': 'Test Company'
            },
            'webhook_url': 'https://api.example.com/whatsapp/webhook'
        })
    }
    
    context = Mock()
    context.aws_request_id = 'test-request-123'
    
    # Call handler
    response = lambda_handler(event, context)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['success'] is True
    assert body['business_name'] == 'Test Company'
    assert body['phone_number'] == '+1234567890'
    assert 'setup_config' in body
    assert 'instructions' in body


def test_whatsapp_webhook_verification():
    """Test WhatsApp webhook verification."""
    from engine.handlers.handler_whatsapp import lambda_handler
    
    # Mock webhook verification event
    event = {
        'queryStringParameters': {
            'hub.mode': 'subscribe',
            'hub.verify_token': 'test_token',
            'hub.challenge': 'challenge_string'
        },
        'body': json.dumps({
            'operation': 'webhook'
        })
    }
    
    context = Mock()
    context.aws_request_id = 'test-request-123'
    
    # Call handler
    response = lambda_handler(event, context)
    
    # Verify webhook verification response
    assert response['statusCode'] == 200
    assert response['body'] == 'challenge_string'


def test_whatsapp_message_processing():
    """Test WhatsApp incoming message processing."""
    from engine.handlers.handler_whatsapp import lambda_handler
    
    # Mock incoming message event
    event = {
        'body': json.dumps({
            'operation': 'webhook',
            'messages': [
                {
                    'from': '+1234567890',
                    'id': 'msg_123',
                    'text': {
                        'body': 'I need help with my website'
                    },
                    'timestamp': '1640995200'
                }
            ]
        })
    }
    
    context = Mock()
    context.aws_request_id = 'test-request-123'
    
    # Mock HubSpot client
    with patch('engine.handlers.handler_whatsapp.hubspot_client') as mock_hubspot:
        mock_hubspot.create_contact.return_value = {
            'success': True,
            'contact_id': 'contact_123'
        }
        
        # Call handler
        response = lambda_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['processed_messages'] == 1


def test_slack_integration_setup():
    """Test Slack integration setup."""
    from engine.handlers.handler_collaboration import lambda_handler
    
    # Mock event with Slack setup request
    event = {
        'body': json.dumps({
            'platform': 'slack',
            'operation': 'setup',
            'client_info': {
                'company': 'Test Company'
            },
            'admin_email': 'admin@testcompany.com',
            'webhook_url': 'https://api.example.com/slack/webhook'
        })
    }
    
    context = Mock()
    context.aws_request_id = 'test-request-123'
    
    # Call handler
    response = lambda_handler(event, context)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['success'] is True
    assert body['platform'] == 'slack'
    assert body['workspace_name'] == 'Test Company'
    assert 'slack_config' in body
    assert 'instructions' in body


def test_teams_integration_setup():
    """Test Microsoft Teams integration setup."""
    from engine.handlers.handler_collaboration import lambda_handler
    
    # Mock event with Teams setup request
    event = {
        'body': json.dumps({
            'platform': 'teams',
            'operation': 'setup',
            'client_info': {
                'company': 'Test Company'
            },
            'admin_email': 'admin@testcompany.com',
            'webhook_url': 'https://api.example.com/teams/webhook'
        })
    }
    
    context = Mock()
    context.aws_request_id = 'test-request-123'
    
    # Call handler
    response = lambda_handler(event, context)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['success'] is True
    assert body['platform'] == 'teams'
    assert body['organization_name'] == 'Test Company'
    assert 'teams_config' in body
    assert 'instructions' in body


def test_slack_webhook_challenge():
    """Test Slack webhook URL verification challenge."""
    from engine.handlers.handler_collaboration import _handle_slack_integration
    
    # Mock challenge request
    request_data = {
        'challenge': 'test_challenge_string'
    }
    
    # Call handler
    response = _handle_slack_integration('webhook', request_data)
    
    # Verify challenge response
    assert response['statusCode'] == 200
    assert response['body'] == 'test_challenge_string'


def test_slack_message_processing():
    """Test Slack message processing and lead capture."""
    from engine.handlers.handler_collaboration import _handle_slack_integration
    
    # Mock Slack message event
    request_data = {
        'event': {
            'type': 'message',
            'user': 'U123456',
            'text': 'I need a quote for website development',
            'channel': 'C123456'
        }
    }
    
    # Mock HubSpot client
    with patch('engine.handlers.handler_collaboration.hubspot_client') as mock_hubspot:
        mock_hubspot.create_contact.return_value = {
            'success': True,
            'contact_id': 'contact_123'
        }
        
        # Call handler
        response = _handle_slack_integration('webhook', request_data)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True


def test_slack_slash_command():
    """Test Slack slash command processing."""
    from engine.handlers.handler_collaboration import _process_slack_command
    
    # Mock slash command data
    command_data = {
        'command': '/dtl-help',
        'text': '',
        'user_id': 'U123456',
        'channel_id': 'C123456'
    }
    
    # Call command processor
    response = _process_slack_command(command_data)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert 'text' in body
    assert 'DTL-Global Services' in body['text']


def test_teams_manifest_structure():
    """Test Microsoft Teams app manifest structure."""
    from engine.handlers.handler_collaboration import _generate_teams_config
    
    organization_name = 'Test Organization'
    admin_email = 'admin@test.com'
    webhook_url = 'https://api.example.com/teams/webhook'
    
    config = _generate_teams_config(organization_name, admin_email, webhook_url)
    
    # Verify manifest structure
    assert 'manifest' in config
    manifest = config['manifest']
    
    # Verify required manifest fields
    assert '$schema' in manifest
    assert 'manifestVersion' in manifest
    assert 'version' in manifest
    assert 'id' in manifest
    assert 'name' in manifest
    assert 'developer' in manifest
    
    # Verify bots configuration
    assert 'bots' in config
    assert len(config['bots']) > 0
    
    # Verify permissions
    assert 'permissions' in config


def test_ai_chatbot_system_prompt():
    """Test AI chatbot system prompt generation."""
    from engine.handlers.handler_chatbot import _build_chatbot_system_prompt
    
    website_context = {
        'company_name': 'Test Company',
        'industry': 'Technology'
    }
    
    system_prompt = _build_chatbot_system_prompt(website_context)
    
    # Verify prompt contains required elements
    assert 'DTL-Global' in system_prompt
    assert 'Test Company' in system_prompt
    assert 'Technology' in system_prompt
    assert 'website development' in system_prompt
    assert 'CRM setup' in system_prompt


def test_lead_information_extraction():
    """Test AI lead information extraction."""
    from engine.shared.ai_client import AIClient
    
    # Mock Anthropic client
    with patch('engine.shared.ai_client.Anthropic') as mock_anthropic:
        # Mock response with extracted lead info
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '{"company": "ABC Corp", "email": "john@abccorp.com", "needs": "website development"}'
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        # Create AI client and test extraction
        ai_client = AIClient()
        
        message = "Hi, I'm John from ABC Corp and we need a new website. You can reach me at john@abccorp.com"
        result = ai_client.extract_lead_information(message)
        
        # Verify extraction results
        assert result is not None
        assert result['company'] == 'ABC Corp'
        assert result['email'] == 'john@abccorp.com'
        assert result['needs'] == 'website development'


def test_whatsapp_config_generation():
    """Test WhatsApp Business API configuration generation."""
    from engine.handlers.handler_whatsapp import _generate_whatsapp_config
    
    business_name = 'Test Business'
    phone_number = '+1234567890'
    webhook_url = 'https://api.example.com/webhook'
    
    config = _generate_whatsapp_config(business_name, phone_number, webhook_url)
    
    # Verify configuration structure
    assert 'business_profile' in config
    assert 'webhook_config' in config
    assert 'message_templates' in config
    assert 'integration_settings' in config
    
    # Verify business profile
    profile = config['business_profile']
    assert profile['name'] == business_name
    assert profile['phone_number'] == phone_number
    
    # Verify webhook configuration
    webhook = config['webhook_config']
    assert webhook['url'] == webhook_url
    assert 'verify_token' in webhook
    assert 'events' in webhook
    
    # Verify message templates
    templates = config['message_templates']
    assert len(templates) >= 2  # Should have welcome and reminder templates


def test_error_handling_invalid_json():
    """Test error handling for invalid JSON requests."""
    from engine.handlers.handler_chatbot import lambda_handler
    
    # Mock event with invalid JSON
    event = {
        'body': 'invalid json string'
    }
    
    context = Mock()
    context.aws_request_id = 'test-request-123'
    
    # Call handler
    response = lambda_handler(event, context)
    
    # Verify error response
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['success'] is False
    assert 'Invalid JSON' in body['error']


def test_error_handling_missing_required_fields():
    """Test error handling for missing required fields."""
    from engine.handlers.handler_workspace import lambda_handler
    
    # Mock event without required domain field
    event = {
        'body': json.dumps({
            'workspace_type': 'google',
            'admin_email': 'admin@test.com'
        })
    }
    
    context = Mock()
    context.aws_request_id = 'test-request-123'
    
    # Call handler
    response = lambda_handler(event, context)
    
    # Verify error response
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['success'] is False
    assert 'Domain is required' in body['error']


def test_cors_headers_present():
    """Test that CORS headers are present in all responses."""
    from engine.handlers.handler_chatbot import lambda_handler
    
    # Mock valid event
    event = {
        'body': json.dumps({
            'message': 'test message',
            'website_context': {}
        })
    }
    
    context = Mock()
    context.aws_request_id = 'test-request-123'
    
    # Mock AI client
    with patch('engine.handlers.handler_chatbot.ai_client') as mock_ai:
        mock_ai.generate_chatbot_response.return_value = 'Test response'
        
        # Call handler
        response = lambda_handler(event, context)
        
        # Verify CORS headers
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert response['headers']['Access-Control-Allow-Origin'] == '*'


if __name__ == '__main__':
    """Run all Phase 5 add-on module tests."""
    print("Running Phase 5: Add-On Modules Tests")
    print("=" * 50)
    
    # Test results tracking
    tests_run = 0
    tests_passed = 0
    
    # List of all test functions
    test_functions = [
        test_chatbot_handler_basic_conversation,
        test_chatbot_lead_capture,
        test_workspace_google_setup,
        test_workspace_dns_records_structure,
        test_whatsapp_setup,
        test_whatsapp_webhook_verification,
        test_whatsapp_message_processing,
        test_slack_integration_setup,
        test_teams_integration_setup,
        test_slack_webhook_challenge,
        test_slack_message_processing,
        test_slack_slash_command,
        test_teams_manifest_structure,
        test_ai_chatbot_system_prompt,
        test_lead_information_extraction,
        test_whatsapp_config_generation,
        test_error_handling_invalid_json,
        test_error_handling_missing_required_fields,
        test_cors_headers_present
    ]
    
    # Run each test
    for test_func in test_functions:
        tests_run += 1
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
            tests_passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: {str(e)}")
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {tests_run}")
    print(f"Tests passed: {tests_passed}")
    print(f"Tests failed: {tests_run - tests_passed}")
    print(f"Success rate: {(tests_passed/tests_run)*100:.1f}%")
    
    if tests_passed == tests_run:
        print("\n🎉 All Phase 5 add-on module tests passed!")
        print("✓ AI Chatbot with HubSpot lead capture")
        print("✓ Google Workspace email DNS configuration")
        print("✓ WhatsApp Business API integration")
        print("✓ Slack and Teams collaboration setup")
        print("✓ Error handling and CORS support")
    else:
        print(f"\n⚠️  {tests_run - tests_passed} tests failed. Review implementation.")
    
    print("\nPhase 5: Add-On Modules testing complete!")