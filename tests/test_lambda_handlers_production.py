#!/usr/bin/env python3
"""
Comprehensive unit tests for all Lambda handlers - Production Ready
Tests all 5 main API endpoints with proper parameter formats
"""

import json
import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'engine'))
sys.path.insert(0, os.path.join(project_root, 'engine', 'shared'))

class TestLambdaHandlersProduction(unittest.TestCase):
    """Production-ready tests for all Lambda handlers"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_client_info = {
            "company": "Business Center Solutions",
            "email": "aduarte@businesscentersolutions.net",
            "phone": "(816) 204-7169",
            "contact_name": "Alondra Duarte",
            "industry": "consulting",
            "package": "FREE_WEBSITE_DISCOUNTED",
            "setup_fee": 0,
            "monthly_fee": 20
        }
        
        self.sample_crm_config = {
            "pipeline": "dtl_onboarding",
            "stage": "Build Website",
            "deal_amount": 0,
            "monthly_value": 20
        }
        
        self.sample_deployment_config = {
            "domain": "businesscentersolutions.net",
            "github_repo": "https://github.com/tolkiger/businesscenter",
            "s3_bucket": "businesscentersolutions-net-website",
            "cloudfront_enabled": True
        }

    def test_crm_setup_handler_parameters(self):
        """Test CRM setup handler with correct parameters"""
        try:
            from engine.handlers.handler_crm_setup import lambda_handler
            
            event = {
                "client_info": self.sample_client_info,
                "crm_config": self.sample_crm_config
            }
            
            context = Mock()
            context.aws_request_id = "test-request-id"
            
            # Mock the HubSpot client import inside the handler
            with patch('hubspot_client.hubspot_client') as mock_hubspot:
                mock_hubspot.get_contact_by_email.return_value = None
                mock_hubspot.create_contact.return_value = {"id": "12345"}
                mock_hubspot.create_deal.return_value = {"id": "67890"}
                
                result = lambda_handler(event, context)
                
                # Should return success response
                self.assertEqual(result['statusCode'], 200)
                response_body = json.loads(result['body'])
                self.assertIn('contact_id', response_body)
                
        except ImportError as e:
            self.fail(f"Failed to import CRM handler: {e}")
        except Exception as e:
            # Log the actual error for debugging
            print(f"CRM Handler Error: {e}")
            self.fail(f"CRM handler failed with proper parameters: {e}")

    def test_deployment_handler_parameters(self):
        """Test deployment handler with correct parameters"""
        try:
            from engine.handlers.handler_deploy import lambda_handler
            
            event = {
                "client_info": self.sample_client_info,
                "deployment_config": self.sample_deployment_config
            }
            
            context = Mock()
            context.aws_request_id = "test-request-id"
            
            # Mock the AWS clients that are imported inside the handler
            with patch('s3_client.s3_client') as mock_s3, \
                 patch('route53_client.route53_client') as mock_route53, \
                 patch('ai_client.ai_client') as mock_ai:
                
                mock_s3.create_website_bucket.return_value = {"bucket_name": "test-bucket"}
                mock_route53.create_hosted_zone.return_value = {"zone_id": "Z123456789"}
                mock_ai.generate_website_content.return_value = {"content": "test content"}
                
                result = lambda_handler(event, context)
                
                # Should return success response
                self.assertEqual(result['statusCode'], 200)
                
        except ImportError as e:
            self.fail(f"Failed to import deployment handler: {e}")
        except Exception as e:
            print(f"Deployment Handler Error: {e}")
            self.fail(f"Deployment handler failed with proper parameters: {e}")

    def test_dns_handler_parameters(self):
        """Test DNS handler with correct parameters"""
        try:
            from engine.handlers.handler_dns import lambda_handler
            
            event = {
                "domain": "businesscentersolutions.net",
                "dns_config": {
                    "create_hosted_zone": True,
                    "ssl_certificate": True,
                    "cloudfront_alias": True
                }
            }
            
            context = Mock()
            context.aws_request_id = "test-request-id"
            
            # Mock Route53 client that is imported inside the handler
            with patch('route53_client.route53_client') as mock_route53:
                mock_route53.create_hosted_zone.return_value = {
                    "zone_id": "Z123456789",
                    "name_servers": ["ns1.example.com", "ns2.example.com"]
                }
                
                result = lambda_handler(event, context)
                
                # Should return success response
                self.assertEqual(result['statusCode'], 200)
                
        except ImportError as e:
            self.fail(f"Failed to import DNS handler: {e}")
        except Exception as e:
            print(f"DNS Handler Error: {e}")
            self.fail(f"DNS handler failed with proper parameters: {e}")

    def test_subscription_handler_parameters(self):
        """Test subscription handler with correct parameters"""
        try:
            from engine.handlers.handler_subscribe import lambda_handler
            
            event = {
                "action": "create",
                "client_info": self.sample_client_info,
                "subscription_config": {
                    "product_name": "DTL-Global Free Website + Discounted Maintenance",
                    "price": 20,
                    "currency": "usd",
                    "interval": "month"
                }
            }
            
            context = Mock()
            context.aws_request_id = "test-request-id"
            
            # Mock Stripe and SES clients that are imported inside the handler
            with patch('stripe_client.stripe_client') as mock_stripe, \
                 patch('ses_client.ses_client') as mock_ses:
                
                mock_stripe.create_customer.return_value = {"id": "cus_123456"}
                mock_stripe.create_subscription.return_value = {"id": "sub_123456"}
                mock_ses.send_email.return_value = {"MessageId": "msg_123456"}
                
                result = lambda_handler(event, context)
                
                # Should return success response
                self.assertEqual(result['statusCode'], 200)
                
        except ImportError as e:
            self.fail(f"Failed to import subscription handler: {e}")
        except Exception as e:
            print(f"Subscription Handler Error: {e}")
            self.fail(f"Subscription handler failed with proper parameters: {e}")

    def test_notification_handler_parameters(self):
        """Test notification handler with correct parameters"""
        try:
            from engine.handlers.handler_notify import lambda_handler
            
            event = {
                "client_info": self.sample_client_info,
                "notification_type": "welcome",
                "notification_config": {
                    "email_type": "welcome",
                    "template": "onboarding_welcome",
                    "send_dns_instructions": True
                }
            }
            
            context = Mock()
            context.aws_request_id = "test-request-id"
            
            # Mock SES client that is imported inside the handler
            with patch('ses_client.ses_client') as mock_ses:
                mock_ses.send_onboarding_welcome.return_value = {"MessageId": "msg_123456"}
                
                result = lambda_handler(event, context)
                
                # Should return success response
                self.assertEqual(result['statusCode'], 200)
                
        except ImportError as e:
            self.fail(f"Failed to import notification handler: {e}")
        except Exception as e:
            print(f"Notification Handler Error: {e}")
            self.fail(f"Notification handler failed with proper parameters: {e}")

    def test_parameter_validation(self):
        """Test that handlers properly validate required parameters"""
        # Test missing email in client_info
        invalid_client_info = self.sample_client_info.copy()
        del invalid_client_info['email']
        
        try:
            from engine.handlers.handler_crm_setup import lambda_handler
            
            event = {
                "client_info": invalid_client_info,
                "crm_config": self.sample_crm_config
            }
            
            context = Mock()
            context.aws_request_id = "test-request-id"
            
            # Mock HubSpot client
            with patch('hubspot_client.hubspot_client') as mock_hubspot:
                result = lambda_handler(event, context)
                
                # Should return error for missing email
                self.assertEqual(result['statusCode'], 400)
                response_body = json.loads(result['body'])
                self.assertIn('email', response_body['error'].lower())
            
        except Exception as e:
            # This is expected for validation errors
            self.assertIn('email', str(e).lower())

if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)