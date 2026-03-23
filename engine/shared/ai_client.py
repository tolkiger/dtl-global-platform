"""AI client for DTL-Global onboarding platform using Claude Haiku 4.5.

This module provides AI-powered functionality for the onboarding platform:
- Bid generation for different industries and client types
- SEO-optimized website content prompts
- Custom request estimation and pricing
- Template customization based on industry
- CRM column mapping suggestions

Uses Anthropic Claude Haiku 4.5 via direct API integration.
API key loaded from SSM Parameter Store for security.

Per DTL_MASTER_PLAN.md Section 11: Claude Haiku 4.5 direct API.
Per DTL_MASTER_PLAN.md Section 18: Pricing formula and guardrails.
Per Rule 001: Google-style docstrings for all functions and classes.
Per Rule 002: Inline comments on every meaningful line.
Per Rule 009: try/except blocks with specific exception types.

Author: DTL-Global Platform
"""

from __future__ import annotations

import json  # JSON parsing for AI responses and structured data
import re  # Regular expressions for content validation and parsing
from typing import Dict, List, Optional, Any, Union  # Type hints for function signatures
from decimal import Decimal  # Precise decimal arithmetic for pricing calculations

import anthropic  # Anthropic Claude API client for AI operations
from anthropic import APIError, APIConnectionError, RateLimitError  # Specific Anthropic exceptions

from .config import config  # Shared configuration manager for SSM secrets


class AIClient:
    """AI client for DTL-Global platform operations using Claude Haiku 4.5.
    
    Provides AI-powered features for onboarding automation including bid generation,
    content creation, pricing estimation, and CRM data mapping.
    """
    
    def __init__(self):
        """Initialize AI client with Anthropic API authentication.
        
        Loads Anthropic API key from SSM Parameter Store and creates
        authenticated Claude client instance.
        
        Raises:
            RuntimeError: If SSM parameter retrieval fails
        """
        # Get Anthropic API key from SSM Parameter Store (may raise RuntimeError)
        self._api_key = config.get_secret("anthropic_api_key")  # Load API key from SSM securely
        
        # Initialize Anthropic client with API key
        self._client = anthropic.Anthropic(api_key=self._api_key)  # Create authenticated client instance
        
        # AI model configuration (per DTL_MASTER_PLAN.md Section 11)
        self._model = "claude-3-haiku-20240307"  # Claude Haiku 4.5 model identifier
        self._max_tokens = 4000  # Maximum tokens for responses (balance cost vs completeness)
        
        # Pricing guardrails (per DTL_MASTER_PLAN.md Section 18)
        self._pricing_limits = {  # Dictionary of pricing constraints
            "min_setup": 300,  # Minimum setup price in dollars
            "max_setup": 10000,  # Maximum setup price in dollars
            "min_monthly": 20,  # Minimum monthly price (Friends & Family)
            "regular_min_monthly": 49,  # Regular minimum monthly price
            "max_monthly": 999,  # Maximum monthly price
            "hourly_rate": 75  # Fixed hourly rate in dollars
        }  # End pricing limits

    def generate_bid(self, industry: str, client_type: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a pricing bid for a client based on industry and requirements.
        
        Uses AI to analyze requirements and generate appropriate pricing within
        DTL-Global guardrails. Considers industry complexity and client type.
        
        Args:
            industry: Target industry (e.g., "roofing", "dental", "legal")
            client_type: Client package type (from CLIENT_TYPES)
            requirements: Dictionary of client requirements and specifications
            
        Returns:
            Dictionary containing bid details with setup cost, monthly cost, and breakdown
            
        Raises:
            ValueError: If industry or client_type is invalid
            RuntimeError: If AI API call fails
        """
        # Validate client type exists in configuration
        if client_type not in config.get_all_client_types():  # Check against valid client types
            raise ValueError(f"Invalid client type: {client_type}")  # Reject unknown client types
        
        # Get services required for this client type
        required_services = config.get_client_services(client_type)  # List of services for pricing
        
        # Build AI prompt for bid generation
        prompt = self._build_bid_prompt(industry, client_type, required_services, requirements)  # Create structured prompt
        
        try:
            # Call Claude API for bid generation
            response = self._client.messages.create(  # Send message to Claude
                model=self._model,  # Use Claude Haiku 4.5
                max_tokens=self._max_tokens,  # Limit response length
                messages=[{  # Message format for Claude
                    "role": "user",  # User role for prompt
                    "content": prompt  # Bid generation prompt
                }]  # End messages list
            )  # End Claude API call
            
            # Extract and parse AI response
            ai_content = response.content[0].text  # Get text content from response
            bid_data = self._parse_bid_response(ai_content)  # Parse structured bid data
            
            # Apply pricing guardrails and validation
            validated_bid = self._validate_and_adjust_pricing(bid_data)  # Ensure pricing within limits
            
            # Add metadata to bid response
            validated_bid.update({  # Add additional bid metadata
                "industry": industry,  # Target industry for reference
                "client_type": client_type,  # Package type for reference
                "services": required_services,  # List of included services
                "ai_model": self._model,  # AI model used for generation
                "guardrails_applied": True  # Confirm pricing validation applied
            })  # End metadata addition
            
            return validated_bid  # Return complete bid with validation
            
        except (APIError, APIConnectionError, RateLimitError) as e:  # Handle Anthropic API errors
            # Handle Anthropic API errors with context
            error_msg = f"Failed to generate bid for {industry} {client_type}: {e}"  # Include context in error
            raise RuntimeError(error_msg) from e  # Re-raise as application error

    def generate_seo_prompt(self, industry: str, business_name: str, 
                           location: str, services: List[str]) -> str:
        """Generate SEO-optimized website content prompt for a business.
        
        Creates comprehensive prompt for website content generation including
        all SEO elements from DTL_MASTER_PLAN.md Section 17.
        
        Args:
            industry: Business industry for keyword targeting
            business_name: Client business name
            location: Business location for local SEO
            services: List of services offered by the business
            
        Returns:
            SEO-optimized content prompt string for website generation
            
        Raises:
            RuntimeError: If AI API call fails
        """
        # Build comprehensive SEO prompt (per DTL_MASTER_PLAN.md Section 17)
        seo_prompt = self._build_seo_prompt_template(industry, business_name, location, services)  # Create base template
        
        try:
            # Call Claude API for SEO content enhancement
            response = self._client.messages.create(  # Send message to Claude
                model=self._model,  # Use Claude Haiku 4.5
                max_tokens=self._max_tokens,  # Limit response length
                messages=[{  # Message format for Claude
                    "role": "user",  # User role for prompt
                    "content": seo_prompt  # SEO prompt template
                }]  # End messages list
            )  # End Claude API call
            
            # Return enhanced SEO content prompt
            return response.content[0].text  # Extract text content from AI response
            
        except (APIError, APIConnectionError, RateLimitError) as e:  # Handle Anthropic API errors
            # Handle Anthropic API errors with business context
            error_msg = f"Failed to generate SEO prompt for {business_name} in {industry}: {e}"  # Include business context
            raise RuntimeError(error_msg) from e  # Re-raise as application error

    def estimate_custom_request(self, request_description: str, 
                               estimated_hours: Optional[float] = None) -> Dict[str, Any]:
        """Estimate pricing for custom client requests using AI analysis.
        
        Analyzes custom request descriptions and provides pricing estimates
        based on complexity, time requirements, and DTL pricing formula.
        
        Args:
            request_description: Detailed description of custom request
            estimated_hours: Optional manual hour estimate (overrides AI estimate)
            
        Returns:
            Dictionary with cost breakdown and pricing details
            
        Raises:
            RuntimeError: If AI API call fails
        """
        # Build prompt for custom request analysis
        analysis_prompt = self._build_custom_request_prompt(request_description)  # Create analysis prompt
        
        try:
            # Call Claude API for request analysis
            response = self._client.messages.create(  # Send message to Claude
                model=self._model,  # Use Claude Haiku 4.5
                max_tokens=self._max_tokens,  # Limit response length
                messages=[{  # Message format for Claude
                    "role": "user",  # User role for prompt
                    "content": analysis_prompt  # Custom request analysis prompt
                }]  # End messages list
            )  # End Claude API call
            
            # Parse AI response for hour estimate
            ai_content = response.content[0].text  # Get text content from response
            ai_hours = self._extract_hour_estimate(ai_content)  # Parse hour estimate from response
            
            # Use provided hours or AI estimate
            final_hours = estimated_hours if estimated_hours is not None else ai_hours  # Choose hour source
            
            # Calculate pricing using DTL formula (per DTL_MASTER_PLAN.md Section 18)
            setup_cost = final_hours * self._pricing_limits["hourly_rate"]  # Hours × $75/hour
            monthly_maintenance = max(  # Calculate monthly maintenance
                setup_cost * 0.20,  # 20% of setup cost
                self._pricing_limits["regular_min_monthly"]  # Minimum $49/month
            )  # End monthly calculation
            
            # Apply pricing guardrails
            setup_cost = max(  # Ensure minimum setup cost
                min(setup_cost, self._pricing_limits["max_setup"]),  # Cap at maximum
                self._pricing_limits["min_setup"]  # Floor at minimum
            )  # End setup cost validation
            
            monthly_maintenance = min(  # Cap monthly maintenance
                monthly_maintenance, self._pricing_limits["max_monthly"]  # Maximum monthly limit
            )  # End monthly validation
            
            # Return comprehensive estimate
            return {  # Dictionary with complete pricing breakdown
                "setup_cost": round(setup_cost, 2),  # Setup cost in dollars
                "monthly_cost": round(monthly_maintenance, 2),  # Monthly cost in dollars
                "estimated_hours": final_hours,  # Total estimated hours
                "hourly_rate": self._pricing_limits["hourly_rate"],  # Rate used for calculation
                "ai_analysis": ai_content,  # Full AI analysis for reference
                "guardrails_applied": True  # Confirm validation applied
            }  # End estimate dictionary
            
        except (APIError, APIConnectionError, RateLimitError) as e:  # Handle Anthropic API errors
            # Handle Anthropic API errors with request context
            error_msg = f"Failed to estimate custom request: {e}"  # Include operation context
            raise RuntimeError(error_msg) from e  # Re-raise as application error

    def suggest_crm_mapping(self, csv_headers: List[str], 
                           target_system: str = "hubspot") -> Dict[str, str]:
        """Suggest CRM field mappings for CSV import data.
        
        Analyzes CSV column headers and suggests appropriate mappings to
        target CRM system fields using AI pattern recognition.
        
        Args:
            csv_headers: List of CSV column header names
            target_system: Target CRM system ("hubspot" supported)
            
        Returns:
            Dictionary mapping CSV headers to CRM field names
            
        Raises:
            ValueError: If target_system is not supported
            RuntimeError: If AI API call fails
        """
        # Validate target system
        if target_system.lower() != "hubspot":  # Only HubSpot supported currently
            raise ValueError(f"Unsupported CRM system: {target_system}")  # Reject unknown systems
        
        # Build mapping analysis prompt
        mapping_prompt = self._build_crm_mapping_prompt(csv_headers, target_system)  # Create mapping prompt
        
        try:
            # Call Claude API for mapping suggestions
            response = self._client.messages.create(  # Send message to Claude
                model=self._model,  # Use Claude Haiku 4.5
                max_tokens=self._max_tokens,  # Limit response length
                messages=[{  # Message format for Claude
                    "role": "user",  # User role for prompt
                    "content": mapping_prompt  # CRM mapping prompt
                }]  # End messages list
            )  # End Claude API call
            
            # Parse AI response for field mappings
            ai_content = response.content[0].text  # Get text content from response
            mappings = self._parse_crm_mappings(ai_content)  # Parse mapping suggestions
            
            return mappings  # Return suggested field mappings
            
        except (APIError, APIConnectionError, RateLimitError) as e:  # Handle Anthropic API errors
            # Handle Anthropic API errors with CRM context
            error_msg = f"Failed to suggest CRM mappings for {target_system}: {e}"  # Include CRM system
            raise RuntimeError(error_msg) from e  # Re-raise as application error

    def _build_bid_prompt(self, industry: str, client_type: str, 
                         services: List[str], requirements: Dict[str, Any]) -> str:
        """Build structured prompt for AI bid generation.
        
        Args:
            industry: Target industry
            client_type: Client package type
            services: Required services list
            requirements: Client requirements dictionary
            
        Returns:
            Formatted prompt string for AI bid generation
        """
        # Create structured bid generation prompt
        prompt = f"""Generate a pricing bid for a {industry} business requiring {client_type} services.

SERVICES INCLUDED: {', '.join(services)}

CLIENT REQUIREMENTS:
{json.dumps(requirements, indent=2)}

PRICING GUIDELINES:
- Setup cost: ${self._pricing_limits['min_setup']} - ${self._pricing_limits['max_setup']}
- Monthly cost: ${self._pricing_limits['min_monthly']} - ${self._pricing_limits['max_monthly']}
- Hourly rate: ${self._pricing_limits['hourly_rate']}/hour
- Friends & Family minimum: ${self._pricing_limits['min_monthly']}/month

RESPONSE FORMAT (JSON):
{{
    "setup_cost": <dollar_amount>,
    "monthly_cost": <dollar_amount>,
    "estimated_hours": <hours>,
    "breakdown": {{
        "website": <cost>,
        "crm": <cost>,
        "payments": <cost>,
        "other": <cost>
    }},
    "justification": "<explanation>"
}}

Consider industry complexity, service requirements, and provide realistic estimates."""  # End prompt template
        
        return prompt  # Return formatted prompt

    def _build_seo_prompt_template(self, industry: str, business_name: str, 
                                  location: str, services: List[str]) -> str:
        """Build SEO-optimized content prompt template.
        
        Args:
            industry: Business industry
            business_name: Client business name
            location: Business location
            services: Services offered
            
        Returns:
            SEO prompt template string
        """
        # Create comprehensive SEO prompt (per DTL_MASTER_PLAN.md Section 17)
        prompt = f"""Create SEO-optimized website content for {business_name}, a {industry} business in {location}.

SERVICES: {', '.join(services)}

REQUIREMENTS (DTL_MASTER_PLAN.md Section 17):
1. Semantic HTML5 structure
2. Meta title/description with keywords
3. H1/H2/H3 hierarchy
4. Schema.org markup (LocalBusiness + industry)
5. Open Graph tags
6. Mobile-first responsive design
7. robots.txt + sitemap.xml guidance
8. NAP consistency (Name, Address, Phone)
9. Internal linking strategy
10. CTA above the fold
11. Contact form with honeypot
12. Google Maps embed
13. Accessibility (ARIA, contrast, keyboard nav)

Generate comprehensive content including:
- Homepage copy with local keywords
- Service page outlines
- About page content
- Contact page elements
- Meta descriptions for each page
- Schema markup examples
- Local SEO recommendations

Focus on {location} market and {industry} industry keywords."""  # End SEO prompt
        
        return prompt  # Return SEO template

    def _build_custom_request_prompt(self, request_description: str) -> str:
        """Build prompt for custom request analysis.
        
        Args:
            request_description: Description of custom request
            
        Returns:
            Analysis prompt string
        """
        # Create custom request analysis prompt
        prompt = f"""Analyze this custom development request and estimate hours required:

REQUEST: {request_description}

Consider:
- Technical complexity
- Integration requirements
- Testing and deployment time
- Documentation needs
- Potential challenges

Provide hour estimate (range if uncertain) and detailed breakdown of work involved.
Be realistic about time requirements for quality delivery."""  # End analysis prompt
        
        return prompt  # Return analysis prompt

    def _build_crm_mapping_prompt(self, csv_headers: List[str], target_system: str) -> str:
        """Build prompt for CRM field mapping suggestions.
        
        Args:
            csv_headers: CSV column headers
            target_system: Target CRM system
            
        Returns:
            Mapping prompt string
        """
        # Create CRM mapping analysis prompt
        prompt = f"""Map these CSV headers to {target_system.upper()} CRM fields:

CSV HEADERS: {', '.join(csv_headers)}

Suggest the best {target_system.upper()} field mapping for each header.
Consider common field names and data types.
If uncertain, suggest the closest match.

RESPONSE FORMAT:
CSV_Header -> CRM_Field_Name

Example:
First Name -> firstname
Email Address -> email
Company -> company"""  # End mapping prompt
        
        return prompt  # Return mapping prompt

    def _parse_bid_response(self, ai_content: str) -> Dict[str, Any]:
        """Parse AI bid response into structured data.
        
        Args:
            ai_content: Raw AI response text
            
        Returns:
            Parsed bid data dictionary
        """
        try:
            # Try to extract JSON from AI response
            json_match = re.search(r'\{.*\}', ai_content, re.DOTALL)  # Find JSON block in response
            if json_match:  # JSON found in response
                return json.loads(json_match.group())  # Parse JSON content
            else:  # No JSON found, create fallback structure
                return {  # Default bid structure
                    "setup_cost": 1000,  # Default setup cost
                    "monthly_cost": 149,  # Default monthly cost
                    "estimated_hours": 13.3,  # Calculated from setup cost
                    "breakdown": {"website": 500, "other": 500},  # Simple breakdown
                    "justification": "AI response parsing failed, using defaults"  # Explanation
                }  # End fallback structure
        except json.JSONDecodeError:  # JSON parsing failed
            # Return fallback bid if parsing fails
            return {  # Fallback bid structure
                "setup_cost": 1000,  # Safe default setup cost
                "monthly_cost": 149,  # Safe default monthly cost
                "estimated_hours": 13.3,  # Hours based on setup cost
                "breakdown": {"parsing_error": 1000},  # Error indicator
                "justification": "JSON parsing failed, using safe defaults"  # Error explanation
            }  # End error fallback

    def _validate_and_adjust_pricing(self, bid_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and adjust pricing within DTL guardrails.
        
        Args:
            bid_data: Raw bid data from AI
            
        Returns:
            Validated and adjusted bid data
        """
        # Extract pricing values with defaults
        setup_cost = float(bid_data.get("setup_cost", 1000))  # Get setup cost or default
        monthly_cost = float(bid_data.get("monthly_cost", 149))  # Get monthly cost or default
        
        # Apply setup cost guardrails
        if setup_cost < self._pricing_limits["min_setup"]:  # Below minimum
            setup_cost = self._pricing_limits["min_setup"]  # Raise to minimum
        elif setup_cost > self._pricing_limits["max_setup"]:  # Above maximum
            setup_cost = self._pricing_limits["max_setup"]  # Cap at maximum
        
        # Apply monthly cost guardrails
        if monthly_cost < self._pricing_limits["min_monthly"]:  # Below minimum
            monthly_cost = self._pricing_limits["regular_min_monthly"]  # Raise to regular minimum
        elif monthly_cost > self._pricing_limits["max_monthly"]:  # Above maximum
            monthly_cost = self._pricing_limits["max_monthly"]  # Cap at maximum
        
        # Update bid data with validated pricing
        bid_data["setup_cost"] = round(setup_cost, 2)  # Store validated setup cost
        bid_data["monthly_cost"] = round(monthly_cost, 2)  # Store validated monthly cost
        bid_data["estimated_hours"] = round(setup_cost / self._pricing_limits["hourly_rate"], 1)  # Calculate hours
        
        return bid_data  # Return validated bid data

    def _extract_hour_estimate(self, ai_content: str) -> float:
        """Extract hour estimate from AI analysis text.
        
        Args:
            ai_content: AI analysis response text
            
        Returns:
            Estimated hours as float
        """
        # Look for hour patterns in AI response
        hour_patterns = [  # List of regex patterns for hour extraction
            r'(\d+(?:\.\d+)?)\s*hours?',  # "X hours" pattern
            r'(\d+(?:\.\d+)?)\s*hrs?',  # "X hrs" pattern
            r'estimate[d]?:\s*(\d+(?:\.\d+)?)',  # "estimated: X" pattern
        ]  # End hour patterns
        
        for pattern in hour_patterns:  # Try each pattern
            match = re.search(pattern, ai_content.lower())  # Search for pattern
            if match:  # Pattern found
                return float(match.group(1))  # Return extracted hours
        
        # Default to 10 hours if no estimate found
        return 10.0  # Safe default hour estimate

    def _parse_crm_mappings(self, ai_content: str) -> Dict[str, str]:
        """Parse CRM field mappings from AI response.
        
        Args:
            ai_content: AI mapping response text
            
        Returns:
            Dictionary mapping CSV headers to CRM fields
        """
        mappings = {}  # Initialize mappings dictionary
        
        # Look for mapping patterns in AI response
        mapping_lines = ai_content.split('\n')  # Split response into lines
        for line in mapping_lines:  # Process each line
            if '->' in line:  # Line contains mapping arrow
                parts = line.split('->')  # Split on arrow
                if len(parts) == 2:  # Valid mapping format
                    csv_field = parts[0].strip()  # Clean CSV field name
                    crm_field = parts[1].strip()  # Clean CRM field name
                    mappings[csv_field] = crm_field  # Store mapping
        
        return mappings  # Return parsed mappings


# Global AI client instance (singleton pattern for Lambda efficiency)
ai_client = AIClient()  # Shared instance across all handler modules