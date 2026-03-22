#!/usr/bin/env python3
"""Basic infrastructure tests for DTL-Global Platform Phase 1.

Tests verify that CDK stacks can be synthesized and basic configurations
are correct. These are smoke tests to catch obvious issues before deployment.

Per DTL_MASTER_PLAN.md Phase 1 gate requirements
Per Rule 002: Every line commented for Gerardo's understanding
Per Rule 009: Error handling with try/except blocks
"""

from __future__ import annotations

import json  # JSON parsing for CDK template validation
import os  # File system operations for template reading
import unittest  # Python unit testing framework
from pathlib import Path  # Modern path handling for file operations


class TestPhase1Infrastructure(unittest.TestCase):
    """Test suite for Phase 1 CDK infrastructure validation."""

    def setUp(self) -> None:
        """Set up test environment and locate CDK output directory.
        
        Finds the cdk.out directory and prepares for template validation.
        Called before each test method execution.
        """
        # Find the project root directory (contains DTL_MASTER_PLAN.md)
        self.project_root = Path(__file__).parent.parent  # Go up from tests/ to project root
        self.cdk_out_dir = self.project_root / "cdk" / "cdk.out"  # CDK output directory path
        
        # Verify CDK output exists (templates have been synthesized)
        self.assertTrue(  # Assert CDK output directory exists
            self.cdk_out_dir.exists(),  # Check if cdk.out directory is present
            "CDK output directory not found. Run 'cdk synth' first."  # Error message for missing output
        )  # End CDK output verification

    def test_all_seven_stacks_exist(self) -> None:
        """Verify all 7 Phase 1 stacks have CloudFormation templates.
        
        Per DTL_MASTER_PLAN.md Section 9.3: Storage, CDN, DNS, SSL, Email, API, Pipeline
        """
        # Expected stack names from master plan Section 9.3
        expected_stacks = [  # List of all Phase 1 stack names
            "DtlStorage",  # DynamoDB tables and S3 buckets
            "DtlCdn",  # CloudFront distribution and client websites bucket
            "DtlDns",  # Route 53 hosted zone
            "DtlSsl",  # ACM certificate
            "DtlEmail",  # SES domain identity
            "DtlApi",  # API Gateway and Lambda functions
            "DtlPipeline",  # CodePipeline and CodeBuild
        ]  # End expected stacks list
        
        # Check each stack has a CloudFormation template
        for stack_name in expected_stacks:  # Iterate through expected stack names
            template_file = self.cdk_out_dir / f"{stack_name}.template.json"  # Template file path
            self.assertTrue(  # Assert template file exists
                template_file.exists(),  # Check if template file is present
                f"Missing CloudFormation template for stack: {stack_name}"  # Error message for missing template
            )  # End template existence check
            
            # Verify template is valid JSON
            try:  # Attempt to parse template as JSON
                with open(template_file, 'r') as f:  # Open template file for reading
                    template_data = json.load(f)  # Parse JSON content
                self.assertIsInstance(template_data, dict)  # Verify template is a dictionary
                self.assertIn("Resources", template_data)  # Verify template has Resources section
                
            except json.JSONDecodeError as e:  # Handle JSON parsing errors
                self.fail(f"Invalid JSON in template {stack_name}: {str(e)}")  # Fail test with error details
            except Exception as e:  # Handle file reading errors
                self.fail(f"Error reading template {stack_name}: {str(e)}")  # Fail test with error details

    def test_storage_stack_resources(self) -> None:
        """Verify Storage stack contains required DynamoDB tables and S3 buckets.
        
        Per DTL_MASTER_PLAN.md Section 9.3: 3 DynamoDB tables, 2 S3 buckets in Storage stack
        """
        # Load Storage stack template
        storage_template_path = self.cdk_out_dir / "DtlStorage.template.json"  # Storage template file path
        
        try:  # Attempt to load and parse Storage template
            with open(storage_template_path, 'r') as f:  # Open Storage template file
                storage_template = json.load(f)  # Parse template JSON content
                
        except Exception as e:  # Handle file or JSON errors
            self.fail(f"Failed to load Storage stack template: {str(e)}")  # Fail test with error details
            
        resources = storage_template.get("Resources", {})  # Extract Resources section from template
        
        # Count DynamoDB tables in template
        dynamodb_tables = [  # List comprehension to find DynamoDB table resources
            resource_name for resource_name, resource_data in resources.items()  # Iterate through all resources
            if resource_data.get("Type") == "AWS::DynamoDB::Table"  # Filter for DynamoDB table type
        ]  # End DynamoDB tables list comprehension
        
        self.assertEqual(  # Assert correct number of DynamoDB tables
            len(dynamodb_tables), 3,  # Expected count is 3 tables
            f"Expected 3 DynamoDB tables, found {len(dynamodb_tables)}: {dynamodb_tables}"  # Error message with details
        )  # End DynamoDB table count assertion
        
        # Count S3 buckets in Storage stack (assets and CSV import buckets)
        s3_buckets = [  # List comprehension to find S3 bucket resources
            resource_name for resource_name, resource_data in resources.items()  # Iterate through all resources
            if resource_data.get("Type") == "AWS::S3::Bucket"  # Filter for S3 bucket type
        ]  # End S3 buckets list comprehension
        
        self.assertEqual(  # Assert correct number of S3 buckets in Storage stack
            len(s3_buckets), 2,  # Expected count is 2 buckets (assets + CSV import)
            f"Expected 2 S3 buckets in Storage stack, found {len(s3_buckets)}: {s3_buckets}"  # Error message with details
        )  # End S3 bucket count assertion

    def test_api_stack_endpoints(self) -> None:
        """Verify API stack contains 12 Lambda functions and API Gateway routes.
        
        Per DTL_MASTER_PLAN.md Section 9.3: 12 API endpoints with Lambda integrations
        """
        # Load API stack template
        api_template_path = self.cdk_out_dir / "DtlApi.template.json"  # API template file path
        
        try:  # Attempt to load and parse API template
            with open(api_template_path, 'r') as f:  # Open API template file
                api_template = json.load(f)  # Parse template JSON content
                
        except Exception as e:  # Handle file or JSON errors
            self.fail(f"Failed to load API stack template: {str(e)}")  # Fail test with error details
            
        resources = api_template.get("Resources", {})  # Extract Resources section from template
        
        # Count Lambda functions in template
        lambda_functions = [  # List comprehension to find Lambda function resources
            resource_name for resource_name, resource_data in resources.items()  # Iterate through all resources
            if resource_data.get("Type") == "AWS::Lambda::Function"  # Filter for Lambda function type
        ]  # End Lambda functions list comprehension
        
        self.assertEqual(  # Assert correct number of Lambda functions
            len(lambda_functions), 12,  # Expected count is 12 functions
            f"Expected 12 Lambda functions, found {len(lambda_functions)}: {lambda_functions}"  # Error message with details
        )  # End Lambda function count assertion
        
        # Verify API Gateway exists
        api_gateways = [  # List comprehension to find API Gateway resources
            resource_name for resource_name, resource_data in resources.items()  # Iterate through all resources
            if resource_data.get("Type") == "AWS::ApiGateway::RestApi"  # Filter for API Gateway REST API type
        ]  # End API Gateway list comprehension
        
        self.assertGreaterEqual(  # Assert at least one API Gateway exists
            len(api_gateways), 1,  # Minimum expected count is 1
            f"Expected at least 1 API Gateway, found {len(api_gateways)}"  # Error message with count
        )  # End API Gateway existence assertion

    def test_pipeline_stack_codepipeline_v2(self) -> None:
        """Verify Pipeline stack uses CodePipeline V2 as required.
        
        Per DTL_MASTER_PLAN.md Section 9.3: CodePipeline V2 with existing CodeStar connection
        """
        # Load Pipeline stack template
        pipeline_template_path = self.cdk_out_dir / "DtlPipeline.template.json"  # Pipeline template file path
        
        try:  # Attempt to load and parse Pipeline template
            with open(pipeline_template_path, 'r') as f:  # Open Pipeline template file
                pipeline_template = json.load(f)  # Parse template JSON content
                
        except Exception as e:  # Handle file or JSON errors
            self.fail(f"Failed to load Pipeline stack template: {str(e)}")  # Fail test with error details
            
        resources = pipeline_template.get("Resources", {})  # Extract Resources section from template
        
        # Find CodePipeline resource
        pipelines = [  # List comprehension to find CodePipeline resources
            (resource_name, resource_data) for resource_name, resource_data in resources.items()  # Get name and data pairs
            if resource_data.get("Type") == "AWS::CodePipeline::Pipeline"  # Filter for CodePipeline type
        ]  # End pipelines list comprehension
        
        self.assertEqual(  # Assert exactly one pipeline exists
            len(pipelines), 1,  # Expected count is 1 pipeline
            f"Expected 1 CodePipeline, found {len(pipelines)}"  # Error message with count
        )  # End pipeline count assertion
        
        # Verify pipeline uses V2 (PipelineType property)
        pipeline_name, pipeline_data = pipelines[0]  # Extract first (and only) pipeline data
        pipeline_properties = pipeline_data.get("Properties", {})  # Get pipeline properties section
        pipeline_type = pipeline_properties.get("PipelineType")  # Extract PipelineType property
        
        self.assertEqual(  # Assert pipeline type is V2
            pipeline_type, "V2",  # Expected value is "V2"
            f"Expected CodePipeline V2, found type: {pipeline_type}"  # Error message with actual type
        )  # End pipeline type assertion


if __name__ == "__main__":  # Allow running tests directly from command line
    unittest.main()  # Execute all test methods in this module