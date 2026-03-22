"""API stack: API Gateway REST API and onboarding Lambda functions."""

from __future__ import annotations

import os  # Resolve filesystem paths to the Lambda source bundle

from aws_cdk import Duration, RemovalPolicy, Stack, Tags  # CDK core helpers
from aws_cdk import aws_apigateway as apigateway  # REST API constructs
from aws_cdk import aws_dynamodb as dynamodb  # DynamoDB table references
from aws_cdk import aws_iam as iam  # IAM policies for Lambda roles
from aws_cdk import aws_lambda as lambda_  # Lambda function constructs
from aws_cdk import aws_logs as logs  # CloudWatch Logs for retention policies
from aws_cdk import aws_s3 as s3  # S3 bucket references
from constructs import Construct  # Base construct class

# Route slug -> Python module name under engine/handlers (handler_<module>.py)
_HANDLER_ROUTE_SPECS: list[tuple[str, str]] = [
    ("bid", "bid"),  # Bid generation endpoint
    ("prompt", "prompt"),  # SEO prompt generation endpoint
    ("invoice", "invoice"),  # Stripe invoice endpoint
    ("crm-setup", "crm_setup"),  # HubSpot CRM setup endpoint
    ("stripe-setup", "stripe_setup"),  # Stripe Connect setup endpoint
    ("dns", "dns"),  # DNS automation endpoint
    ("deploy", "deploy"),  # Website deploy orchestration endpoint
    ("email-setup", "email_setup"),  # Email setup endpoint
    ("subscribe", "subscribe"),  # Subscription billing endpoint
    ("notify", "notify"),  # Notifications endpoint
    ("crm-import", "crm_import"),  # CRM CSV import endpoint
    ("onboard", "onboard"),  # Orchestrator endpoint
]


class ApiStack(Stack):
    """Expose onboarding operations through API Gateway and Lambda."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        templates_table: dynamodb.ITable,
        clients_table: dynamodb.ITable,
        state_table: dynamodb.ITable,
        website_bucket: s3.IBucket,
        assets_bucket: s3.IBucket,
        csv_import_bucket: s3.IBucket,
        **kwargs: object,
    ) -> None:
        """Create REST resources and Lambda integrations for onboarding.

        Args:
            scope: Parent construct (typically the CDK app).
            construct_id: Logical stack identifier.
            templates_table: Industry templates DynamoDB table.
            clients_table: Clients DynamoDB table.
            state_table: Onboarding state DynamoDB table.
            website_bucket: Client website S3 bucket.
            assets_bucket: Shared assets S3 bucket.
            csv_import_bucket: CRM CSV import S3 bucket.
            **kwargs: Passed through to ``Stack`` (env, stackName, etc.).
        """
        super().__init__(scope, construct_id, **kwargs)  # Initialize CloudFormation stack
        stack = Stack.of(self)  # Resolve stack metadata for ARN construction
        region = stack.region  # AWS region for IAM resource ARNs
        account = stack.account  # AWS account id for IAM resource ARNs
        engine_path = os.path.abspath(  # Absolute path to Lambda source tree
            os.path.join(os.path.dirname(__file__), "..", "..", "engine"),  # Repo engine/ directory
        )  # End path join
        common_environment = {  # Shared environment variables for all onboarding Lambdas
            "HUBSPOT_TOKEN_PARAM": "/dtl-global-platform/hubspot/token",  # HubSpot token SSM name
            "STRIPE_SECRET_PARAM": "/dtl-global-platform/stripe/secret",  # Stripe secret SSM name
            "STRIPE_CONNECT_CLIENT_ID_PARAM": "/dtl-global-platform/stripe/connect_client_id",  # Connect id SSM name
            "ANTHROPIC_API_KEY_PARAM": "/dtl-global-platform/anthropic/api_key",  # Anthropic key SSM name
            "TEMPLATES_TABLE": templates_table.table_name,  # Templates table name
            "CLIENTS_TABLE": clients_table.table_name,  # Clients table name
            "STATE_TABLE": state_table.table_name,  # State table name
            "WEBSITE_BUCKET": website_bucket.bucket_name,  # Website bucket name
            "ASSETS_BUCKET": assets_bucket.bucket_name,  # Assets bucket name
            "CSV_IMPORT_BUCKET": csv_import_bucket.bucket_name,  # CSV import bucket name
            "SES_FROM_EMAIL": "onboarding@dtl-global.org",  # Default SES sender per master plan
        }  # End common environment dict
        rest_api = apigateway.RestApi(  # Public REST API for onboarding
            self,  # Parent construct is this stack
            "OnboardingRestApi",  # Logical id inside the template
            rest_api_name="dtl-onboarding-api",  # Visible name in API Gateway console
            deploy_options=apigateway.StageOptions(  # Default stage configuration
                stage_name="prod",  # Single production stage for Phase 1
            ),  # End stage options
            default_cors_preflight_options=apigateway.CorsOptions(  # CORS for browser clients
                allow_origins=apigateway.Cors.ALL_ORIGINS,  # Allow any origin for now
                allow_methods=["POST", "OPTIONS"],  # Onboarding uses POST JSON bodies
                allow_headers=["Content-Type", "Authorization"],  # Typical headers for JSON + auth
            ),  # End CORS options
        )  # End RestApi definition
        for route_path, module_suffix in _HANDLER_ROUTE_SPECS:  # Create one Lambda + route per handler
            handler_id = f"handler_{module_suffix}"  # Python module name without .py
            function_name = f"dtl-onboarding-{module_suffix.replace('_', '-')}"  # AWS Lambda function name
            log_group = logs.LogGroup(  # Explicit log group with retention for cost optimization
                self,  # Parent construct is this stack
                f"LogGroup{module_suffix.title().replace('_', '')}",  # Stable logical id per handler log group
                log_group_name=f"/aws/lambda/{function_name}",  # Standard Lambda log group naming convention
                retention=logs.RetentionDays.ONE_MONTH,  # 30-day log retention for cost optimization
                removal_policy=RemovalPolicy.DESTROY,  # Allow log group cleanup when stack is deleted
            )  # End log group definition
            lambda_function = lambda_.Function(  # Python 3.12 function with shared code bundle
                self,  # Parent construct is this stack
                f"Lambda{module_suffix.title().replace('_', '')}",  # Stable logical id per handler
                runtime=lambda_.Runtime.PYTHON_3_12,  # Python runtime required by the master plan
                handler=f"handlers.{handler_id}.lambda_handler",  # Module path inside engine/
                code=lambda_.Code.from_asset(engine_path),  # Zip the engine/ tree for deployment
                timeout=Duration.minutes(5),  # Long-running onboarding steps (master plan: 5 minutes)
                memory_size=256,  # Memory size per master plan baseline
                environment=common_environment,  # Inject shared configuration
                function_name=function_name,  # Predictable name in the Lambda console
                log_group=log_group,  # Use explicit log group instead of deprecated log_retention
            )  # End Lambda function definition
            templates_table.grant_read_write_data(lambda_function)  # Allow DynamoDB access for templates
            clients_table.grant_read_write_data(lambda_function)  # Allow DynamoDB access for clients
            state_table.grant_read_write_data(lambda_function)  # Allow DynamoDB access for state
            website_bucket.grant_read_write(lambda_function)  # Allow website bucket read/write
            assets_bucket.grant_read_write(lambda_function)  # Allow assets bucket read/write
            csv_import_bucket.grant_read_write(lambda_function)  # Allow CSV import bucket read/write
            ssm_parameter_arn = f"arn:aws:ssm:{region}:{account}:parameter/dtl-global-platform/*"  # SSM path ARN
            lambda_function.add_to_role_policy(  # Allow reading SecureString parameters at runtime
                iam.PolicyStatement(  # Inline policy statement on the function role
                    actions=["ssm:GetParameter", "ssm:GetParameters"],  # Minimal SSM read actions
                    resources=[ssm_parameter_arn],  # Restrict to DTL parameter namespace
                ),  # End policy statement
            )  # End add_to_role_policy
            resource = rest_api.root.add_resource(route_path)  # Add /{route_path} under root
            resource.add_method(  # Wire POST to the Lambda integration
                "POST",  # Onboarding actions are invoked via POST bodies
                apigateway.LambdaIntegration(lambda_function),  # Lambda proxy integration
            )  # End add_method
        Tags.of(self).add("Project", "dtl-global-platform")  # Tag stack for cost tracking
