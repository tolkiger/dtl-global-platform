"""Pipeline stack: CodePipeline that builds and deploys the CDK app via CodeBuild."""

from __future__ import annotations

from aws_cdk import Stack, Tags  # CDK core helpers
from aws_cdk import aws_codebuild as codebuild  # CodeBuild project for CDK deploy
from aws_cdk import aws_codepipeline as codepipeline  # CodePipeline service
from aws_cdk import aws_codepipeline_actions as codepipeline_actions  # Pipeline action helpers
from aws_cdk import aws_iam as iam  # IAM roles for CodeBuild
from constructs import Construct  # Base construct class


class PipelineStack(Stack):
    """Continuous delivery pipeline backed by an existing CodeStar connection."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        github_owner: str,
        github_repo: str,
        connection_arn: str,
        **kwargs: object,
    ) -> None:
        """Create a source->build pipeline for this repository.

        Args:
            scope: Parent construct (typically the CDK app).
            construct_id: Logical stack identifier.
            github_owner: GitHub owner or organization (must match the CodeStar connection).
            github_repo: GitHub repository name (without ``.git``).
            connection_arn: CodeStar connection ARN for GitHub integration.
            **kwargs: Passed through to ``Stack`` (env, stackName, etc.).
        """
        super().__init__(scope, construct_id, **kwargs)  # Initialize CloudFormation stack
        source_artifact = codepipeline.Artifact("SourceArtifact")  # Source checkout output
        source_action = codepipeline_actions.CodeStarConnectionsSourceAction(  # GitHub source via CodeStar
            action_name="GitHub_Source",  # Stage action name
            owner=github_owner,  # GitHub namespace
            repo=github_repo,  # Repository name
            branch="main",  # Default branch for deployments
            connection_arn=connection_arn,  # Existing CodeStar connection ARN
            output=source_artifact,  # Feed the build stage
            trigger_on_push=True,  # Start pipeline on pushes to main
        )  # End source action
        build_role = iam.Role(  # Role assumed by CodeBuild during synth and deploy
            self,  # Parent construct is this stack
            "CodeBuildDeployRole",  # Logical id inside the template
            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),  # CodeBuild service principal
            managed_policies=[  # Attach AWS managed policies for CDK deployments
                iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess"),  # Broad access for CDK bootstrap
            ],  # End managed policies list
        )  # End role definition
        build_project = codebuild.PipelineProject(  # Project that runs buildspec.yml at repo root
            self,  # Parent construct is this stack
            "CdkDeployProject",  # Logical id inside the template
            project_name="dtl-global-platform-cdk-deploy",  # Console-visible project name
            role=build_role,  # Use the deploy role defined above
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec.yml"),  # Standard buildspec location
            environment=codebuild.BuildEnvironment(  # Build container settings
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,  # Amazon Linux 2023 image with runtimes
                privileged=False,  # Privileged mode not required for CDK
            ),  # End environment
        )  # End CodeBuild project definition
        build_action = codepipeline_actions.CodeBuildAction(  # Build action consuming the source artifact
            action_name="Cdk_Deploy",  # Stage action name
            project=build_project,  # CodeBuild project to execute
            input=source_artifact,  # Use the GitHub checkout as input
        )  # End build action
        codepipeline.Pipeline(  # Top-level pipeline with two stages (V2: recommended execution model)
            self,  # Parent construct is this stack
            "DtlDeploymentPipeline",  # Logical id inside the template
            pipeline_name="dtl-global-platform-deploy",  # Console-visible pipeline name
            pipeline_type=codepipeline.PipelineType.V2,  # Explicit V2 to avoid implicit V1 and match current defaults
            stages=[  # Ordered pipeline stages
                codepipeline.StageProps(  # Source stage
                    stage_name="Source",  # Human-readable stage name
                    actions=[source_action],  # Single GitHub checkout action
                ),  # End source stage
                codepipeline.StageProps(  # Build stage
                    stage_name="Build",  # Human-readable stage name
                    actions=[build_action],  # Single CodeBuild deploy action
                ),  # End build stage
            ],  # End stages list
        )  # End pipeline definition
        Tags.of(self).add("Project", "dtl-global-platform")  # Tag stack for cost tracking
