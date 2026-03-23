"""POST /prompt Lambda handler for DTL-Global onboarding platform.

This handler generates SEO-optimized website content prompts using AI analysis.
Creates comprehensive website content specifications following DTL SEO standards.

Endpoint: POST /prompt
Purpose: Generate detailed, SEO-optimized website content prompts
Dependencies: AI client (Claude), DynamoDB for template storage

Author: DTL-Global Platform
"""

import json
import boto3
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta

# Import shared modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import config
from ai_client import ai_client


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Generate SEO-optimized website content prompt.
    
    This function creates comprehensive website content specifications using
    AI analysis of business information and industry best practices.
    
    Args:
        event: API Gateway proxy request event containing business information
        context: Lambda runtime context object
        
    Returns:
        API Gateway proxy response with detailed website content prompt
        
    Expected Request Body:
        {
            "business_info": {
                "name": "Business Name",
                "description": "Business description",
                "location": "City, State",
                "services": ["service1", "service2"],
                "keywords": ["keyword1", "keyword2"],
                "industry": "roofing",
                "phone": "555-1234",
                "address": "123 Main St, City, State 12345",
                "website_goals": ["generate_leads", "showcase_work", "build_trust"]
            },
            "template_preferences": {
                "style": "modern",  // modern, classic, minimal
                "color_scheme": "blue",  // blue, green, red, neutral
                "layout": "single_page",  // single_page, multi_page
                "features": ["contact_form", "gallery", "testimonials"]
            }
        }
    """
    print(f"Website prompt generation started - Request ID: {context.aws_request_id}")
    
    try:
        # Parse request body
        if not event.get('body'):
            return _create_error_response(400, "Request body is required")
        
        # Parse JSON body from API Gateway
        try:
            request_data = json.loads(event['body'])
        except json.JSONDecodeError as e:
            return _create_error_response(400, f"Invalid JSON in request body: {e}")
        
        # Validate required fields
        validation_error = _validate_prompt_request(request_data)
        if validation_error:
            return _create_error_response(400, validation_error)
        
        # Extract business information and preferences
        business_info = request_data['business_info']
        template_prefs = request_data.get('template_preferences', {})
        
        print(f"Generating website prompt for {business_info['name']} - Industry: {business_info['industry']}")
        
        # Enhance business info with industry-specific data
        enhanced_business_info = _enhance_business_info(business_info)
        
        # Generate AI-powered website prompt
        print("Calling AI client for website prompt generation")
        website_prompt = ai_client.generate_website_prompt(
            business_info=enhanced_business_info,
            industry=business_info['industry']
        )
        
        # Load industry template if available
        industry_template = _get_industry_template(business_info['industry'])
        
        # Create structured prompt data
        prompt_data = _structure_prompt_data(
            website_prompt, 
            business_info, 
            template_prefs, 
            industry_template
        )
        
        # Store prompt data for future reference
        print("Storing prompt data in DynamoDB")
        prompt_record = _store_prompt_data(prompt_data, business_info)
        
        # Generate additional SEO recommendations
        seo_recommendations = _generate_seo_recommendations(business_info)
        
        # Prepare response data
        response_data = {
            'prompt_id': prompt_record['prompt_id'],
            'business_name': business_info['name'],
            'industry': business_info['industry'],
            'website_prompt': website_prompt,
            'structured_content': {
                'page_sections': prompt_data['page_sections'],
                'seo_elements': prompt_data['seo_elements'],
                'technical_requirements': prompt_data['technical_requirements']
            },
            'seo_recommendations': seo_recommendations,
            'industry_template': industry_template,
            'implementation_notes': _get_implementation_notes(business_info['industry']),
            'generated_at': datetime.utcnow().isoformat()
        }
        
        print(f"Website prompt generation completed successfully - Prompt ID: {prompt_record['prompt_id']}")
        
        # Return successful response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  # Enable CORS
            },
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        # Log error for debugging
        print(f"Error in website prompt generation: {str(e)}")
        
        # Return error response
        return _create_error_response(500, f"Internal server error: {str(e)}")


def _validate_prompt_request(request_data: Dict[str, Any]) -> Optional[str]:
    """Validate the website prompt request data.
    
    Args:
        request_data: Parsed request body data
        
    Returns:
        Error message if validation fails, None if valid
    """
    # Check required top-level fields
    if 'business_info' not in request_data:
        return "Missing required field: business_info"
    
    # Validate business_info fields
    business_info = request_data['business_info']
    required_fields = ['name', 'industry']
    for field in required_fields:
        if field not in business_info or not business_info[field]:
            return f"Missing required business_info field: {field}"
    
    # Validate industry (should match available templates)
    valid_industries = ['roofing', 'plumbing', 'hvac', 'electrical', 'landscaping', 'general']
    if business_info['industry'] not in valid_industries:
        print(f"Warning: Industry '{business_info['industry']}' not in predefined list, using general template")
    
    return None  # Validation passed


def _enhance_business_info(business_info: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance business information with industry-specific defaults.
    
    Args:
        business_info: Original business information
        
    Returns:
        Enhanced business information dictionary
    """
    # Create enhanced copy
    enhanced = business_info.copy()
    
    # Add default services based on industry
    if 'services' not in enhanced or not enhanced['services']:
        enhanced['services'] = _get_default_services(business_info['industry'])
    
    # Add default keywords based on industry
    if 'keywords' not in enhanced or not enhanced['keywords']:
        enhanced['keywords'] = _get_default_keywords(business_info['industry'])
    
    # Add default website goals if not specified
    if 'website_goals' not in enhanced:
        enhanced['website_goals'] = ['generate_leads', 'build_trust', 'showcase_expertise']
    
    # Ensure location is formatted properly
    if 'location' not in enhanced and 'address' in enhanced:
        # Extract city/state from address
        address_parts = enhanced['address'].split(',')
        if len(address_parts) >= 2:
            enhanced['location'] = f"{address_parts[-2].strip()}, {address_parts[-1].strip()}"
    
    return enhanced


def _get_default_services(industry: str) -> List[str]:
    """Get default services for an industry.
    
    Args:
        industry: Industry type
        
    Returns:
        List of default services
    """
    # Industry-specific service mappings
    industry_services = {
        'roofing': ['Roof Repair', 'Roof Replacement', 'Roof Inspection', 'Gutter Services', 'Emergency Repairs'],
        'plumbing': ['Drain Cleaning', 'Pipe Repair', 'Water Heater Service', 'Leak Detection', 'Emergency Plumbing'],
        'hvac': ['AC Repair', 'Heating Repair', 'HVAC Installation', 'Maintenance Plans', 'Energy Audits'],
        'electrical': ['Electrical Repair', 'Panel Upgrades', 'Outlet Installation', 'Lighting', 'Emergency Service'],
        'landscaping': ['Lawn Care', 'Tree Service', 'Landscape Design', 'Irrigation', 'Seasonal Cleanup']
    }
    
    return industry_services.get(industry, ['Professional Services', 'Consultation', 'Maintenance', 'Emergency Service'])


def _get_default_keywords(industry: str) -> List[str]:
    """Get default SEO keywords for an industry.
    
    Args:
        industry: Industry type
        
    Returns:
        List of default keywords
    """
    # Industry-specific keyword mappings
    industry_keywords = {
        'roofing': ['roofing contractor', 'roof repair', 'roof replacement', 'local roofer', 'emergency roof repair'],
        'plumbing': ['plumber', 'plumbing services', 'drain cleaning', 'emergency plumber', 'water heater repair'],
        'hvac': ['HVAC contractor', 'AC repair', 'heating repair', 'HVAC installation', 'air conditioning service'],
        'electrical': ['electrician', 'electrical services', 'electrical repair', 'panel upgrade', 'emergency electrician'],
        'landscaping': ['landscaping', 'lawn care', 'tree service', 'landscape design', 'yard maintenance']
    }
    
    return industry_keywords.get(industry, ['professional services', 'local contractor', 'expert service'])


def _get_industry_template(industry: str) -> Dict[str, Any]:
    """Load industry-specific template data.
    
    Args:
        industry: Industry type
        
    Returns:
        Industry template dictionary
    """
    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(config.DYNAMODB_TABLES['templates'])
        
        # Try to get industry template
        response = table.get_item(
            Key={
                'pk': f'TEMPLATE#{industry.upper()}',
                'sk': 'METADATA'
            }
        )
        
        if 'Item' in response:
            return response['Item']
        
    except Exception as e:
        print(f"Could not load industry template for {industry}: {e}")
    
    # Return default template structure
    return {
        'industry': industry,
        'color_scheme': 'blue',
        'layout_type': 'single_page',
        'sections': ['hero', 'services', 'about', 'testimonials', 'contact'],
        'features': ['contact_form', 'phone_number', 'service_areas']
    }


def _structure_prompt_data(website_prompt: str, business_info: Dict[str, Any],
                          template_prefs: Dict[str, Any], 
                          industry_template: Dict[str, Any]) -> Dict[str, Any]:
    """Structure the website prompt data into organized sections.
    
    Args:
        website_prompt: Generated AI prompt text
        business_info: Business information
        template_prefs: Template preferences
        industry_template: Industry template data
        
    Returns:
        Structured prompt data dictionary
    """
    # Define standard page sections per DTL master plan Section 17
    page_sections = [
        {
            'name': 'hero',
            'title': 'Hero Section',
            'description': 'Above-the-fold section with main headline and CTA',
            'required_elements': ['h1_headline', 'subheadline', 'primary_cta', 'hero_image']
        },
        {
            'name': 'services',
            'title': 'Services Section',
            'description': 'Detailed service offerings with SEO keywords',
            'required_elements': ['service_list', 'service_descriptions', 'keywords']
        },
        {
            'name': 'about',
            'title': 'About Section',
            'description': 'Company information and trust signals',
            'required_elements': ['company_story', 'credentials', 'experience']
        },
        {
            'name': 'testimonials',
            'title': 'Testimonials Section',
            'description': 'Customer reviews and social proof',
            'required_elements': ['customer_reviews', 'ratings', 'case_studies']
        },
        {
            'name': 'contact',
            'title': 'Contact Section',
            'description': 'Contact information and lead capture form',
            'required_elements': ['contact_form', 'nap_info', 'google_map']
        }
    ]
    
    # Define SEO elements per DTL master plan Section 17
    seo_elements = {
        'meta_title': f"{business_info['name']} - {business_info['industry'].title()} Services",
        'meta_description': f"Professional {business_info['industry']} services. Contact {business_info['name']} for expert service.",
        'h1_structure': 'Single H1 with primary keyword',
        'h2_h3_hierarchy': 'Logical heading structure with secondary keywords',
        'schema_markup': ['LocalBusiness', f'{business_info["industry"].title()}Contractor'],
        'open_graph_tags': ['og:title', 'og:description', 'og:image', 'og:type'],
        'internal_linking': 'Link between service pages and contact',
        'image_alt_text': 'Descriptive alt text with keywords',
        'robots_txt': 'Allow all, sitemap reference',
        'sitemap_xml': 'Include all pages and services'
    }
    
    # Define technical requirements
    technical_requirements = {
        'html_structure': 'Semantic HTML5 elements',
        'responsive_design': 'Mobile-first CSS framework',
        'accessibility': 'ARIA labels, keyboard navigation, color contrast',
        'performance': 'Optimized images, minified CSS/JS',
        'forms': 'Honeypot anti-spam, validation',
        'analytics': 'Google Analytics 4 integration',
        'speed_optimization': 'Image compression, lazy loading'
    }
    
    return {
        'page_sections': page_sections,
        'seo_elements': seo_elements,
        'technical_requirements': technical_requirements,
        'industry_specific': industry_template,
        'template_preferences': template_prefs
    }


def _generate_seo_recommendations(business_info: Dict[str, Any]) -> Dict[str, Any]:
    """Generate SEO recommendations based on business information.
    
    Args:
        business_info: Business information dictionary
        
    Returns:
        SEO recommendations dictionary
    """
    location = business_info.get('location', 'your area')
    industry = business_info['industry']
    
    return {
        'local_seo': {
            'google_my_business': 'Claim and optimize Google My Business listing',
            'local_keywords': f'Target "{industry} in {location}" and similar local terms',
            'nap_consistency': 'Ensure Name, Address, Phone consistent across all platforms',
            'local_citations': 'Submit to industry-specific directories'
        },
        'content_strategy': {
            'blog_topics': [
                f'Common {industry} problems in {location}',
                f'How to choose a {industry} contractor',
                f'Seasonal {industry} maintenance tips'
            ],
            'service_pages': 'Create dedicated pages for each service',
            'faq_section': 'Answer common customer questions',
            'case_studies': 'Showcase successful projects with before/after'
        },
        'technical_seo': {
            'page_speed': 'Optimize for Core Web Vitals',
            'mobile_optimization': 'Ensure mobile-friendly design',
            'ssl_certificate': 'Install SSL certificate for HTTPS',
            'structured_data': 'Implement LocalBusiness schema markup'
        }
    }


def _get_implementation_notes(industry: str) -> List[str]:
    """Get implementation notes specific to the industry.
    
    Args:
        industry: Industry type
        
    Returns:
        List of implementation notes
    """
    # Industry-specific implementation guidance
    industry_notes = {
        'roofing': [
            'Include before/after photo gallery',
            'Emphasize emergency service availability',
            'Show licensing and insurance information prominently',
            'Add weather-related service alerts'
        ],
        'plumbing': [
            'Highlight 24/7 emergency services',
            'Include service area map',
            'Show certifications and licenses',
            'Add water damage prevention tips'
        ],
        'hvac': [
            'Include seasonal maintenance reminders',
            'Show energy efficiency benefits',
            'Add financing options information',
            'Include system replacement calculator'
        ]
    }
    
    return industry_notes.get(industry, [
        'Include professional certifications',
        'Show service area coverage',
        'Add customer testimonials',
        'Include contact form with service selection'
    ])


def _store_prompt_data(prompt_data: Dict[str, Any], business_info: Dict[str, Any]) -> Dict[str, Any]:
    """Store prompt data in DynamoDB.
    
    Args:
        prompt_data: Structured prompt data
        business_info: Business information
        
    Returns:
        Stored prompt record with generated ID
    """
    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(config.DYNAMODB_TABLES['state'])  # Use onboarding state table
    
    # Generate unique prompt ID
    import uuid
    prompt_id = str(uuid.uuid4())
    
    # Prepare prompt record
    prompt_record = {
        'pk': f'PROMPT#{prompt_id}',
        'sk': 'METADATA',
        'prompt_id': prompt_id,
        'business_name': business_info['name'],
        'industry': business_info['industry'],
        'location': business_info.get('location', ''),
        'services': business_info.get('services', []),
        'keywords': business_info.get('keywords', []),
        'prompt_data': prompt_data,
        'status': 'generated',
        'created_at': datetime.utcnow().isoformat(),
        'ttl': int((datetime.utcnow() + timedelta(days=30)).timestamp())  # Expire after 30 days
    }
    
    # Store in DynamoDB
    table.put_item(Item=prompt_record)
    print(f"Stored prompt data in DynamoDB: {prompt_id}")
    
    return prompt_record


def _create_error_response(status_code: int, error_message: str) -> Dict[str, Any]:
    """Create a standardized error response.
    
    Args:
        status_code: HTTP status code
        error_message: Error message to return
        
    Returns:
        API Gateway proxy response dictionary
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'  # Enable CORS
        },
        'body': json.dumps({
            'error': error_message,
            'timestamp': datetime.utcnow().isoformat()
        })
    }
