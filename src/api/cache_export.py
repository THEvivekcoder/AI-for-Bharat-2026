"""Lambda function for exporting offline cache data to S3.

This function exports frequently accessed schemes to JSON files
and stores them in S3 for offline download.
"""

import json
import gzip
import hashlib
import os
from datetime import datetime
from typing import List, Dict, Any
import boto3
from boto3.dynamodb.conditions import Attr

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

# Environment variables
SCHEMES_TABLE = os.environ.get('SCHEMES_TABLE', 'bharatsahayak-schemes-dev')
INTERACTIONS_TABLE = os.environ.get('INTERACTIONS_TABLE', 'bharatsahayak-interactions-dev')
S3_BUCKET = os.environ.get('STATIC_CONTENT_BUCKET', 'bharatsahayak-static-content-dev')
CACHE_VERSION = os.environ.get('CACHE_VERSION', '1.0.0')


def lambda_handler(event, context):
    """
    Export offline cache data to S3.
    
    Query parameters:
    - priority: Filter by priority level (1-5)
    - category: Filter by scheme category
    - limit: Maximum number of schemes to export (default: 100)
    
    Returns:
    - file_key: S3 key where cache file is stored
    - file_size: Size of the exported file in bytes
    - schemes_count: Number of schemes exported
    - version: Cache version
    - timestamp: Export timestamp
    - s3_url: Public URL to download the cache file
    """
    try:
        # Parse query parameters
        params = event.get('queryStringParameters', {}) or {}
        priority_filter = params.get('priority')
        category_filter = params.get('category')
        limit = int(params.get('limit', 100))
        
        # Get frequently accessed schemes
        schemes = get_frequently_accessed_schemes(
            priority_filter=priority_filter,
            category_filter=category_filter,
            limit=limit
        )
        
        # Prepare cache data
        cache_data = {
            'version': CACHE_VERSION,
            'timestamp': datetime.utcnow().isoformat(),
            'schemes_count': len(schemes),
            'schemes': schemes
        }
        
        # Convert to JSON and compress
        json_data = json.dumps(cache_data, ensure_ascii=False, indent=2)
        compressed_data = gzip.compress(json_data.encode('utf-8'))
        
        # Calculate checksum
        checksum = hashlib.sha256(compressed_data).hexdigest()
        
        # Generate S3 key
        timestamp_str = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        file_key = f'cache/schemes_cache_{timestamp_str}.json.gz'
        
        # Upload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=file_key,
            Body=compressed_data,
            ContentType='application/json',
            ContentEncoding='gzip',
            Metadata={
                'version': CACHE_VERSION,
                'checksum': checksum,
                'schemes_count': str(len(schemes))
            }
        )
        
        # Generate public URL
        s3_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{file_key}"
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'file_key': file_key,
                'file_size': len(compressed_data),
                'schemes_count': len(schemes),
                'version': CACHE_VERSION,
                'timestamp': cache_data['timestamp'],
                's3_url': s3_url,
                'checksum': checksum
            })
        }
        
    except Exception as e:
        print(f"Error exporting cache: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }


def get_frequently_accessed_schemes(
    priority_filter: str = None,
    category_filter: str = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get frequently accessed schemes based on interaction data.
    
    Priority levels:
    1 - Critical (most accessed, essential schemes)
    2 - High (frequently accessed)
    3 - Medium (moderately accessed)
    4 - Low (occasionally accessed)
    5 - Nice-to-have (rarely accessed)
    
    Args:
        priority_filter: Filter by priority level (1-5)
        category_filter: Filter by scheme category
        limit: Maximum number of schemes to return
        
    Returns:
        List of scheme dictionaries with simplified data
    """
    schemes_table = dynamodb.Table(SCHEMES_TABLE)
    interactions_table = dynamodb.Table(INTERACTIONS_TABLE)
    
    # Get scheme access counts from interactions
    scheme_access_counts = get_scheme_access_counts(interactions_table)
    
    # Scan schemes table
    scan_kwargs = {}
    if category_filter:
        scan_kwargs['FilterExpression'] = Attr('category').eq(category_filter)
    
    response = schemes_table.scan(**scan_kwargs)
    all_schemes = response.get('Items', [])
    
    # Continue scanning if there are more items
    while 'LastEvaluatedKey' in response:
        response = schemes_table.scan(
            ExclusiveStartKey=response['LastEvaluatedKey'],
            **scan_kwargs
        )
        all_schemes.extend(response.get('Items', []))
    
    # Calculate priority for each scheme based on access count
    schemes_with_priority = []
    for scheme in all_schemes:
        scheme_id = scheme.get('scheme_id')
        access_count = scheme_access_counts.get(scheme_id, 0)
        
        # Assign priority based on access count
        if access_count >= 100:
            priority = 1  # Critical
        elif access_count >= 50:
            priority = 2  # High
        elif access_count >= 20:
            priority = 3  # Medium
        elif access_count >= 5:
            priority = 4  # Low
        else:
            priority = 5  # Nice-to-have
        
        # Apply priority filter if specified
        if priority_filter and priority != int(priority_filter):
            continue
        
        # Simplify scheme data for offline cache
        cached_scheme = {
            'scheme_id': scheme_id,
            'name': scheme.get('name', ''),
            'category': scheme.get('category', ''),
            'description': scheme.get('description', ''),
            'benefits': scheme.get('benefits', []),
            'eligibility_summary': get_eligibility_summary(scheme.get('eligibility_criteria', {})),
            'required_documents': scheme.get('required_documents', []),
            'application_process': scheme.get('application_process', []),
            'priority': priority,
            'last_updated': scheme.get('last_updated', '')
        }
        
        schemes_with_priority.append((priority, access_count, cached_scheme))
    
    # Sort by priority (ascending) and access count (descending)
    schemes_with_priority.sort(key=lambda x: (x[0], -x[1]))
    
    # Return top schemes up to limit
    return [scheme for _, _, scheme in schemes_with_priority[:limit]]


def get_scheme_access_counts(interactions_table) -> Dict[str, int]:
    """
    Get access counts for each scheme from interactions table.
    
    Args:
        interactions_table: DynamoDB table resource
        
    Returns:
        Dictionary mapping scheme_id to access count
    """
    access_counts = {}
    
    try:
        # Scan interactions table for scheme_accessed events
        response = interactions_table.scan(
            FilterExpression=Attr('event_type').eq('scheme_accessed')
        )
        
        for item in response.get('Items', []):
            event_data = item.get('event_data', {})
            scheme_id = event_data.get('scheme_id')
            if scheme_id:
                access_counts[scheme_id] = access_counts.get(scheme_id, 0) + 1
        
        # Continue scanning if there are more items
        while 'LastEvaluatedKey' in response:
            response = interactions_table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey'],
                FilterExpression=Attr('event_type').eq('scheme_accessed')
            )
            for item in response.get('Items', []):
                event_data = item.get('event_data', {})
                scheme_id = event_data.get('scheme_id')
                if scheme_id:
                    access_counts[scheme_id] = access_counts.get(scheme_id, 0) + 1
    
    except Exception as e:
        print(f"Error getting scheme access counts: {str(e)}")
        # Return empty dict if there's an error
    
    return access_counts


def get_eligibility_summary(criteria: Dict[str, Any]) -> str:
    """
    Generate a simplified eligibility summary from criteria.
    
    Args:
        criteria: Eligibility criteria dictionary
        
    Returns:
        Human-readable eligibility summary
    """
    summary_parts = []
    
    if criteria.get('age_min') or criteria.get('age_max'):
        age_min = criteria.get('age_min', 0)
        age_max = criteria.get('age_max', 100)
        summary_parts.append(f"Age: {age_min}-{age_max} years")
    
    if criteria.get('income_max'):
        summary_parts.append(f"Income: Up to ₹{criteria['income_max']}")
    
    if criteria.get('gender'):
        summary_parts.append(f"Gender: {criteria['gender']}")
    
    if criteria.get('occupation'):
        occupations = criteria['occupation']
        if isinstance(occupations, list):
            summary_parts.append(f"Occupation: {', '.join(occupations)}")
        else:
            summary_parts.append(f"Occupation: {occupations}")
    
    if criteria.get('location'):
        locations = criteria['location']
        if isinstance(locations, list):
            summary_parts.append(f"Location: {', '.join(locations)}")
        else:
            summary_parts.append(f"Location: {locations}")
    
    return '; '.join(summary_parts) if summary_parts else 'Open to all eligible citizens'
