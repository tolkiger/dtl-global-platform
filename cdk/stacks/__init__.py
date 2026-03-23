"""CDK stack modules for the DTL-Global Platform (Phase 1 foundation)."""

from stacks.api_stack import ApiStack  # REST API + onboarding Lambdas
from stacks.cdn_stack import CdnStack  # CloudFront + OAC for website bucket
from stacks.pipeline_stack import PipelineStack  # CodePipeline + CodeBuild
from stacks.storage_stack import StorageStack  # DynamoDB + S3

__all__ = [
    "ApiStack",
    "CdnStack",
    "PipelineStack",
    "StorageStack",
]
