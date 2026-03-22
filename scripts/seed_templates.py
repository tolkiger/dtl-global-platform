#!/usr/bin/env python3
"""Seed industry templates into DynamoDB for DTL-Global onboarding platform.

This script populates the dtl-industry-templates table with initial template data
for common industries like roofing, plumbing, HVAC, etc. Templates include
HubSpot pipeline configurations, Stripe product mappings, SEO keywords, and
AI chatbot system prompts.

Per DTL_MASTER_PLAN.md Section 15: Industry Templates Schema
Per Rule 002: Every line commented for Gerardo's understanding
Per Rule 009: Error handling with try/except blocks
"""

from __future__ import annotations

import json  # JSON serialization for template data structures
import sys  # Exit codes and command line argument access
from typing import Any, Dict  # Type hints for template data dictionaries

import boto3  # AWS SDK for DynamoDB table operations
from botocore.exceptions import ClientError  # AWS API error handling


def get_roofing_template() -> Dict[str, Any]:
    """Generate the roofing industry template with all required fields.
    
    Returns:
        Dict containing roofing template with HubSpot, Stripe, SEO, and AI config.
        
    Raises:
        None: This function only constructs data, no external calls.
    """
    # Roofing template per DTL_MASTER_PLAN.md Section 15 requirements
    return {
        "template_id": "roofing",  # Primary key for DynamoDB table
        "industry_name": "Roofing & Exterior Services",  # Human-readable industry name
        "description": "Complete roofing contractor template with CRM, payments, and SEO",  # Template description
        "hubspot_config": {  # HubSpot CRM pipeline and properties configuration
            "pipeline_stages": [  # Custom pipeline stages for roofing sales process
                "New Lead",  # Initial contact stage
                "Site Inspection Scheduled",  # Appointment booking stage
                "Estimate Provided",  # Quote delivery stage
                "Contract Signed",  # Deal closure stage
                "Materials Ordered",  # Project preparation stage
                "Work in Progress",  # Active installation stage
                "Job Completed",  # Delivery completion stage
                "Payment Received",  # Financial closure stage
                "Follow-up/Warranty",  # Post-sale relationship stage
            ],  # End pipeline stages list
            "custom_properties": [  # Industry-specific contact and deal properties
                {"name": "roof_type", "label": "Roof Type", "type": "enumeration", "options": ["Shingle", "Metal", "Tile", "Flat"]},  # Roof material classification
                {"name": "roof_size_sqft", "label": "Roof Size (sq ft)", "type": "number"},  # Square footage for pricing
                {"name": "insurance_claim", "label": "Insurance Claim", "type": "bool"},  # Insurance work indicator
                {"name": "emergency_repair", "label": "Emergency Repair", "type": "bool"},  # Urgent work flag
                {"name": "preferred_material", "label": "Preferred Material", "type": "string"},  # Customer material preference
            ],  # End custom properties list
        },  # End HubSpot configuration
        "stripe_products": [  # Stripe product IDs for roofing service packages
            "DTL Starter Setup",  # Basic website + hosting setup product
            "DTL Growth Setup",  # Website + CRM + payments setup product
            "DTL Professional Setup",  # Full package setup product
            "DTL Starter Monthly",  # Basic monthly subscription product
            "DTL Growth Monthly",  # Growth monthly subscription product
            "DTL Professional Monthly",  # Professional monthly subscription product
        ],  # End Stripe products list
        "seo_keywords": [  # Primary SEO keywords for roofing websites
            "roofing contractor",  # Main service keyword
            "roof repair",  # Repair service keyword
            "roof replacement",  # Replacement service keyword
            "emergency roof repair",  # Emergency service keyword
            "residential roofing",  # Residential market keyword
            "commercial roofing",  # Commercial market keyword
            "roof inspection",  # Inspection service keyword
            "storm damage repair",  # Weather damage keyword
            "insurance roof claims",  # Insurance work keyword
            "local roofer",  # Local SEO keyword
        ],  # End SEO keywords list
        "chatbot_system_prompt": "You are a helpful assistant for a roofing contractor. Help visitors understand our services including roof repair, replacement, inspection, and emergency services. Ask about their roof type, size, and whether they have insurance claims. Always encourage them to schedule a free inspection and provide contact information.",  # AI chatbot personality and instructions
        "website_template": "roofing_contractor",  # Website template identifier for deployment
        "created_at": "2026-03-22T00:00:00Z",  # Template creation timestamp
        "updated_at": "2026-03-22T00:00:00Z",  # Last modification timestamp
        "active": True,  # Template availability flag
    }  # End roofing template dictionary


def seed_templates_table() -> None:
    """Populate the industry templates DynamoDB table with initial data.
    
    Creates the roofing template and any other initial templates needed
    for Phase 1 completion. Uses boto3 DynamoDB client with error handling.
    
    Raises:
        ClientError: If DynamoDB operations fail (table not found, permissions, etc.)
        Exception: For any other unexpected errors during seeding.
    """
    try:  # Wrap all DynamoDB operations in error handling
        # Initialize DynamoDB resource for table operations
        dynamodb = boto3.resource('dynamodb')  # AWS DynamoDB service client
        table = dynamodb.Table('dtl-industry-templates')  # Reference to templates table
        
        # Get roofing template data structure
        roofing_template = get_roofing_template()  # Generate roofing industry template
        
        print("Seeding industry templates table...")  # Progress indicator for user
        
        # Insert roofing template into DynamoDB table
        table.put_item(Item=roofing_template)  # Store template with all attributes
        print(f"✓ Added roofing template: {roofing_template['template_id']}")  # Success confirmation
        
        # Verify the template was inserted correctly
        response = table.get_item(Key={'template_id': 'roofing'})  # Retrieve inserted item
        if 'Item' in response:  # Check if item exists in response
            print("✓ Roofing template verified in database")  # Verification success
        else:  # Item not found after insertion
            print("✗ Failed to verify roofing template")  # Verification failure
            sys.exit(1)  # Exit with error code
            
        print("✓ Industry templates seeding completed successfully")  # Overall success message
        
    except ClientError as e:  # Handle AWS DynamoDB specific errors
        error_code = e.response['Error']['Code']  # Extract AWS error code
        error_message = e.response['Error']['Message']  # Extract AWS error message
        print(f"✗ DynamoDB error ({error_code}): {error_message}")  # Display formatted error
        print("Ensure the dtl-industry-templates table exists and you have write permissions")  # Troubleshooting hint
        sys.exit(1)  # Exit with error code
        
    except Exception as e:  # Handle any other unexpected errors
        print(f"✗ Unexpected error during template seeding: {str(e)}")  # Display generic error
        sys.exit(1)  # Exit with error code


def main() -> None:
    """Main script entrypoint for seeding industry templates.
    
    Validates environment and calls the seeding function with proper error handling.
    Script can be run directly or imported as a module.
    """
    print("DTL-Global Platform: Industry Templates Seeder")  # Script identification
    print("=" * 50)  # Visual separator
    
    # Check if running in correct AWS environment
    try:  # Validate AWS credentials and region
        session = boto3.Session()  # Create AWS session
        region = session.region_name  # Get configured AWS region
        print(f"AWS Region: {region}")  # Display current region
        
        if not region:  # No region configured
            print("✗ AWS region not configured. Set AWS_DEFAULT_REGION or configure AWS CLI")  # Error message
            sys.exit(1)  # Exit with error code
            
    except Exception as e:  # Handle AWS configuration errors
        print(f"✗ AWS configuration error: {str(e)}")  # Display configuration error
        print("Run 'aws configure' or set AWS credentials environment variables")  # Troubleshooting hint
        sys.exit(1)  # Exit with error code
    
    # Execute the seeding process
    seed_templates_table()  # Call main seeding function


if __name__ == "__main__":  # Allow script execution from command line
    main()  # Execute main function when run directly