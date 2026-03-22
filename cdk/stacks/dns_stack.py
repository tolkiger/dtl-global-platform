"""DNS stack: Route 53 hosted zone for the DTL-Global domain."""

from __future__ import annotations

from aws_cdk import Stack, Tags  # CDK core helpers
from aws_cdk import aws_route53 as route53  # Hosted zone construct
from constructs import Construct  # Base construct class


class DnsStack(Stack):
    """Create the public hosted zone used for ACM validation and future records."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        domain_name: str,
        **kwargs: object,
    ) -> None:
        """Create a hosted zone for ``domain_name``.

        Args:
            scope: Parent construct (typically the CDK app).
            construct_id: Logical stack identifier.
            domain_name: Apex domain (for example ``dtl-global.org``).
            **kwargs: Passed through to ``Stack`` (env, stackName, etc.).
        """
        super().__init__(scope, construct_id, **kwargs)  # Initialize CloudFormation stack
        self.domain_name = domain_name  # Store apex domain for sibling stacks
        self.hosted_zone = route53.HostedZone(  # Public DNS zone for DTL-Global
            self,  # Parent construct is this stack
            "DtlHostedZone",  # Logical id inside the template
            zone_name=domain_name,  # Apex domain for the hosted zone
        )  # End hosted zone definition
        Tags.of(self).add("Project", "dtl-global-platform")  # Tag stack for cost tracking
