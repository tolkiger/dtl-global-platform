"""POST /crm-import Lambda handler for DTL-Global onboarding platform.

This handler imports CSV data into HubSpot CRM with AI-powered column mapping.

Endpoint: POST /crm-import
Purpose: Import client CRM data from CSV files
Dependencies: HubSpot client, AI client for mapping, S3 for file storage

Author: DTL-Global Platform
"""

import json
import csv
import io
from typing import Any, Dict, List
from datetime import datetime

# Import shared modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import config
from hubspot_client import hubspot_client
from ai_client import ai_client
from s3_client import s3_client


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Import CSV data into HubSpot CRM."""
    print(f"CRM import started - Request ID: {context.aws_request_id}")
    
    try:
        request_data = json.loads(event['body'])
        client_id = request_data['client_id']
        csv_content = request_data['csv_content']
        import_type = request_data.get('import_type', 'contacts')
        
        # Parse CSV content
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        csv_headers = csv_reader.fieldnames
        csv_rows = list(csv_reader)
        
        print(f"Processing {len(csv_rows)} rows with headers: {csv_headers}")
        
        # Use AI to suggest column mappings
        column_mappings = ai_client.analyze_crm_columns(csv_headers, 'hubspot')
        
        # Upload CSV to S3 for backup
        upload_result = s3_client.upload_csv_import(
            client_id=client_id,
            csv_content=csv_content,
            import_type=import_type
        )
        
        # Import contacts to HubSpot (batch processing)
        imported_contacts = []
        batch_size = 50  # HubSpot batch limit
        
        for i in range(0, len(csv_rows), batch_size):
            batch = csv_rows[i:i + batch_size]
            
            # Map CSV data to HubSpot format
            hubspot_contacts = []
            for row in batch:
                contact_data = {}
                for csv_field, hubspot_field in column_mappings.items():
                    if csv_field in row and row[csv_field]:
                        contact_data[hubspot_field] = row[csv_field]
                
                # Add import metadata
                contact_data['lead_source'] = 'dtl_global_csv_import'
                contact_data['import_date'] = datetime.utcnow().strftime('%Y-%m-%d')
                
                hubspot_contacts.append(contact_data)
            
            # Batch create contacts in HubSpot
            if hubspot_contacts:
                batch_result = hubspot_client.batch_create_contacts(hubspot_contacts)
                imported_contacts.extend(batch_result)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'total_rows': len(csv_rows),
                'imported_count': len(imported_contacts),
                'column_mappings': column_mappings,
                'csv_backup_url': upload_result['url'],
                'message': f'Successfully imported {len(imported_contacts)} contacts'
            })
        }
        
    except Exception as e:
        print(f"Error in CRM import: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e), 'timestamp': datetime.utcnow().isoformat()})
        }
