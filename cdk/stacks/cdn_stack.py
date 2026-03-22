"""CDN stack: CloudFront distribution with OAI for the client website bucket."""

from __future__ import annotations

from aws_cdk import Stack, Tags  # CDK core helpers
from aws_cdk import aws_certificatemanager as acm  # ACM certificate reference
from aws_cdk import aws_cloudfront as cloudfront  # CloudFront distribution
from aws_cdk import aws_cloudfront_origins as origins  # S3 origin helpers
from aws_cdk import aws_route53 as route53  # Alias record to CloudFront
from aws_cdk import aws_route53_targets as route53_targets  # CloudFront alias target
from aws_cdk import aws_s3 as s3  # Website bucket reference
from constructs import Construct  # Base construct class


class CdnStack(Stack):
    """Serve the website bucket through HTTPS with a friendly subdomain."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        website_bucket: s3.IBucket,
        origin_access_identity: cloudfront.IOriginAccessIdentity,
        certificate: acm.ICertificate,
        hosted_zone: route53.IHostedZone,
        website_alias: str,
        **kwargs: object,
    ) -> None:
        """Create a CloudFront distribution and a Route 53 alias record.

        Args:
            scope: Parent construct (typically the CDK app).
            construct_id: Logical stack identifier.
            website_bucket: S3 bucket that stores static client sites.
            origin_access_identity: OAI created alongside the bucket to avoid cross-stack cycles.
            certificate: ACM certificate in ``us-east-1`` for CloudFront custom domains.
            hosted_zone: Route 53 hosted zone for DNS alias records.
            website_alias: Full hostname served by CloudFront (for example ``www.dtl-global.org``).
            **kwargs: Passed through to ``Stack`` (env, stackName, etc.).
        """
        super().__init__(scope, construct_id, **kwargs)  # Initialize CloudFormation stack
        self.distribution = cloudfront.Distribution(  # Global CDN in front of S3
            self,  # Parent construct is this stack
            "ClientWebsiteDistribution",  # Logical id inside the template
            default_behavior=cloudfront.BehaviorOptions(  # Default cache behavior
                origin=origins.S3Origin(  # S3 static website origin
                    website_bucket,  # Bucket containing deployed sites
                    origin_access_identity=origin_access_identity,  # Match OAI used by the bucket policy
                ),  # End S3 origin definition
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,  # Force HTTPS
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,  # Static site verbs
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,  # Cache GET/HEAD/OPTIONS
            ),  # End default behavior
            domain_names=[website_alias],  # Custom hostname on the distribution
            certificate=certificate,  # TLS certificate for the custom hostname
            minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,  # Modern TLS floor
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,  # US/Europe edge locations to control cost
            comment="DTL-Global client website CDN",  # Console-visible description
        )  # End distribution definition
        route53.ARecord(  # Alias record from www subdomain to CloudFront
            self,  # Parent construct is this stack
            "WebsiteAliasRecord",  # Logical id inside the template
            zone=hosted_zone,  # Hosted zone that owns the domain
            record_name="www",  # Relative name (www.<apex>) for the website hostname
            target=route53.RecordTarget.from_alias(  # Route 53 alias target wrapper
                route53_targets.CloudFrontTarget(self.distribution),  # Point to this distribution
            ),  # End alias target
        )  # End A record definition
        Tags.of(self).add("Project", "dtl-global-platform")  # Tag stack for cost tracking
