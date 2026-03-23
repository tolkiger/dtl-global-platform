"""Anthropic Claude AI client for DTL-Global onboarding platform.

This module provides AI capabilities for the DTL-Global platform including:
- Bid generation and pricing estimation
- SEO-optimized website content creation
- CRM column mapping suggestions
- Custom request analysis and scoping
- Industry-specific content generation

Uses Claude Haiku 4.5 for cost-effective AI operations with API key from SSM.

Author: DTL-Global Platform
"""

import json
from typing import Dict, List, Optional, Any, Union
from anthropic import Anthropic
from anthropic.types import Message

from .config import config


class AIClient:
    """Anthropic Claude AI client for DTL-Global platform operations.
    
    Provides AI-powered features for bid generation, content creation,
    and data analysis. Uses Claude Haiku 4.5 for optimal cost/performance.
    """
    
    def __init__(self):
        """Initialize AI client with authentication.
        
        Loads Anthropic API key from SSM Parameter Store and creates
        authenticated Anthropic client instance.
        """
        # Get Anthropic API key from SSM Parameter Store
        self._api_key = config.get_secret("anthropic_api_key")
        
        # Initialize Anthropic client with API key
        self._client = Anthropic(api_key=self._api_key)
        
        # Claude model configuration
        self._model = "claude-3-5-haiku-20241022"  # Claude Haiku 4.5
        self._max_tokens = 4096  # Maximum response length
        self._temperature = 0.3  # Low temperature for consistent outputs
    
    def generate_bid(self, client_requirements: Dict[str, Any], 
                    industry: str) -> Dict[str, Any]:
        """Generate a project bid based on client requirements.
        
        Args:
            client_requirements: Dictionary containing client needs
                Required: services, timeline, budget_range, company_info
            industry: Industry type for specialized pricing
            
        Returns:
            Dictionary containing bid details, pricing, and timeline
            
        Raises:
            Exception: If AI API call fails
        """
        # Create bid generation prompt
        prompt = self._create_bid_prompt(client_requirements, industry)
        
        try:
            # Call Claude API for bid generation
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse response content
            bid_content = response.content[0].text
            
            # Extract structured bid data from response
            bid_data = self._parse_bid_response(bid_content)
            
            # Apply DTL pricing guardrails from master plan Section 18
            bid_data = self._apply_pricing_guardrails(bid_data)
            
            return bid_data
            
        except Exception as e:
            # Handle AI API errors
            error_msg = f"Failed to generate bid: {e}"
            raise Exception(error_msg) from e
    
    def generate_website_prompt(self, business_info: Dict[str, Any], 
                              industry: str) -> str:
        """Generate SEO-optimized website content prompt.
        
        Args:
            business_info: Dictionary containing business details
                Required: name, description, location, services
            industry: Industry type for specialized content
            
        Returns:
            Detailed website content prompt with SEO elements
            
        Raises:
            Exception: If AI API call fails
        """
        # Create website prompt generation request
        prompt = self._create_website_prompt_template(business_info, industry)
        
        try:
            # Call Claude API for website prompt generation
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                temperature=0.4,  # Slightly higher for creative content
                messages=[{
                    "role": "user", 
                    "content": prompt
                }]
            )
            
            # Return generated website prompt
            return response.content[0].text
            
        except Exception as e:
            # Handle AI API errors
            error_msg = f"Failed to generate website prompt: {e}"
            raise Exception(error_msg) from e
    
    def analyze_crm_columns(self, csv_headers: List[str], 
                          target_system: str = "hubspot") -> Dict[str, str]:
        """Analyze CSV headers and suggest CRM field mappings.
        
        Args:
            csv_headers: List of CSV column headers
            target_system: Target CRM system (default: hubspot)
            
        Returns:
            Dictionary mapping CSV headers to CRM field names
            
        Raises:
            Exception: If AI API call fails
        """
        # Create CRM mapping analysis prompt
        prompt = self._create_crm_mapping_prompt(csv_headers, target_system)
        
        try:
            # Call Claude API for column analysis
            response = self._client.messages.create(
                model=self._model,
                max_tokens=2048,  # Smaller response for mapping
                temperature=0.1,  # Very low for precise mapping
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse mapping response
            mapping_content = response.content[0].text
            mapping_data = self._parse_crm_mapping_response(mapping_content)
            
            return mapping_data
            
        except Exception as e:
            # Handle AI API errors
            error_msg = f"Failed to analyze CRM columns: {e}"
            raise Exception(error_msg) from e
    
    def estimate_custom_request(self, request_description: str) -> Dict[str, Any]:
        """Estimate hours and cost for a custom request.
        
        Args:
            request_description: Detailed description of custom work
            
        Returns:
            Dictionary containing hour estimate, cost, and breakdown
            
        Raises:
            Exception: If AI API call fails
        """
        # Create custom request estimation prompt
        prompt = self._create_estimation_prompt(request_description)
        
        try:
            # Call Claude API for estimation
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                temperature=0.2,  # Low temperature for consistent estimates
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse estimation response
            estimation_content = response.content[0].text
            estimation_data = self._parse_estimation_response(estimation_content)
            
            # Apply DTL pricing formula from master plan Section 18
            estimation_data = self._apply_custom_pricing_formula(estimation_data)
            
            return estimation_data
            
        except Exception as e:
            # Handle AI API errors
            error_msg = f"Failed to estimate custom request: {e}"
            raise Exception(error_msg) from e
    
    def _create_bid_prompt(self, requirements: Dict[str, Any], industry: str) -> str:
        """Create a structured prompt for bid generation.
        
        Args:
            requirements: Client requirements dictionary
            industry: Industry type
            
        Returns:
            Formatted prompt string for AI model
        """
        # Build comprehensive bid generation prompt
        prompt = f"""
You are a professional project estimator for DTL-Global, a digital transformation consultancy.

Generate a detailed project bid based on these client requirements:

INDUSTRY: {industry}
SERVICES REQUESTED: {requirements.get('services', [])}
TIMELINE: {requirements.get('timeline', 'Not specified')}
BUDGET RANGE: {requirements.get('budget_range', 'Not specified')}
COMPANY INFO: {json.dumps(requirements.get('company_info', {}), indent=2)}

PRICING GUIDELINES:
- Minimum setup: $300
- Maximum setup: $10,000
- Hourly rate: $75 (fixed)
- Monthly minimum: $49 (regular clients), $20 (friends & family)
- Monthly maximum: $999

REQUIRED OUTPUT FORMAT (JSON):
{{
    "setup_cost": <dollar_amount>,
    "monthly_cost": <dollar_amount>,
    "estimated_hours": <number>,
    "timeline_weeks": <number>,
    "services_included": [<list_of_services>],
    "deliverables": [<list_of_deliverables>],
    "assumptions": [<list_of_assumptions>],
    "risks": [<list_of_risks>],
    "next_steps": [<list_of_next_steps>]
}}

Focus on value delivery and be conservative with estimates. Include industry-specific considerations.
"""
        return prompt.strip()
    
    def _create_website_prompt_template(self, business_info: Dict[str, Any], 
                                      industry: str) -> str:
        """Create a prompt for SEO-optimized website content generation.
        
        Args:
            business_info: Business information dictionary
            industry: Industry type
            
        Returns:
            Formatted prompt string for website content
        """
        # Build SEO-focused website prompt per master plan Section 17
        prompt = f"""
Create a comprehensive website content prompt for a {industry} business.

BUSINESS INFORMATION:
- Name: {business_info.get('name', 'Not specified')}
- Description: {business_info.get('description', 'Not specified')}
- Location: {business_info.get('location', 'Not specified')}
- Services: {business_info.get('services', [])}
- Target Keywords: {business_info.get('keywords', [])}

REQUIRED SEO ELEMENTS (per DTL Master Plan Section 17):
1. Semantic HTML5 structure
2. Meta title/description with keywords
3. H1/H2/H3 hierarchy
4. Schema.org markup (LocalBusiness + industry-specific)
5. Open Graph tags
6. Mobile-first responsive design
7. robots.txt + sitemap.xml
8. NAP (Name, Address, Phone) consistency
9. Internal linking strategy
10. CTA above the fold
11. Contact form with honeypot anti-spam
12. Google Maps embed
13. Accessibility (ARIA, contrast, keyboard navigation)

Generate a detailed website content prompt that includes:
- Page structure and content outline
- SEO-optimized copy for each section
- Technical implementation requirements
- Local SEO considerations for {industry} businesses
- Industry-specific trust signals and social proof elements

Make the content engaging, professional, and conversion-focused.
"""
        return prompt.strip()
    
    def _create_crm_mapping_prompt(self, csv_headers: List[str], 
                                 target_system: str) -> str:
        """Create a prompt for CRM field mapping analysis.
        
        Args:
            csv_headers: List of CSV column headers
            target_system: Target CRM system
            
        Returns:
            Formatted prompt string for mapping analysis
        """
        # Build CRM mapping analysis prompt
        prompt = f"""
Analyze these CSV column headers and suggest mappings to {target_system.upper()} CRM fields:

CSV HEADERS:
{json.dumps(csv_headers, indent=2)}

COMMON {target_system.upper()} FIELDS:
- firstname, lastname, email, phone, company
- address, city, state, zip, country
- website, industry, jobtitle, lifecyclestage
- hubspot_owner_id, createdate, lastmodifieddate

MAPPING RULES:
1. Match exact field names when possible
2. Suggest closest semantic match for variations
3. Flag unmappable or custom fields
4. Prioritize standard contact/company fields
5. Handle common variations (e.g., "first_name" -> "firstname")

OUTPUT FORMAT (JSON):
{{
    "mappings": {{
        "<csv_header>": "<crm_field>",
        ...
    }},
    "unmapped": ["<csv_header>", ...],
    "suggestions": {{
        "<csv_header>": ["<possible_field1>", "<possible_field2>"]
    }},
    "confidence": "<high|medium|low>"
}}

Provide confident mappings for standard fields and suggestions for ambiguous ones.
"""
        return prompt.strip()
    
    def _create_estimation_prompt(self, request_description: str) -> str:
        """Create a prompt for custom request estimation.
        
        Args:
            request_description: Description of custom work
            
        Returns:
            Formatted prompt string for estimation
        """
        # Build custom request estimation prompt
        prompt = f"""
Estimate the time and complexity for this custom development request:

REQUEST DESCRIPTION:
{request_description}

ESTIMATION FACTORS:
- Development complexity (simple/medium/complex)
- Integration requirements
- Testing and QA needs
- Documentation requirements
- Potential risks and unknowns

DTL HOURLY RATE: $75 (fixed)

OUTPUT FORMAT (JSON):
{{
    "estimated_hours": <number>,
    "complexity": "<simple|medium|complex>",
    "breakdown": {{
        "analysis": <hours>,
        "development": <hours>,
        "testing": <hours>,
        "documentation": <hours>
    }},
    "assumptions": [<list_of_assumptions>],
    "risks": [<list_of_risks>],
    "recommendations": [<list_of_recommendations>]
}}

Be conservative with estimates and include buffer time for unknowns.
"""
        return prompt.strip()
    
    def _parse_bid_response(self, response_content: str) -> Dict[str, Any]:
        """Parse AI response for bid generation.
        
        Args:
            response_content: Raw AI response content
            
        Returns:
            Parsed bid data dictionary
        """
        try:
            # Extract JSON from response (handle potential markdown formatting)
            json_start = response_content.find('{')
            json_end = response_content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = response_content[json_start:json_end]
                return json.loads(json_content)
            else:
                # Fallback: create basic structure from text
                return {
                    'setup_cost': 500,  # Default starter setup
                    'monthly_cost': 49,  # Default starter monthly
                    'estimated_hours': 10,
                    'timeline_weeks': 2,
                    'services_included': ['website', 'hosting'],
                    'deliverables': ['Website', 'Hosting Setup'],
                    'assumptions': ['Standard requirements'],
                    'risks': ['Scope creep'],
                    'next_steps': ['Schedule discovery call']
                }
                
        except json.JSONDecodeError:
            # Return default bid structure on parse error
            return {
                'setup_cost': 500,
                'monthly_cost': 49,
                'estimated_hours': 10,
                'timeline_weeks': 2,
                'services_included': ['website'],
                'deliverables': ['Basic Website'],
                'assumptions': ['Standard scope'],
                'risks': ['Requirements clarification needed'],
                'next_steps': ['Detailed requirements gathering']
            }
    
    def _parse_crm_mapping_response(self, response_content: str) -> Dict[str, str]:
        """Parse AI response for CRM field mapping.
        
        Args:
            response_content: Raw AI response content
            
        Returns:
            Dictionary mapping CSV headers to CRM fields
        """
        try:
            # Extract JSON from response
            json_start = response_content.find('{')
            json_end = response_content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = response_content[json_start:json_end]
                parsed_data = json.loads(json_content)
                
                # Return just the mappings dictionary
                return parsed_data.get('mappings', {})
            else:
                return {}  # Return empty mapping on parse failure
                
        except json.JSONDecodeError:
            return {}  # Return empty mapping on JSON error
    
    def _parse_estimation_response(self, response_content: str) -> Dict[str, Any]:
        """Parse AI response for custom request estimation.
        
        Args:
            response_content: Raw AI response content
            
        Returns:
            Parsed estimation data dictionary
        """
        try:
            # Extract JSON from response
            json_start = response_content.find('{')
            json_end = response_content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = response_content[json_start:json_end]
                return json.loads(json_content)
            else:
                # Return default estimation on parse failure
                return {
                    'estimated_hours': 8,
                    'complexity': 'medium',
                    'breakdown': {
                        'analysis': 2,
                        'development': 4,
                        'testing': 1,
                        'documentation': 1
                    },
                    'assumptions': ['Standard requirements'],
                    'risks': ['Scope definition needed'],
                    'recommendations': ['Detailed requirements gathering']
                }
                
        except json.JSONDecodeError:
            # Return default estimation on JSON error
            return {
                'estimated_hours': 8,
                'complexity': 'medium',
                'breakdown': {'development': 8},
                'assumptions': ['Standard scope'],
                'risks': ['Requirements clarification needed'],
                'recommendations': ['Schedule discovery call']
            }
    
    def _apply_pricing_guardrails(self, bid_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply DTL pricing guardrails to bid data.
        
        Args:
            bid_data: Raw bid data from AI
            
        Returns:
            Bid data with pricing guardrails applied
        """
        # Apply guardrails from master plan Section 18
        setup_cost = bid_data.get('setup_cost', 500)
        monthly_cost = bid_data.get('monthly_cost', 49)
        
        # Enforce minimum and maximum setup costs
        setup_cost = max(300, min(10000, setup_cost))  # $300 - $10,000
        
        # Enforce minimum and maximum monthly costs
        monthly_cost = max(49, min(999, monthly_cost))  # $49 - $999 (regular clients)
        
        # Update bid data with enforced pricing
        bid_data['setup_cost'] = setup_cost
        bid_data['monthly_cost'] = monthly_cost
        
        # Calculate deposit (50% of setup cost)
        bid_data['deposit_amount'] = setup_cost // 2
        
        return bid_data
    
    def _apply_custom_pricing_formula(self, estimation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply DTL custom pricing formula to estimation data.
        
        Args:
            estimation_data: Raw estimation data from AI
            
        Returns:
            Estimation data with DTL pricing formula applied
        """
        # Get estimated hours
        hours = estimation_data.get('estimated_hours', 8)
        
        # Apply DTL pricing formula from master plan Section 18
        hourly_rate = 75  # Fixed DTL hourly rate
        setup_cost = hours * hourly_rate
        
        # Calculate monthly maintenance (20% of setup, minimum $49)
        monthly_cost = max(49, int(setup_cost * 0.20))
        
        # Add pricing to estimation data
        estimation_data['setup_cost'] = setup_cost
        estimation_data['monthly_cost'] = monthly_cost
        estimation_data['hourly_rate'] = hourly_rate
        estimation_data['deposit_amount'] = setup_cost // 2  # 50% deposit
        
        return estimation_data


# Global AI client instance
ai_client = AIClient()