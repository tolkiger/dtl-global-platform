"""HubSpot CRM client for DTL-Global onboarding platform.

This module provides a comprehensive HubSpot API client for managing:
- Contacts and companies
- Deals and pipelines
- Custom properties
- CRM data import and export
- Pipeline stage management

Uses HubSpot Private App authentication with token from SSM Parameter Store.
All operations follow HubSpot API v3 best practices.

Per DTL_MASTER_PLAN.md Section 4: HubSpot CRM API with Bearer token.
Per DTL_MASTER_PLAN.md Section 16: DTL-Global pipeline stages.
Per Rule 001: Google-style docstrings for all functions and classes.
Per Rule 002: Inline comments on every meaningful line.
Per Rule 009: try/except blocks with specific exception types.

Author: DTL-Global Platform
"""

from __future__ import annotations

import json  # JSON parsing for HubSpot API responses and batch operations
from typing import Dict, List, Optional, Any, Union  # Type hints for function signatures
from hubspot import HubSpot  # Main HubSpot SDK client class
from hubspot.crm.contacts import SimplePublicObjectInput, ApiException  # Contact operations and error handling
from hubspot.crm.companies import SimplePublicObjectInput as CompanyInput  # Company creation input
from hubspot.crm.deals import SimplePublicObjectInput as DealInput  # Deal creation input
from hubspot.crm.pipelines import PipelineInput, PipelineStageInput  # Pipeline management (future use)

from .config import config  # Shared configuration manager for SSM secrets


class HubSpotClient:
    """HubSpot CRM client for DTL-Global platform operations.
    
    Provides methods for managing contacts, companies, deals, and pipelines
    in HubSpot CRM. Handles authentication via SSM Parameter Store.
    """
    
    def __init__(self):
        """Initialize HubSpot client with authentication.
        
        Loads HubSpot access token from SSM Parameter Store and creates
        authenticated HubSpot API client instance.
        
        Raises:
            RuntimeError: If SSM parameter retrieval fails
        """
        # Get HubSpot token from SSM Parameter Store (may raise RuntimeError)
        self._access_token = config.get_secret("hubspot_token")  # Load token from SSM securely
        
        # Initialize HubSpot API client with token (uses Bearer authentication)
        self._client = HubSpot(access_token=self._access_token)  # Create authenticated client instance
        
        # Cache for pipeline and property metadata (performance optimization)
        self._pipelines_cache = {}  # Cache pipeline definitions to avoid repeated API calls
        self._properties_cache = {}  # Cache custom property definitions for validation
    
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
            # Create contact input object with validated properties
            contact_input = SimplePublicObjectInput(properties=contact_data)  # Wrap properties for API call
            
            # Call HubSpot API to create contact
            response = self._client.crm.contacts.basic_api.create(  # Create contact via CRM API
                simple_public_object_input=contact_input  # Pass contact data to API
            )  # End HubSpot API call
            
            # Return contact data with HubSpot ID and timestamps
            return {  # Dictionary with standardized contact response
                'id': response.id,  # HubSpot-assigned contact ID
                'properties': response.properties,  # All contact properties from HubSpot
                'created_at': response.created_at,  # Contact creation timestamp
                'updated_at': response.updated_at  # Last modification timestamp
            }  # End contact response dictionary
            
        except ApiException as e:  # Handle HubSpot API-specific errors
            # Handle HubSpot API errors with detailed context
            error_msg = f"Failed to create contact: {e}"  # Base error message
            if hasattr(e, 'body'):  # Check if error has detailed body
                error_msg += f" - {e.body}"  # Add API error details
            raise RuntimeError(error_msg) from e  # Re-raise as application error with context
    
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
            # Build search request for email lookup
            search_request = {  # HubSpot search API request structure
                'filterGroups': [{  # Group of filters (AND logic within group)
                    'filters': [{  # Individual filter criteria
                        'propertyName': 'email',  # Search by email property
                        'operator': 'EQ',  # Exact match operator
                        'value': email  # Email address to search for
                    }]  # End filters list
                }],  # End filter groups list
                'limit': 1  # Only need first match (performance optimization)
            }  # End search request structure
            
            # Execute search via HubSpot API
            response = self._client.crm.contacts.search_api.do_search(  # Call search API
                public_object_search_request=search_request  # Pass search criteria
            )  # End search API call
            
            # Return first result if found, None if not found
            if response.results:  # Check if any contacts were found
                contact = response.results[0]  # Get first matching contact
                return {  # Dictionary with standardized contact response
                    'id': contact.id,  # HubSpot contact ID
                    'properties': contact.properties,  # All contact properties
                    'created_at': contact.created_at,  # Creation timestamp
                    'updated_at': contact.updated_at  # Last update timestamp
                }  # End contact response dictionary
            
            return None  # Contact not found (empty results)
            
        except ApiException as e:  # Handle HubSpot API-specific errors
            # Handle HubSpot API errors with email context
            error_msg = f"Failed to search contact by email {email}: {e}"  # Include email in error
            raise RuntimeError(error_msg) from e  # Re-raise as application error
    
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
            
        except ApiException as e:  # Handle HubSpot API-specific errors
            # Handle HubSpot API errors with context
            error_msg = f"Failed to create company: {e}"  # Include operation context in error
            raise RuntimeError(error_msg) from e  # Re-raise as application error
    
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
                simple_public_object_input=deal_input
            )
            
            # Return deal data with HubSpot ID
            return {
                'id': response.id,
                'properties': response.properties,
                'created_at': response.created_at,
                'updated_at': response.updated_at
            }
            
        except ApiException as e:  # Handle HubSpot API-specific errors
            # Handle HubSpot API errors with context
            error_msg = f"Failed to create deal: {e}"  # Include operation context in error
            raise RuntimeError(error_msg) from e  # Re-raise as application error
    
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
            
        except ApiException as e:  # Handle HubSpot API-specific errors
            # Handle HubSpot API errors with deal context
            error_msg = f"Failed to update deal {deal_id} stage: {e}"  # Include deal id in error
            raise RuntimeError(error_msg) from e  # Re-raise as application error
    
    def get_dtl_pipeline_stages(self) -> Dict[str, str]:
        """Get DTL-Global pipeline stages mapping.
        
        Returns the standard DTL-Global onboarding pipeline stages
        as defined in DTL_MASTER_PLAN.md Section 16.
        
        Returns:
            Dictionary mapping stage names to HubSpot stage IDs
        """
        # DTL-Global standard pipeline stages (from master plan Section 16)
        return {  # Dictionary mapping logical stage names to HubSpot stage IDs
            'new_lead': 'appointmentscheduled',      # New Lead - initial contact made
            'discovery': 'qualifiedtobuy',           # Discovery Call - needs assessment
            'proposal': 'presentationscheduled',     # Proposal and Bid - pricing presented
            'contract': 'decisionmakerboughtin',     # Contract and Deposit - agreement signed
            'build': 'contractsent',                 # Build Website - development phase
            'deploy': 'closedwon',                   # Deploy and Connect - site goes live
            'payment': 'closedwon',                  # Final Payment - project completed
            'live': 'closedwon',                     # Live and Monthly - ongoing service
            'nurture': 'closedwon',                  # Nurture - relationship maintenance
            'lost': 'closedlost'                     # Lost - deal did not close
        }  # End pipeline stages mapping
    
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
            
        except ApiException as e:  # Handle HubSpot API-specific errors
            # Handle HubSpot API errors with association context
            error_msg = f"Failed to associate contact {contact_id} to company {company_id}: {e}"  # Include IDs in error
            raise RuntimeError(error_msg) from e  # Re-raise as application error
    
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
            
        except ApiException as e:  # Handle HubSpot API-specific errors
            # Handle HubSpot API errors with association context
            error_msg = f"Failed to associate contact {contact_id} to deal {deal_id}: {e}"  # Include IDs in error
            raise RuntimeError(error_msg) from e  # Re-raise as application error
    
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
            
        except ApiException as e:  # Handle HubSpot API-specific errors
            # Handle HubSpot API errors with batch context
            error_msg = f"Failed to batch create {len(contacts_data)} contacts: {e}"  # Include batch size
            raise RuntimeError(error_msg) from e  # Re-raise as application error
    
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
            
        except ApiException as e:  # Handle HubSpot API-specific errors
            # Handle HubSpot API errors with company context
            error_msg = f"Failed to search deals for company {company_id}: {e}"  # Include company id
            raise RuntimeError(error_msg) from e  # Re-raise as application error
    
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
            
        except ApiException as e:  # Handle HubSpot API-specific errors
            # Handle HubSpot API errors with operation context
            error_msg = f"Failed to get contact properties: {e}"  # Describe failed operation
            raise RuntimeError(error_msg) from e  # Re-raise as application error


# Global HubSpot client instance (singleton pattern for Lambda efficiency)
hubspot_client = HubSpotClient()  # Shared instance across all handler modules