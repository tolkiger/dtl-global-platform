"""SSL stack: ACM certificate with DNS validation in the DTL-Global hosted zone."""

from __future__ import annotations

from aws_cdk import Stack, Tags  # CDK core helpers
from aws_cdk import aws_certificatemanager as acm  # ACM certificate constructs
from aws_cdk import aws_route53 as route53  # Hosted zone reference for validation
from constructs import Construct  # Base construct class


class SslStack(Stack):
    """Issue an ACM certificate suitable for CloudFront custom domain names."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        hosted_zone: route53.IHostedZone,
        domain_name: str,
        **kwargs: object,
    ) -> None:
        """Create a wildcard + apex certificate for ``domain_name``.

        Args:
            scope: Parent construct (typically the CDK app).
            construct_id: Logical stack identifier.
            hosted_zone: Route 53 hosted zone used for DNS validation records.
            domain_name: Apex domain (for example ``dtl-global.com``).
            **kwargs: Passed through to ``Stack`` (env, stackName, etc.).
        """
        super().__init__(scope, construct_id, **kwargs)  # Initialize CloudFormation stack
        self.certificate = acm.Certificate(  # DNS-validated certificate for HTTPS
            self,  # Parent construct is this stack
            "DtlCertificate",  # Logical id inside the template
            domain_name=domain_name,  # Primary name on the certificate
            subject_alternative_names=[f"*.{domain_name}"],  # Wildcard for subdomains
            validation=acm.CertificateValidation.from_dns(hosted_zone),  # Create DNS validation records
        )  # End certificate definition
        Tags.of(self).add("Project", "dtl-global-platform")  # Tag stack for cost tracking
