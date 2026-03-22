"""CDK stack modules for the DTL-Global Platform (Phase 1 foundation)."""

from stacks.api_stack import ApiStack  # REST API + onboarding Lambdas
from stacks.cdn_stack import CdnStack  # CloudFront + OAI for website bucket
from stacks.dns_stack import DnsStack  # Route 53 hosted zone for DTL-Global
from stacks.email_stack import EmailStack  # SES domain identity
from stacks.pipeline_stack import PipelineStack  # CodePipeline + CodeBuild
from stacks.ssl_stack import SslStack  # ACM certificate (DNS validation)
from stacks.storage_stack import StorageStack  # DynamoDB + S3

__all__ = [
    "ApiStack",
    "CdnStack",
    "DnsStack",
    "EmailStack",
    "PipelineStack",
    "SslStack",
    "StorageStack",
]
