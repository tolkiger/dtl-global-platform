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
    
    def customize_industry_template(self, base_template: Dict[str, Any], 
                                  industry: str, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """Customize a base template for a specific industry and business.
        
        Args:
            base_template: Base template configuration
            industry: Target industry
            business_info: Business-specific information
            
        Returns:
            Customized template configuration
            
        Raises:
            Exception: If AI API call fails
        """
        # Create template customization prompt
        prompt = self._create_template_customization_prompt(base_template, industry, business_info)
        
        try:
            # Call Claude API for template customization
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                temperature=0.2,  # Low temperature for consistent customization
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse customization response
            customization_content = response.content[0].text
            customized_template = self._parse_template_customization_response(customization_content)
            
            # Merge customizations with base template
            final_template = self._merge_template_customizations(base_template, customized_template)
            
            return final_template
            
        except Exception as e:
            # Handle AI API errors
            error_msg = f"Failed to customize template for {industry}: {e}"
            raise Exception(error_msg) from e
    
    def _create_bid_prompt(self, requirements: Dict[str, Any], industry: str) -> str:
        """Create a structured prompt for bid generation.
        
        Args:
            requirements: Client requirements dictionary
            industry: Industry type
            
        Returns:
            Formatted prompt string for AI model
        """
        # Get industry-specific context
        industry_context = self._get_industry_context(industry)
        
        # Build comprehensive bid generation prompt
        prompt = f"""
You are a professional project estimator for DTL-Global, a digital transformation consultancy specializing in {industry} businesses.

Generate a detailed project bid based on these client requirements:

INDUSTRY: {industry}
SERVICES REQUESTED: {requirements.get('services', [])}
TIMELINE: {requirements.get('timeline', 'Not specified')}
BUDGET RANGE: {requirements.get('budget_range', 'Not specified')}
COMPANY INFO: {json.dumps(requirements.get('company_info', {}), indent=2)}

INDUSTRY-SPECIFIC CONTEXT:
{industry_context}

PRICING GUIDELINES:
- Minimum setup: $300
- Maximum setup: $10,000
- Hourly rate: $75 (fixed)
- Monthly minimum: $49 (regular clients), $20 (friends & family)
- Monthly maximum: $999

SERVICE PACKAGES:
- STARTER ($500 setup / $49 monthly): Website + hosting + SEO
- GROWTH ($1,250 setup / $149 monthly): Starter + HubSpot CRM + Stripe + email
- PROFESSIONAL ($2,500 setup / $249 monthly): Growth + AI chatbot + CRM import + priority support
- PREMIUM ($4,000+ setup / $399+ monthly): Professional + custom automations + advanced features

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
    "next_steps": [<list_of_next_steps>],
    "package_recommendation": "<STARTER|GROWTH|PROFESSIONAL|PREMIUM>",
    "industry_specific_features": [<list_of_industry_features>],
    "competitive_advantages": [<list_of_advantages>]
}}

Focus on value delivery and be conservative with estimates. Include industry-specific considerations and competitive advantages.
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
        # Get industry-specific SEO context
        industry_seo_context = self._get_industry_seo_context(industry)
        
        # Build comprehensive SEO-focused website prompt per master plan Section 17
        prompt = f"""
You are an expert SEO content strategist creating a comprehensive website for a {industry} business.

BUSINESS INFORMATION:
- Name: {business_info.get('name', 'Not specified')}
- Description: {business_info.get('description', 'Not specified')}
- Location: {business_info.get('location', 'Not specified')}
- Services: {business_info.get('services', [])}
- Target Keywords: {business_info.get('keywords', [])}
- Phone: {business_info.get('phone', 'Not specified')}
- Address: {business_info.get('address', 'Not specified')}

INDUSTRY-SPECIFIC SEO CONTEXT:
{industry_seo_context}

MANDATORY SEO ELEMENTS (per DTL Master Plan Section 17):
1. **Semantic HTML5 Structure**: Use proper header, nav, main, section, article, aside, footer elements
2. **Meta Title/Description**: Include primary keywords, location, and compelling CTAs (title ≤60 chars, description ≤160 chars)
3. **H1/H2/H3 Hierarchy**: Logical heading structure with keywords, only one H1 per page
4. **Schema.org Markup**: LocalBusiness + industry-specific structured data (Organization, Service, Review, etc.)
5. **Open Graph Tags**: Facebook/social sharing optimization with images and descriptions
6. **Mobile-First Responsive**: Touch-friendly design, fast loading, thumb-friendly navigation
7. **robots.txt + sitemap.xml**: SEO crawling optimization and site structure
8. **NAP Consistency**: Name, Address, Phone identical across all pages and directories
9. **Internal Linking**: Strategic linking between related pages and services
10. **CTA Above Fold**: Primary conversion action visible without scrolling
11. **Contact Form**: Honeypot anti-spam, required field validation, success/error states
12. **Google Maps Embed**: Interactive map with business location and directions
13. **Accessibility**: ARIA labels, alt text, keyboard navigation, color contrast compliance

CONTENT STRUCTURE REQUIREMENTS:
- Homepage with hero section, services overview, testimonials, contact CTA
- About Us page with team, history, credentials, trust signals
- Services pages for each offering with detailed descriptions
- Contact page with multiple contact methods and form
- Blog/Resources section for content marketing
- Privacy Policy and Terms of Service pages

TECHNICAL IMPLEMENTATION:
- Page load speed optimization
- Image optimization with alt text
- SSL certificate and security headers
- Analytics tracking setup
- Local SEO optimization
- Social media integration
- Review management system integration

Generate a detailed, actionable website content specification that includes:
1. Complete page structure and navigation
2. SEO-optimized copy for each section
3. Technical implementation checklist
4. Local SEO strategy specific to {industry}
5. Conversion optimization elements
6. Industry-specific trust signals and social proof
7. Content marketing recommendations

Make the content compelling, professional, and conversion-focused while maintaining all SEO best practices.
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
    
    def _get_industry_context(self, industry: str) -> str:
        """Get industry-specific context for bid generation.
        
        Args:
            industry: Industry type
            
        Returns:
            Industry-specific context string
        """
        # Industry-specific contexts for better bid generation
        industry_contexts = {
            'roofing': """
ROOFING INDUSTRY SPECIFICS:
- High competition, local SEO critical
- Seasonal demand patterns (spring/summer peak)
- Emergency services need 24/7 availability
- Insurance claim integration important
- Before/after photo galleries essential
- Customer reviews and testimonials crucial
- Local licensing and certification display
- Weather-resistant contact forms
- Mobile-first design for field workers
- Integration with project management tools
            """.strip(),
            
            'dental': """
DENTAL PRACTICE SPECIFICS:
- HIPAA compliance requirements
- Online appointment booking essential
- Insurance verification systems
- Patient portal integration
- Before/after treatment galleries
- Service-specific landing pages
- Local SEO for "dentist near me"
- Review management critical
- Emergency contact prominence
- Accessibility compliance (ADA)
            """.strip(),
            
            'legal': """
LAW FIRM SPECIFICS:
- Attorney profiles and credentials
- Practice area specialization pages
- Client confidentiality emphasis
- Case results and testimonials
- Consultation booking systems
- Legal resource libraries
- Bar association memberships
- Professional photography important
- Trust signals and security badges
- Multilingual support considerations
            """.strip(),
            
            'medical': """
MEDICAL PRACTICE SPECIFICS:
- HIPAA compliance mandatory
- Provider credentialing display
- Insurance acceptance lists
- Patient portal integration
- Telemedicine capabilities
- Appointment scheduling systems
- Medical specialization focus
- Accessibility compliance (ADA)
- Emergency contact information
- Health education resources
            """.strip(),
            
            'restaurant': """
RESTAURANT INDUSTRY SPECIFICS:
- Online ordering and delivery integration
- Menu display with dietary restrictions
- Reservation booking systems
- Photo-heavy design for food appeal
- Location and hours prominence
- Social media integration
- Customer review management
- Event booking capabilities
- Mobile ordering optimization
- Local SEO for food searches
            """.strip(),
            
            'retail': """
RETAIL BUSINESS SPECIFICS:
- E-commerce integration
- Product catalog management
- Inventory tracking systems
- Payment processing setup
- Shipping and return policies
- Customer account systems
- Loyalty program integration
- Mobile shopping optimization
- Social commerce features
- Multi-location support
            """.strip(),
            
            'professional_services': """
PROFESSIONAL SERVICES SPECIFICS:
- Service portfolio showcase
- Client case studies and results
- Professional team profiles
- Consultation booking systems
- Resource libraries and downloads
- Industry expertise demonstration
- Certification and credential display
- Client testimonials and reviews
- Contact and proposal systems
- Professional photography needs
            """.strip()
        }
        
        # Return industry-specific context or default
        return industry_contexts.get(industry.lower(), """
GENERAL BUSINESS SPECIFICS:
- Professional brand representation
- Service/product showcase
- Contact and inquiry systems
- Customer testimonials
- About us and team information
- Local SEO optimization
- Mobile-responsive design
- Basic analytics and tracking
- Social media integration
- Professional photography
        """.strip())
    
    def _get_industry_seo_context(self, industry: str) -> str:
        """Get industry-specific SEO context for website generation.
        
        Args:
            industry: Industry type
            
        Returns:
            Industry-specific SEO context string
        """
        # Industry-specific SEO contexts
        seo_contexts = {
            'roofing': """
ROOFING SEO SPECIFICS:
- Primary Keywords: "roofing contractor [city]", "roof repair [city]", "roof replacement [city]"
- Long-tail Keywords: "emergency roof repair", "storm damage roofing", "residential roofing services"
- Local SEO: Target "roofer near me", "roofing companies in [city]"
- Schema Types: LocalBusiness, RoofingContractor, Service, Review, Organization
- Trust Signals: BBB rating, insurance certifications, manufacturer certifications, license numbers
- Content Focus: Storm damage, insurance claims, material types (asphalt, metal, tile)
- Seasonal Content: Storm season preparation, winter roof maintenance, spring inspections
- Review Keywords: "reliable roofer", "quality roofing", "professional installation"
            """.strip(),
            
            'dental': """
DENTAL PRACTICE SEO SPECIFICS:
- Primary Keywords: "dentist [city]", "dental office [city]", "family dentist [city]"
- Long-tail Keywords: "cosmetic dentistry", "dental implants", "emergency dentist"
- Local SEO: Target "dentist near me", "dental clinic in [city]"
- Schema Types: LocalBusiness, Dentist, MedicalOrganization, Service, Review
- Trust Signals: ADA membership, state licensing, patient testimonials, before/after photos
- Content Focus: Preventive care, cosmetic procedures, pediatric dentistry, emergency services
- HIPAA Compliance: Privacy notices, secure forms, patient portal links
- Review Keywords: "gentle dentist", "professional dental care", "modern dental office"
            """.strip(),
            
            'legal': """
LAW FIRM SEO SPECIFICS:
- Primary Keywords: "[practice area] lawyer [city]", "[practice area] attorney [city]"
- Long-tail Keywords: "personal injury lawyer", "divorce attorney", "criminal defense"
- Local SEO: Target "lawyer near me", "attorney in [city]"
- Schema Types: LocalBusiness, LegalService, Attorney, Organization, Review
- Trust Signals: Bar association membership, case results, attorney credentials, awards
- Content Focus: Practice areas, case studies, legal resources, attorney profiles
- Authority Building: Legal blog, FAQ sections, legal guides, news commentary
- Review Keywords: "experienced attorney", "successful lawyer", "professional legal services"
            """.strip(),
            
            'medical': """
MEDICAL PRACTICE SEO SPECIFICS:
- Primary Keywords: "[specialty] doctor [city]", "[specialty] physician [city]"
- Long-tail Keywords: "family medicine", "internal medicine", "specialist near me"
- Local SEO: Target "doctor near me", "[specialty] in [city]"
- Schema Types: LocalBusiness, Physician, MedicalOrganization, Service, Review
- Trust Signals: Board certifications, hospital affiliations, medical school credentials
- Content Focus: Medical services, physician bios, patient education, health resources
- HIPAA Compliance: Privacy policies, secure patient portals, confidentiality notices
- Review Keywords: "caring doctor", "professional medical care", "experienced physician"
            """.strip(),
            
            'restaurant': """
RESTAURANT SEO SPECIFICS:
- Primary Keywords: "[cuisine] restaurant [city]", "dining [city]", "[restaurant name] menu"
- Long-tail Keywords: "best [cuisine] food", "family restaurant", "fine dining [city]"
- Local SEO: Target "restaurants near me", "[cuisine] food in [city]"
- Schema Types: LocalBusiness, Restaurant, FoodEstablishment, Menu, Review
- Trust Signals: Health department ratings, awards, chef credentials, customer photos
- Content Focus: Menu items, chef specialties, dining atmosphere, catering services
- Visual Content: High-quality food photography, restaurant ambiance, chef photos
- Review Keywords: "delicious food", "great atmosphere", "excellent service"
            """.strip(),
            
            'retail': """
RETAIL BUSINESS SEO SPECIFICS:
- Primary Keywords: "[product category] store [city]", "[brand] retailer [city]"
- Long-tail Keywords: "buy [product] online", "[product] near me", "best [product] deals"
- Local SEO: Target "store near me", "[product] shop in [city]"
- Schema Types: LocalBusiness, Store, Product, Offer, Review, Organization
- Trust Signals: Return policies, security badges, customer reviews, brand partnerships
- Content Focus: Product categories, brand information, shopping guides, promotions
- E-commerce Elements: Product catalogs, shopping cart, payment security, shipping info
- Review Keywords: "quality products", "great selection", "excellent customer service"
            """.strip(),
            
            'professional_services': """
PROFESSIONAL SERVICES SEO SPECIFICS:
- Primary Keywords: "[service] consultant [city]", "[service] services [city]"
- Long-tail Keywords: "business consulting", "professional advice", "[service] expert"
- Local SEO: Target "[service] near me", "consultant in [city]"
- Schema Types: LocalBusiness, ProfessionalService, Service, Review, Organization
- Trust Signals: Certifications, client testimonials, case studies, industry awards
- Content Focus: Service offerings, expertise areas, client success stories, resources
- Authority Building: Industry blog, whitepapers, speaking engagements, media mentions
- Review Keywords: "expert consultant", "professional service", "knowledgeable advisor"
            """.strip()
        }
        
        # Return industry-specific SEO context or default
        return seo_contexts.get(industry.lower(), """
GENERAL BUSINESS SEO SPECIFICS:
- Primary Keywords: "[business type] [city]", "[service] [city]"
- Long-tail Keywords: "[service] near me", "professional [service]", "best [business type]"
- Local SEO: Target "business near me", "[service] in [city]"
- Schema Types: LocalBusiness, Service, Review, Organization
- Trust Signals: Customer testimonials, professional credentials, industry memberships
- Content Focus: Services, about us, contact information, customer success stories
- Authority Building: Blog content, resource pages, FAQ sections
- Review Keywords: "professional service", "reliable business", "quality work"
        """.strip())
    
    def _create_template_customization_prompt(self, base_template: Dict[str, Any], 
                                            industry: str, business_info: Dict[str, Any]) -> str:
        """Create a prompt for industry-specific template customization.
        
        Args:
            base_template: Base template configuration
            industry: Target industry
            business_info: Business information
            
        Returns:
            Formatted prompt string for template customization
        """
        # Get industry context for customization
        industry_context = self._get_industry_context(industry)
        
        # Build template customization prompt
        prompt = f"""
You are an expert web designer specializing in {industry} businesses. Customize this base template for optimal performance in the {industry} industry.

BASE TEMPLATE:
{json.dumps(base_template, indent=2)}

BUSINESS INFORMATION:
{json.dumps(business_info, indent=2)}

INDUSTRY CONTEXT:
{industry_context}

CUSTOMIZATION REQUIREMENTS:
1. **Color Scheme**: Industry-appropriate colors that build trust and professionalism
2. **Content Sections**: Industry-specific sections and content blocks
3. **Navigation**: Optimized menu structure for {industry} user journeys
4. **Call-to-Actions**: Industry-specific CTAs that drive conversions
5. **Trust Signals**: Relevant certifications, badges, and social proof elements
6. **Forms**: Industry-appropriate contact and lead capture forms
7. **Media**: Recommended image types and video content
8. **SEO Elements**: Industry-specific meta tags and structured data
9. **Compliance**: Industry regulations and accessibility requirements
10. **Integrations**: Relevant third-party tools and services

OUTPUT FORMAT (JSON):
{{
    "color_scheme": {{
        "primary": "#hex_color",
        "secondary": "#hex_color", 
        "accent": "#hex_color",
        "background": "#hex_color",
        "text": "#hex_color"
    }},
    "sections": [
        {{
            "name": "section_name",
            "title": "Section Title",
            "content_type": "hero|services|testimonials|contact|about",
            "priority": 1-10,
            "industry_specific": true|false
        }}
    ],
    "navigation": {{
        "menu_items": ["Home", "Services", "About", "Contact"],
        "cta_button": "Primary CTA Text"
    }},
    "forms": [
        {{
            "name": "form_name",
            "fields": ["field1", "field2"],
            "purpose": "lead_capture|contact|quote_request"
        }}
    ],
    "trust_signals": ["certification1", "badge1", "testimonial_type"],
    "integrations": ["tool1", "service1"],
    "compliance_notes": ["requirement1", "regulation1"]
}}

Focus on industry best practices and conversion optimization for {industry} businesses.
"""
        return prompt.strip()
    
    def _parse_template_customization_response(self, response_content: str) -> Dict[str, Any]:
        """Parse AI response for template customization.
        
        Args:
            response_content: Raw AI response content
            
        Returns:
            Parsed template customization data
        """
        try:
            # Extract JSON from response
            json_start = response_content.find('{')
            json_end = response_content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = response_content[json_start:json_end]
                return json.loads(json_content)
            else:
                # Return default customization on parse failure
                return {
                    "color_scheme": {
                        "primary": "#2c5aa0",
                        "secondary": "#34495e", 
                        "accent": "#e74c3c",
                        "background": "#ffffff",
                        "text": "#333333"
                    },
                    "sections": [
                        {"name": "hero", "title": "Hero Section", "content_type": "hero", "priority": 1, "industry_specific": False},
                        {"name": "services", "title": "Our Services", "content_type": "services", "priority": 2, "industry_specific": True},
                        {"name": "about", "title": "About Us", "content_type": "about", "priority": 3, "industry_specific": False},
                        {"name": "contact", "title": "Contact Us", "content_type": "contact", "priority": 4, "industry_specific": False}
                    ],
                    "navigation": {
                        "menu_items": ["Home", "Services", "About", "Contact"],
                        "cta_button": "Get Started"
                    },
                    "forms": [
                        {"name": "contact_form", "fields": ["name", "email", "phone", "message"], "purpose": "contact"}
                    ],
                    "trust_signals": ["testimonials", "certifications", "reviews"],
                    "integrations": ["analytics", "crm"],
                    "compliance_notes": ["accessibility", "privacy_policy"]
                }
                
        except json.JSONDecodeError:
            # Return default customization on JSON error
            return {
                "color_scheme": {"primary": "#2c5aa0", "secondary": "#34495e", "accent": "#e74c3c", "background": "#ffffff", "text": "#333333"},
                "sections": [{"name": "hero", "title": "Welcome", "content_type": "hero", "priority": 1, "industry_specific": False}],
                "navigation": {"menu_items": ["Home", "About", "Contact"], "cta_button": "Contact Us"},
                "forms": [{"name": "contact", "fields": ["name", "email", "message"], "purpose": "contact"}],
                "trust_signals": ["testimonials"],
                "integrations": ["analytics"],
                "compliance_notes": ["privacy_policy"]
            }
    
    def _merge_template_customizations(self, base_template: Dict[str, Any], 
                                     customizations: Dict[str, Any]) -> Dict[str, Any]:
        """Merge customizations with base template.
        
        Args:
            base_template: Original template configuration
            customizations: AI-generated customizations
            
        Returns:
            Merged template configuration
        """
        # Create a deep copy of base template
        merged_template = base_template.copy()
        
        # Merge customizations into base template
        for key, value in customizations.items():
            if key in merged_template and isinstance(merged_template[key], dict) and isinstance(value, dict):
                # Merge nested dictionaries
                merged_template[key].update(value)
            else:
                # Replace or add new keys
                merged_template[key] = value
        
        # Add metadata about customization
        merged_template['customization_metadata'] = {
            'customized': True,
            'customization_version': '1.0',
            'ai_generated': True
        }
        
        return merged_template


# Global AI client instance
ai_client = AIClient()