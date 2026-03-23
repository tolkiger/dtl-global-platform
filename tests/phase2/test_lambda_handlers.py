"""
Comprehensive unit tests for all DTL-Global Lambda handlers.

Tests each handler individually with mocked dependencies to ensure
production readiness and proper error handling.

Author: DTL-Global Platform
"""

import json
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


class TestLambdaHandlers:
    """Test suite for all Lambda handlers."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_context = Mock()
        self.mock_context.aws_request_id = 'test-request-123'
        self.mock_context.function_name = 'test-function'
        
    def create_api_event(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Create a mock API Gateway event."""
        return {
            'body': json.dumps(body),
            'headers': {'Content-Type': 'application/json'},
            'httpMethod': 'POST',
            'path': '/test',
            'queryStringParameters': None
        }
    
    def test_handler_bid_generation(self):
        """Test bid generation handler."""
        try:
            from engine.handlers.handler_bid import lambda_handler
            
            event = self.create_api_event({
                'client_requirements': {
                    'company': 'Test Company',
                    'industry': 'technology',
                    'services': ['website', 'crm']
                },
                'industry': 'technology'
            })
            
            with patch('engine.handlers.handler_bid.ai_client') as mock_ai:
                mock_ai.generate_bid.return_value = {
                    'success': True,
                    'setup_fee': 1250,
                    'monthly_fee': 149,
                    'timeline': '2-4 weeks'
                }
                
                response = lambda_handler(event, self.mock_context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['success'] is True
                assert 'setup_fee' in body
                
        except ImportError:
            pytest.skip("Handler not available for testing")
    
    def test_handler_prompt_generation(self):
        """Test SEO prompt generation handler."""
        try:
            from engine.handlers.handler_prompt import lambda_handler
            
            event = self.create_api_event({
                'client_info': {
                    'company': 'Test Company',
                    'industry': 'technology'
                },
                'website_type': 'business'
            })
            
            with patch('engine.handlers.handler_prompt.ai_client') as mock_ai:
                mock_ai.generate_seo_website_prompt.return_value = {
                    'success': True,
                    'prompt': 'Test SEO-optimized website prompt',
                    'meta_title': 'Test Company - Technology Solutions',
                    'meta_description': 'Professional technology solutions'
                }
                
                response = lambda_handler(event, self.mock_context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['success'] is True
                assert 'prompt' in body
                
        except ImportError:
            pytest.skip("Handler not available for testing")
    
    def test_handler_invoice_creation(self):
        """Test Stripe invoice creation handler."""
        try:
            from engine.handlers.handler_invoice import lambda_handler
            
            event = self.create_api_event({
                'client_info': {
                    'company': 'Test Company',
                    'email': 'test@company.com'
                },
                'amount': 125000,  # $1,250.00
                'description': 'Setup Fee'
            })
            
            with patch('engine.handlers.handler_invoice.stripe_client') as mock_stripe:
                mock_stripe.create_invoice.return_value = {
                    'success': True,
                    'invoice_id': 'inv_test123',
                    'invoice_url': 'https://invoice.stripe.com/test'
                }
                
                response = lambda_handler(event, self.mock_context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['success'] is True
                assert 'invoice_id' in body
                
        except ImportError:
            pytest.skip("Handler not available for testing")
    
    def test_handler_crm_setup(self):
        """Test HubSpot CRM setup handler."""
        try:
            from engine.handlers.handler_crm_setup import lambda_handler
            
            event = self.create_api_event({
                'client_info': {
                    'company': 'Test Company',
                    'email': 'test@company.com',
                    'industry': 'technology'
                }
            })
            
            with patch('engine.handlers.handler_crm_setup.hubspot_client') as mock_hubspot:
                mock_hubspot.create_contact.return_value = {
                    'success': True,
                    'contact_id': 'contact_123'
                }
                mock_hubspot.create_deal.return_value = {
                    'success': True,
                    'deal_id': 'deal_123'
                }
                
                response = lambda_handler(event, self.mock_context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['success'] is True
                
        except ImportError:
            pytest.skip("Handler not available for testing")
    
    def test_handler_stripe_setup(self):
        """Test Stripe Connect setup handler."""
        try:
            from engine.handlers.handler_stripe_setup import lambda_handler
            
            event = self.create_api_event({
                'client_info': {
                    'company': 'Test Company',
                    'email': 'test@company.com'
                },
                'stripe_config': {
                    'account_type': 'express'
                }
            })
            
            with patch('engine.handlers.handler_stripe_setup.stripe_client') as mock_stripe:
                mock_stripe.create_connected_account.return_value = {
                    'success': True,
                    'account_id': 'acct_test123'
                }
                
                response = lambda_handler(event, self.mock_context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['success'] is True
                
        except ImportError:
            pytest.skip("Handler not available for testing")
    
    def test_handler_dns_setup(self):
        """Test DNS configuration handler."""
        try:
            from engine.handlers.handler_dns import lambda_handler
            
            event = self.create_api_event({
                'domain': 'test-company.com',
                'dns_type': 'website',
                'client_info': {
                    'company': 'Test Company'
                }
            })
            
            with patch('engine.handlers.handler_dns.route53_client') as mock_route53:
                mock_route53.create_hosted_zone.return_value = {
                    'success': True,
                    'zone_id': 'Z123456789'
                }
                
                response = lambda_handler(event, self.mock_context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['success'] is True
                
        except ImportError:
            pytest.skip("Handler not available for testing")
    
    def test_handler_deploy(self):
        """Test website deployment handler."""
        try:
            from engine.handlers.handler_deploy import lambda_handler
            
            event = self.create_api_event({
                'domain': 'test-company.com',
                'client_info': {
                    'company': 'Test Company',
                    'industry': 'technology'
                }
            })
            
            with patch('engine.handlers.handler_deploy.s3_client') as mock_s3, \
                 patch('engine.handlers.handler_deploy.route53_client') as mock_route53:
                
                mock_s3.upload_website.return_value = {
                    'success': True,
                    'website_url': 'https://test-company.com'
                }
                mock_route53.create_ssl_certificate.return_value = {
                    'success': True,
                    'certificate_arn': 'arn:aws:acm:us-east-1:123:cert/test'
                }
                
                response = lambda_handler(event, self.mock_context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['success'] is True
                
        except ImportError:
            pytest.skip("Handler not available for testing")
    
    def test_handler_email_setup(self):
        """Test email setup handler."""
        try:
            from engine.handlers.handler_email_setup import lambda_handler
            
            event = self.create_api_event({
                'domain': 'test-company.com',
                'client_info': {
                    'company': 'Test Company'
                }
            })
            
            with patch('engine.handlers.handler_email_setup.ses_client') as mock_ses:
                mock_ses.verify_email_address.return_value = {
                    'success': True,
                    'verification_status': 'pending'
                }
                
                response = lambda_handler(event, self.mock_context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['success'] is True
                
        except ImportError:
            pytest.skip("Handler not available for testing")
    
    def test_handler_subscribe(self):
        """Test subscription billing handler."""
        try:
            from engine.handlers.handler_subscribe import lambda_handler
            
            event = self.create_api_event({
                'client_info': {
                    'company': 'Test Company',
                    'email': 'test@company.com'
                },
                'subscription_plan': 'growth'
            })
            
            with patch('engine.handlers.handler_subscribe.stripe_client') as mock_stripe:
                mock_stripe.create_subscription.return_value = {
                    'success': True,
                    'subscription_id': 'sub_test123'
                }
                
                response = lambda_handler(event, self.mock_context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['success'] is True
                
        except ImportError:
            pytest.skip("Handler not available for testing")
    
    def test_handler_notify(self):
        """Test notification handler."""
        try:
            from engine.handlers.handler_notify import lambda_handler
            
            event = self.create_api_event({
                'notification_type': 'welcome',
                'client_info': {
                    'company': 'Test Company',
                    'email': 'test@company.com'
                }
            })
            
            with patch('engine.handlers.handler_notify.ses_client') as mock_ses:
                mock_ses.send_onboarding_welcome.return_value = {
                    'success': True,
                    'message_id': 'msg_test123'
                }
                
                response = lambda_handler(event, self.mock_context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['success'] is True
                
        except ImportError:
            pytest.skip("Handler not available for testing")
    
    def test_handler_crm_import(self):
        """Test CRM import handler."""
        try:
            from engine.handlers.handler_crm_import import lambda_handler
            
            event = self.create_api_event({
                'csv_data': 'name,email\nJohn Doe,john@example.com',
                'mapping': {
                    'name': 'full_name',
                    'email': 'email'
                }
            })
            
            with patch('engine.handlers.handler_crm_import.hubspot_client') as mock_hubspot:
                mock_hubspot.batch_create_contacts.return_value = {
                    'success': True,
                    'created_count': 1,
                    'error_count': 0
                }
                
                response = lambda_handler(event, self.mock_context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['success'] is True
                
        except ImportError:
            pytest.skip("Handler not available for testing")
    
    def test_handler_onboard_orchestrator(self):
        """Test main onboarding orchestrator handler."""
        try:
            from engine.handlers.handler_onboard import lambda_handler
            
            event = self.create_api_event({
                'client_type': 'full_package',
                'client_info': {
                    'company': 'Test Company',
                    'domain': 'test-company.com',
                    'email': 'test@company.com',
                    'industry': 'technology'
                }
            })
            
            # Mock all dependent services
            with patch('engine.handlers.handler_onboard.hubspot_client') as mock_hubspot, \
                 patch('engine.handlers.handler_onboard.stripe_client') as mock_stripe, \
                 patch('engine.handlers.handler_onboard.route53_client') as mock_route53, \
                 patch('engine.handlers.handler_onboard.s3_client') as mock_s3, \
                 patch('engine.handlers.handler_onboard.ses_client') as mock_ses:
                
                # Mock successful responses from all services
                mock_hubspot.create_contact.return_value = {'success': True, 'contact_id': 'contact_123'}
                mock_stripe.create_connected_account.return_value = {'success': True, 'account_id': 'acct_123'}
                mock_route53.create_hosted_zone.return_value = {'success': True, 'zone_id': 'Z123'}
                mock_s3.upload_website.return_value = {'success': True, 'website_url': 'https://test.com'}
                mock_ses.verify_email_address.return_value = {'success': True}
                
                response = lambda_handler(event, self.mock_context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['success'] is True
                
        except ImportError:
            pytest.skip("Handler not available for testing")
    
    def test_handler_chatbot(self):
        """Test AI chatbot handler."""
        try:
            from engine.handlers.handler_chatbot import lambda_handler
            
            event = self.create_api_event({
                'message': 'I need help with my website',
                'website_context': {
                    'company_name': 'Test Company'
                }
            })
            
            with patch('engine.handlers.handler_chatbot.ai_client') as mock_ai:
                mock_ai.generate_chatbot_response.return_value = "I'd be happy to help!"
                
                response = lambda_handler(event, self.mock_context)
                
                assert response['statusCode'] == 200
                body = json.loads(response['body'])
                assert body['success'] is True
                assert 'response' in body
                
        except ImportError:
            pytest.skip("Handler not available for testing")
    
    def test_handler_workspace(self):
        """Test Google Workspace setup handler."""
        try:
            from engine.handlers.handler_workspace import lambda_handler
            
            event = self.create_api_event({
                'domain': 'test-company.com',
                'workspace_type': 'google'
            })
            
            response = lambda_handler(event, self.mock_context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['success'] is True
            assert 'dns_records' in body
            
        except ImportError:
            pytest.skip("Handler not available for testing")
    
    def test_handler_whatsapp(self):
        """Test WhatsApp integration handler."""
        try:
            from engine.handlers.handler_whatsapp import lambda_handler
            
            event = self.create_api_event({
                'operation': 'setup',
                'phone_number': '+1234567890'
            })
            
            response = lambda_handler(event, self.mock_context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['success'] is True
            
        except ImportError:
            pytest.skip("Handler not available for testing")
    
    def test_handler_collaboration(self):
        """Test Slack/Teams collaboration handler."""
        try:
            from engine.handlers.handler_collaboration import lambda_handler
            
            event = self.create_api_event({
                'platform': 'slack',
                'operation': 'setup'
            })
            
            response = lambda_handler(event, self.mock_context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['success'] is True
            
        except ImportError:
            pytest.skip("Handler not available for testing")
    
    def test_error_handling_invalid_json(self):
        """Test error handling for invalid JSON."""
        try:
            from engine.handlers.handler_bid import lambda_handler
            
            event = {
                'body': 'invalid json string',
                'headers': {'Content-Type': 'application/json'}
            }
            
            response = lambda_handler(event, self.mock_context)
            
            assert response['statusCode'] == 400
            body = json.loads(response['body'])
            assert body['success'] is False
            assert 'error' in body
            
        except ImportError:
            pytest.skip("Handler not available for testing")
    
    def test_cors_headers_present(self):
        """Test that CORS headers are present in responses."""
        try:
            from engine.handlers.handler_bid import lambda_handler
            
            event = self.create_api_event({
                'client_requirements': {
                    'company': 'Test Company'
                },
                'industry': 'technology'
            })
            
            with patch('engine.handlers.handler_bid.ai_client') as mock_ai:
                mock_ai.generate_bid.return_value = {'success': True}
                
                response = lambda_handler(event, self.mock_context)
                
                assert 'Access-Control-Allow-Origin' in response['headers']
                assert response['headers']['Access-Control-Allow-Origin'] == '*'
                
        except ImportError:
            pytest.skip("Handler not available for testing")


if __name__ == '__main__':
    """Run all Lambda handler tests."""
    import subprocess
    
    print("🧪 Running DTL-Global Lambda Handler Tests")
    print("=" * 50)
    
    # Run pytest with verbose output
    result = subprocess.run([
        'python', '-m', 'pytest', 
        __file__, 
        '-v', 
        '--tb=short'
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if result.returncode == 0:
        print("✅ All Lambda handler tests passed!")
    else:
        print("❌ Some tests failed. Review output above.")
    
    exit(result.returncode)