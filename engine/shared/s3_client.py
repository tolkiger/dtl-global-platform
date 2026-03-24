"""AWS S3 client for DTL-Global onboarding platform.

This module provides S3 storage functionality for the DTL-Global platform including:
- Website file deployment and management
- Asset storage and retrieval
- CSV import file handling
- Static website hosting configuration
- File upload and download operations
- Bucket policy and CORS management

Manages three S3 buckets: websites, assets, and CSV imports.

Author: DTL-Global Platform
"""

import boto3
import json
import mimetypes
from typing import Dict, List, Optional, Any, Union, BinaryIO
from botocore.exceptions import ClientError
from pathlib import Path
import os

from config import config


class S3Client:
    """AWS S3 client for DTL-Global platform operations.
    
    Handles file storage and website deployment across multiple S3 buckets.
    Supports static website hosting, asset management, and CSV imports.
    """
    
    def __init__(self):
        """Initialize S3 client with AWS configuration.
        
        Sets up S3 client and loads bucket names from configuration.
        """
        # Initialize S3 client
        self._s3_client = boto3.client('s3')
        self._s3_resource = boto3.resource('s3')
        
        # Get bucket names from configuration
        self._websites_bucket = config.get_s3_bucket_name('websites')
        self._assets_bucket = config.get_s3_bucket_name('assets')
        self._csv_imports_bucket = config.get_s3_bucket_name('csv_imports')
        
        # Cache for bucket policies and configurations
        self._bucket_configs_cache = {}  # Cache bucket configurations
    
    def upload_file(self, file_path: str, bucket_type: str, s3_key: str,
                   content_type: Optional[str] = None, 
                   metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Upload a file to S3.
        
        Args:
            file_path: Local file path to upload
            bucket_type: Bucket type (websites, assets, csv_imports)
            s3_key: S3 object key (path within bucket)
            content_type: Optional MIME content type
            metadata: Optional metadata dictionary
            
        Returns:
            Dictionary containing upload information
            
        Raises:
            ClientError: If S3 API call fails
            ValueError: If bucket type is invalid
        """
        # Get bucket name for the specified type
        bucket_name = self._get_bucket_name(bucket_type)
        
        # Auto-detect content type if not provided
        if not content_type:
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = 'application/octet-stream'
        
        try:
            # Prepare extra arguments for upload
            extra_args = {
                'ContentType': content_type
            }
            
            # Add metadata if provided
            if metadata:
                extra_args['Metadata'] = metadata
            
            # Add cache control for website assets
            if bucket_type == 'websites':
                if s3_key.endswith(('.html', '.htm')):
                    extra_args['CacheControl'] = 'max-age=300'  # 5 minutes for HTML
                elif s3_key.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg')):
                    extra_args['CacheControl'] = 'max-age=31536000'  # 1 year for assets
            
            # Upload file to S3
            self._s3_client.upload_file(
                Filename=file_path,
                Bucket=bucket_name,
                Key=s3_key,
                ExtraArgs=extra_args
            )
            
            # Return upload information
            return {
                'bucket': bucket_name,
                'key': s3_key,
                'content_type': content_type,
                'url': f'https://{bucket_name}.s3.amazonaws.com/{s3_key}',
                'uploaded': True
            }
            
        except ClientError as e:
            # Handle S3 API errors
            error_msg = f"Failed to upload {file_path} to s3://{bucket_name}/{s3_key}: {e}"
            raise ClientError(error_msg) from e
    
    def upload_string(self, content: str, bucket_type: str, s3_key: str,
                     content_type: str = 'text/plain',
                     metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Upload string content to S3.
        
        Args:
            content: String content to upload
            bucket_type: Bucket type (websites, assets, csv_imports)
            s3_key: S3 object key (path within bucket)
            content_type: MIME content type
            metadata: Optional metadata dictionary
            
        Returns:
            Dictionary containing upload information
            
        Raises:
            ClientError: If S3 API call fails
        """
        # Get bucket name for the specified type
        bucket_name = self._get_bucket_name(bucket_type)
        
        try:
            # Prepare extra arguments for upload
            extra_args = {
                'ContentType': content_type
            }
            
            # Add metadata if provided
            if metadata:
                extra_args['Metadata'] = metadata
            
            # Add cache control for website files
            if bucket_type == 'websites':
                if content_type in ['text/html', 'application/xhtml+xml']:
                    extra_args['CacheControl'] = 'max-age=300'  # 5 minutes for HTML
                elif content_type in ['text/css', 'application/javascript']:
                    extra_args['CacheControl'] = 'max-age=31536000'  # 1 year for CSS/JS
            
            # Upload string content to S3
            self._s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=content.encode('utf-8'),
                **extra_args
            )
            
            # Return upload information
            return {
                'bucket': bucket_name,
                'key': s3_key,
                'content_type': content_type,
                'url': f'https://{bucket_name}.s3.amazonaws.com/{s3_key}',
                'uploaded': True
            }
            
        except ClientError as e:
            # Handle S3 API errors
            error_msg = f"Failed to upload content to s3://{bucket_name}/{s3_key}: {e}"
            raise ClientError(error_msg) from e
    
    def download_file(self, bucket_type: str, s3_key: str, 
                     local_path: str) -> Dict[str, Any]:
        """Download a file from S3.
        
        Args:
            bucket_type: Bucket type (websites, assets, csv_imports)
            s3_key: S3 object key to download
            local_path: Local file path to save to
            
        Returns:
            Dictionary containing download information
            
        Raises:
            ClientError: If S3 API call fails
        """
        # Get bucket name for the specified type
        bucket_name = self._get_bucket_name(bucket_type)
        
        try:
            # Download file from S3
            self._s3_client.download_file(
                Bucket=bucket_name,
                Key=s3_key,
                Filename=local_path
            )
            
            # Return download information
            return {
                'bucket': bucket_name,
                'key': s3_key,
                'local_path': local_path,
                'downloaded': True
            }
            
        except ClientError as e:
            # Handle S3 API errors
            error_msg = f"Failed to download s3://{bucket_name}/{s3_key}: {e}"
            raise ClientError(error_msg) from e
    
    def get_object_content(self, bucket_type: str, s3_key: str) -> str:
        """Get object content as string from S3.
        
        Args:
            bucket_type: Bucket type (websites, assets, csv_imports)
            s3_key: S3 object key to retrieve
            
        Returns:
            Object content as string
            
        Raises:
            ClientError: If S3 API call fails
        """
        # Get bucket name for the specified type
        bucket_name = self._get_bucket_name(bucket_type)
        
        try:
            # Get object from S3
            response = self._s3_client.get_object(
                Bucket=bucket_name,
                Key=s3_key
            )
            
            # Return content as string
            return response['Body'].read().decode('utf-8')
            
        except ClientError as e:
            # Handle S3 API errors
            error_msg = f"Failed to get content from s3://{bucket_name}/{s3_key}: {e}"
            raise ClientError(error_msg) from e
    
    def list_objects(self, bucket_type: str, prefix: str = '',
                    max_keys: int = 1000) -> List[Dict[str, Any]]:
        """List objects in an S3 bucket.
        
        Args:
            bucket_type: Bucket type (websites, assets, csv_imports)
            prefix: Optional prefix to filter objects
            max_keys: Maximum number of objects to return
            
        Returns:
            List of object information dictionaries
            
        Raises:
            ClientError: If S3 API call fails
        """
        # Get bucket name for the specified type
        bucket_name = self._get_bucket_name(bucket_type)
        
        try:
            # List objects in S3 bucket
            response = self._s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            # Return list of objects
            objects = []
            for obj in response.get('Contents', []):
                objects.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag'].strip('"'),
                    'storage_class': obj.get('StorageClass', 'STANDARD')
                })
            
            return objects
            
        except ClientError as e:
            # Handle S3 API errors
            error_msg = f"Failed to list objects in s3://{bucket_name}: {e}"
            raise ClientError(error_msg) from e
    
    def delete_object(self, bucket_type: str, s3_key: str) -> Dict[str, Any]:
        """Delete an object from S3.
        
        Args:
            bucket_type: Bucket type (websites, assets, csv_imports)
            s3_key: S3 object key to delete
            
        Returns:
            Dictionary containing deletion information
            
        Raises:
            ClientError: If S3 API call fails
        """
        # Get bucket name for the specified type
        bucket_name = self._get_bucket_name(bucket_type)
        
        try:
            # Delete object from S3
            self._s3_client.delete_object(
                Bucket=bucket_name,
                Key=s3_key
            )
            
            # Return deletion information
            return {
                'bucket': bucket_name,
                'key': s3_key,
                'deleted': True
            }
            
        except ClientError as e:
            # Handle S3 API errors
            error_msg = f"Failed to delete s3://{bucket_name}/{s3_key}: {e}"
            raise ClientError(error_msg) from e
    
    def deploy_website(self, client_domain: str, website_files: Dict[str, str],
                      enable_spa: bool = False) -> Dict[str, Any]:
        """Deploy a complete website to S3.
        
        Args:
            client_domain: Client domain name (used as prefix)
            website_files: Dictionary mapping file paths to content
            enable_spa: Whether to enable single-page application routing
            
        Returns:
            Dictionary containing deployment information
            
        Raises:
            ClientError: If S3 operations fail
        """
        # Create domain-specific prefix
        domain_prefix = client_domain.replace('.', '-')
        
        # Deploy all website files
        deployed_files = []
        
        for file_path, content in website_files.items():
            # Determine content type based on file extension
            content_type = self._get_content_type(file_path)
            
            # Create S3 key with domain prefix
            s3_key = f"{domain_prefix}/{file_path}"
            
            # Upload file content
            upload_result = self.upload_string(
                content=content,
                bucket_type='websites',
                s3_key=s3_key,
                content_type=content_type
            )
            
            deployed_files.append(upload_result)
        
        # Configure website hosting if this is the main site
        if 'index.html' in website_files:
            self._configure_website_hosting(domain_prefix, enable_spa)
        
        # Return deployment information
        return {
            'bucket': self._websites_bucket,  # Return the actual websites bucket used for hosting
            'client_domain': client_domain,
            'domain_prefix': domain_prefix,
            'deployed_files': deployed_files,
            'website_url': f'https://{self._websites_bucket}.s3-website-us-east-1.amazonaws.com/{domain_prefix}/',
            'spa_enabled': enable_spa
        }
    
    def upload_csv_import(self, client_id: str, csv_content: str,
                         import_type: str = 'contacts') -> Dict[str, Any]:
        """Upload CSV file for CRM import.
        
        Args:
            client_id: Client identifier
            csv_content: CSV file content as string
            import_type: Type of import (contacts, companies, deals)
            
        Returns:
            Dictionary containing upload information
        """
        # Create timestamped filename
        import time
        timestamp = int(time.time())
        filename = f"{client_id}/{import_type}_{timestamp}.csv"
        
        # Upload CSV content
        upload_result = self.upload_string(
            content=csv_content,
            bucket_type='csv_imports',
            s3_key=filename,
            content_type='text/csv',
            metadata={
                'client_id': client_id,
                'import_type': import_type,
                'uploaded_at': str(timestamp)
            }
        )
        
        return upload_result
    
    def get_presigned_url(self, bucket_type: str, s3_key: str,
                         expiration: int = 3600, 
                         http_method: str = 'GET') -> str:
        """Generate a presigned URL for S3 object access.
        
        Args:
            bucket_type: Bucket type (websites, assets, csv_imports)
            s3_key: S3 object key
            expiration: URL expiration time in seconds
            http_method: HTTP method (GET, PUT, POST)
            
        Returns:
            Presigned URL string
            
        Raises:
            ClientError: If S3 API call fails
        """
        # Get bucket name for the specified type
        bucket_name = self._get_bucket_name(bucket_type)
        
        try:
            # Generate presigned URL
            if http_method == 'GET':
                url = self._s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': s3_key},
                    ExpiresIn=expiration
                )
            elif http_method == 'PUT':
                url = self._s3_client.generate_presigned_url(
                    'put_object',
                    Params={'Bucket': bucket_name, 'Key': s3_key},
                    ExpiresIn=expiration
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {http_method}")
            
            return url
            
        except ClientError as e:
            # Handle S3 API errors
            error_msg = f"Failed to generate presigned URL for s3://{bucket_name}/{s3_key}: {e}"
            raise ClientError(error_msg) from e
    
    def _get_bucket_name(self, bucket_type: str) -> str:
        """Get bucket name for the specified type.
        
        Args:
            bucket_type: Bucket type identifier
            
        Returns:
            Full S3 bucket name
            
        Raises:
            ValueError: If bucket type is invalid
        """
        # Map bucket types to actual bucket names
        bucket_mapping = {
            'websites': self._websites_bucket,
            'assets': self._assets_bucket,
            'csv_imports': self._csv_imports_bucket
        }
        
        if bucket_type not in bucket_mapping:
            raise ValueError(f"Invalid bucket type: {bucket_type}")
        
        return bucket_mapping[bucket_type]
    
    def _get_content_type(self, file_path: str) -> str:
        """Get MIME content type for a file path.
        
        Args:
            file_path: File path or name
            
        Returns:
            MIME content type string
        """
        # Get content type from file extension
        content_type, _ = mimetypes.guess_type(file_path)
        
        if content_type:
            return content_type
        
        # Default content types for common web files
        extension = Path(file_path).suffix.lower()
        
        extension_map = {
            '.html': 'text/html',
            '.htm': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.txt': 'text/plain',
            '.md': 'text/markdown'
        }
        
        return extension_map.get(extension, 'application/octet-stream')
    
    def _configure_website_hosting(self, domain_prefix: str, enable_spa: bool) -> None:
        """Configure S3 bucket for static website hosting.
        
        Args:
            domain_prefix: Domain prefix for the website
            enable_spa: Whether to enable SPA routing
        """
        try:
            # Configure website hosting
            website_config = {
                'IndexDocument': {'Suffix': f'{domain_prefix}/index.html'}
            }
            
            # Add error document for SPA routing
            if enable_spa:
                website_config['ErrorDocument'] = {'Key': f'{domain_prefix}/index.html'}
            else:
                website_config['ErrorDocument'] = {'Key': f'{domain_prefix}/404.html'}
            
            # Apply website configuration (note: this may not work with CloudFront OAC)
            # This is mainly for direct S3 website access
            self._s3_client.put_bucket_website(
                Bucket=self._websites_bucket,
                WebsiteConfiguration=website_config
            )
            
        except ClientError as e:
            # Website configuration is optional, don't fail deployment
            print(f"Warning: Could not configure website hosting: {e}")


# Global S3 client instance
s3_client = S3Client()