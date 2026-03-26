#!/usr/bin/env python3
"""Setup HubSpot automations from YAML configuration.

This script reads config/hubspot_automations.yaml and creates all the defined
automation components in HubSpot via API. It's designed to be idempotent - 
running it multiple times will skip existing items.

Dependencies:
- PyYAML for configuration parsing
- HubSpot API client for CRM operations
- Local .env file with HUBSPOT_ACCESS_TOKEN

Author: DTL-Global Platform
"""

import os
import sys
import yaml
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'engine', 'shared'))

# Import shared modules
from config import config
from hubspot_client import hubspot_client


def load_automation_config() -> Dict[str, Any]:
    """Load HubSpot automation configuration from YAML file.
    
    Returns:
        Dictionary containing all automation definitions
        
    Raises:
        FileNotFoundError: If config/hubspot_automations.yaml doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'hubspot_automations.yaml')
    
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)  # Parse YAML configuration
        
        print(f"Loaded automation config from {config_path}")
        return config_data
        
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found: {config_path}")
        raise
    except yaml.YAMLError as e:
        print(f"ERROR: Failed to parse YAML configuration: {e}")
        raise


def add_pipeline_stage(stage_name: str, display_order: int) -> bool:
    """Add a new stage to the default HubSpot deals pipeline.
    
    Args:
        stage_name: Name of the stage to add (e.g., "Churned")
        display_order: Order position in the pipeline
        
    Returns:
        True if stage was created or already exists, False on error
    """
    try:
        print(f"Adding pipeline stage: {stage_name} (order: {display_order})")
        
        # Check if stage already exists
        existing_stages = hubspot_client.get_pipeline_stages()  # Get current pipeline stages
        for stage in existing_stages:
            if stage.get('label', '').lower() == stage_name.lower():
                print(f"Stage '{stage_name}' already exists, skipping")
                return True
        
        # Create new pipeline stage
        stage_data = {
            'label': stage_name,  # Display name for the stage
            'displayOrder': display_order,  # Position in pipeline
            'metadata': {
                'isClosed': stage_name.lower() in ['churned', 'lost', 'cancelled']  # Mark terminal stages as closed
            }
        }
        
        result = hubspot_client.create_pipeline_stage(stage_data)  # Create stage via HubSpot API
        if result:
            print(f"Successfully created pipeline stage: {stage_name}")
            return True
        else:
            print(f"Failed to create pipeline stage: {stage_name}")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to add pipeline stage '{stage_name}': {e}")
        return False


def create_email_template(name: str, subject: str, body: str) -> bool:
    """Create a marketing email template in HubSpot.
    
    Args:
        name: Template name for identification
        subject: Email subject line
        body: HTML email body content
        
    Returns:
        True if template was created or already exists, False on error
    """
    try:
        print(f"Creating email template: {name}")
        
        # Check if template already exists
        existing_templates = hubspot_client.get_email_templates()  # Get current email templates
        for template in existing_templates:
            if template.get('name', '').lower() == name.lower():
                print(f"Email template '{name}' already exists, skipping")
                return True
        
        # Create new email template
        template_data = {
            'name': name,  # Template identifier
            'subject': subject,  # Email subject line
            'htmlBody': body,  # HTML content for email
            'templateType': 'REGULAR',  # Regular marketing email type
        }
        
        result = hubspot_client.create_email_template(template_data)  # Create template via HubSpot API
        if result:
            print(f"Successfully created email template: {name}")
            return True
        else:
            print(f"Failed to create email template: {name}")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to create email template '{name}': {e}")
        return False


def create_workflow(name: str, trigger: Dict[str, Any], actions: List[Dict[str, Any]]) -> bool:
    """Create an automation workflow in HubSpot.
    
    Note: HubSpot Starter plan has LIMITED workflow capabilities.
    If the API doesn't support full workflow creation, this will print
    manual setup instructions instead.
    
    Args:
        name: Workflow name for identification
        trigger: Workflow trigger configuration
        actions: List of workflow actions to execute
        
    Returns:
        True if workflow was created or manual instructions provided, False on error
    """
    try:
        print(f"Creating workflow: {name}")
        
        # Check if workflow already exists
        existing_workflows = hubspot_client.get_workflows()  # Get current workflows
        if existing_workflows:
            for workflow in existing_workflows:
                if workflow.get('name', '').lower() == name.lower():
                    print(f"Workflow '{name}' already exists, skipping")
                    return True
        
        # Try to create workflow via API
        workflow_data = {
            'name': name,  # Workflow identifier
            'type': 'DRIP_DELAY',  # Sequential workflow type
            'enabled': True,  # Activate workflow immediately
            'triggerSets': [trigger],  # Workflow trigger conditions
            'actions': actions,  # Actions to execute when triggered
        }
        
        try:
            result = hubspot_client.create_workflow(workflow_data)  # Create workflow via HubSpot API
            if result:
                print(f"Successfully created workflow: {name}")
                return True
            else:
                print(f"Workflow creation failed, providing manual instructions for: {name}")
                _print_manual_workflow_instructions(name, trigger, actions)
                return True
                
        except Exception as api_error:
            # HubSpot Starter plan may not support workflow API
            print(f"Workflow API not available (likely Starter plan limitation)")
            print(f"Providing manual setup instructions for: {name}")
            _print_manual_workflow_instructions(name, trigger, actions)
            return True
            
    except Exception as e:
        print(f"ERROR: Failed to create workflow '{name}': {e}")
        return False


def create_sequence(name: str, emails: List[Dict[str, Any]]) -> bool:
    """Create an email sequence in HubSpot.
    
    Args:
        name: Sequence name for identification
        emails: List of email configurations in the sequence
        
    Returns:
        True if sequence was created or already exists, False on error
    """
    try:
        print(f"Creating email sequence: {name}")
        
        # Check if sequence already exists
        existing_sequences = hubspot_client.get_sequences()  # Get current email sequences
        if existing_sequences:
            for sequence in existing_sequences:
                if sequence.get('name', '').lower() == name.lower():
                    print(f"Email sequence '{name}' already exists, skipping")
                    return True
        
        # Create new email sequence
        sequence_data = {
            'name': name,  # Sequence identifier
            'steps': []  # Email steps in the sequence
        }
        
        # Add each email as a sequence step
        for i, email in enumerate(emails):
            step = {
                'order': i + 1,  # Step order in sequence
                'delay': email.get('delay_days', 1) * 24 * 60 * 60 * 1000,  # Delay in milliseconds
                'templateId': email.get('template_id'),  # Email template to send
                'subject': email.get('subject', ''),  # Email subject line
            }
            sequence_data['steps'].append(step)
        
        result = hubspot_client.create_sequence(sequence_data)  # Create sequence via HubSpot API
        if result:
            print(f"Successfully created email sequence: {name}")
            return True
        else:
            print(f"Failed to create email sequence: {name}")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to create email sequence '{name}': {e}")
        return False


def _print_manual_workflow_instructions(name: str, trigger: Dict[str, Any], actions: List[Dict[str, Any]]) -> None:
    """Print manual setup instructions for HubSpot workflow.
    
    Args:
        name: Workflow name
        trigger: Trigger configuration
        actions: List of actions to perform
    """
    print(f"\n=== MANUAL SETUP REQUIRED: {name} ===")
    print("Go to HubSpot > Automation > Workflows and create manually:")
    print(f"1. Workflow Name: {name}")
    print(f"2. Trigger: {trigger.get('type', 'Unknown')} - {trigger.get('description', 'See YAML config')}")
    print("3. Actions:")
    for i, action in enumerate(actions, 1):
        print(f"   {i}. {action.get('type', 'Unknown')} - {action.get('description', 'See YAML config')}")
    print("4. Save and activate the workflow")
    print("=" * 50)


def main():
    """Main function to set up all HubSpot automations."""
    print("DTL-Global HubSpot Automation Setup")
    print("=" * 40)
    
    try:
        # Load automation configuration
        automation_config = load_automation_config()
        
        # Track setup results
        results = {
            'pipeline_stages': {'created': 0, 'skipped': 0, 'failed': 0},
            'email_templates': {'created': 0, 'skipped': 0, 'failed': 0},
            'workflows': {'created': 0, 'skipped': 0, 'failed': 0},
            'sequences': {'created': 0, 'skipped': 0, 'failed': 0}
        }
        
        # Set up pipeline stages
        print("\n--- Setting up Pipeline Stages ---")
        pipeline_config = automation_config.get('pipeline_stages', {})
        for stage_name, stage_info in pipeline_config.items():
            display_order = stage_info.get('display_order', 999)  # Default to end of pipeline
            if add_pipeline_stage(stage_name, display_order):
                results['pipeline_stages']['created'] += 1
            else:
                results['pipeline_stages']['failed'] += 1
        
        # Set up email templates
        print("\n--- Setting up Email Templates ---")
        templates_config = automation_config.get('email_templates', {})
        for template_name, template_info in templates_config.items():
            subject = template_info.get('subject', f'Template: {template_name}')
            body = template_info.get('body', '<p>Default template body</p>')
            if create_email_template(template_name, subject, body):
                results['email_templates']['created'] += 1
            else:
                results['email_templates']['failed'] += 1
        
        # Set up workflows
        print("\n--- Setting up Workflows ---")
        workflows_config = automation_config.get('workflows', {})
        for workflow_name, workflow_info in workflows_config.items():
            trigger = workflow_info.get('trigger', {})
            actions = workflow_info.get('actions', [])
            if create_workflow(workflow_name, trigger, actions):
                results['workflows']['created'] += 1
            else:
                results['workflows']['failed'] += 1
        
        # Set up email sequences
        print("\n--- Setting up Email Sequences ---")
        sequences_config = automation_config.get('sequences', {})
        for sequence_name, sequence_info in sequences_config.items():
            emails = sequence_info.get('emails', [])
            if create_sequence(sequence_name, emails):
                results['sequences']['created'] += 1
            else:
                results['sequences']['failed'] += 1
        
        # Print summary
        print("\n" + "=" * 40)
        print("SETUP SUMMARY")
        print("=" * 40)
        for category, counts in results.items():
            total = counts['created'] + counts['skipped'] + counts['failed']
            print(f"{category.replace('_', ' ').title()}: {total} total")
            print(f"  Created: {counts['created']}")
            print(f"  Skipped: {counts['skipped']}")
            print(f"  Failed: {counts['failed']}")
        
        # Check for any failures
        total_failures = sum(counts['failed'] for counts in results.values())
        if total_failures > 0:
            print(f"\nWARNING: {total_failures} items failed to set up")
            sys.exit(1)
        else:
            print("\nAll automations set up successfully!")
            sys.exit(0)
            
    except Exception as e:
        print(f"FATAL ERROR: Automation setup failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()