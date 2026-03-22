#!/usr/bin/env python3
"""CDK application entrypoint for DTL-Global Phase 1 foundation infrastructure."""

from __future__ import annotations

import os  # Read CDK default account/region from the environment

import aws_cdk as cdk  # CDK core application and environment types
from stacks.api_stack import ApiStack  # API Gateway + Lambda onboarding API
from stacks.cdn_stack import CdnStack  # CloudFront distribution for websites
from stacks.dns_stack import DnsStack  # Route 53 hosted zone
from stacks.email_stack import EmailStack  # SES domain identity
from stacks.pipeline_stack import PipelineStack  # CodePipeline + CodeBuild
from stacks.ssl_stack import SslStack  # ACM certificate for HTTPS
from stacks.storage_stack import StorageStack  # DynamoDB + S3 storage layer


def main() -> None:
    """Instantiate Phase 1 stacks and synthesize CloudFormation templates."""
    app = cdk.App()  # CDK application container for all stacks
    env = cdk.Environment(  # Deployment account/region for all stacks
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),  # From AWS profile or CI
        region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),  # Default to us-east-1 for CloudFront + ACM
    )  # End environment definition
    domain_name = str(app.node.try_get_context("domainName") or "dtl-global.com")  # Apex domain for DNS + SES + CDN
    github_owner = str(app.node.try_get_context("githubOwner") or "REPLACE_ME")  # GitHub namespace for CodeStar source
    github_repo = str(app.node.try_get_context("githubRepo") or "dtl-global-platform")  # Repository name for pipeline source
    storage = StorageStack(app, "DtlStorage", env=env)  # Data plane tables and buckets
    dns = DnsStack(app, "DtlDns", env=env, domain_name=domain_name)  # Public hosted zone for DNS validation
    ssl = SslStack(  # TLS certificate for CloudFront and future HTTPS endpoints
        app,  # CDK app scope
        "DtlSsl",  # Stack id
        env=env,  # Target account/region
        hosted_zone=dns.hosted_zone,  # DNS validation records
        domain_name=domain_name,  # Primary name on the certificate
    )  # End SSL stack
    ssl.add_dependency(dns)  # Ensure the hosted zone exists before DNS validation
    EmailStack(app, "DtlEmail", env=env, domain_name=domain_name)  # SES domain identity for outbound mail
    cdn = CdnStack(  # CDN in front of the static website bucket
        app,  # CDK app scope
        "DtlCdn",  # Stack id
        env=env,  # Target account/region
        website_bucket=storage.website_bucket,  # Origin bucket for static sites
        origin_access_identity=storage.website_origin_access_identity,  # OAI lives with bucket policy (no cycles)
        certificate=ssl.certificate,  # TLS cert for the custom domain
        hosted_zone=dns.hosted_zone,  # DNS alias record for www
        website_alias=f"www.{domain_name}",  # Public hostname for client sites
    )  # End CDN stack
    cdn.add_dependency(dns)  # Ensure the hosted zone exists before alias records
    cdn.add_dependency(storage)  # Ensure the bucket exists before the distribution
    cdn.add_dependency(ssl)  # Ensure the certificate exists before the distribution
    api = ApiStack(  # REST API + Lambdas for onboarding
        app,  # CDK app scope
        "DtlApi",  # Stack id
        env=env,  # Target account/region
        templates_table=storage.templates_table,  # Templates table name for env vars
        clients_table=storage.clients_table,  # Clients table name for env vars
        state_table=storage.state_table,  # State table name for env vars
        website_bucket=storage.website_bucket,  # Website bucket name for env vars
        assets_bucket=storage.assets_bucket,  # Assets bucket name for env vars
        csv_import_bucket=storage.csv_import_bucket,  # CSV import bucket name for env vars
    )  # End API stack
    api.add_dependency(storage)  # Ensure tables/buckets exist before IAM grants
    PipelineStack(  # CI/CD pipeline for automated CDK deployments
        app,  # CDK app scope
        "DtlPipeline",  # Stack id
        env=env,  # Target account/region
        github_owner=github_owner,  # GitHub owner for CodeStar source action
        github_repo=github_repo,  # GitHub repo for CodeStar source action
    )  # End pipeline stack
    app.synth()  # Emit CloudFormation templates to cdk.out


if __name__ == "__main__":  # Allow running as a script for local synthesis
    main()  # Execute the CDK app entrypoint
