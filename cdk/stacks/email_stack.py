"""Email stack: SES identity for the DTL-Global sending domain."""

from __future__ import annotations

from aws_cdk import Stack, Tags  # CDK core helpers
from aws_cdk import aws_ses as ses  # SES email identity resource
from constructs import Construct  # Base construct class


class EmailStack(Stack):
    """Create a SES domain identity for outbound onboarding email."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        domain_name: str,
        **kwargs: object,
    ) -> None:
        """Create a domain identity for ``domain_name``.

        Args:
            scope: Parent construct (typically the CDK app).
            construct_id: Logical stack identifier.
            domain_name: Apex domain used for SES domain verification (for example ``dtl-global.org``).
            **kwargs: Passed through to ``Stack`` (env, stackName, etc.).

        Note:
            Domain verification may require manual DNS steps in SES if records are not automated.
        """
        super().__init__(scope, construct_id, **kwargs)  # Initialize CloudFormation stack
        self.email_identity = ses.CfnEmailIdentity(  # Domain identity for SES sending
            self,  # Parent construct is this stack
            "SesDomainIdentity",  # Logical id inside the template
            email_identity=domain_name,  # Verify the apex domain in SES
        )  # End SES domain identity definition
        Tags.of(self).add("Project", "dtl-global-platform")  # Tag stack for cost tracking
