"""Configuration module for DTL-Global onboarding platform.

This module provides centralized configuration management including:
- SSM Parameter Store integration for secure secrets
- Client type definitions and service mappings
- Environment variable management
- AWS service configuration constants

All secrets are loaded from AWS SSM Parameter Store with the prefix:
/dtl-global-platform/

Per DTL_MASTER_PLAN.md Section 10.2 and Appendix C.
Per Rule 001: Google-style docstrings for all functions and classes.
Per Rule 002: Inline comments on every meaningful line.
Per Rule 009: try/except blocks with specific exception types.

Author: DTL-Global Platform
"""

from __future__ import annotations

import os  # Environment variable access for Lambda runtime
import boto3  # AWS SDK for SSM Parameter Store and STS operations
from typing import Dict, List, Optional  # Type hints for function signatures
from botocore.exceptions import ClientError  # AWS API error handling


# SSM Parameter Store paths for all secrets (per DTL_MASTER_PLAN.md Section 10.2)
SSM_PARAMS = {  # Dictionary mapping secret names to SSM parameter paths
    "hubspot_token": "/dtl-global-platform/hubspot/token",  # HubSpot Private App access token
    "stripe_secret": "/dtl-global-platform/stripe/secret",  # Stripe Secret Key (sk_test_ until production)
    "stripe_connect_client_id": "/dtl-global-platform/stripe/connect_client_id",  # Stripe Connect client ID
    "anthropic_api_key": "/dtl-global-platform/anthropic/api_key",  # Anthropic Claude API key
}  # End SSM parameter paths

# Client type definitions mapping to required services (per DTL_MASTER_PLAN.md Section 10.2)
CLIENT_TYPES = {  # Dictionary mapping client types to service lists
    "full_package": ["dns", "website", "crm", "stripe", "email", "notify"],  # TYPE A: Full package
    "website_only": ["dns", "website", "email_optional", "notify"],  # TYPE B: Website + email only
    "website_crm": ["dns", "website", "crm", "notify"],  # TYPE C: Website + CRM
    "crm_payments": ["crm", "stripe", "notify"]  # TYPE D: CRM + payments only
}  # End client type definitions

# DynamoDB table names (per DTL_MASTER_PLAN.md Appendix A)
DYNAMODB_TABLES = {  # Dictionary mapping table types to actual table names
    "templates": os.environ.get("TEMPLATES_TABLE", "dtl-industry-templates"),  # Industry templates table
    "clients": os.environ.get("CLIENTS_TABLE", "dtl-clients"),  # Client records table
    "state": os.environ.get("STATE_TABLE", "dtl-onboarding-state")  # Onboarding state tracking table
}  # End DynamoDB table names

# S3 bucket name patterns (account ID gets substituted at runtime)
S3_BUCKETS = {  # Dictionary mapping bucket types to name patterns
    "websites": "dtl-client-websites-{account_id}",  # Client websites bucket (CDN stack)
    "assets": "dtl-assets-{account_id}",  # Platform assets bucket (Storage stack)
    "csv_imports": "dtl-csv-imports-{account_id}"  # CRM import CSV bucket (Storage stack)
}  # End S3 bucket patterns

# SES configuration (per DTL_MASTER_PLAN.md Appendix A)
SES_CONFIG = {  # Dictionary for SES email configuration
    "from_email": os.environ.get("SES_FROM_EMAIL", "noreply@dtl-global.org"),  # Default sender email
    "region": "us-east-1"  # SES sending region (required for SES operations)
}  # End SES configuration

# Lambda function configuration (per DTL_MASTER_PLAN.md Section 9.3)
LAMBDA_CONFIG = {  # Dictionary for Lambda function defaults
    "timeout": 300,  # 5 minutes max execution time (API Gateway limit)
    "memory": 256,   # 256MB memory allocation (cost-optimized)
    "runtime": "python3.12"  # Python runtime version (per Rule 005)
}  # End Lambda configuration

# Stripe configuration constants (per DTL_MASTER_PLAN.md Section 4)
STRIPE_CONFIG = {  # Dictionary for Stripe API configuration
    "api_version": "2024-12-18",  # Latest Stripe API version (as of plan creation)
    "currency": "usd",            # Default currency for payments (US market focus)
    "mode": "sandbox"             # Always sandbox until production switch (per plan Section 4)
}  # End Stripe configuration


class ConfigManager:
    """Manages configuration and secrets for the DTL-Global platform.
    
    This class handles loading secrets from SSM Parameter Store and provides
    centralized access to all configuration values needed by Lambda functions.
    """
    
    def __init__(self):
        """Initialize the configuration manager.
        
        Sets up AWS clients and initializes empty cache for secrets.
        Per Rule 009: AWS clients use default session credentials.
        """
        self._ssm_client = boto3.client('ssm')  # SSM client for parameter retrieval (uses default session)
        self._secrets_cache = {}  # Cache to avoid repeated SSM calls (memory optimization)
        self._account_id = None   # AWS account ID (lazy loaded on first access)
    
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
            response = self._ssm_client.get_parameter(  # Call SSM API to get parameter
                Name=parameter_path,  # Full SSM parameter path
                WithDecryption=True  # Decrypt SecureString parameters automatically
            )  # End SSM get_parameter call
            
            # Extract the parameter value from response
            secret_value = response['Parameter']['Value']  # Get decrypted parameter value
            
            # Cache the value to avoid repeated SSM calls
            self._secrets_cache[secret_name] = secret_value  # Store in memory cache
            
            return secret_value  # Return decrypted secret value
            
        except ClientError as e:  # Handle AWS SSM API errors
            # Extract AWS error code for specific handling
            error_code = e.response['Error']['Code']  # Get AWS error code from response
            if error_code == 'ParameterNotFound':  # Parameter doesn't exist in SSM
                raise RuntimeError(  # Use RuntimeError for application-level errors
                    f"SSM parameter not found: {parameter_path}. "
                    f"Run setup_ssm_parameters.py first."
                ) from e  # Chain original AWS error for debugging
            else:  # Other AWS API errors (permissions, network, etc.)
                raise RuntimeError(  # Use RuntimeError for application-level errors
                    f"Failed to retrieve SSM parameter {parameter_path}: {e}"
                ) from e  # Chain original AWS error for debugging
    
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
            # Get account ID from STS service
            sts_client = boto3.client('sts')  # Create STS client for identity operations
            response = sts_client.get_caller_identity()  # Get current AWS identity information
            
            # Cache and return the account ID
            self._account_id = response['Account']  # Extract account ID from STS response
            return self._account_id  # Return cached account ID
            
        except ClientError as e:  # Handle AWS STS API errors
            # Handle STS call failures with proper error wrapping
            raise RuntimeError(f"Failed to get AWS account ID: {e}") from e  # Chain original error
    
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
        """Validate that Stripe key is in sandbox mode.
        
        Per DTL_MASTER_PLAN.md Section 4: All Stripe operations must use sandbox keys
        until production switch. This enforces safety during development.
        
        Args:
            stripe_key: The Stripe secret key to validate
            
        Returns:
            True if key is valid sandbox key, False otherwise
        """
        # Check if key starts with sandbox prefix (per plan Section 4)
        is_sandbox = stripe_key.startswith('sk_test_')  # Stripe test keys start with sk_test_
        
        # Log validation result for debugging (per Rule 009 error handling)
        if not is_sandbox:  # Key is not a sandbox key
            print(f"WARNING: Stripe key does not appear to be sandbox: {stripe_key[:10]}...")  # Log first 10 chars only
        
        return is_sandbox  # Return validation result


# Global configuration manager instance (singleton pattern for Lambda efficiency)
config = ConfigManager()  # Shared instance across all handler modules


def get_lambda_env_vars() -> Dict[str, str]:
    """Get environment variables for Lambda function deployment.
    
    Per DTL_MASTER_PLAN.md Appendix A: Lambda environment variables reference
    SSM parameters and resource names for runtime configuration.
    
    Returns:
        Dictionary of environment variable names and values for CDK deployment
    """
    # Return environment variables that reference SSM parameters (per Appendix A)
    return {  # Dictionary of env var names to values
        "HUBSPOT_TOKEN_PARAM": SSM_PARAMS["hubspot_token"],  # SSM path for HubSpot token
        "STRIPE_SECRET_PARAM": SSM_PARAMS["stripe_secret"],  # SSM path for Stripe secret
        "STRIPE_CONNECT_CLIENT_ID_PARAM": SSM_PARAMS["stripe_connect_client_id"],  # SSM path for Connect ID
        "ANTHROPIC_API_KEY_PARAM": SSM_PARAMS["anthropic_api_key"],  # SSM path for Claude API key
        "TEMPLATES_TABLE": DYNAMODB_TABLES["templates"],  # DynamoDB table name for templates
        "CLIENTS_TABLE": DYNAMODB_TABLES["clients"],  # DynamoDB table name for clients
        "STATE_TABLE": DYNAMODB_TABLES["state"],  # DynamoDB table name for onboarding state
        "SES_FROM_EMAIL": SES_CONFIG["from_email"]  # Default sender email address
    }  # End Lambda environment variables


def get_all_client_types() -> List[str]:
    """Get list of all supported client types.
    
    Per DTL_MASTER_PLAN.md Section 6.1: Four client types supported.
    
    Returns:
        List of client type names (full_package, website_only, website_crm, crm_payments)
    """
    # Return all available client type keys (from CLIENT_TYPES dictionary)
    return list(CLIENT_TYPES.keys())  # Convert dict keys to list for iteration


def is_service_required(client_type: str, service: str) -> bool:
    """Check if a service is required for a specific client type.
    
    Args:
        client_type: The client type to check (from CLIENT_TYPES keys)
        service: The service name to check for
        
    Returns:
        True if service is required, False if optional or not included
        
    Raises:
        ValueError: If client_type is not valid
    """
    # Get services for this client type (validates client_type exists)
    services = config.get_client_services(client_type)  # Raises ValueError if invalid
    
    # Handle email service special case (optional vs required)
    if service == "email":  # Check for email service specifically
        if "email" in services:  # Email is explicitly required
            return True  # Email service is mandatory for this client type
        elif "email_optional" in services:  # Email is optional
            return False  # Email service is optional (not required)
        else:  # Email not mentioned at all
            return False  # Email service not included for this client type
    
    # For all other services, check direct inclusion
    return service in services  # True if service is in the required services list