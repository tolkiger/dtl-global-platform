"""POST /deploy Lambda handler for DTL-Global onboarding platform.

This handler deploys websites to S3 and configures CloudFront distribution.

Endpoint: POST /deploy
Purpose: Deploy client websites to S3 with CloudFront
Dependencies: S3 client, AI client for content generation

Author: DTL-Global Platform
"""

import json
from typing import Any, Dict
from datetime import datetime

# Import shared modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import config
from s3_client import s3_client
from ai_client import ai_client


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Deploy website to S3 and configure CloudFront."""
    print(f"Website deployment started - Request ID: {context.aws_request_id}")
    
    try:
        request_data = json.loads(event['body'])
        client_info = request_data['client_info']
        
        # Generate website content using AI
        website_prompt = ai_client.generate_website_prompt(
            business_info=client_info,
            industry=client_info.get('industry', 'general')
        )
        
        # Create basic website files
        website_files = {
            'index.html': _generate_website_html(client_info),
            '404.html': _generate_404_html(client_info)
        }
        
        # Deploy to S3
        domain = client_info.get('domain', f"{client_info['company'].lower().replace(' ', '-')}.example.com")
        deploy_result = s3_client.deploy_website(
            client_domain=domain,
            website_files=website_files,
            enable_spa=False
        )
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'website_url': deploy_result['website_url'],
                'domain_prefix': deploy_result['domain_prefix'],
                'files_deployed': len(deploy_result['deployed_files']),
                'message': 'Website deployed successfully'
            })
        }
        
    except Exception as e:
        print(f"Error in website deployment: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e), 'timestamp': datetime.utcnow().isoformat()})
        }


def _generate_website_html(client_info: Dict[str, Any]) -> str:
    """Generate basic website HTML."""
    company_name = client_info.get('company', 'Your Company')
    industry = client_info.get('industry', 'business')
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{company_name} - Professional {industry.title()} Services</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        header {{ background: #2c5aa0; color: white; padding: 1rem 0; }}
        .hero {{ text-align: center; padding: 4rem 0; background: #f8f9fa; }}
        .contact {{ background: #2c5aa0; color: white; padding: 3rem 0; text-align: center; }}
        .btn {{ background: #ff6b35; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>{company_name}</h1>
            <p>Professional {industry.title()} Services</p>
        </div>
    </header>
    <section class="hero">
        <div class="container">
            <h2>Welcome to {company_name}</h2>
            <p>Your trusted partner for professional {industry} services.</p>
            <a href="#contact" class="btn">Get Started Today</a>
        </div>
    </section>
    <section class="contact" id="contact">
        <div class="container">
            <h2>Contact Us</h2>
            <p>Email: {client_info.get('email', 'info@company.com')}</p>
            <p>Phone: {client_info.get('phone', '(555) 123-4567')}</p>
        </div>
    </section>
</body>
</html>"""


def _generate_404_html(client_info: Dict[str, Any]) -> str:
    """Generate 404 page HTML."""
    return f"""<!DOCTYPE html>
<html><head><title>Page Not Found</title></head>
<body style="text-align:center;padding:4rem;">
<h1>404 - Page Not Found</h1>
<p>The page you're looking for doesn't exist.</p>
<a href="/">Return Home</a>
</body></html>"""
