"""Configuration module for DTL-Global onboarding platform.

This module provides centralized configuration management including:
- SSM Parameter Store integration for secure secrets
- Client type definitions and service mappings
- Environment variable management
- AWS service configuration constants

All secrets are loaded from AWS SSM Parameter Store with the prefix:
/dtl-global-platform/

Author: DTL-Global Platform
"""

import os
import boto3
import requests
from typing import Dict, List, Optional
from botocore.exceptions import ClientError


# SSM Parameter Store paths for all secrets
SSM_PARAMS = {
    "hubspot_token": "/dtl-global-platform/hubspot/token",
    "stripe_secret": "/dtl-global-platform/stripe/secret", 
    "stripe_connect_client_id": "/dtl-global-platform/stripe/connect_client_id",
    "anthropic_api_key": "/dtl-global-platform/anthropic/api_key",
    "stripe_webhook_secret": "/dtl-global-platform/stripe/webhook_secret",
    "slack_webhook_url": "/dtl-global-platform/slack/webhook_url",
}

# Client type definitions mapping to required services
CLIENT_TYPES = {
    "full_package": ["dns", "website", "crm", "stripe", "email", "notify"],
    "website_only": ["dns", "website", "email_optional", "notify"],
    "website_crm": ["dns", "website", "crm", "notify"],
    "crm_payments": ["crm", "stripe", "notify"]
}

# DynamoDB table names
DYNAMODB_TABLES = {
    "templates": "dtl-industry-templates",
    "clients": "dtl-clients", 
    "state": "dtl-onboarding-state"
}

# S3 bucket name patterns (account ID gets substituted)
S3_BUCKETS = {
    "websites": "dtl-client-websites-{account_id}",
    "assets": "dtl-assets-{account_id}",
    "csv_imports": "dtl-csv-imports-{account_id}"
}

# SES configuration
SES_CONFIG = {
    "from_email": "noreply@dtl-global.org",
    "region": "us-east-1"  # SES sending region
}

# Lambda function configuration
LAMBDA_CONFIG = {
    "timeout": 300,  # 5 minutes max execution time
    "memory": 256,   # 256MB memory allocation
    "runtime": "python3.12"  # Python runtime version
}

# Stripe configuration constants
STRIPE_CONFIG = {
    "api_version": "2024-06-20",  # Valid Stripe API version for stripe SDK
    "currency": "usd",            # Default currency for payments
    "mode": "sandbox"             # Always sandbox until production switch
}


class ConfigManager:
    """Manages configuration and secrets for the DTL-Global platform.
    
    This class handles loading secrets from SSM Parameter Store and provides
    centralized access to all configuration values needed by Lambda functions.
    """
    
    def __init__(self):
        """Initialize the configuration manager.
        
        Sets up AWS clients and initializes empty cache for secrets.
        """
        self._ssm_client = boto3.client('ssm')  # SSM client for parameter retrieval
        self._secrets_cache = {}  # Cache to avoid repeated SSM calls
        self._account_id = None   # AWS account ID (lazy loaded)
    
    def get_secret(self, secret_name: str) -> str:
        """Retrieve a secret from SSM Parameter Store.
        
        Args:
            secret_name: The key name from SSM_PARAMS dict
            
        Returns:
            The decrypted secret value from SSM
            
        Raises:
            ValueError: If secret_name is not in SSM_PARAMS
            ClientError: If SSM parameter retrieval fails
        """
        # Validate secret name exists in our configuration
        if secret_name not in SSM_PARAMS:
            raise ValueError(f"Unknown secret name: {secret_name}")
        
        # Return cached value if available
        if secret_name in self._secrets_cache:
            return self._secrets_cache[secret_name]
        
        # Get the SSM parameter path for this secret
        parameter_path = SSM_PARAMS[secret_name]
        
        try:
            # Retrieve the encrypted parameter from SSM
            response = self._ssm_client.get_parameter(
                Name=parameter_path,
                WithDecryption=True  # Decrypt SecureString parameters
            )
            
            # Extract the parameter value
            secret_value = response['Parameter']['Value']
            
            # Cache the value to avoid repeated SSM calls
            self._secrets_cache[secret_name] = secret_value
            
            return secret_value
            
        except ClientError as e:
            # Handle SSM parameter retrieval errors
            error_code = e.response['Error']['Code']
            if error_code == 'ParameterNotFound':
                raise ClientError(
                    f"SSM parameter not found: {parameter_path}. "
                    f"Run setup_ssm_parameters.py first."
                ) from e
            else:
                raise ClientError(
                    f"Failed to retrieve SSM parameter {parameter_path}: {e}"
                ) from e
    
    def get_account_id(self) -> str:
        """Get the current AWS account ID.
        
        Returns:
            The AWS account ID as a string
            
        Raises:
            ClientError: If STS call fails
        """
        # Return cached account ID if available
        if self._account_id is not None:
            return self._account_id
        
        try:
            # Get account ID from STS
            sts_client = boto3.client('sts')
            response = sts_client.get_caller_identity()
            
            # Cache and return the account ID
            self._account_id = response['Account']
            return self._account_id
            
        except ClientError as e:
            # Handle STS call failures
            raise ClientError(f"Failed to get AWS account ID: {e}") from e
    
    def get_s3_bucket_name(self, bucket_type: str) -> str:
        """Get the full S3 bucket name with account ID substituted.
        
        Args:
            bucket_type: The bucket type key from S3_BUCKETS dict
            
        Returns:
            The full S3 bucket name with account ID
            
        Raises:
            ValueError: If bucket_type is not in S3_BUCKETS
        """
        # Validate bucket type exists in our configuration
        if bucket_type not in S3_BUCKETS:
            raise ValueError(f"Unknown bucket type: {bucket_type}")
        
        # Get the bucket name pattern
        bucket_pattern = S3_BUCKETS[bucket_type]
        
        # Substitute the account ID and return full bucket name
        return bucket_pattern.format(account_id=self.get_account_id())
    
    def get_client_services(self, client_type: str) -> List[str]:
        """Get the list of services required for a client type.
        
        Args:
            client_type: The client type key from CLIENT_TYPES dict
            
        Returns:
            List of service names required for this client type
            
        Raises:
            ValueError: If client_type is not in CLIENT_TYPES
        """
        # Validate client type exists in our configuration
        if client_type not in CLIENT_TYPES:
            raise ValueError(f"Unknown client type: {client_type}")
        
        # Return the list of services for this client type
        return CLIENT_TYPES[client_type].copy()  # Return copy to prevent modification
    
    def validate_stripe_key(self, stripe_key: str) -> bool:
        """Validate that Stripe key is a supported Stripe secret.
        
        Args:
            stripe_key: The Stripe secret key to validate
            
        Returns:
            True when the key is either a test secret (``sk_test_``) or a live secret (``sk_live_``)
        """
        # Accept both sandbox and live keys after the production switch.
        # The presence of ``sk_live_`` indicates the operator has intentionally switched SSM.
        is_sandbox = stripe_key.startswith('sk_test_')  # True for Stripe test mode keys
        is_live = stripe_key.startswith('sk_live_')  # True for Stripe live mode keys
        
        # Log which mode we detected to aid debugging in CloudWatch.
        if is_live:  # If the key is live, provide a warning but do not block.
            print("WARNING: Using Stripe LIVE key (sk_live_)")  # Operator signal
        elif not is_sandbox:  # If it's neither test nor live, it is invalid.
            print(f"WARNING: Stripe key does not appear to be valid: {stripe_key[:10]}...")  # Debug snippet
        
        return is_sandbox or is_live  # Only accept sk_test_ or sk_live_


# Global configuration manager instance
config = ConfigManager()


def get_lambda_env_vars() -> Dict[str, str]:
    """Get environment variables for Lambda function deployment.
    
    Returns:
        Dictionary of environment variable names and SSM parameter paths
    """
    # Return environment variables that reference SSM parameters
    return {
        "HUBSPOT_TOKEN_PARAM": SSM_PARAMS["hubspot_token"],
        "STRIPE_SECRET_PARAM": SSM_PARAMS["stripe_secret"],
        "STRIPE_CONNECT_CLIENT_ID_PARAM": SSM_PARAMS["stripe_connect_client_id"],
        "ANTHROPIC_API_KEY_PARAM": SSM_PARAMS["anthropic_api_key"],
        "TEMPLATES_TABLE": DYNAMODB_TABLES["templates"],
        "CLIENTS_TABLE": DYNAMODB_TABLES["clients"],
        "STATE_TABLE": DYNAMODB_TABLES["state"],
        "SES_FROM_EMAIL": SES_CONFIG["from_email"]
    }


def get_all_client_types() -> List[str]:
    """Get list of all supported client types.
    
    Returns:
        List of client type names
    """
    # Return all available client type keys
    return list(CLIENT_TYPES.keys())


def is_service_required(client_type: str, service: str) -> bool:
    """Check if a service is required for a specific client type.
    
    Args:
        client_type: The client type to check
        service: The service name to check for
        
    Returns:
        True if service is required, False otherwise
        
    Raises:
        ValueError: If client_type is not valid
    """
    # Get services for this client type
    services = config.get_client_services(client_type)
    
    # Check if service is in the list (handle optional services)
    if service == "email" and "email_optional" in services:
        return False  # Email is optional for this client type
    
    return service in services


def send_slack_notification(message: str) -> None:
    """Send notification to Slack webhook.
    
    This function sends a message to the configured Slack webhook URL.
    It's designed to be non-critical - if Slack fails, it won't break
    the main workflow.
    
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
        # Don't fail the main workflow if Slack fails (non-critical)