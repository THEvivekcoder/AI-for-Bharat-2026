"""
Index Documents Lambda Handler

Handles POST /rag/index endpoint for indexing scheme documents into OpenSearch
"""

import json
import os
from typing import Dict, Any
import boto3

from src.services.rag_engine import RAGEngine


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Index scheme documents into OpenSearch vector database
    
    Request body:
    {
        "scheme_ids": ["scheme-1", "scheme-2"],  // Optional, if not provided indexes all
        "force_reindex": false  // Optional, default false
    }
    
    Response:
    {
        "indexed_count": 42,
        "total_schemes": 50,
        "status": "success"
    }
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        scheme_ids = body.get('scheme_ids')
        force_reindex = body.get('force_reindex', False)
        
        # Initialize services
        opensearch_endpoint = os.environ.get('OPENSEARCH_ENDPOINT')
        embedding_model_id = os.environ.get('EMBEDDING_MODEL_ID', 'amazon.titan-embed-text-v1')
        schemes_table = os.environ.get('SCHEMES_TABLE')
        
        rag_engine = RAGEngine(opensearch_endpoint, embedding_model_id=embedding_model_id)
        
        # Create index if it doesn't exist
        rag_engine.vector_store.create_index()
        
        # Fetch schemes from DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(schemes_table)
        
        if scheme_ids:
            # Fetch specific schemes
            schemes = []
            for scheme_id in scheme_ids:
                response = table.get_item(Key={'scheme_id': scheme_id})
                if 'Item' in response:
                    schemes.append(response['Item'])
        else:
            # Fetch all schemes
            response = table.scan()
            schemes = response.get('Items', [])
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                schemes.extend(response.get('Items', []))
        
        # Prepare documents for indexing
        documents = []
        for scheme in schemes:
            # Create searchable content by combining key fields
            content_parts = [
                scheme.get('name', ''),
                scheme.get('description', ''),
                ' '.join(scheme.get('benefits', [])) if isinstance(scheme.get('benefits'), list) else str(scheme.get('benefits', '')),
                scheme.get('department', ''),
                scheme.get('category', '')
            ]
            content = ' '.join(filter(None, content_parts))
            
            doc = {
                'id': scheme['scheme_id'],
                'content': content,
                'scheme_id': scheme['scheme_id'],
                'name': scheme.get('name', ''),
                'category': scheme.get('category', ''),
                'description': scheme.get('description', ''),
                'benefits': scheme.get('benefits', []),
                'eligibility_criteria': scheme.get('eligibility_criteria', {}),
                'source_type': 'official',  # All schemes are from official sources
                'department': scheme.get('department', ''),
                'state': scheme.get('state')
            }
            documents.append(doc)
        
        # Index documents
        indexed_count = rag_engine.add_documents(documents)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'indexed_count': indexed_count,
                'total_schemes': len(schemes),
                'status': 'success' if indexed_count > 0 else 'partial_failure'
            })
        }
        
    except Exception as e:
        print(f"Error indexing documents: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'INDEXING_ERROR',
                'message': f'Failed to index documents: {str(e)}'
            })
        }
