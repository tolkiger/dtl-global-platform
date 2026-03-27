"""Tests for handler_webhook.py - Stripe webhook processing."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import the handler module
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'engine', 'handlers'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'engine', 'shared'))

from handler_webhook import lambda_handler, _handle_invoice_paid, _handle_subscription_deleted


class TestWebhookHandler:
    """Test cases for Stripe webhook handler."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Mock Lambda context
        self.context = Mock()
        self.context.aws_request_id = 'test-request-123'
        
        # Mock Stripe webhook event
        self.mock_invoice_event = {
            'type': 'invoice.paid',
            'data': {
                'object': {
                    'customer': 'cus_test123',
                    'amount_paid': 50000  # $500.00 in cents
                }
            }
        }
        
        self.mock_subscription_event = {
            'type': 'customer.subscription.deleted',
            'data': {
                'object': {
                    'customer': 'cus_test123'
                }
            }
        }
    
    @patch('handler_webhook.config.get_secret')
    @patch('handler_webhook.stripe.Webhook.construct_event')
    @patch('handler_webhook._handle_invoice_paid')
    def test_invoice_paid_webhook_success(self, mock_handle_invoice, mock_construct_event, mock_get_secret):
        """Test successful processing of invoice.paid webhook."""
        # Arrange
        mock_get_secret.return_value = 'whsec_test_secret'
        mock_construct_event.return_value = self.mock_invoice_event
        mock_handle_invoice.return_value = {
            'success': True,
            'message': 'Deal advanced successfully',
            'deal_id': '12345'
        }
        
        event = {
            'body': json.dumps({'test': 'payload'}),
            'headers': {'stripe-signature': 'test-signature'}
        }
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert response_body['success'] is True
        assert 'Deal advanced successfully' in response_body['message']
        
        # Verify webhook validation was called
        mock_construct_event.assert_called_once()
        mock_handle_invoice.assert_called_once()
    
    @patch('handler_webhook.config.get_secret')
    @patch('handler_webhook.stripe.Webhook.construct_event')
    @patch('handler_webhook._handle_subscription_deleted')
    def test_subscription_deleted_webhook_success(self, mock_handle_subscription, mock_construct_event, mock_get_secret):
        """Test successful processing of customer.subscription.deleted webhook."""
        # Arrange
        mock_get_secret.return_value = 'whsec_test_secret'
        mock_construct_event.return_value = self.mock_subscription_event
        mock_handle_subscription.return_value = {
            'success': True,
            'message': 'Deal moved to Churned',
            'deal_id': '12345'
        }
        
        event = {
            'body': json.dumps({'test': 'payload'}),
            'headers': {'stripe-signature': 'test-signature'}
        }
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert response_body['success'] is True
        assert 'Deal moved to Churned' in response_body['message']
        
        # Verify webhook validation was called
        mock_construct_event.assert_called_once()
        mock_handle_subscription.assert_called_once()
    
    @patch('handler_webhook.config.get_secret')
    @patch('handler_webhook.stripe.Webhook.construct_event')
    def test_invalid_signature_rejection(self, mock_construct_event, mock_get_secret):
        """Test rejection of webhook with invalid signature."""
        # Arrange
        mock_get_secret.return_value = 'whsec_test_secret'
        import stripe
        mock_construct_event.side_effect = stripe.error.SignatureVerificationError(
            'Invalid signature', 'test-signature'
        )
        
        event = {
            'body': json.dumps({'test': 'payload'}),
            'headers': {'stripe-signature': 'invalid-signature'}
        }
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response['statusCode'] == 400
        response_body = json.loads(response['body'])
        assert response_body['success'] is False
        assert 'Invalid webhook signature' in response_body['error']
    
    @patch('handler_webhook.config.get_secret')
    @patch('handler_webhook.stripe.Webhook.construct_event')
    def test_unknown_event_type_handling(self, mock_construct_event, mock_get_secret):
        """Test handling of unknown webhook event types."""
        # Arrange
        mock_get_secret.return_value = 'whsec_test_secret'
        unknown_event = {
            'type': 'unknown.event.type',
            'data': {'object': {}}
        }
        mock_construct_event.return_value = unknown_event
        
        event = {
            'body': json.dumps({'test': 'payload'}),
            'headers': {'stripe-signature': 'test-signature'}
        }
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert response_body['success'] is True
        assert 'not handled' in response_body['message']
    
    def test_missing_webhook_payload(self):
        """Test error handling when webhook payload is missing."""
        # Arrange
        event = {'headers': {'stripe-signature': 'test-signature'}}
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response['statusCode'] == 400
        response_body = json.loads(response['body'])
        assert response_body['success'] is False
        assert 'Missing webhook payload' in response_body['error']
    
    def test_missing_signature_header(self):
        """Test error handling when signature header is missing."""
        # Arrange
        event = {'body': json.dumps({'test': 'payload'})}
        
        # Act
        response = lambda_handler(event, self.context)
        
        # Assert
        assert response['statusCode'] == 400
        response_body = json.loads(response['body'])
        assert response_body['success'] is False
        assert 'Missing webhook payload or signature' in response_body['error']


class TestInvoicePaidHandler:
    """Test cases for invoice.paid event handling."""
    
    @patch('handler_webhook._get_client_by_stripe_id')
    @patch('handler_webhook._get_deal_stage')
    @patch('handler_webhook._update_deal_stage')
    @patch('handler_webhook._send_slack_notification')
    def test_invoice_paid_contract_deposit(self, mock_slack, mock_update_stage, mock_get_stage, mock_get_client):
        """Test invoice.paid advancing from Contract & Deposit to Build Website."""
        # Arrange
        invoice_data = {'customer': 'cus_test123', 'amount_paid': 50000}
        mock_get_client.return_value = {
            'hubspot_deal_id': '12345',
            'company': 'Test Company'
        }
        mock_get_stage.return_value = 'Contract & Deposit'
        mock_update_stage.return_value = True
        
        # Act
        result = _handle_invoice_paid(invoice_data)
        
        # Assert
        assert result['success'] is True
        assert result['new_stage'] == 'Build Website'
        assert result['previous_stage'] == 'Contract & Deposit'
        mock_update_stage.assert_called_once_with('12345', 'Build Website')
        mock_slack.assert_called_once()
    
    @patch('handler_webhook._get_client_by_stripe_id')
    @patch('handler_webhook._get_deal_stage')
    @patch('handler_webhook._update_deal_stage')
    @patch('handler_webhook._send_slack_notification')
    def test_invoice_paid_final_payment(self, mock_slack, mock_update_stage, mock_get_stage, mock_get_client):
        """Test invoice.paid advancing from Final Payment to Live & Monthly."""
        # Arrange
        invoice_data = {'customer': 'cus_test123', 'amount_paid': 50000}
        mock_get_client.return_value = {
            'hubspot_deal_id': '12345',
            'company': 'Test Company'
        }
        mock_get_stage.return_value = 'Final Payment'
        mock_update_stage.return_value = True
        
        # Act
        result = _handle_invoice_paid(invoice_data)
        
        # Assert
        assert result['success'] is True
        assert result['new_stage'] == 'Live & Monthly'
        assert result['previous_stage'] == 'Final Payment'
        mock_update_stage.assert_called_once_with('12345', 'Live & Monthly')
        mock_slack.assert_called_once()
    
    @patch('handler_webhook._get_client_by_stripe_id')
    def test_invoice_paid_client_not_found(self, mock_get_client):
        """Test invoice.paid when client is not found in DynamoDB."""
        # Arrange
        invoice_data = {'customer': 'cus_unknown'}
        mock_get_client.return_value = None
        
        # Act
        result = _handle_invoice_paid(invoice_data)
        
        # Assert
        assert result['success'] is False
        assert 'Client not found' in result['message']
    
    def test_invoice_paid_missing_customer_id(self):
        """Test invoice.paid with missing customer ID."""
        # Arrange
        invoice_data = {}
        
        # Act
        result = _handle_invoice_paid(invoice_data)
        
        # Assert
        assert result['success'] is False
        assert 'No customer ID' in result['message']


class TestSubscriptionDeletedHandler:
    """Test cases for customer.subscription.deleted event handling."""
    
    @patch('handler_webhook._get_client_by_stripe_id')
    @patch('handler_webhook._update_deal_stage')
    @patch('handler_webhook._send_slack_notification')
    def test_subscription_deleted_success(self, mock_slack, mock_update_stage, mock_get_client):
        """Test successful subscription deletion handling."""
        # Arrange
        subscription_data = {'customer': 'cus_test123'}
        mock_get_client.return_value = {
            'hubspot_deal_id': '12345',
            'company': 'Test Company'
        }
        mock_update_stage.return_value = True
        
        # Act
        result = _handle_subscription_deleted(subscription_data)
        
        # Assert
        assert result['success'] is True
        assert result['new_stage'] == 'Churned'
        mock_update_stage.assert_called_once_with('12345', 'Churned')
        mock_slack.assert_called_once()
    
    @patch('handler_webhook._get_client_by_stripe_id')
    def test_subscription_deleted_client_not_found(self, mock_get_client):
        """Test subscription deletion when client is not found."""
        # Arrange
        subscription_data = {'customer': 'cus_unknown'}
        mock_get_client.return_value = None
        
        # Act
        result = _handle_subscription_deleted(subscription_data)
        
        # Assert
        assert result['success'] is False
        assert 'Client not found' in result['message']
    
    def test_subscription_deleted_missing_customer_id(self):
        """Test subscription deletion with missing customer ID."""
        # Arrange
        subscription_data = {}
        
        # Act
        result = _handle_subscription_deleted(subscription_data)
        
        # Assert
        assert result['success'] is False
        assert 'No customer ID' in result['message']


if __name__ == '__main__':
    pytest.main([__file__])