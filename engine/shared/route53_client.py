"""Route 53 DNS client for DTL-Global onboarding platform.

This module provides DNS management functionality for the DTL-Global platform including:
- Hosted zone creation and management
- DNS record creation (A, AAAA, CNAME, MX, TXT)
- SSL certificate validation records
- Domain verification for email and websites
- Health checks and routing policies

Supports both new domain registration and existing domain management.

Author: DTL-Global Platform
"""

import boto3
import json
from typing import Dict, List, Optional, Any, Union
from botocore.exceptions import ClientError
import time

from config import config


class Route53Client:
    """Route 53 DNS client for DTL-Global platform operations.
    
    Handles DNS management for client domains including hosted zone
    creation, record management, and SSL certificate validation.
    """
    
    def __init__(self):
        """Initialize Route 53 client with AWS configuration.
        
        Sets up Route 53 client and related AWS services for DNS management.
        """
        # Initialize Route 53 client
        self._route53_client = boto3.client('route53')
        
        # Initialize ACM client for certificate validation
        self._acm_client = boto3.client('acm', region_name='us-east-1')  # ACM for CloudFront
        
        # Cache for hosted zone data
        self._hosted_zones_cache = {}  # Cache zone information
    
    def create_hosted_zone(self, domain_name: str, 
                          caller_reference: Optional[str] = None) -> Dict[str, Any]:
        """Create a new hosted zone for a domain.
        
        Args:
            domain_name: Domain name for the hosted zone
            caller_reference: Optional unique reference for the request
            
        Returns:
            Dictionary containing hosted zone information
            
        Raises:
            ClientError: If Route 53 API call fails
        """
        # Generate caller reference if not provided
        if not caller_reference:
            caller_reference = f"dtl-{domain_name}-{int(time.time())}"
        
        try:
            # Create hosted zone
            response = self._route53_client.create_hosted_zone(
                Name=domain_name,
                CallerReference=caller_reference,
                HostedZoneConfig={
                    'Comment': f'DTL-Global managed zone for {domain_name}',
                    'PrivateZone': False  # Public hosted zone
                }
            )
            
            # Extract hosted zone information
            hosted_zone = response['HostedZone']
            name_servers = response['DelegationSet']['NameServers']
            
            # Cache the hosted zone data
            zone_data = {
                'id': hosted_zone['Id'].split('/')[-1],  # Remove /hostedzone/ prefix
                'name': hosted_zone['Name'],
                'caller_reference': hosted_zone['CallerReference'],
                'resource_record_set_count': hosted_zone['ResourceRecordSetCount'],
                'name_servers': name_servers
            }
            
            self._hosted_zones_cache[domain_name] = zone_data
            
            return zone_data
            
        except ClientError as e:
            # Handle Route 53 API errors
            error_code = e.response['Error']['Code']
            if error_code == 'HostedZoneAlreadyExists':
                # Zone already exists, get existing zone info
                return self.get_hosted_zone_by_name(domain_name)
            else:
                error_msg = f"Failed to create hosted zone for {domain_name}: {e}"
                raise Exception(error_msg) from e
    
    def get_hosted_zone_by_name(self, domain_name: str) -> Optional[Dict[str, Any]]:
        """Get hosted zone information by domain name.
        
        Args:
            domain_name: Domain name to search for
            
        Returns:
            Hosted zone data dictionary if found, None if not found
            
        Raises:
            ClientError: If Route 53 API call fails
        """
        # Check cache first
        if domain_name in self._hosted_zones_cache:
            return self._hosted_zones_cache[domain_name]
        
        try:
            # List all hosted zones
            response = self._route53_client.list_hosted_zones()
            
            # Search for matching domain
            for zone in response['HostedZones']:
                zone_name = zone['Name'].rstrip('.')  # Remove trailing dot
                if zone_name == domain_name:
                    # Get name servers for this zone
                    zone_id = zone['Id'].split('/')[-1]
                    ns_response = self._route53_client.get_hosted_zone(Id=zone_id)
                    
                    # Build zone data
                    zone_data = {
                        'id': zone_id,
                        'name': zone_name,
                        'caller_reference': zone['CallerReference'],
                        'resource_record_set_count': zone['ResourceRecordSetCount'],
                        'name_servers': ns_response['DelegationSet']['NameServers']
                    }
                    
                    # Cache the zone data
                    self._hosted_zones_cache[domain_name] = zone_data
                    
                    return zone_data
            
            return None  # Hosted zone not found
            
        except ClientError as e:
            # Handle Route 53 API errors
            error_msg = f"Failed to get hosted zone for {domain_name}: {e}"
            raise Exception(error_msg) from e
    
    def create_record(self, zone_id: str, record_name: str, record_type: str,
                     record_values: Union[str, List[str]], ttl: int = 300,
                     alias_target: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create or update a DNS record in a hosted zone.
        
        Args:
            zone_id: Hosted zone ID
            record_name: DNS record name
            record_type: Record type (A, AAAA, CNAME, MX, TXT, etc.)
            record_values: Record value(s) as string or list
            ttl: Time to live in seconds (ignored for alias records)
            alias_target: Optional alias target configuration
            
        Returns:
            Dictionary containing change information
            
        Raises:
            ClientError: If Route 53 API call fails
        """
        # Normalize record values to list
        if isinstance(record_values, str):
            record_values = [record_values]
        
        # Build resource record set
        resource_record_set = {
            'Name': record_name,
            'Type': record_type
        }
        
        if alias_target:
            # Alias record (for CloudFront, ELB, etc.)
            resource_record_set['AliasTarget'] = alias_target
        else:
            # Standard record with values and TTL
            resource_record_set['TTL'] = ttl
            resource_record_set['ResourceRecords'] = [
                {'Value': value} for value in record_values
            ]
        
        try:
            # Create change batch
            change_batch = {
                'Comment': f'DTL-Global: Create {record_type} record for {record_name}',
                'Changes': [{
                    'Action': 'UPSERT',  # Create or update
                    'ResourceRecordSet': resource_record_set
                }]
            }
            
            # Submit change request
            response = self._route53_client.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch=change_batch
            )
            
            # Return change information
            return {
                'change_id': response['ChangeInfo']['Id'],
                'status': response['ChangeInfo']['Status'],
                'submitted_at': response['ChangeInfo']['SubmittedAt'],
                'record_name': record_name,
                'record_type': record_type
            }
            
        except ClientError as e:
            # Handle Route 53 API errors
            error_msg = f"Failed to create {record_type} record {record_name}: {e}"
            raise Exception(error_msg) from e
    
    def create_cloudfront_alias(self, zone_id: str, domain_name: str,
                              cloudfront_domain: str, 
                              cloudfront_zone_id: str = 'Z2FDTNDATAQYW2') -> Dict[str, Any]:
        """Create an alias record pointing to a CloudFront distribution.
        
        Args:
            zone_id: Hosted zone ID
            domain_name: Domain name for the alias
            cloudfront_domain: CloudFront distribution domain
            cloudfront_zone_id: CloudFront hosted zone ID (default for global)
            
        Returns:
            Dictionary containing change information
        """
        # Create alias target for CloudFront
        alias_target = {
            'DNSName': cloudfront_domain,
            'EvaluateTargetHealth': False,
            'HostedZoneId': cloudfront_zone_id  # CloudFront global zone ID
        }
        
        # Create A record alias
        return self.create_record(
            zone_id=zone_id,
            record_name=domain_name,
            record_type='A',
            record_values=[],  # Empty for alias records
            alias_target=alias_target
        )
    
    def create_acm_validation_records(self, zone_id: str, domain_name: str,
                                    subject_alternative_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Request SSL certificate and create DNS validation records.
        
        Args:
            zone_id: Hosted zone ID for validation records
            domain_name: Primary domain for the certificate
            subject_alternative_names: Optional additional domains
            
        Returns:
            Dictionary containing certificate ARN and validation info
            
        Raises:
            ClientError: If ACM or Route 53 API calls fail
        """
        # Build domain list
        domains = [domain_name]
        if subject_alternative_names:
            domains.extend(subject_alternative_names)
        
        try:
            # Request SSL certificate
            cert_response = self._acm_client.request_certificate(
                DomainName=domain_name,
                SubjectAlternativeNames=subject_alternative_names or [],
                ValidationMethod='DNS',
                Options={
                    'CertificateTransparencyLoggingPreference': 'ENABLED'
                }
            )
            
            certificate_arn = cert_response['CertificateArn']
            
            # Wait for certificate details to be available
            time.sleep(5)  # Give ACM time to generate validation records
            
            # Get certificate details for validation records
            cert_details = self._acm_client.describe_certificate(
                CertificateArn=certificate_arn
            )
            
            # Create DNS validation records
            validation_records = []
            for domain_validation in cert_details['Certificate']['DomainValidationOptions']:
                if 'ResourceRecord' in domain_validation:
                    record_info = domain_validation['ResourceRecord']
                    
                    # Create validation record
                    change_response = self.create_record(
                        zone_id=zone_id,
                        record_name=record_info['Name'],
                        record_type=record_info['Type'],
                        record_values=[record_info['Value']],
                        ttl=300
                    )
                    
                    validation_records.append({
                        'domain': domain_validation['DomainName'],
                        'record_name': record_info['Name'],
                        'record_type': record_info['Type'],
                        'record_value': record_info['Value'],
                        'change_id': change_response['change_id']
                    })
            
            return {
                'certificate_arn': certificate_arn,
                'validation_records': validation_records,
                'status': 'PENDING_VALIDATION'
            }
            
        except ClientError as e:
            # Handle ACM/Route 53 API errors
            error_msg = f"Failed to create SSL certificate for {domain_name}: {e}"
            raise Exception(error_msg) from e
    
    def create_mx_records(self, zone_id: str, domain_name: str,
                         mail_servers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create MX records for email routing.
        
        Args:
            zone_id: Hosted zone ID
            domain_name: Domain name for MX records
            mail_servers: List of mail server configurations
                Each item should have 'priority' and 'server' keys
                
        Returns:
            Dictionary containing change information
        """
        # Build MX record values
        mx_values = []
        for server in mail_servers:
            priority = server.get('priority', 10)
            server_name = server.get('server', '')
            mx_values.append(f"{priority} {server_name}")
        
        # Create MX records
        return self.create_record(
            zone_id=zone_id,
            record_name=domain_name,
            record_type='MX',
            record_values=mx_values,
            ttl=3600  # Longer TTL for MX records
        )
    
    def create_txt_record(self, zone_id: str, record_name: str,
                         txt_value: str, ttl: int = 300) -> Dict[str, Any]:
        """Create a TXT record (for domain verification, SPF, etc.).
        
        Args:
            zone_id: Hosted zone ID
            record_name: DNS record name
            txt_value: TXT record value
            ttl: Time to live in seconds
            
        Returns:
            Dictionary containing change information
        """
        # Ensure TXT value is properly quoted
        if not txt_value.startswith('"'):
            txt_value = f'"{txt_value}"'
        
        # Create TXT record
        return self.create_record(
            zone_id=zone_id,
            record_name=record_name,
            record_type='TXT',
            record_values=[txt_value],
            ttl=ttl
        )
    
    def get_change_status(self, change_id: str) -> Dict[str, Any]:
        """Get the status of a DNS change request.
        
        Args:
            change_id: Change request ID from Route 53
            
        Returns:
            Dictionary containing change status information
            
        Raises:
            ClientError: If Route 53 API call fails
        """
        try:
            # Get change status
            response = self._route53_client.get_change(Id=change_id)
            
            # Return change status
            return {
                'change_id': response['ChangeInfo']['Id'],
                'status': response['ChangeInfo']['Status'],
                'submitted_at': response['ChangeInfo']['SubmittedAt']
            }
            
        except ClientError as e:
            # Handle Route 53 API errors
            error_msg = f"Failed to get change status for {change_id}: {e}"
            raise Exception(error_msg) from e
    
    def wait_for_change(self, change_id: str, max_wait_seconds: int = 300) -> bool:
        """Wait for a DNS change to propagate.
        
        Args:
            change_id: Change request ID to wait for
            max_wait_seconds: Maximum time to wait in seconds
            
        Returns:
            True if change completed, False if timeout
        """
        start_time = time.time()
        
        while (time.time() - start_time) < max_wait_seconds:
            try:
                # Check change status
                status_info = self.get_change_status(change_id)
                
                if status_info['status'] == 'INSYNC':
                    return True  # Change completed successfully
                
                # Wait before checking again
                time.sleep(10)
                
            except ClientError:
                # Continue waiting on API errors
                time.sleep(10)
        
        return False  # Timeout reached
    
    def list_records(self, zone_id: str, record_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List DNS records in a hosted zone.
        
        Args:
            zone_id: Hosted zone ID
            record_type: Optional record type filter
            
        Returns:
            List of DNS record dictionaries
            
        Raises:
            ClientError: If Route 53 API call fails
        """
        try:
            # List resource record sets
            response = self._route53_client.list_resource_record_sets(
                HostedZoneId=zone_id
            )
            
            # Filter and format records
            records = []
            for record_set in response['ResourceRecordSets']:
                # Apply type filter if specified
                if record_type and record_set['Type'] != record_type:
                    continue
                
                # Build record data
                record_data = {
                    'name': record_set['Name'],
                    'type': record_set['Type'],
                    'ttl': record_set.get('TTL'),
                    'values': []
                }
                
                # Add record values or alias target
                if 'ResourceRecords' in record_set:
                    record_data['values'] = [
                        record['Value'] for record in record_set['ResourceRecords']
                    ]
                elif 'AliasTarget' in record_set:
                    record_data['alias_target'] = record_set['AliasTarget']
                
                records.append(record_data)
            
            return records
            
        except ClientError as e:
            # Handle Route 53 API errors
            error_msg = f"Failed to list records for zone {zone_id}: {e}"
            raise Exception(error_msg) from e


# Global Route 53 client instance
route53_client = Route53Client()