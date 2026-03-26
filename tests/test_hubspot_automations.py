"""Tests for HubSpot automation setup script."""

import os
import tempfile
import yaml
import pytest
from unittest.mock import Mock, patch, mock_open
from typing import Dict, Any

# Import the setup script
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'engine', 'shared'))

from setup_hubspot_automations import (
    load_automation_config,
    add_pipeline_stage,
    create_email_template,
    create_workflow,
    create_sequence
)


class TestAutomationConfigLoading:
    """Test cases for YAML configuration loading."""
    
    def test_load_automation_config_success(self):
        """Test successful loading of automation configuration."""
        # Arrange
        test_config = {
            'pipeline_stages': {
                'Churned': {'display_order': 99}
            },
            'email_templates': {
                'Welcome Email': {
                    'subject': 'Welcome to DTL-Global',
                    'body': '<p>Welcome!</p>'
                }
            }
        }
        
        yaml_content = yaml.dump(test_config)
        
        # Mock file reading
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            with patch('os.path.join') as mock_join:
                mock_join.return_value = 'config/hubspot_automations.yaml'
                
                # Act
                result = load_automation_config()
                
                # Assert
                assert result == test_config
                assert 'pipeline_stages' in result
                assert 'email_templates' in result
    
    def test_load_automation_config_file_not_found(self):
        """Test handling of missing configuration file."""
        # Arrange
        with patch('builtins.open', side_effect=FileNotFoundError()):
            with patch('os.path.join') as mock_join:
                mock_join.return_value = 'nonexistent/config.yaml'
                
                # Act & Assert
                with pytest.raises(FileNotFoundError):
                    load_automation_config()
    
    def test_load_automation_config_invalid_yaml(self):
        """Test handling of invalid YAML content."""
        # Arrange
        invalid_yaml = "invalid: yaml: content: [unclosed"
        
        with patch('builtins.open', mock_open(read_data=invalid_yaml)):
            with patch('os.path.join') as mock_join:
                mock_join.return_value = 'config/hubspot_automations.yaml'
                
                # Act & Assert
                with pytest.raises(yaml.YAMLError):
                    load_automation_config()


class TestPipelineStageCreation:
    """Test cases for HubSpot pipeline stage creation."""
    
    @patch('setup_hubspot_automations.hubspot_client')
    def test_add_pipeline_stage_success(self, mock_hubspot_client):
        """Test successful creation of new pipeline stage."""
        # Arrange
        mock_hubspot_client.get_pipeline_stages.return_value = []  # No existing stages
        mock_hubspot_client.create_pipeline_stage.return_value = {'id': 'stage_123'}
        
        # Act
        result = add_pipeline_stage('Churned', 99)
        
        # Assert
        assert result is True
        mock_hubspot_client.create_pipeline_stage.assert_called_once()
        call_args = mock_hubspot_client.create_pipeline_stage.call_args[0][0]
        assert call_args['label'] == 'Churned'
        assert call_args['displayOrder'] == 99
        assert call_args['metadata']['isClosed'] is True  # Churned should be closed stage
    
    @patch('setup_hubspot_automations.hubspot_client')
    def test_add_pipeline_stage_already_exists(self, mock_hubspot_client):
        """Test skipping creation when stage already exists."""
        # Arrange
        existing_stages = [
            {'label': 'Churned', 'id': 'existing_stage_123'}
        ]
        mock_hubspot_client.get_pipeline_stages.return_value = existing_stages
        
        # Act
        result = add_pipeline_stage('Churned', 99)
        
        # Assert
        assert result is True
        mock_hubspot_client.create_pipeline_stage.assert_not_called()  # Should skip creation
    
    @patch('setup_hubspot_automations.hubspot_client')
    def test_add_pipeline_stage_creation_failure(self, mock_hubspot_client):
        """Test handling of pipeline stage creation failure."""
        # Arrange
        mock_hubspot_client.get_pipeline_stages.return_value = []
        mock_hubspot_client.create_pipeline_stage.return_value = None  # Creation failed
        
        # Act
        result = add_pipeline_stage('Churned', 99)
        
        # Assert
        assert result is False
    
    @patch('setup_hubspot_automations.hubspot_client')
    def test_add_pipeline_stage_api_exception(self, mock_hubspot_client):
        """Test handling of API exceptions during stage creation."""
        # Arrange
        mock_hubspot_client.get_pipeline_stages.side_effect = Exception('API Error')
        
        # Act
        result = add_pipeline_stage('Churned', 99)
        
        # Assert
        assert result is False


class TestEmailTemplateCreation:
    """Test cases for HubSpot email template creation."""
    
    @patch('setup_hubspot_automations.hubspot_client')
    def test_create_email_template_success(self, mock_hubspot_client):
        """Test successful creation of email template."""
        # Arrange
        mock_hubspot_client.get_email_templates.return_value = []  # No existing templates
        mock_hubspot_client.create_email_template.return_value = {'id': 'template_123'}
        
        # Act
        result = create_email_template('Welcome Email', 'Welcome!', '<p>Welcome to DTL-Global</p>')
        
        # Assert
        assert result is True
        mock_hubspot_client.create_email_template.assert_called_once()
        call_args = mock_hubspot_client.create_email_template.call_args[0][0]
        assert call_args['name'] == 'Welcome Email'
        assert call_args['subject'] == 'Welcome!'
        assert call_args['htmlBody'] == '<p>Welcome to DTL-Global</p>'
        assert call_args['templateType'] == 'REGULAR'
    
    @patch('setup_hubspot_automations.hubspot_client')
    def test_create_email_template_already_exists(self, mock_hubspot_client):
        """Test skipping creation when template already exists."""
        # Arrange
        existing_templates = [
            {'name': 'Welcome Email', 'id': 'existing_template_123'}
        ]
        mock_hubspot_client.get_email_templates.return_value = existing_templates
        
        # Act
        result = create_email_template('Welcome Email', 'Welcome!', '<p>Welcome</p>')
        
        # Assert
        assert result is True
        mock_hubspot_client.create_email_template.assert_not_called()  # Should skip creation
    
    @patch('setup_hubspot_automations.hubspot_client')
    def test_create_email_template_creation_failure(self, mock_hubspot_client):
        """Test handling of email template creation failure."""
        # Arrange
        mock_hubspot_client.get_email_templates.return_value = []
        mock_hubspot_client.create_email_template.return_value = None  # Creation failed
        
        # Act
        result = create_email_template('Welcome Email', 'Welcome!', '<p>Welcome</p>')
        
        # Assert
        assert result is False


class TestWorkflowCreation:
    """Test cases for HubSpot workflow creation."""
    
    @patch('setup_hubspot_automations.hubspot_client')
    @patch('setup_hubspot_automations._print_manual_workflow_instructions')
    def test_create_workflow_success(self, mock_print_instructions, mock_hubspot_client):
        """Test successful creation of workflow."""
        # Arrange
        mock_hubspot_client.get_workflows.return_value = []  # No existing workflows
        mock_hubspot_client.create_workflow.return_value = {'id': 'workflow_123'}
        
        trigger = {'type': 'PROPERTY_CHANGE', 'property': 'dealstage'}
        actions = [{'type': 'SEND_EMAIL', 'template_id': 'template_123'}]
        
        # Act
        result = create_workflow('Welcome Sequence', trigger, actions)
        
        # Assert
        assert result is True
        mock_hubspot_client.create_workflow.assert_called_once()
        mock_print_instructions.assert_not_called()  # Should not print manual instructions
    
    @patch('setup_hubspot_automations.hubspot_client')
    @patch('setup_hubspot_automations._print_manual_workflow_instructions')
    def test_create_workflow_api_limitation(self, mock_print_instructions, mock_hubspot_client):
        """Test handling of workflow API limitations (Starter plan)."""
        # Arrange
        mock_hubspot_client.get_workflows.return_value = []
        mock_hubspot_client.create_workflow.side_effect = Exception('API not available')
        
        trigger = {'type': 'PROPERTY_CHANGE', 'property': 'dealstage'}
        actions = [{'type': 'SEND_EMAIL', 'template_id': 'template_123'}]
        
        # Act
        result = create_workflow('Welcome Sequence', trigger, actions)
        
        # Assert
        assert result is True  # Should still return True (manual instructions provided)
        mock_print_instructions.assert_called_once_with('Welcome Sequence', trigger, actions)
    
    @patch('setup_hubspot_automations.hubspot_client')
    def test_create_workflow_already_exists(self, mock_hubspot_client):
        """Test skipping creation when workflow already exists."""
        # Arrange
        existing_workflows = [
            {'name': 'Welcome Sequence', 'id': 'existing_workflow_123'}
        ]
        mock_hubspot_client.get_workflows.return_value = existing_workflows
        
        trigger = {'type': 'PROPERTY_CHANGE', 'property': 'dealstage'}
        actions = [{'type': 'SEND_EMAIL', 'template_id': 'template_123'}]
        
        # Act
        result = create_workflow('Welcome Sequence', trigger, actions)
        
        # Assert
        assert result is True
        mock_hubspot_client.create_workflow.assert_not_called()  # Should skip creation


class TestSequenceCreation:
    """Test cases for HubSpot email sequence creation."""
    
    @patch('setup_hubspot_automations.hubspot_client')
    def test_create_sequence_success(self, mock_hubspot_client):
        """Test successful creation of email sequence."""
        # Arrange
        mock_hubspot_client.get_sequences.return_value = []  # No existing sequences
        mock_hubspot_client.create_sequence.return_value = {'id': 'sequence_123'}
        
        emails = [
            {'template_id': 'template_1', 'delay_days': 1, 'subject': 'Day 1'},
            {'template_id': 'template_2', 'delay_days': 3, 'subject': 'Day 3'}
        ]
        
        # Act
        result = create_sequence('Onboarding Sequence', emails)
        
        # Assert
        assert result is True
        mock_hubspot_client.create_sequence.assert_called_once()
        call_args = mock_hubspot_client.create_sequence.call_args[0][0]
        assert call_args['name'] == 'Onboarding Sequence'
        assert len(call_args['steps']) == 2
        assert call_args['steps'][0]['order'] == 1
        assert call_args['steps'][1]['order'] == 2
    
    @patch('setup_hubspot_automations.hubspot_client')
    def test_create_sequence_already_exists(self, mock_hubspot_client):
        """Test skipping creation when sequence already exists."""
        # Arrange
        existing_sequences = [
            {'name': 'Onboarding Sequence', 'id': 'existing_sequence_123'}
        ]
        mock_hubspot_client.get_sequences.return_value = existing_sequences
        
        emails = [{'template_id': 'template_1', 'delay_days': 1}]
        
        # Act
        result = create_sequence('Onboarding Sequence', emails)
        
        # Assert
        assert result is True
        mock_hubspot_client.create_sequence.assert_not_called()  # Should skip creation
    
    @patch('setup_hubspot_automations.hubspot_client')
    def test_create_sequence_creation_failure(self, mock_hubspot_client):
        """Test handling of sequence creation failure."""
        # Arrange
        mock_hubspot_client.get_sequences.return_value = []
        mock_hubspot_client.create_sequence.return_value = None  # Creation failed
        
        emails = [{'template_id': 'template_1', 'delay_days': 1}]
        
        # Act
        result = create_sequence('Onboarding Sequence', emails)
        
        # Assert
        assert result is False


class TestIdempotency:
    """Test cases for idempotent behavior of automation setup."""
    
    @patch('setup_hubspot_automations.hubspot_client')
    def test_multiple_runs_skip_existing_items(self, mock_hubspot_client):
        """Test that multiple runs skip already existing items."""
        # Arrange - simulate existing items
        mock_hubspot_client.get_pipeline_stages.return_value = [
            {'label': 'Churned', 'id': 'existing_stage'}
        ]
        mock_hubspot_client.get_email_templates.return_value = [
            {'name': 'Welcome Email', 'id': 'existing_template'}
        ]
        
        # Act
        stage_result = add_pipeline_stage('Churned', 99)
        template_result = create_email_template('Welcome Email', 'Subject', 'Body')
        
        # Assert
        assert stage_result is True
        assert template_result is True
        mock_hubspot_client.create_pipeline_stage.assert_not_called()
        mock_hubspot_client.create_email_template.assert_not_called()


if __name__ == '__main__':
    pytest.main([__file__])