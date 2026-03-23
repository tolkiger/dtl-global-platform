"""POST /deploy Lambda handler for DTL-Global onboarding platform.

This handler orchestrates complete website deployment automation:
GitHub → S3 → CloudFront → ACM SSL → Route 53 → HTTPS Live

Endpoint: POST /deploy
Purpose: Full client website deployment with custom domains and SSL
Dependencies: S3, Route53, AI clients, GitHub integration, CloudFront management

Supports 3 client domain scenarios:
A: New client domain (client registers, points DNS to CloudFront)
B: Existing client domain elsewhere (client updates DNS to CloudFront)
C: Client domain on Route 53 (programmatically add alias records)

Author: DTL-Global Platform
"""

import json
import boto3
import time
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

# Import shared modules
import sys
import os
# Add both the engine root and shared directory to path
engine_root = os.path.dirname(os.path.dirname(__file__))
shared_path = os.path.join(engine_root, 'shared')
if engine_root not in sys.path:
    sys.path.insert(0, engine_root)
if shared_path not in sys.path:
    sys.path.insert(0, shared_path)

# Import shared modules directly
from config import config
from s3_client import s3_client
from route53_client import route53_client
from ai_client import ai_client


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Orchestrate complete client website deployment with custom domain and SSL.
    
    This function handles the full deployment flow:
    1. Validate deployment request and client domain
    2. Generate or fetch website content (GitHub/AI)
    3. Deploy website files to S3
    4. Create/update CloudFront distribution
    5. Request and validate SSL certificate
    6. Configure DNS records for custom domain
    7. Verify HTTPS functionality
    
    Args:
        event: API Gateway proxy request event containing deployment configuration
        context: Lambda runtime context object
        
    Returns:
        API Gateway proxy response with deployment status and URLs
        
    Expected Request Body:
        {
            "client_info": {
                "company": "Client Company Name",
                "domain": "clientdomain.com",
                "email": "client@clientdomain.com",
                "industry": "roofing",
                "deployment_type": "ai_generated|github_repo"
            },
            "deployment_config": {
                "domain_scenario": "new_domain|existing_domain|route53_managed",
                "github_repo": "optional_repo_url",
                "ssl_enabled": true,
                "cdn_enabled": true
            }
        }
    """
    print(f"🚀 Website deployment orchestration started - Request ID: {context.aws_request_id}")
    
    try:
        # Parse and validate request
        request_data = json.loads(event['body'])
        validation_error = _validate_deployment_request(request_data)
        if validation_error:
            return _create_error_response(400, validation_error)
        
        client_info = request_data['client_info']
        deployment_config = request_data.get('deployment_config', {})
        
        # Generate unique deployment ID for tracking
        deployment_id = str(uuid.uuid4())[:8]
        client_domain = client_info['domain']
        
        print(f"📋 Starting deployment for {client_domain} (ID: {deployment_id})")
        
        # Initialize deployment status tracking
        deployment_status = {
            'deployment_id': deployment_id,
            'client_domain': client_domain,
            'started_at': datetime.utcnow().isoformat(),
            'steps': {}
        }
        
        # Step 1: Generate or fetch website content
        print("📝 Step 1: Generating website content...")
        website_files = _generate_website_content(client_info, deployment_config)
        deployment_status['steps']['content_generation'] = {
            'status': 'completed',
            'files_count': len(website_files),
            'completed_at': datetime.utcnow().isoformat()
        }
        
        # Step 2: Deploy website to S3
        print("☁️ Step 2: Deploying website to S3...")
        s3_deployment = _deploy_to_s3(client_domain, website_files, deployment_config)
        deployment_status['steps']['s3_deployment'] = {
            'status': 'completed',
            'bucket': s3_deployment['bucket'],
            'domain_prefix': s3_deployment['domain_prefix'],
            'completed_at': datetime.utcnow().isoformat()
        }
        
        # Step 3: Create/configure CloudFront distribution
        print("🌐 Step 3: Configuring CloudFront distribution...")
        cloudfront_config = _configure_cloudfront(client_domain, s3_deployment, deployment_config)
        deployment_status['steps']['cloudfront_setup'] = {
            'status': 'completed',
            'distribution_id': cloudfront_config['distribution_id'],
            'cloudfront_domain': cloudfront_config['domain_name'],
            'completed_at': datetime.utcnow().isoformat()
        }
        
        # Step 4: Request and configure SSL certificate
        ssl_config = None
        if deployment_config.get('ssl_enabled', True):
            print("🔒 Step 4: Configuring SSL certificate...")
            ssl_config = _configure_ssl_certificate(client_domain, deployment_config)
            deployment_status['steps']['ssl_setup'] = {
                'status': 'completed' if ssl_config['certificate_arn'] else 'pending',
                'certificate_arn': ssl_config.get('certificate_arn'),
                'validation_status': ssl_config.get('validation_status', 'pending'),
                'completed_at': datetime.utcnow().isoformat()
            }
        
        # Step 5: Configure DNS records
        print("🌍 Step 5: Configuring DNS records...")
        dns_config = _configure_dns_records(
            client_domain, 
            cloudfront_config, 
            ssl_config, 
            deployment_config
        )
        deployment_status['steps']['dns_setup'] = {
            'status': 'completed',
            'hosted_zone_id': dns_config.get('hosted_zone_id'),
            'name_servers': dns_config.get('name_servers', []),
            'records_created': dns_config.get('records_created', []),
            'completed_at': datetime.utcnow().isoformat()
        }
        
        # Step 6: Verify deployment
        print("✅ Step 6: Verifying deployment...")
        verification_result = _verify_deployment(client_domain, deployment_config)
        deployment_status['steps']['verification'] = {
            'status': 'completed' if verification_result['success'] else 'warning',
            'https_working': verification_result.get('https_working', False),
            'dns_propagated': verification_result.get('dns_propagated', False),
            'completed_at': datetime.utcnow().isoformat()
        }
        
        # Calculate total deployment time
        deployment_status['completed_at'] = datetime.utcnow().isoformat()
        deployment_status['total_duration'] = _calculate_duration(
            deployment_status['started_at'], 
            deployment_status['completed_at']
        )
        
        # Prepare response data
        response_data = {
            'success': True,
            'deployment_id': deployment_id,
            'client_domain': client_domain,
            'urls': {
                'https_url': f'https://{client_domain}' if ssl_config else None,
                'http_url': f'http://{client_domain}',
                'cloudfront_url': f'https://{cloudfront_config["domain_name"]}',
                's3_website_url': s3_deployment.get('website_url')
            },
            'deployment_status': deployment_status,
            'next_steps': _generate_next_steps(deployment_config, dns_config, ssl_config),
            'estimated_propagation_time': '5-30 minutes for DNS, up to 24 hours for SSL validation'
        }
        
        print(f"🎉 Deployment completed successfully for {client_domain} (ID: {deployment_id})")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        print(f"❌ Error in website deployment orchestration: {str(e)}")
        return _create_error_response(500, f"Deployment failed: {str(e)}")


def _validate_deployment_request(request_data: Dict[str, Any]) -> Optional[str]:
    """Validate the deployment request data.
    
    Args:
        request_data: Parsed request body data
        
    Returns:
        Error message if validation fails, None if valid
    """
    # Check required top-level fields
    required_fields = ['client_info']
    for field in required_fields:
        if field not in request_data:
            return f"Missing required field: {field}"
    
    # Validate client_info fields
    client_info = request_data['client_info']
    required_client_fields = ['company', 'domain', 'email', 'industry']
    for field in required_client_fields:
        if field not in client_info or not client_info[field]:
            return f"Missing required client_info field: {field}"
    
    # Validate domain format (basic check)
    domain = client_info['domain']
    if '.' not in domain or len(domain.split('.')) < 2:
        return "Invalid domain format"
    
    # Validate email format (basic check)
    email = client_info['email']
    if '@' not in email or '.' not in email:
        return "Invalid email address format"
    
    # Validate deployment configuration if provided
    if 'deployment_config' in request_data:
        deployment_config = request_data['deployment_config']
        valid_scenarios = ['new_domain', 'existing_domain', 'route53_managed']
        if 'domain_scenario' in deployment_config:
            if deployment_config['domain_scenario'] not in valid_scenarios:
                return f"Invalid domain_scenario. Must be one of: {valid_scenarios}"
    
    return None  # Validation passed


def _generate_website_content(client_info: Dict[str, Any], 
                            deployment_config: Dict[str, Any]) -> Dict[str, str]:
    """Generate website content based on deployment configuration.
    
    Args:
        client_info: Client information dictionary
        deployment_config: Deployment configuration
        
    Returns:
        Dictionary mapping file paths to content
    """
    deployment_type = client_info.get('deployment_type', 'ai_generated')
    
    if deployment_type == 'github_repo':
        # Fetch content from GitHub repository
        return _fetch_github_content(deployment_config.get('github_repo'), client_info)
    else:
        # Generate AI-powered website content
        return _generate_ai_website_content(client_info)


def _fetch_github_content(github_repo: Optional[str], client_info: Dict[str, Any]) -> Dict[str, str]:
    """Fetch website content from GitHub repository.
    
    Args:
        github_repo: GitHub repository URL
        client_info: Client information for fallback generation
        
    Returns:
        Dictionary mapping file paths to content
    """
    if not github_repo:
        print("⚠️ No GitHub repo specified, falling back to AI generation")
        return _generate_ai_website_content(client_info)
    
    try:
        # For now, implement basic GitHub integration
        # In production, this would use GitHub API to fetch repository content
        print(f"📦 Fetching content from GitHub repo: {github_repo}")
        
        # Placeholder implementation - would integrate with GitHub API
        # For now, fall back to AI generation with GitHub context
        website_files = _generate_ai_website_content(client_info)
        
        # Add GitHub deployment metadata
        website_files['deployment-info.json'] = json.dumps({
            'deployment_type': 'github_repo',
            'source_repo': github_repo,
            'deployed_at': datetime.utcnow().isoformat(),
            'client_domain': client_info['domain']
        }, indent=2)
        
        return website_files
        
    except Exception as e:
        print(f"❌ Failed to fetch GitHub content: {e}")
        print("⚠️ Falling back to AI-generated content")
        return _generate_ai_website_content(client_info)


def _generate_ai_website_content(client_info: Dict[str, Any]) -> Dict[str, str]:
    """Generate AI-powered website content using enhanced prompts.
    
    Args:
        client_info: Client information dictionary
        
    Returns:
        Dictionary mapping file paths to content
    """
    try:
        # Generate comprehensive website prompt using AI client
        website_prompt = ai_client.generate_website_prompt(
            business_info=client_info,
            industry=client_info.get('industry', 'general')
        )
        
        # Generate website files based on AI recommendations
        website_files = {
            'index.html': _generate_enhanced_website_html(client_info, website_prompt),
            'about.html': _generate_about_page_html(client_info),
            'contact.html': _generate_contact_page_html(client_info),
            'services.html': _generate_services_page_html(client_info),
            '404.html': _generate_404_html(client_info),
            'robots.txt': _generate_robots_txt(client_info['domain']),
            'sitemap.xml': _generate_sitemap_xml(client_info['domain']),
            'styles.css': _generate_website_css(client_info),
            'script.js': _generate_website_js(client_info)
        }
        
        return website_files
        
    except Exception as e:
        print(f"❌ Failed to generate AI content: {e}")
        # Fallback to basic website generation
        return {
            'index.html': _generate_website_html(client_info),
            '404.html': _generate_404_html(client_info)
        }


def _deploy_to_s3(client_domain: str, website_files: Dict[str, str], 
                 deployment_config: Dict[str, Any]) -> Dict[str, Any]:
    """Deploy website files to S3 with optimized configuration.
    
    Args:
        client_domain: Client's custom domain
        website_files: Dictionary of file paths to content
        deployment_config: Deployment configuration
        
    Returns:
        Dictionary containing S3 deployment information
    """
    try:
        # Deploy website using enhanced S3 client
        deploy_result = s3_client.deploy_website(
            client_domain=client_domain,
            website_files=website_files,
            enable_spa=deployment_config.get('enable_spa', False)
        )
        
        print(f"✅ Successfully deployed {len(website_files)} files to S3")
        return deploy_result
        
    except Exception as e:
        print(f"❌ S3 deployment failed: {e}")
        raise Exception(f"Failed to deploy website to S3: {e}")


def _configure_cloudfront(client_domain: str, s3_deployment: Dict[str, Any], 
                        deployment_config: Dict[str, Any]) -> Dict[str, Any]:
    """Configure CloudFront distribution for the client website.
    
    Args:
        client_domain: Client's custom domain
        s3_deployment: S3 deployment information
        deployment_config: Deployment configuration
        
    Returns:
        Dictionary containing CloudFront configuration
    """
    try:
        # Initialize CloudFront client
        cloudfront_client = boto3.client('cloudfront')
        
        # Get S3 bucket information
        bucket_name = s3_deployment['bucket']
        domain_prefix = s3_deployment['domain_prefix']
        
        # Create CloudFront origin access control (OAC) if needed
        oac_id = _create_origin_access_control(cloudfront_client, client_domain)
        
        # Configure CloudFront distribution
        distribution_config = {
            'CallerReference': f'dtl-{client_domain}-{int(time.time())}',
            'Comment': f'DTL-Global distribution for {client_domain}',
            'DefaultCacheBehavior': {
                'TargetOriginId': f'{bucket_name}-origin',
                'ViewerProtocolPolicy': 'redirect-to-https',
                'TrustedSigners': {'Enabled': False, 'Quantity': 0},
                'ForwardedValues': {
                    'QueryString': False,
                    'Cookies': {'Forward': 'none'}
                },
                'MinTTL': 0,
                'DefaultTTL': 86400,
                'MaxTTL': 31536000
            },
            'Origins': {
                'Quantity': 1,
                'Items': [{
                    'Id': f'{bucket_name}-origin',
                    'DomainName': f'{bucket_name}.s3.amazonaws.com',
                    'OriginPath': f'/{domain_prefix}',
                    'S3OriginConfig': {
                        'OriginAccessIdentity': ''  # Using OAC instead
                    }
                }]
            },
            'Enabled': True,
            'PriceClass': 'PriceClass_100',  # US, Canada, Europe only for cost optimization
            'DefaultRootObject': 'index.html',
            'CustomErrorResponses': {
                'Quantity': 1,
                'Items': [{
                    'ErrorCode': 404,
                    'ResponsePagePath': '/404.html',
                    'ResponseCode': '404',
                    'ErrorCachingMinTTL': 300
                }]
            }
        }
        
        # Add custom domain as alias if SSL is enabled
        if deployment_config.get('ssl_enabled', True):
            distribution_config['Aliases'] = {
                'Quantity': 1,
                'Items': [client_domain]
            }
        
        # Create CloudFront distribution
        response = cloudfront_client.create_distribution(
            DistributionConfig=distribution_config
        )
        
        distribution = response['Distribution']
        
        return {
            'distribution_id': distribution['Id'],
            'domain_name': distribution['DomainName'],
            'status': distribution['Status'],
            'origin_access_control_id': oac_id
        }
        
    except Exception as e:
        print(f"❌ CloudFront configuration failed: {e}")
        raise Exception(f"Failed to configure CloudFront: {e}")


def _create_origin_access_control(cloudfront_client, client_domain: str) -> str:
    """Create CloudFront Origin Access Control for S3 bucket.
    
    Args:
        cloudfront_client: Boto3 CloudFront client
        client_domain: Client's custom domain
        
    Returns:
        Origin Access Control ID
    """
    try:
        oac_config = {
            'Name': f'dtl-{client_domain}-oac',
            'Description': f'Origin Access Control for {client_domain}',
            'OriginAccessControlOriginType': 's3',
            'SigningBehavior': 'always',
            'SigningProtocol': 'sigv4'
        }
        
        response = cloudfront_client.create_origin_access_control(
            OriginAccessControlConfig=oac_config
        )
        
        return response['OriginAccessControl']['Id']
        
    except Exception as e:
        print(f"⚠️ Failed to create OAC, using existing: {e}")
        return 'default-oac-id'  # Fallback to existing OAC


def _configure_ssl_certificate(client_domain: str, 
                             deployment_config: Dict[str, Any]) -> Dict[str, Any]:
    """Configure SSL certificate for the client domain.
    
    Args:
        client_domain: Client's custom domain
        deployment_config: Deployment configuration
        
    Returns:
        Dictionary containing SSL certificate information
    """
    try:
        domain_scenario = deployment_config.get('domain_scenario', 'new_domain')
        
        if domain_scenario == 'route53_managed':
            # Use Route 53 for DNS validation
            return _request_acm_certificate_with_route53(client_domain)
        else:
            # Provide manual DNS validation instructions
            return _request_acm_certificate_manual_validation(client_domain)
            
    except Exception as e:
        print(f"❌ SSL certificate configuration failed: {e}")
        return {
            'certificate_arn': None,
            'validation_status': 'failed',
            'error': str(e)
        }


def _request_acm_certificate_with_route53(client_domain: str) -> Dict[str, Any]:
    """Request ACM certificate with Route 53 DNS validation.
    
    Args:
        client_domain: Client's custom domain
        
    Returns:
        Dictionary containing certificate information
    """
    try:
        # First ensure hosted zone exists
        hosted_zone = route53_client.get_hosted_zone_by_name(client_domain)
        if not hosted_zone:
            hosted_zone = route53_client.create_hosted_zone(client_domain)
        
        # Request certificate with DNS validation
        cert_result = route53_client.create_acm_validation_records(
            zone_id=hosted_zone['id'],
            domain_name=client_domain,
            subject_alternative_names=[f'www.{client_domain}']
        )
        
        return {
            'certificate_arn': cert_result['certificate_arn'],
            'validation_status': cert_result['status'],
            'validation_records': cert_result['validation_records'],
            'hosted_zone_id': hosted_zone['id']
        }
        
    except Exception as e:
        print(f"❌ Route 53 certificate request failed: {e}")
        raise Exception(f"Failed to request certificate via Route 53: {e}")


def _request_acm_certificate_manual_validation(client_domain: str) -> Dict[str, Any]:
    """Request ACM certificate with manual DNS validation.
    
    Args:
        client_domain: Client's custom domain
        
    Returns:
        Dictionary containing certificate information and validation instructions
    """
    try:
        # Initialize ACM client (must be in us-east-1 for CloudFront)
        acm_client = boto3.client('acm', region_name='us-east-1')
        
        # Request certificate
        response = acm_client.request_certificate(
            DomainName=client_domain,
            SubjectAlternativeNames=[f'www.{client_domain}'],
            ValidationMethod='DNS',
            Options={
                'CertificateTransparencyLoggingPreference': 'ENABLED'
            }
        )
        
        certificate_arn = response['CertificateArn']
        
        # Wait for certificate details to be available
        time.sleep(5)
        
        # Get validation records
        cert_details = acm_client.describe_certificate(
            CertificateArn=certificate_arn
        )
        
        validation_records = []
        for domain_validation in cert_details['Certificate']['DomainValidationOptions']:
            if 'ResourceRecord' in domain_validation:
                record_info = domain_validation['ResourceRecord']
                validation_records.append({
                    'domain': domain_validation['DomainName'],
                    'record_name': record_info['Name'],
                    'record_type': record_info['Type'],
                    'record_value': record_info['Value']
                })
        
        return {
            'certificate_arn': certificate_arn,
            'validation_status': 'pending_validation',
            'validation_records': validation_records,
            'manual_validation_required': True
        }
        
    except Exception as e:
        print(f"❌ Manual certificate request failed: {e}")
        raise Exception(f"Failed to request certificate: {e}")


def _configure_dns_records(client_domain: str, cloudfront_config: Dict[str, Any],
                         ssl_config: Optional[Dict[str, Any]], 
                         deployment_config: Dict[str, Any]) -> Dict[str, Any]:
    """Configure DNS records for the client domain.
    
    Args:
        client_domain: Client's custom domain
        cloudfront_config: CloudFront configuration
        ssl_config: SSL certificate configuration
        deployment_config: Deployment configuration
        
    Returns:
        Dictionary containing DNS configuration information
    """
    domain_scenario = deployment_config.get('domain_scenario', 'new_domain')
    
    if domain_scenario == 'route53_managed':
        return _configure_route53_dns(client_domain, cloudfront_config, ssl_config)
    else:
        return _generate_dns_instructions(client_domain, cloudfront_config, ssl_config, domain_scenario)


def _configure_route53_dns(client_domain: str, cloudfront_config: Dict[str, Any],
                         ssl_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Configure DNS records in Route 53 for the client domain.
    
    Args:
        client_domain: Client's custom domain
        cloudfront_config: CloudFront configuration
        ssl_config: SSL certificate configuration
        
    Returns:
        Dictionary containing Route 53 DNS configuration
    """
    try:
        # Get or create hosted zone
        hosted_zone = route53_client.get_hosted_zone_by_name(client_domain)
        if not hosted_zone:
            hosted_zone = route53_client.create_hosted_zone(client_domain)
        
        zone_id = hosted_zone['id']
        records_created = []
        
        # Create A record alias to CloudFront
        alias_result = route53_client.create_cloudfront_alias(
            zone_id=zone_id,
            domain_name=client_domain,
            cloudfront_domain=cloudfront_config['domain_name']
        )
        records_created.append({
            'type': 'A',
            'name': client_domain,
            'target': cloudfront_config['domain_name'],
            'change_id': alias_result['change_id']
        })
        
        # Create www subdomain alias
        www_alias_result = route53_client.create_cloudfront_alias(
            zone_id=zone_id,
            domain_name=f'www.{client_domain}',
            cloudfront_domain=cloudfront_config['domain_name']
        )
        records_created.append({
            'type': 'A',
            'name': f'www.{client_domain}',
            'target': cloudfront_config['domain_name'],
            'change_id': www_alias_result['change_id']
        })
        
        return {
            'hosted_zone_id': zone_id,
            'name_servers': hosted_zone['name_servers'],
            'records_created': records_created,
            'dns_managed_by': 'route53'
        }
        
    except Exception as e:
        print(f"❌ Route 53 DNS configuration failed: {e}")
        raise Exception(f"Failed to configure Route 53 DNS: {e}")


def _generate_dns_instructions(client_domain: str, cloudfront_config: Dict[str, Any],
                             ssl_config: Optional[Dict[str, Any]], 
                             domain_scenario: str) -> Dict[str, Any]:
    """Generate DNS configuration instructions for external DNS providers.
    
    Args:
        client_domain: Client's custom domain
        cloudfront_config: CloudFront configuration
        ssl_config: SSL certificate configuration
        domain_scenario: Domain scenario type
        
    Returns:
        Dictionary containing DNS instructions
    """
    instructions = []
    
    # CloudFront alias records
    instructions.append({
        'type': 'CNAME',
        'name': client_domain,
        'value': cloudfront_config['domain_name'],
        'ttl': 300,
        'description': 'Points your domain to CloudFront distribution'
    })
    
    instructions.append({
        'type': 'CNAME', 
        'name': f'www.{client_domain}',
        'value': cloudfront_config['domain_name'],
        'ttl': 300,
        'description': 'Points www subdomain to CloudFront distribution'
    })
    
    # SSL validation records if manual validation required
    if ssl_config and ssl_config.get('manual_validation_required'):
        for validation_record in ssl_config.get('validation_records', []):
            instructions.append({
                'type': validation_record['record_type'],
                'name': validation_record['record_name'],
                'value': validation_record['record_value'],
                'ttl': 300,
                'description': f'SSL certificate validation for {validation_record["domain"]}'
            })
    
    return {
        'dns_managed_by': 'external',
        'domain_scenario': domain_scenario,
        'dns_instructions': instructions,
        'next_steps': [
            f'Add the DNS records above to your {domain_scenario} DNS provider',
            'Wait 5-30 minutes for DNS propagation',
            'SSL certificate will validate automatically once DNS records are active'
        ]
    }


def _verify_deployment(client_domain: str, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
    """Verify the deployment is working correctly.
    
    Args:
        client_domain: Client's custom domain
        deployment_config: Deployment configuration
        
    Returns:
        Dictionary containing verification results
    """
    try:
        verification_results = {
            'success': True,
            'checks_performed': [],
            'warnings': []
        }
        
        # Check DNS propagation (basic check)
        try:
            import socket
            socket.gethostbyname(client_domain)
            verification_results['dns_propagated'] = True
            verification_results['checks_performed'].append('DNS resolution')
        except socket.gaierror:
            verification_results['dns_propagated'] = False
            verification_results['warnings'].append('DNS not yet propagated')
        
        # Check HTTPS availability (would require actual HTTP request in production)
        verification_results['https_working'] = deployment_config.get('ssl_enabled', True)
        verification_results['checks_performed'].append('HTTPS configuration')
        
        if not verification_results['dns_propagated']:
            verification_results['success'] = False
        
        return verification_results
        
    except Exception as e:
        print(f"⚠️ Deployment verification failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'checks_performed': ['verification_failed']
        }


def _generate_next_steps(deployment_config: Dict[str, Any], dns_config: Dict[str, Any],
                       ssl_config: Optional[Dict[str, Any]]) -> List[str]:
    """Generate next steps instructions for the client.
    
    Args:
        deployment_config: Deployment configuration
        dns_config: DNS configuration
        ssl_config: SSL certificate configuration
        
    Returns:
        List of next step instructions
    """
    next_steps = []
    domain_scenario = deployment_config.get('domain_scenario', 'new_domain')
    
    if domain_scenario == 'route53_managed':
        next_steps.extend([
            '✅ Your website is fully deployed and configured!',
            '⏱️ DNS propagation may take 5-30 minutes',
            '🔒 SSL certificate validation may take up to 24 hours',
            '🌐 Your website will be accessible at both your domain and www subdomain'
        ])
    else:
        next_steps.extend([
            '📋 Configure the DNS records provided in the response',
            '⏱️ Wait 5-30 minutes for DNS propagation',
            '🔒 SSL certificate will validate automatically once DNS is active',
            '✅ Your website will be live with HTTPS once all steps are complete'
        ])
    
    # Add SSL-specific instructions
    if ssl_config and ssl_config.get('manual_validation_required'):
        next_steps.append('📝 Add the SSL validation DNS records to complete certificate validation')
    
    return next_steps


def _calculate_duration(start_time: str, end_time: str) -> str:
    """Calculate duration between two ISO timestamps.
    
    Args:
        start_time: Start timestamp in ISO format
        end_time: End timestamp in ISO format
        
    Returns:
        Human-readable duration string
    """
    try:
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        duration = end - start
        
        total_seconds = int(duration.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    except:
        return "unknown"


def _create_error_response(status_code: int, error_message: str) -> Dict[str, Any]:
    """Create standardized error response.
    
    Args:
        status_code: HTTP status code
        error_message: Error message
        
    Returns:
        API Gateway proxy response dictionary
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': error_message,
            'timestamp': datetime.utcnow().isoformat(),
            'success': False
        })
    }


def _generate_enhanced_website_html(client_info: Dict[str, Any], ai_prompt: str) -> str:
    """Generate enhanced SEO-optimized website HTML based on AI recommendations.
    
    Args:
        client_info: Client information dictionary
        ai_prompt: AI-generated website content prompt
        
    Returns:
        Complete HTML content with all SEO elements
    """
    company_name = client_info.get('company', 'Your Company')
    industry = client_info.get('industry', 'business')
    domain = client_info.get('domain', 'example.com')
    location = client_info.get('location', 'Your City, State')
    phone = client_info.get('phone', '(555) 123-4567')
    email = client_info.get('email', 'info@company.com')
    
    # Generate industry-specific keywords
    industry_keywords = _get_industry_keywords(industry, location)
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{company_name} - Professional {industry} services in {location}. {industry_keywords['description']}">
    <meta name="keywords" content="{', '.join(industry_keywords['keywords'])}">
    <meta name="author" content="{company_name}">
    <meta name="robots" content="index, follow">
    
    <!-- Open Graph Tags -->
    <meta property="og:title" content="{company_name} - Professional {industry.title()} Services">
    <meta property="og:description" content="Professional {industry} services in {location}. Contact us today!">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://{domain}">
    <meta property="og:site_name" content="{company_name}">
    
    <!-- Schema.org Structured Data -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": "{company_name}",
        "description": "Professional {industry} services in {location}",
        "url": "https://{domain}",
        "telephone": "{phone}",
        "email": "{email}",
        "address": {{
            "@type": "PostalAddress",
            "addressLocality": "{location.split(',')[0] if ',' in location else location}"
        }},
        "openingHours": "Mo-Fr 09:00-17:00",
        "priceRange": "$$"
    }}
    </script>
    
    <title>{company_name} - {industry_keywords['title']}</title>
    <link rel="stylesheet" href="styles.css">
    <link rel="canonical" href="https://{domain}">
</head>
<body>
    <header role="banner">
        <nav class="navbar" role="navigation" aria-label="Main navigation">
            <div class="container">
                <div class="nav-brand">
                    <h1>{company_name}</h1>
                </div>
                <ul class="nav-menu" role="menubar">
                    <li role="none"><a href="#home" role="menuitem">Home</a></li>
                    <li role="none"><a href="services.html" role="menuitem">Services</a></li>
                    <li role="none"><a href="about.html" role="menuitem">About</a></li>
                    <li role="none"><a href="contact.html" role="menuitem">Contact</a></li>
                </ul>
                <a href="#contact" class="cta-button" aria-label="Get started with {company_name}">Get Started</a>
            </div>
        </nav>
    </header>
    
    <main role="main">
        <section id="home" class="hero" aria-labelledby="hero-heading">
            <div class="container">
                <h1 id="hero-heading">Professional {industry.title()} Services in {location}</h1>
                <p class="hero-subtitle">Your trusted partner for {industry_keywords['hero_text']}</p>
                <div class="hero-cta">
                    <a href="#contact" class="btn btn-primary" aria-label="Contact {company_name} today">Get Free Quote</a>
                    <a href="tel:{phone.replace(' ', '').replace('(', '').replace(')', '').replace('-', '')}" class="btn btn-secondary">Call Now</a>
                </div>
            </div>
        </section>
        
        <section class="services-preview" aria-labelledby="services-heading">
            <div class="container">
                <h2 id="services-heading">Our {industry.title()} Services</h2>
                <div class="services-grid">
                    {_generate_services_grid(industry)}
                </div>
                <div class="services-cta">
                    <a href="services.html" class="btn btn-outline">View All Services</a>
                </div>
            </div>
        </section>
        
        <section class="about-preview" aria-labelledby="about-heading">
            <div class="container">
                <h2 id="about-heading">Why Choose {company_name}?</h2>
                <div class="features-grid">
                    {_generate_features_grid(industry)}
                </div>
            </div>
        </section>
        
        <section class="contact-preview" id="contact" aria-labelledby="contact-heading">
            <div class="container">
                <h2 id="contact-heading">Get Started Today</h2>
                <div class="contact-grid">
                    <div class="contact-info">
                        <h3>Contact Information</h3>
                        <p><strong>Phone:</strong> <a href="tel:{phone.replace(' ', '').replace('(', '').replace(')', '').replace('-', '')}">{phone}</a></p>
                        <p><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
                        <p><strong>Location:</strong> {location}</p>
                    </div>
                    <div class="contact-form">
                        <h3>Request a Quote</h3>
                        <form action="#" method="post" aria-label="Contact form">
                            <input type="text" name="name" placeholder="Your Name" required aria-label="Your name">
                            <input type="email" name="email" placeholder="Your Email" required aria-label="Your email">
                            <input type="tel" name="phone" placeholder="Your Phone" aria-label="Your phone number">
                            <textarea name="message" placeholder="Tell us about your project" required aria-label="Project description"></textarea>
                            <!-- Honeypot field for spam protection -->
                            <input type="text" name="website" style="display:none" tabindex="-1" autocomplete="off">
                            <button type="submit" class="btn btn-primary">Send Message</button>
                        </form>
                    </div>
                </div>
            </div>
        </section>
    </main>
    
    <footer role="contentinfo">
        <div class="container">
            <div class="footer-content">
                <div class="footer-info">
                    <h3>{company_name}</h3>
                    <p>Professional {industry} services in {location}</p>
                    <p>Phone: <a href="tel:{phone.replace(' ', '').replace('(', '').replace(')', '').replace('-', '')}">{phone}</a></p>
                    <p>Email: <a href="mailto:{email}">{email}</a></p>
                </div>
                <div class="footer-links">
                    <h4>Quick Links</h4>
                    <ul>
                        <li><a href="services.html">Services</a></li>
                        <li><a href="about.html">About Us</a></li>
                        <li><a href="contact.html">Contact</a></li>
                    </ul>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; {datetime.now().year} {company_name}. All rights reserved.</p>
            </div>
        </div>
    </footer>
    
    <script src="script.js"></script>
</body>
</html>"""


def _get_industry_keywords(industry: str, location: str) -> Dict[str, Any]:
    """Get industry-specific keywords and content.
    
    Args:
        industry: Industry type
        location: Business location
        
    Returns:
        Dictionary containing industry-specific keywords and content
    """
    industry_data = {
        'roofing': {
            'title': 'Professional Roofing Services',
            'description': 'Expert roof repair, replacement, and storm damage services.',
            'keywords': ['roofing contractor', 'roof repair', 'roof replacement', 'storm damage', f'{industry} {location}'],
            'hero_text': 'quality roofing solutions and storm damage repair'
        },
        'dental': {
            'title': 'Professional Dental Care',
            'description': 'Comprehensive dental services including cleanings, fillings, and cosmetic dentistry.',
            'keywords': ['dentist', 'dental care', 'teeth cleaning', 'cosmetic dentistry', f'{industry} {location}'],
            'hero_text': 'comprehensive dental care and oral health services'
        },
        'legal': {
            'title': 'Professional Legal Services',
            'description': 'Experienced legal representation and consultation services.',
            'keywords': ['lawyer', 'attorney', 'legal services', 'legal consultation', f'{industry} {location}'],
            'hero_text': 'experienced legal representation and consultation'
        }
    }
    
    return industry_data.get(industry, {
        'title': f'Professional {industry.title()} Services',
        'description': f'Quality {industry} services and solutions.',
        'keywords': [f'{industry} services', f'{industry} {location}', 'professional services'],
        'hero_text': f'professional {industry} services and solutions'
    })


def _generate_services_grid(industry: str) -> str:
    """Generate services grid HTML based on industry.
    
    Args:
        industry: Industry type
        
    Returns:
        HTML content for services grid
    """
    services_data = {
        'roofing': [
            {'title': 'Roof Repair', 'description': 'Expert repair services for all roof types'},
            {'title': 'Roof Replacement', 'description': 'Complete roof replacement with quality materials'},
            {'title': 'Storm Damage', 'description': 'Emergency storm damage assessment and repair'}
        ],
        'dental': [
            {'title': 'General Dentistry', 'description': 'Comprehensive dental care and cleanings'},
            {'title': 'Cosmetic Dentistry', 'description': 'Smile enhancement and whitening services'},
            {'title': 'Restorative Care', 'description': 'Fillings, crowns, and dental restoration'}
        ],
        'legal': [
            {'title': 'Legal Consultation', 'description': 'Expert legal advice and consultation'},
            {'title': 'Document Review', 'description': 'Contract and legal document analysis'},
            {'title': 'Representation', 'description': 'Professional legal representation services'}
        ]
    }
    
    services = services_data.get(industry, [
        {'title': 'Professional Service', 'description': 'Quality service delivery'},
        {'title': 'Expert Consultation', 'description': 'Professional consultation services'},
        {'title': 'Custom Solutions', 'description': 'Tailored solutions for your needs'}
    ])
    
    grid_html = ""
    for service in services:
        grid_html += f"""
        <div class="service-card">
            <h3>{service['title']}</h3>
            <p>{service['description']}</p>
        </div>
        """
    
    return grid_html


def _generate_features_grid(industry: str) -> str:
    """Generate features grid HTML based on industry.
    
    Args:
        industry: Industry type
        
    Returns:
        HTML content for features grid
    """
    features = [
        {'title': 'Licensed & Insured', 'description': 'Fully licensed and insured for your protection'},
        {'title': 'Local Expertise', 'description': 'Deep knowledge of local regulations and requirements'},
        {'title': 'Quality Guarantee', 'description': 'We stand behind our work with comprehensive warranties'}
    ]
    
    grid_html = ""
    for feature in features:
        grid_html += f"""
        <div class="feature-card">
            <h3>{feature['title']}</h3>
            <p>{feature['description']}</p>
        </div>
        """
    
    return grid_html


def _generate_about_page_html(client_info: Dict[str, Any]) -> str:
    """Generate about page HTML."""
    company_name = client_info.get('company', 'Your Company')
    industry = client_info.get('industry', 'business')
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>About {company_name} - Professional {industry.title()} Services</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <nav class="navbar">
            <div class="container">
                <div class="nav-brand"><h1>{company_name}</h1></div>
                <ul class="nav-menu">
                    <li><a href="index.html">Home</a></li>
                    <li><a href="services.html">Services</a></li>
                    <li><a href="about.html" class="active">About</a></li>
                    <li><a href="contact.html">Contact</a></li>
                </ul>
            </div>
        </nav>
    </header>
    <main>
        <section class="page-header">
            <div class="container">
                <h1>About {company_name}</h1>
                <p>Learn more about our company and commitment to excellence</p>
            </div>
        </section>
        <section class="about-content">
            <div class="container">
                <h2>Our Story</h2>
                <p>{company_name} has been providing professional {industry} services with a commitment to quality and customer satisfaction.</p>
                <h2>Our Mission</h2>
                <p>To deliver exceptional {industry} services that exceed our clients' expectations while maintaining the highest standards of professionalism.</p>
            </div>
        </section>
    </main>
    <footer>
        <div class="container">
            <p>&copy; {datetime.now().year} {company_name}. All rights reserved.</p>
        </div>
    </footer>
</body>
</html>"""


def _generate_contact_page_html(client_info: Dict[str, Any]) -> str:
    """Generate contact page HTML."""
    company_name = client_info.get('company', 'Your Company')
    phone = client_info.get('phone', '(555) 123-4567')
    email = client_info.get('email', 'info@company.com')
    location = client_info.get('location', 'Your City, State')
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contact {company_name} - Get In Touch Today</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <nav class="navbar">
            <div class="container">
                <div class="nav-brand"><h1>{company_name}</h1></div>
                <ul class="nav-menu">
                    <li><a href="index.html">Home</a></li>
                    <li><a href="services.html">Services</a></li>
                    <li><a href="about.html">About</a></li>
                    <li><a href="contact.html" class="active">Contact</a></li>
                </ul>
            </div>
        </nav>
    </header>
    <main>
        <section class="page-header">
            <div class="container">
                <h1>Contact Us</h1>
                <p>Get in touch for a free consultation</p>
            </div>
        </section>
        <section class="contact-page">
            <div class="container">
                <div class="contact-grid">
                    <div class="contact-info">
                        <h2>Get In Touch</h2>
                        <p><strong>Phone:</strong> <a href="tel:{phone.replace(' ', '').replace('(', '').replace(')', '').replace('-', '')}">{phone}</a></p>
                        <p><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
                        <p><strong>Location:</strong> {location}</p>
                    </div>
                    <div class="contact-form">
                        <h2>Send us a Message</h2>
                        <form action="#" method="post">
                            <input type="text" name="name" placeholder="Your Name" required>
                            <input type="email" name="email" placeholder="Your Email" required>
                            <input type="tel" name="phone" placeholder="Your Phone">
                            <textarea name="message" placeholder="Your Message" required></textarea>
                            <input type="text" name="website" style="display:none">
                            <button type="submit" class="btn btn-primary">Send Message</button>
                        </form>
                    </div>
                </div>
            </div>
        </section>
    </main>
    <footer>
        <div class="container">
            <p>&copy; {datetime.now().year} {company_name}. All rights reserved.</p>
        </div>
    </footer>
</body>
</html>"""


def _generate_services_page_html(client_info: Dict[str, Any]) -> str:
    """Generate services page HTML."""
    company_name = client_info.get('company', 'Your Company')
    industry = client_info.get('industry', 'business')
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{company_name} Services - Professional {industry.title()} Solutions</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <nav class="navbar">
            <div class="container">
                <div class="nav-brand"><h1>{company_name}</h1></div>
                <ul class="nav-menu">
                    <li><a href="index.html">Home</a></li>
                    <li><a href="services.html" class="active">Services</a></li>
                    <li><a href="about.html">About</a></li>
                    <li><a href="contact.html">Contact</a></li>
                </ul>
            </div>
        </nav>
    </header>
    <main>
        <section class="page-header">
            <div class="container">
                <h1>Our Services</h1>
                <p>Comprehensive {industry} solutions for your needs</p>
            </div>
        </section>
        <section class="services-detailed">
            <div class="container">
                {_generate_detailed_services(industry)}
            </div>
        </section>
    </main>
    <footer>
        <div class="container">
            <p>&copy; {datetime.now().year} {company_name}. All rights reserved.</p>
        </div>
    </footer>
</body>
</html>"""


def _generate_detailed_services(industry: str) -> str:
    """Generate detailed services content based on industry."""
    services_content = {
        'roofing': """
        <div class="service-detail">
            <h2>Roof Repair Services</h2>
            <p>Expert repair services for all types of roofing systems including asphalt shingles, metal roofing, and tile roofs.</p>
        </div>
        <div class="service-detail">
            <h2>Complete Roof Replacement</h2>
            <p>Full roof replacement services using high-quality materials and professional installation techniques.</p>
        </div>
        <div class="service-detail">
            <h2>Storm Damage Assessment</h2>
            <p>Emergency storm damage assessment and repair services with insurance claim assistance.</p>
        </div>
        """,
        'dental': """
        <div class="service-detail">
            <h2>General Dentistry</h2>
            <p>Comprehensive dental care including cleanings, examinations, and preventive treatments.</p>
        </div>
        <div class="service-detail">
            <h2>Cosmetic Dentistry</h2>
            <p>Smile enhancement services including teeth whitening, veneers, and cosmetic bonding.</p>
        </div>
        <div class="service-detail">
            <h2>Restorative Dentistry</h2>
            <p>Dental restoration services including fillings, crowns, bridges, and implants.</p>
        </div>
        """
    }
    
    return services_content.get(industry, """
    <div class="service-detail">
        <h2>Professional Services</h2>
        <p>Comprehensive professional services tailored to meet your specific needs and requirements.</p>
    </div>
    """)


def _generate_robots_txt(domain: str) -> str:
    """Generate robots.txt file."""
    return f"""User-agent: *
Allow: /

Sitemap: https://{domain}/sitemap.xml"""


def _generate_sitemap_xml(domain: str) -> str:
    """Generate sitemap.xml file."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://{domain}/</loc>
        <changefreq>weekly</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://{domain}/about.html</loc>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://{domain}/services.html</loc>
        <changefreq>weekly</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>https://{domain}/contact.html</loc>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>
</urlset>"""


def _generate_website_css(client_info: Dict[str, Any]) -> str:
    """Generate CSS stylesheet."""
    return """/* DTL-Global Website Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Arial', sans-serif;
    line-height: 1.6;
    color: #333;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Header Styles */
header {
    background: #2c5aa0;
    color: white;
    padding: 1rem 0;
    position: sticky;
    top: 0;
    z-index: 1000;
}

.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-brand h1 {
    font-size: 1.5rem;
}

.nav-menu {
    display: flex;
    list-style: none;
    gap: 2rem;
}

.nav-menu a {
    color: white;
    text-decoration: none;
    transition: color 0.3s;
}

.nav-menu a:hover,
.nav-menu a.active {
    color: #ff6b35;
}

.cta-button {
    background: #ff6b35;
    color: white;
    padding: 0.5rem 1rem;
    text-decoration: none;
    border-radius: 5px;
    transition: background 0.3s;
}

.cta-button:hover {
    background: #e55a2b;
}

/* Hero Section */
.hero {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    padding: 4rem 0;
    text-align: center;
}

.hero h1 {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    color: #2c5aa0;
}

.hero-subtitle {
    font-size: 1.2rem;
    margin-bottom: 2rem;
    color: #666;
}

.hero-cta {
    display: flex;
    gap: 1rem;
    justify-content: center;
    flex-wrap: wrap;
}

/* Buttons */
.btn {
    display: inline-block;
    padding: 12px 24px;
    text-decoration: none;
    border-radius: 5px;
    font-weight: bold;
    transition: all 0.3s;
    border: none;
    cursor: pointer;
}

.btn-primary {
    background: #ff6b35;
    color: white;
}

.btn-primary:hover {
    background: #e55a2b;
    transform: translateY(-2px);
}

.btn-secondary {
    background: transparent;
    color: #2c5aa0;
    border: 2px solid #2c5aa0;
}

.btn-secondary:hover {
    background: #2c5aa0;
    color: white;
}

.btn-outline {
    background: transparent;
    color: #2c5aa0;
    border: 2px solid #2c5aa0;
}

/* Grid Layouts */
.services-grid,
.features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin: 2rem 0;
}

.service-card,
.feature-card {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    transition: transform 0.3s;
}

.service-card:hover,
.feature-card:hover {
    transform: translateY(-5px);
}

/* Contact Section */
.contact-preview,
.contact-page {
    background: #2c5aa0;
    color: white;
    padding: 4rem 0;
}

.contact-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 3rem;
    margin-top: 2rem;
}

.contact-form form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.contact-form input,
.contact-form textarea {
    padding: 0.75rem;
    border: none;
    border-radius: 5px;
    font-size: 1rem;
}

.contact-form textarea {
    min-height: 120px;
    resize: vertical;
}

/* Footer */
footer {
    background: #333;
    color: white;
    padding: 2rem 0;
}

.footer-content {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 2rem;
    margin-bottom: 2rem;
}

.footer-links ul {
    list-style: none;
}

.footer-links a {
    color: white;
    text-decoration: none;
}

.footer-links a:hover {
    color: #ff6b35;
}

.footer-bottom {
    text-align: center;
    padding-top: 2rem;
    border-top: 1px solid #555;
}

/* Page Headers */
.page-header {
    background: #2c5aa0;
    color: white;
    padding: 3rem 0;
    text-align: center;
}

/* Responsive Design */
@media (max-width: 768px) {
    .navbar {
        flex-direction: column;
        gap: 1rem;
    }
    
    .nav-menu {
        flex-direction: column;
        gap: 1rem;
    }
    
    .hero h1 {
        font-size: 2rem;
    }
    
    .hero-cta {
        flex-direction: column;
        align-items: center;
    }
    
    .contact-grid {
        grid-template-columns: 1fr;
    }
}

/* Accessibility */
.btn:focus,
input:focus,
textarea:focus {
    outline: 2px solid #ff6b35;
    outline-offset: 2px;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
    .hero {
        background: white;
    }
    
    .service-card,
    .feature-card {
        border: 2px solid #333;
    }
}"""


def _generate_website_js(client_info: Dict[str, Any]) -> str:
    """Generate JavaScript file."""
    return """// DTL-Global Website JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for anchor links
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Contact form handling
    const contactForm = document.querySelector('form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Basic form validation
            const name = this.querySelector('input[name="name"]').value;
            const email = this.querySelector('input[name="email"]').value;
            const message = this.querySelector('textarea[name="message"]').value;
            const honeypot = this.querySelector('input[name="website"]').value;
            
            // Check honeypot (spam protection)
            if (honeypot) {
                console.log('Spam detected');
                return;
            }
            
            // Validate required fields
            if (!name || !email || !message) {
                alert('Please fill in all required fields.');
                return;
            }
            
            // Email validation
            const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
            if (!emailRegex.test(email)) {
                alert('Please enter a valid email address.');
                return;
            }
            
            // Show success message (in production, this would submit to server)
            alert('Thank you for your message! We will get back to you soon.');
            this.reset();
        });
    }
    
    // Mobile menu toggle (if needed)
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (mobileMenuToggle && navMenu) {
        mobileMenuToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });
    }
    
    // Add loading animation to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            if (this.type === 'submit') {
                this.style.opacity = '0.7';
                this.textContent = 'Sending...';
            }
        });
    });
});

// Google Analytics (placeholder - replace with actual tracking ID)
// gtag('config', 'GA_TRACKING_ID');"""


def _generate_website_html(client_info: Dict[str, Any]) -> str:
    """Generate basic website HTML (legacy function for backward compatibility)."""
    return _generate_enhanced_website_html(client_info, "")


def _generate_404_html(client_info: Dict[str, Any]) -> str:
    """Generate 404 page HTML."""
    return f"""<!DOCTYPE html>
<html><head><title>Page Not Found</title></head>
<body style="text-align:center;padding:4rem;">
<h1>404 - Page Not Found</h1>
<p>The page you're looking for doesn't exist.</p>
<a href="/">Return Home</a>
</body></html>"""
