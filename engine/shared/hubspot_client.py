"""HubSpot CRM client for DTL-Global onboarding platform.

This module provides a comprehensive HubSpot API client for managing:
- Contacts and companies
- Deals and pipelines
- Custom properties
- CRM data import and export
- Pipeline stage management

Uses HubSpot Private App authentication with token from SSM Parameter Store.
All operations follow HubSpot API v3 best practices.

Author: DTL-Global Platform
"""

import json
from typing import Dict, List, Optional, Any, Union
from hubspot import HubSpot
from hubspot.crm.contacts import SimplePublicObjectInputForCreate, ApiException
from hubspot.crm.companies import SimplePublicObjectInput as CompanyInput
from hubspot.crm.deals import SimplePublicObjectInputForCreate as DealInput
from hubspot.crm.pipelines import PipelineInput, PipelineStageInput

from config import config


class HubSpotClient:
    """HubSpot CRM client for DTL-Global platform operations.
    
    Provides methods for managing contacts, companies, deals, and pipelines
    in HubSpot CRM. Handles authentication via SSM Parameter Store.
    """
    
    def __init__(self):
        """Initialize HubSpot client with authentication.
        
        Loads HubSpot access token from SSM Parameter Store and creates
        authenticated HubSpot API client instance.
        """
        # Get HubSpot token from SSM Parameter Store
        self._access_token = config.get_secret("hubspot_token")
        
        # Initialize HubSpot API client with token
        self._client = HubSpot(access_token=self._access_token)
        
        # Cache for pipeline and property metadata
        self._pipelines_cache = {}  # Cache pipeline definitions
        self._properties_cache = {}  # Cache custom property definitions
    
    def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new contact in HubSpot.
        
        Args:
            contact_data: Dictionary of contact properties
                Required: email
                Optional: firstname, lastname, phone, company, etc.
        
        Returns:
            Dictionary containing created contact data with HubSpot ID
            
        Raises:
            ApiException: If HubSpot API call fails
            ValueError: If required fields are missing
        """
        # Validate required fields
        if 'email' not in contact_data:
            raise ValueError("Email is required for contact creation")
        
        try:
            # Create contact input object
            contact_input = SimplePublicObjectInputForCreate(properties=contact_data)
            
            # Call HubSpot API to create contact
            response = self._client.crm.contacts.basic_api.create(
                simple_public_object_input_for_create=contact_input
            )
            
            # Return contact data with HubSpot ID
            return {
                'id': response.id,
                'properties': response.properties,
                'created_at': response.created_at,
                'updated_at': response.updated_at
            }
            
        except ApiException as e:
            # Handle HubSpot API errors
            error_msg = f"Failed to create contact: {e}"
            if hasattr(e, 'body'):
                error_msg += f" - {e.body}"
            raise ApiException(error_msg) from e
    
    def get_contact_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieve a contact by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            Contact data dictionary if found, None if not found
            
        Raises:
            ApiException: If HubSpot API call fails
        """
        try:
            # Search for contact by email
            search_request = {
                'filterGroups': [{
                    'filters': [{
                        'propertyName': 'email',
                        'operator': 'EQ',
                        'value': email
                    }]
                }],
                'limit': 1  # Only need first match
            }
            
            # Execute search via HubSpot API
            response = self._client.crm.contacts.search_api.do_search(
                public_object_search_request=search_request
            )
            
            # Return first result if found
            if response.results:
                contact = response.results[0]
                return {
                    'id': contact.id,
                    'properties': contact.properties,
                    'created_at': contact.created_at,
                    'updated_at': contact.updated_at
                }
            
            return None  # Contact not found
            
        except ApiException as e:
            # Handle HubSpot API errors
            error_msg = f"Failed to search contact by email {email}: {e}"
            raise ApiException(error_msg) from e
    
    def create_company(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new company in HubSpot.
        
        Args:
            company_data: Dictionary of company properties
                Required: name
                Optional: domain, industry, phone, etc.
        
        Returns:
            Dictionary containing created company data with HubSpot ID
            
        Raises:
            ApiException: If HubSpot API call fails
            ValueError: If required fields are missing
        """
        # Validate required fields
        if 'name' not in company_data:
            raise ValueError("Company name is required for company creation")
        
        try:
            # Create company input object
            company_input = CompanyInput(properties=company_data)
            
            # Call HubSpot API to create company
            response = self._client.crm.companies.basic_api.create(
                simple_public_object_input=company_input
            )
            
            # Return company data with HubSpot ID
            return {
                'id': response.id,
                'properties': response.properties,
                'created_at': response.created_at,
                'updated_at': response.updated_at
            }
            
        except ApiException as e:
            # Handle HubSpot API errors
            error_msg = f"Failed to create company: {e}"
            raise ApiException(error_msg) from e
    
    def create_deal(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new deal in HubSpot.
        
        Args:
            deal_data: Dictionary of deal properties
                Required: dealname, pipeline, dealstage
                Optional: amount, closedate, etc.
        
        Returns:
            Dictionary containing created deal data with HubSpot ID
            
        Raises:
            ApiException: If HubSpot API call fails
            ValueError: If required fields are missing
        """
        # Validate required fields
        required_fields = ['dealname', 'pipeline', 'dealstage']
        for field in required_fields:
            if field not in deal_data:
                raise ValueError(f"{field} is required for deal creation")
        
        try:
            # Create deal input object
            deal_input = DealInput(properties=deal_data)
            
            # Call HubSpot API to create deal
            response = self._client.crm.deals.basic_api.create(
                simple_public_object_input_for_create=deal_input
            )
            
            # Return deal data with HubSpot ID
            return {
                'id': response.id,
                'properties': response.properties,
                'created_at': response.created_at,
                'updated_at': response.updated_at
            }
            
        except ApiException as e:
            # Handle HubSpot API errors
            error_msg = f"Failed to create deal: {e}"
            raise ApiException(error_msg) from e
    
    def update_deal_stage(self, deal_id: str, new_stage: str) -> Dict[str, Any]:
        """Update a deal's pipeline stage.
        
        Args:
            deal_id: HubSpot deal ID
            new_stage: New pipeline stage ID
            
        Returns:
            Updated deal data dictionary
            
        Raises:
            ApiException: If HubSpot API call fails
        """
        try:
            # Create update properties
            update_properties = {'dealstage': new_stage}
            
            # Create update input object
            deal_input = DealInput(properties=update_properties)
            
            # Call HubSpot API to update deal
            response = self._client.crm.deals.basic_api.update(
                deal_id=deal_id,
                simple_public_object_input=deal_input
            )
            
            # Return updated deal data
            return {
                'id': response.id,
                'properties': response.properties,
                'updated_at': response.updated_at
            }
            
        except ApiException as e:
            # Handle HubSpot API errors
            error_msg = f"Failed to update deal {deal_id} stage: {e}"
            raise ApiException(error_msg) from e
    
    def get_dtl_pipeline_stages(self) -> Dict[str, str]:
        """Get DTL-Global pipeline stages mapping.
        
        Returns the standard DTL-Global onboarding pipeline stages
        as defined in DTL_MASTER_PLAN.md Section 16.
        
        Returns:
            Dictionary mapping stage names to stage IDs
        """
        # DTL-Global standard pipeline stages (from master plan Section 16)
        return {
            'new_lead': 'appointmentscheduled',      # New Lead
            'discovery': 'qualifiedtobuy',           # Discovery Call
            'proposal': 'presentationscheduled',     # Proposal and Bid
            'contract': 'decisionmakerboughtin',     # Contract and Deposit
            'build': 'contractsent',                 # Build Website
            'deploy': 'closedwon',                   # Deploy and Connect
            'payment': 'closedwon',                  # Final Payment
            'live': 'closedwon',                     # Live and Monthly
            'nurture': 'closedwon',                  # Nurture
            'lost': 'closedlost'                     # Lost
        }
    
    def associate_contact_to_company(self, contact_id: str, company_id: str) -> bool:
        """Associate a contact with a company.
        
        Args:
            contact_id: HubSpot contact ID
            company_id: HubSpot company ID
            
        Returns:
            True if association successful, False otherwise
            
        Raises:
            ApiException: If HubSpot API call fails
        """
        try:
            # Create association between contact and company
            self._client.crm.contacts.associations_api.create(
                contact_id=contact_id,
                to_object_type='companies',
                to_object_id=company_id,
                association_type='contact_to_company'
            )
            
            return True  # Association successful
            
        except ApiException as e:
            # Handle HubSpot API errors
            error_msg = f"Failed to associate contact {contact_id} to company {company_id}: {e}"
            raise ApiException(error_msg) from e
    
    def associate_contact_to_deal(self, contact_id: str, deal_id: str) -> bool:
        """Associate a contact with a deal.
        
        Args:
            contact_id: HubSpot contact ID
            deal_id: HubSpot deal ID
            
        Returns:
            True if association successful, False otherwise
            
        Raises:
            ApiException: If HubSpot API call fails
        """
        try:
            # Create association between contact and deal
            self._client.crm.contacts.associations_api.create(
                contact_id=contact_id,
                to_object_type='deals',
                to_object_id=deal_id,
                association_type='contact_to_deal'
            )
            
            return True  # Association successful
            
        except ApiException as e:
            # Handle HubSpot API errors
            error_msg = f"Failed to associate contact {contact_id} to deal {deal_id}: {e}"
            raise ApiException(error_msg) from e
    
    def batch_create_contacts(self, contacts_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple contacts in batch.
        
        Args:
            contacts_data: List of contact property dictionaries
            
        Returns:
            List of created contact data with HubSpot IDs
            
        Raises:
            ApiException: If HubSpot API call fails
            ValueError: If batch size exceeds limits
        """
        # Validate batch size (HubSpot limit is 100)
        if len(contacts_data) > 100:
            raise ValueError("Batch size cannot exceed 100 contacts")
        
        try:
            # Create batch input objects
            batch_inputs = [
                SimplePublicObjectInput(properties=contact)
                for contact in contacts_data
            ]
            
            # Call HubSpot batch API
            response = self._client.crm.contacts.batch_api.create(
                batch_input_simple_public_object_input={
                    'inputs': batch_inputs
                }
            )
            
            # Return list of created contacts
            return [
                {
                    'id': result.id,
                    'properties': result.properties,
                    'created_at': result.created_at
                }
                for result in response.results
            ]
            
        except ApiException as e:
            # Handle HubSpot API errors
            error_msg = f"Failed to batch create {len(contacts_data)} contacts: {e}"
            raise ApiException(error_msg) from e
    
    def search_deals_by_company(self, company_id: str) -> List[Dict[str, Any]]:
        """Search for deals associated with a company.
        
        Args:
            company_id: HubSpot company ID
            
        Returns:
            List of deal data dictionaries
            
        Raises:
            ApiException: If HubSpot API call fails
        """
        try:
            # Search for deals associated with company
            search_request = {
                'filterGroups': [{
                    'filters': [{
                        'propertyName': 'associations.company',
                        'operator': 'EQ',
                        'value': company_id
                    }]
                }],
                'limit': 100  # Get up to 100 deals
            }
            
            # Execute search via HubSpot API
            response = self._client.crm.deals.search_api.do_search(
                public_object_search_request=search_request
            )
            
            # Return list of deals
            return [
                {
                    'id': deal.id,
                    'properties': deal.properties,
                    'created_at': deal.created_at,
                    'updated_at': deal.updated_at
                }
                for deal in response.results
            ]
            
        except ApiException as e:
            # Handle HubSpot API errors
            error_msg = f"Failed to search deals for company {company_id}: {e}"
            raise ApiException(error_msg) from e
    
    def get_contact_properties(self) -> List[Dict[str, Any]]:
        """Get all available contact properties.
        
        Returns:
            List of contact property definitions
            
        Raises:
            ApiException: If HubSpot API call fails
        """
        try:
            # Get contact properties from HubSpot
            response = self._client.crm.properties.core_api.get_all(
                object_type='contacts'
            )
            
            # Return property definitions
            return [
                {
                    'name': prop.name,
                    'label': prop.label,
                    'type': prop.type,
                    'field_type': prop.field_type,
                    'description': prop.description
                }
                for prop in response.results
            ]
            
        except ApiException as e:
            # Handle HubSpot API errors
            error_msg = f"Failed to get contact properties: {e}"
            raise ApiException(error_msg) from e


# Global HubSpot client instance
hubspot_client = HubSpotClient()