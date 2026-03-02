"""Lambda function for cache synchronization.

This function checks for cache updates and returns a list of updated schemes
since the last sync, supporting incremental updates to minimize bandwidth.
"""

import json
import gzip
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import boto3
from boto3.dynamodb.conditions import Attr

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

# Environment variables
SCHEMES_TABLE = os.environ.get('SCHEMES_TABLE', 'bharatsahayak-schemes-dev')
S3_BUCKET = os.environ.get('STATIC_CONTENT_BUCKET', 'bharatsahayak-static-content-dev')


def lambda_handler(event, context):
    """
    Check for cache updates and return incremental changes.
    
    Request body:
    {
        "last_sync_timestamp": "2024-01-15T10:30:00Z",  # Optional
        "categories": ["agriculture", "health"],  # Optional
        "max_size_kb": 100  # Maximum response size in KB
    }
    
    Returns:
    {
        "updated_schemes": [...],  # List of updated scheme IDs
        "deleted_schemes": [...],  # List of deleted scheme IDs
        "total_size_kb": 45.2,
        "sync_timestamp": "2024-01-20T15:45:00Z",
        "incremental": true,
        "schemes_data": {...}  # Actual scheme data if size permits
    }
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        last_sync_timestamp = body.get('last_sync_timestamp')
        categories = body.get('categories')
        max_size_kb = body.get('max_size_kb', 100)
        
        # Convert timestamp string to datetime if provided
        last_sync_dt = None
        if last_sync_timestamp:
            last_sync_dt = datetime.fromisoformat(last_sync_timestamp.replace('Z', '+00:00'))
        
        # Get updated schemes
        updated_schemes, deleted_schemes = get_updated_schemes(
            last_sync_timestamp=last_sync_dt,
            categories=categories
        )
        
        # Prepare response data
        sync_timestamp = datetime.utcnow()
        
        # Get full scheme data for updated schemes
        schemes_data = {}
        total_size = 0
        
        if updated_schemes:
            schemes_table = dynamodb.Table(SCHEMES_TABLE)
            
            for scheme_id in updated_schemes:
                # Check if we've exceeded size limit
                if total_size > max_size_kb * 1024:
                    break
                
                try:
                    response = schemes_table.get_item(Key={'scheme_id': scheme_id})
                    if 'Item' in response:
                        scheme = response['Item']
                        # Simplify scheme data
                        simplified_scheme = {
                            'scheme_id': scheme.get('scheme_id'),
                            'name': scheme.get('name'),
                            'category': scheme.get('category'),
                            'description': scheme.get('description'),
                            'benefits': scheme.get('benefits', []),
                            'eligibility_criteria': scheme.get('eligibility_criteria', {}),
                            'required_documents': scheme.get('required_documents', []),
                            'application_process': scheme.get('application_process', []),
                            'last_updated': scheme.get('last_updated')
                        }
                        
                        # Calculate size
                        scheme_json = json.dumps(simplified_scheme)
                        scheme_size = len(scheme_json.encode('utf-8'))
                        
                        if total_size + scheme_size <= max_size_kb * 1024:
                            schemes_data[scheme_id] = simplified_scheme
                            total_size += scheme_size
                        else:
                            break
                
                except Exception as e:
                    print(f"Error fetching scheme {scheme_id}: {str(e)}")
                    continue
        
        # Prepare response
        response_data = {
            'updated_schemes': updated_schemes,
            'deleted_schemes': deleted_schemes,
            'total_size_kb': round(total_size / 1024, 2),
            'sync_timestamp': sync_timestamp.isoformat(),
            'incremental': last_sync_dt is not None,
            'schemes_data': schemes_data if schemes_data else None
        }
        
        # Compress response if it's large
        response_json = json.dumps(response_data, ensure_ascii=False)
        response_size = len(response_json.encode('utf-8'))
        
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
        
        # If response is large, compress it
        if response_size > 10 * 1024:  # > 10KB
            compressed_data = gzip.compress(response_json.encode('utf-8'))
            headers['Content-Encoding'] = 'gzip'
            body_data = compressed_data
        else:
            body_data = response_json
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': body_data if isinstance(body_data, str) else body_data.decode('latin-1'),
            'isBase64Encoded': not isinstance(body_data, str)
        }
        
    except Exception as e:
        print(f"Error in cache sync: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }


def get_updated_schemes(
    last_sync_timestamp: Optional[datetime] = None,
    categories: Optional[List[str]] = None
) -> tuple[List[str], List[str]]:
    """
    Get list of schemes updated since last sync.
    
    Args:
        last_sync_timestamp: Timestamp of last sync (None for full sync)
        categories: Filter by categories
        
    Returns:
        Tuple of (updated_scheme_ids, deleted_scheme_ids)
    """
    schemes_table = dynamodb.Table(SCHEMES_TABLE)
    
    updated_schemes = []
    deleted_schemes = []  # Would need a separate tracking mechanism
    
    # Build scan parameters
    scan_kwargs = {}
    filter_expressions = []
    
    # Filter by last_updated timestamp if provided
    if last_sync_timestamp:
        # Convert datetime to ISO string for comparison
        timestamp_str = last_sync_timestamp.isoformat()
        filter_expressions.append(Attr('last_updated').gt(timestamp_str))
    
    # Filter by categories if provided
    if categories:
        category_filter = Attr('category').is_in(categories)
        filter_expressions.append(category_filter)
    
    # Combine filters
    if filter_expressions:
        combined_filter = filter_expressions[0]
        for expr in filter_expressions[1:]:
            combined_filter = combined_filter & expr
        scan_kwargs['FilterExpression'] = combined_filter
    
    # Scan for updated schemes
    try:
        response = schemes_table.scan(**scan_kwargs)
        
        for item in response.get('Items', []):
            updated_schemes.append(item.get('scheme_id'))
        
        # Continue scanning if there are more items
        while 'LastEvaluatedKey' in response:
            response = schemes_table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey'],
                **scan_kwargs
            )
            for item in response.get('Items', []):
                updated_schemes.append(item.get('scheme_id'))
    
    except Exception as e:
        print(f"Error scanning schemes: {str(e)}")
    
    return updated_schemes, deleted_schemes


def get_scheme_by_id(scheme_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a single scheme by ID.
    
    Args:
        scheme_id: Scheme identifier
        
    Returns:
        Scheme dictionary or None if not found
    """
    schemes_table = dynamodb.Table(SCHEMES_TABLE)
    
    try:
        response = schemes_table.get_item(Key={'scheme_id': scheme_id})
        return response.get('Item')
    except Exception as e:
        print(f"Error fetching scheme {scheme_id}: {str(e)}")
        return None
