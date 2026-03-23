#!/usr/bin/env python3
"""Tests for DTL-Global Platform shared configuration module.

Tests verify configuration management, SSM parameter handling,
and client type validation functionality.

Per DTL_MASTER_PLAN.md Phase 2 testing requirements
Per Rule 002: Every line commented for Gerardo's understanding
Per Rule 009: Error handling with try/except blocks
"""

from __future__ import annotations

import os  # Environment variable manipulation for testing
import unittest  # Python unit testing framework
from unittest.mock import Mock, patch, MagicMock  # Mocking for AWS service calls
from botocore.exceptions import ClientError  # AWS API error simulation

# Import the module under test
from engine.shared.config import (  # Configuration module components
    ConfigManager,  # Main configuration manager class
    SSM_PARAMS,  # SSM parameter path constants
    CLIENT_TYPES,  # Client type definitions
    DYNAMODB_TABLES,  # DynamoDB table name mappings
    S3_BUCKETS,  # S3 bucket name patterns
    get_lambda_env_vars,  # Lambda environment variable function
    get_all_client_types,  # Client type listing function
    is_service_required,  # Service requirement checker
    config  # Global configuration instance
)


class TestConfigManager(unittest.TestCase):
    """Test suite for ConfigManager class functionality."""

    def setUp(self) -> None:
        """Set up test environment before each test method.
        
        Creates fresh ConfigManager instance and mocks for AWS services.
        Called before each test method execution.
        """
        # Create fresh ConfigManager instance for each test
        self.config_manager = ConfigManager()  # New instance to avoid state pollution
        
        # Clear any cached values from previous tests
        self.config_manager._secrets_cache = {}  # Reset secrets cache
        self.config_manager._account_id = None  # Reset account ID cache

    @patch('engine.shared.config.boto3.client')  # Mock boto3 client creation
    def test_get_secret_success(self, mock_boto3_client: Mock) -> None:
        """Test successful secret retrieval from SSM Parameter Store.
        
        Verifies that secrets are retrieved, cached, and returned correctly.
        """
        # Set up mock SSM client response
        mock_ssm_client = Mock()  # Mock SSM client instance
        mock_boto3_client.return_value = mock_ssm_client  # Return mock when boto3.client() called
        
        # Configure mock response for get_parameter call
        mock_response = {  # Simulated SSM API response
            'Parameter': {  # Parameter data structure
                'Value': 'test-secret-value'  # Decrypted parameter value
            }  # End parameter structure
        }  # End mock response
        mock_ssm_client.get_parameter.return_value = mock_response  # Set mock return value
        
        # Create new ConfigManager to use mocked client
        config_manager = ConfigManager()  # Fresh instance with mocked boto3
        
        # Test secret retrieval
        result = config_manager.get_secret("hubspot_token")  # Get HubSpot token from SSM
        
        # Verify correct SSM API call was made
        mock_ssm_client.get_parameter.assert_called_once_with(  # Verify API call parameters
            Name="/dtl-global-platform/hubspot/token",  # Correct SSM parameter path
            WithDecryption=True  # Decrypt SecureString parameters
        )  # End API call verification
        
        # Verify returned value is correct
        self.assertEqual(result, 'test-secret-value')  # Check returned secret value
        
        # Verify value is cached for subsequent calls
        self.assertEqual(  # Check cache contains the secret
            config_manager._secrets_cache["hubspot_token"],  # Cached value
            'test-secret-value'  # Expected value
        )  # End cache verification

    @patch('engine.shared.config.boto3.client')  # Mock boto3 client creation
    def test_get_secret_parameter_not_found(self, mock_boto3_client: Mock) -> None:
        """Test handling of missing SSM parameters.
        
        Verifies that appropriate errors are raised when parameters don't exist.
        """
        # Set up mock SSM client to raise ParameterNotFound error
        mock_ssm_client = Mock()  # Mock SSM client instance
        mock_boto3_client.return_value = mock_ssm_client  # Return mock when boto3.client() called
        
        # Configure mock to raise ParameterNotFound error
        error_response = {  # AWS error response structure
            'Error': {  # Error details
                'Code': 'ParameterNotFound',  # AWS error code
                'Message': 'Parameter not found'  # Error message
            }  # End error details
        }  # End error response
        mock_ssm_client.get_parameter.side_effect = ClientError(  # Raise ClientError
            error_response, 'GetParameter'  # Error response and operation name
        )  # End ClientError configuration
        
        # Create new ConfigManager to use mocked client
        config_manager = ConfigManager()  # Fresh instance with mocked boto3
        
        # Test that RuntimeError is raised for missing parameter
        with self.assertRaises(RuntimeError) as context:  # Expect RuntimeError to be raised
            config_manager.get_secret("hubspot_token")  # Try to get non-existent parameter
        
        # Verify error message contains helpful information
        self.assertIn("SSM parameter not found", str(context.exception))  # Check error message
        self.assertIn("/dtl-global-platform/hubspot/token", str(context.exception))  # Check parameter path
        self.assertIn("setup_ssm_parameters.py", str(context.exception))  # Check setup script reference

    def test_get_secret_invalid_name(self) -> None:
        """Test handling of invalid secret names.
        
        Verifies that ValueError is raised for unknown secret names.
        """
        # Test with invalid secret name
        with self.assertRaises(ValueError) as context:  # Expect ValueError to be raised
            self.config_manager.get_secret("invalid_secret_name")  # Try to get unknown secret
        
        # Verify error message is descriptive
        self.assertIn("Unknown secret name", str(context.exception))  # Check error message
        self.assertIn("invalid_secret_name", str(context.exception))  # Check secret name in error

    @patch('engine.shared.config.boto3.client')  # Mock boto3 client creation
    def test_get_account_id_success(self, mock_boto3_client: Mock) -> None:
        """Test successful AWS account ID retrieval.
        
        Verifies that account ID is retrieved from STS and cached.
        """
        # Set up mock STS client response
        mock_sts_client = Mock()  # Mock STS client instance
        mock_boto3_client.return_value = mock_sts_client  # Return mock when boto3.client() called
        
        # Configure mock response for get_caller_identity call
        mock_response = {  # Simulated STS API response
            'Account': '123456789012'  # AWS account ID
        }  # End mock response
        mock_sts_client.get_caller_identity.return_value = mock_response  # Set mock return value
        
        # Create new ConfigManager to use mocked client
        config_manager = ConfigManager()  # Fresh instance with mocked boto3
        
        # Test account ID retrieval
        result = config_manager.get_account_id()  # Get AWS account ID from STS
        
        # Verify correct STS API call was made
        mock_sts_client.get_caller_identity.assert_called_once()  # Verify API call made
        
        # Verify returned value is correct
        self.assertEqual(result, '123456789012')  # Check returned account ID
        
        # Verify value is cached for subsequent calls
        self.assertEqual(config_manager._account_id, '123456789012')  # Check cached value

    def test_get_s3_bucket_name_success(self) -> None:
        """Test successful S3 bucket name generation.
        
        Verifies that bucket names are formatted with account ID correctly.
        """
        # Mock the get_account_id method to return test account ID
        with patch.object(self.config_manager, 'get_account_id', return_value='123456789012'):  # Mock account ID
            # Test bucket name generation for each bucket type
            websites_bucket = self.config_manager.get_s3_bucket_name('websites')  # Get websites bucket name
            assets_bucket = self.config_manager.get_s3_bucket_name('assets')  # Get assets bucket name
            csv_bucket = self.config_manager.get_s3_bucket_name('csv_imports')  # Get CSV imports bucket name
            
            # Verify bucket names are formatted correctly
            self.assertEqual(websites_bucket, 'dtl-client-websites-123456789012')  # Check websites bucket
            self.assertEqual(assets_bucket, 'dtl-assets-123456789012')  # Check assets bucket
            self.assertEqual(csv_bucket, 'dtl-csv-imports-123456789012')  # Check CSV bucket

    def test_get_s3_bucket_name_invalid_type(self) -> None:
        """Test handling of invalid bucket types.
        
        Verifies that ValueError is raised for unknown bucket types.
        """
        # Test with invalid bucket type
        with self.assertRaises(ValueError) as context:  # Expect ValueError to be raised
            self.config_manager.get_s3_bucket_name('invalid_bucket_type')  # Try to get unknown bucket
        
        # Verify error message is descriptive
        self.assertIn("Unknown bucket type", str(context.exception))  # Check error message
        self.assertIn("invalid_bucket_type", str(context.exception))  # Check bucket type in error

    def test_get_client_services_success(self) -> None:
        """Test successful client service retrieval.
        
        Verifies that correct services are returned for each client type.
        """
        # Test each client type returns correct services
        full_services = self.config_manager.get_client_services('full_package')  # Get full package services
        website_services = self.config_manager.get_client_services('website_only')  # Get website-only services
        crm_services = self.config_manager.get_client_services('website_crm')  # Get website+CRM services
        payments_services = self.config_manager.get_client_services('crm_payments')  # Get CRM+payments services
        
        # Verify correct services are returned (per DTL_MASTER_PLAN.md Section 6.1)
        self.assertEqual(full_services, ["dns", "website", "crm", "stripe", "email", "notify"])  # Full package
        self.assertEqual(website_services, ["dns", "website", "email_optional", "notify"])  # Website only
        self.assertEqual(crm_services, ["dns", "website", "crm", "notify"])  # Website + CRM
        self.assertEqual(payments_services, ["crm", "stripe", "notify"])  # CRM + payments

    def test_get_client_services_invalid_type(self) -> None:
        """Test handling of invalid client types.
        
        Verifies that ValueError is raised for unknown client types.
        """
        # Test with invalid client type
        with self.assertRaises(ValueError) as context:  # Expect ValueError to be raised
            self.config_manager.get_client_services('invalid_client_type')  # Try to get unknown client type
        
        # Verify error message is descriptive
        self.assertIn("Unknown client type", str(context.exception))  # Check error message
        self.assertIn("invalid_client_type", str(context.exception))  # Check client type in error

    def test_validate_stripe_key_sandbox(self) -> None:
        """Test Stripe key validation for sandbox keys.
        
        Verifies that sandbox keys are properly validated.
        """
        # Test valid sandbox key
        sandbox_key = "sk_test_1234567890abcdef"  # Valid test key format
        result = self.config_manager.validate_stripe_key(sandbox_key)  # Validate key
        self.assertTrue(result)  # Should return True for sandbox key

    def test_validate_stripe_key_live(self) -> None:
        """Test Stripe key validation for live keys.
        
        Verifies that live keys are rejected in development.
        """
        # Test live key (should be rejected)
        live_key = "sk_live_1234567890abcdef"  # Live key format
        result = self.config_manager.validate_stripe_key(live_key)  # Validate key
        self.assertFalse(result)  # Should return False for live key

    def test_validate_stripe_key_invalid(self) -> None:
        """Test Stripe key validation for invalid keys.
        
        Verifies that malformed keys are rejected.
        """
        # Test invalid key format
        invalid_key = "invalid_key_format"  # Malformed key
        result = self.config_manager.validate_stripe_key(invalid_key)  # Validate key
        self.assertFalse(result)  # Should return False for invalid key


class TestConfigConstants(unittest.TestCase):
    """Test suite for configuration constants and helper functions."""

    def test_ssm_params_structure(self) -> None:
        """Test SSM parameter paths are correctly defined.
        
        Verifies that all required SSM parameters are present with correct paths.
        """
        # Verify all required SSM parameters are defined
        required_params = [  # List of required parameter names
            'hubspot_token',  # HubSpot API token
            'stripe_secret',  # Stripe secret key
            'stripe_connect_client_id',  # Stripe Connect client ID
            'anthropic_api_key'  # Anthropic API key
        ]  # End required parameters list
        
        for param in required_params:  # Check each required parameter
            self.assertIn(param, SSM_PARAMS)  # Verify parameter exists in SSM_PARAMS
            self.assertTrue(SSM_PARAMS[param].startswith('/dtl-global-platform/'))  # Verify path prefix

    def test_client_types_structure(self) -> None:
        """Test client type definitions are correctly structured.
        
        Verifies that all client types are defined with proper service lists.
        """
        # Verify all required client types are defined (per DTL_MASTER_PLAN.md Section 6.1)
        required_types = [  # List of required client types
            'full_package',  # TYPE A: Full package
            'website_only',  # TYPE B: Website + email only
            'website_crm',  # TYPE C: Website + CRM
            'crm_payments'  # TYPE D: CRM + payments only
        ]  # End required types list
        
        for client_type in required_types:  # Check each required client type
            self.assertIn(client_type, CLIENT_TYPES)  # Verify type exists in CLIENT_TYPES
            self.assertIsInstance(CLIENT_TYPES[client_type], list)  # Verify services is a list
            self.assertGreater(len(CLIENT_TYPES[client_type]), 0)  # Verify services list is not empty

    def test_get_lambda_env_vars(self) -> None:
        """Test Lambda environment variables function.
        
        Verifies that all required environment variables are returned.
        """
        # Get environment variables dictionary
        env_vars = get_lambda_env_vars()  # Call function under test
        
        # Verify required environment variables are present
        required_vars = [  # List of required environment variable names
            'HUBSPOT_TOKEN_PARAM',  # HubSpot token SSM path
            'STRIPE_SECRET_PARAM',  # Stripe secret SSM path
            'STRIPE_CONNECT_CLIENT_ID_PARAM',  # Stripe Connect ID SSM path
            'ANTHROPIC_API_KEY_PARAM',  # Anthropic API key SSM path
            'TEMPLATES_TABLE',  # Templates DynamoDB table
            'CLIENTS_TABLE',  # Clients DynamoDB table
            'STATE_TABLE',  # State DynamoDB table
            'SES_FROM_EMAIL'  # SES sender email
        ]  # End required variables list
        
        for var in required_vars:  # Check each required variable
            self.assertIn(var, env_vars)  # Verify variable exists in returned dictionary
            self.assertIsInstance(env_vars[var], str)  # Verify value is a string
            self.assertGreater(len(env_vars[var]), 0)  # Verify value is not empty

    def test_get_all_client_types(self) -> None:
        """Test client types listing function.
        
        Verifies that all client types are returned as a list.
        """
        # Get all client types
        client_types = get_all_client_types()  # Call function under test
        
        # Verify return type and content
        self.assertIsInstance(client_types, list)  # Should return a list
        self.assertEqual(len(client_types), 4)  # Should have 4 client types
        self.assertIn('full_package', client_types)  # Should include full package
        self.assertIn('website_only', client_types)  # Should include website only
        self.assertIn('website_crm', client_types)  # Should include website + CRM
        self.assertIn('crm_payments', client_types)  # Should include CRM + payments

    def test_is_service_required_email_required(self) -> None:
        """Test service requirement checking for required email.
        
        Verifies that email service is correctly identified as required.
        """
        # Mock client type with required email service
        with patch('engine.shared.config.config.get_client_services') as mock_get_services:  # Mock service getter
            mock_get_services.return_value = ['dns', 'website', 'email', 'notify']  # Services with email required
            
            # Test email service requirement
            result = is_service_required('test_type', 'email')  # Check if email is required
            self.assertTrue(result)  # Email should be required

    def test_is_service_required_email_optional(self) -> None:
        """Test service requirement checking for optional email.
        
        Verifies that email service is correctly identified as optional.
        """
        # Mock client type with optional email service
        with patch('engine.shared.config.config.get_client_services') as mock_get_services:  # Mock service getter
            mock_get_services.return_value = ['dns', 'website', 'email_optional', 'notify']  # Services with email optional
            
            # Test email service requirement
            result = is_service_required('test_type', 'email')  # Check if email is required
            self.assertFalse(result)  # Email should be optional (not required)

    def test_is_service_required_other_services(self) -> None:
        """Test service requirement checking for non-email services.
        
        Verifies that other services are correctly identified as required or not.
        """
        # Mock client type services
        with patch('engine.shared.config.config.get_client_services') as mock_get_services:  # Mock service getter
            mock_get_services.return_value = ['dns', 'website', 'crm', 'notify']  # Sample services list
            
            # Test required service
            self.assertTrue(is_service_required('test_type', 'dns'))  # DNS should be required
            self.assertTrue(is_service_required('test_type', 'website'))  # Website should be required
            self.assertTrue(is_service_required('test_type', 'crm'))  # CRM should be required
            
            # Test non-required service
            self.assertFalse(is_service_required('test_type', 'stripe'))  # Stripe should not be required


if __name__ == "__main__":  # Allow running tests directly from command line
    unittest.main()  # Execute all test methods in this module