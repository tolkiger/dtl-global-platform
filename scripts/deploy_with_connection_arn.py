#!/usr/bin/env python3
"""Deploy CDK stacks with CodeStar connection ARN from SSM Parameter Store.

This script reads the CodeStar connection ARN from SSM and sets it as an
environment variable before running cdk deploy. This avoids CloudFormation
dynamic reference issues with CodePipeline.

Per DTL_MASTER_PLAN.md Phase 1 deployment requirements
Per Rule 002: Every line commented for Gerardo's understanding
Per Rule 009: Error handling with try/except blocks
"""

from __future__ import annotations

import os  # Environment variable operations
import subprocess  # Command execution for CDK deploy
import sys  # Exit codes and command line arguments

import boto3  # AWS SDK for SSM parameter retrieval
from botocore.exceptions import ClientError, NoCredentialsError  # AWS error handling


def get_connection_arn_from_ssm() -> str:
    """Retrieve CodeStar connection ARN from SSM Parameter Store.
    
    Returns:
        str: The CodeStar connection ARN value from SSM.
        
    Raises:
        ClientError: If SSM parameter doesn't exist or access denied.
        NoCredentialsError: If AWS credentials are not configured.
    """
    try:  # Attempt to read CodeStar connection ARN from SSM
        ssm_client = boto3.client('ssm')  # Initialize SSM client
        parameter_name = "/dtl-global-platform/github/codestar_connection_arn"  # SSM parameter path
        
        print(f"Reading CodeStar connection ARN from SSM: {parameter_name}")  # Progress indicator
        
        response = ssm_client.get_parameter(  # Retrieve parameter value
            Name=parameter_name,  # Parameter path from master plan
            WithDecryption=True  # Decrypt SecureString if encrypted
        )  # End get_parameter call
        
        connection_arn = response['Parameter']['Value']  # Extract parameter value
        print(f"✓ Retrieved connection ARN: {connection_arn[:50]}...")  # Show partial ARN for confirmation
        
        return connection_arn  # Return the connection ARN value
        
    except ClientError as e:  # Handle AWS API errors
        error_code = e.response['Error']['Code']  # Extract error code
        if error_code == 'ParameterNotFound':  # Parameter doesn't exist
            print(f"✗ SSM parameter not found: {parameter_name}")  # Error message
            print("Run scripts/setup_ssm_parameters.py to create required parameters")  # Fix suggestion
        else:  # Other AWS errors
            print(f"✗ AWS error ({error_code}): {e.response['Error']['Message']}")  # Display error
        sys.exit(1)  # Exit with error code
        
    except NoCredentialsError:  # AWS credentials not configured
        print("✗ AWS credentials not configured")  # Error message
        print("Run 'aws configure' or set AWS credentials environment variables")  # Fix suggestion
        sys.exit(1)  # Exit with error code


def deploy_cdk_stacks(connection_arn: str) -> None:
    """Deploy CDK stacks with CodeStar connection ARN as environment variable.
    
    Args:
        connection_arn: The CodeStar connection ARN to use for pipeline deployment.
        
    Raises:
        subprocess.CalledProcessError: If CDK deploy command fails.
    """
    try:  # Attempt to deploy CDK stacks
        # Set environment variable for CDK app
        env = os.environ.copy()  # Copy current environment
        env['CODESTAR_CONNECTION_ARN'] = connection_arn  # Add connection ARN
        
        print("Deploying CDK stacks with connection ARN...")  # Progress indicator
        print("Running: cdk deploy --all --require-approval never")  # Show command
        
        # Execute CDK deploy command
        result = subprocess.run(  # Run CDK deploy with environment
            ['cdk', 'deploy', '--all', '--require-approval', 'never'],  # CDK command arguments
            cwd='cdk',  # Run from cdk directory
            env=env,  # Use modified environment with connection ARN
            check=True,  # Raise exception on non-zero exit
            capture_output=True,  # Capture stdout/stderr
            text=True  # Return strings instead of bytes
        )  # End subprocess.run
        
        print("✓ CDK deployment completed successfully!")  # Success message
        print("\nDeployment output:")  # Output header
        print(result.stdout)  # Show CDK output
        
    except subprocess.CalledProcessError as e:  # Handle CDK deploy errors
        print(f"✗ CDK deployment failed with exit code {e.returncode}")  # Error message
        print(f"Error output: {e.stderr}")  # Show error details
        sys.exit(1)  # Exit with error code
        
    except FileNotFoundError:  # CDK command not found
        print("✗ CDK command not found")  # Error message
        print("Install CDK: npm install -g aws-cdk")  # Fix suggestion
        sys.exit(1)  # Exit with error code


def main() -> None:
    """Main script entrypoint for CDK deployment with SSM connection ARN.
    
    Reads CodeStar connection ARN from SSM and deploys all CDK stacks.
    """
    print("DTL-Global Platform: CDK Deployment with CodeStar Connection")  # Script identification
    print("=" * 60)  # Visual separator
    
    # Get CodeStar connection ARN from SSM
    connection_arn = get_connection_arn_from_ssm()  # Retrieve ARN from parameter store
    
    # Deploy CDK stacks with connection ARN
    deploy_cdk_stacks(connection_arn)  # Execute deployment
    
    print("\n✅ Phase 1 infrastructure deployment complete!")  # Final success message


if __name__ == "__main__":  # Allow script execution from command line
    main()  # Execute main function when run directly