"""Storage stack: DynamoDB tables and S3 buckets for onboarding and websites."""

from __future__ import annotations

from aws_cdk import Duration, RemovalPolicy, Stack, Tags  # CDK core helpers
from aws_cdk import aws_dynamodb as dynamodb  # DynamoDB table constructs
from aws_cdk import aws_s3 as s3  # S3 bucket constructs
from constructs import Construct  # Base construct class


class StorageStack(Stack):
    """Provision DynamoDB tables and S3 buckets referenced by Lambdas."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs: object,
    ) -> None:
        """Create tables and buckets with serverless-friendly defaults.

        Args:
            scope: Parent construct (typically the CDK app).
            construct_id: Logical stack identifier.
            **kwargs: Passed through to ``Stack`` (env, stackName, etc.).
        """
        super().__init__(scope, construct_id, **kwargs)  # Initialize CloudFormation stack
        account_id = Stack.of(self).account  # Resolve AWS account for unique bucket names (used for S3 names)
        self.templates_table = dynamodb.Table(  # Industry templates metadata
            self,  # Parent construct is this stack
            "IndustryTemplatesTable",  # Logical id inside the template
            table_name="dtl-industry-templates",  # Stable name for Lambda env vars
            partition_key=dynamodb.Attribute(  # Primary key schema
                name="template_id",  # Partition key attribute name
                type=dynamodb.AttributeType.STRING,  # String partition key
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,  # On-demand capacity
            removal_policy=RemovalPolicy.RETAIN,  # Avoid accidental data loss on stack delete
        )  # End templates table definition
        self.clients_table = dynamodb.Table(  # Client onboarding records
            self,  # Parent construct is this stack
            "ClientsTable",  # Logical id inside the template
            table_name="dtl-clients",  # Stable name for Lambda env vars
            partition_key=dynamodb.Attribute(  # Primary key schema
                name="client_id",  # Partition key attribute name
                type=dynamodb.AttributeType.STRING,  # String partition key
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,  # On-demand capacity
            removal_policy=RemovalPolicy.RETAIN,  # Protect production-like data
        )  # End clients table definition
        self.state_table = dynamodb.Table(  # Long-running onboarding state machine rows
            self,  # Parent construct is this stack
            "OnboardingStateTable",  # Logical id inside the template
            table_name="dtl-onboarding-state",  # Stable name for Lambda env vars
            partition_key=dynamodb.Attribute(  # Primary key schema
                name="state_id",  # Partition key attribute name
                type=dynamodb.AttributeType.STRING,  # String partition key
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,  # On-demand capacity
            removal_policy=RemovalPolicy.RETAIN,  # Protect workflow state
        )  # End state table definition
        self.assets_bucket = s3.Bucket(  # Shared assets (logos, uploads)
            self,  # Parent construct is this stack
            "AssetsBucket",  # Logical id inside the template
            bucket_name=f"dtl-assets-{account_id}",  # Globally unique bucket name
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,  # Private bucket
            encryption=s3.BucketEncryption.S3_MANAGED,  # Server-side encryption at rest
            enforce_ssl=True,  # Deny plain HTTP requests
            versioned=False,  # Keep Phase 1 simple
            removal_policy=RemovalPolicy.RETAIN,  # Avoid accidental deletes
            lifecycle_rules=[  # Cost optimization lifecycle rules
                s3.LifecycleRule(  # Transition old assets to cheaper storage
                    id="OptimizeAssetStorage",  # Human-readable rule name
                    enabled=True,  # Rule is active
                    transitions=[  # Storage class transitions for cost savings
                        s3.Transition(  # Move to Infrequent Access after 30 days
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,  # IA storage class
                            transition_after=Duration.days(30),  # After 30 days of creation
                        ),  # End IA transition
                        s3.Transition(  # Move to Glacier Flexible Retrieval after 90 days
                            storage_class=s3.StorageClass.GLACIER,  # Glacier storage class
                            transition_after=Duration.days(90),  # After 90 days of creation
                        ),  # End Glacier transition
                    ],  # End transitions list
                    expiration=Duration.days(2555),  # Delete after 7 years (2555 days) for compliance
                ),  # End lifecycle rule
            ],  # End lifecycle rules list
        )  # End assets bucket definition
        self.csv_import_bucket = s3.Bucket(  # CRM CSV uploads for import workflow
            self,  # Parent construct is this stack
            "CsvImportsBucket",  # Logical id inside the template
            bucket_name=f"dtl-csv-imports-{account_id}",  # Globally unique bucket name
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,  # Private ingest bucket
            encryption=s3.BucketEncryption.S3_MANAGED,  # Server-side encryption at rest
            enforce_ssl=True,  # Deny plain HTTP requests
            versioned=False,  # Versioning not required for CSV staging
            removal_policy=RemovalPolicy.RETAIN,  # Retain imports for auditability
            lifecycle_rules=[  # Optional lifecycle to bound storage growth
                s3.LifecycleRule(  # One lifecycle rule object
                    id="ExpireOldCsvUploads",  # Human-readable rule name
                    expiration=Duration.days(90),  # Delete old objects after 90 days
                    enabled=True,  # Rule is active
                ),  # End lifecycle rule
            ],  # End lifecycle rules list
        )  # End CSV import bucket definition
        Tags.of(self).add("Project", "dtl-global-platform")  # Tag stack for cost tracking
