"""CDN stack: S3 website bucket, CloudFront OAC origin, and Route 53 alias."""

from __future__ import annotations

from aws_cdk import RemovalPolicy, Stack, Tags  # CDK core helpers
from aws_cdk import aws_cloudfront as cloudfront  # CloudFront distribution
from aws_cdk import aws_cloudfront_origins as origins  # S3BucketOrigin (non-deprecated)
from aws_cdk import aws_s3 as s3  # Website bucket (colocated with distribution to avoid cross-stack cycles)
from constructs import Construct  # Base construct class


class CdnStack(Stack):
    """Serve the website bucket through HTTPS with a friendly subdomain."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs: object,
    ) -> None:
        """Create the client websites bucket and CloudFront distribution (no custom domains yet).

        This distribution will serve CLIENT websites (e.g., clientname.com) via custom domains added
        programmatically during onboarding. DTL-Global's corporate site stays on its existing deployment.

        Args:
            scope: Parent construct (typically the CDK app).
            construct_id: Logical stack identifier.
            **kwargs: Passed through to ``Stack`` (env, stackName, etc.).
        """
        super().__init__(scope, construct_id, **kwargs)  # Initialize CloudFormation stack
        account_id = Stack.of(self).account  # AWS account id for globally unique bucket name
        self.website_bucket = s3.Bucket(  # Hosted client static sites (same stack as CloudFront + OAC)
            self,  # Parent construct is this stack
            "ClientWebsitesBucket",  # Logical id inside the template
            bucket_name=f"dtl-client-websites-{account_id}",  # Globally unique bucket name
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,  # Private; OAC grants CloudFront read
            encryption=s3.BucketEncryption.S3_MANAGED,  # Server-side encryption at rest
            enforce_ssl=True,  # Deny plain HTTP requests
            versioned=False,  # Versioning optional for Phase 1
            removal_policy=RemovalPolicy.RETAIN,  # Avoid deleting client sites accidentally
        )  # End website bucket definition
        website_origin = origins.S3BucketOrigin.with_origin_access_control(  # OAC + bucket policy (non-deprecated)
            self.website_bucket,  # Private S3 origin
        )  # End S3 origin with origin access control
        self.distribution = cloudfront.Distribution(  # Global CDN for client websites (no custom domains yet)
            self,  # Parent construct is this stack
            "ClientWebsiteDistribution",  # Logical id inside the template
            default_behavior=cloudfront.BehaviorOptions(  # Default cache behavior
                origin=website_origin,  # S3 + OAC in this stack (no Storage<->CDN cycle)
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,  # Force HTTPS
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,  # Static site verbs
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,  # Cache GET/HEAD/OPTIONS
            ),  # End default behavior
            minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,  # Modern TLS floor
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,  # US/Europe edge locations to control cost
            comment="DTL-Global client website CDN (custom domains added programmatically during onboarding)",  # Console-visible description
        )  # End distribution definition
        Tags.of(self).add("Project", "dtl-global-platform")  # Tag stack for cost tracking
