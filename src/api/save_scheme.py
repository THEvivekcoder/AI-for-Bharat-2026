"""Lambda handler for saving/unsaving schemes."""

import json
import os
import logging
from typing import Dict, Any
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

from src.utils.jwt_auth import require_jwt_auth

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
SAVED_SCHEMES_TABLE = os.environ.get('SAVED_SCHEMES_TABLE', 'bharatsahayak-saved-schemes-dev')
saved_schemes_table = dynamodb.Table(SAVED_SCHEMES_TABLE)


@require_jwt_auth
def lambda_handler(event: Dict[str, Any], context: Any, user_id: str, email: str) -> Dict[str, Any]:
    """
    Save or unsave a scheme for the user.
    
    POST /schemes/save
    Headers:
        Authorization: Bearer <jwt_token>
    
    Request body:
    {
        "scheme_id": "scheme_123",
        "scheme_name": "PM-KISAN",
        "action": "save" | "unsave"
    }
    """
    try:
        body = json.loads(event.get('body', '{}'))
        scheme_id = body.get('scheme_id')
        scheme_name = body.get('scheme_name', '')
        action = body.get('action', 'save')
        
        if not scheme_id:
            return error_response(400, "scheme_id is required")
        
        if action == 'save':
            # Save scheme
            item = {
                'user_id': user_id,
                'scheme_id': scheme_id,
                'scheme_name': scheme_name,
                'saved_at': datetime.utcnow().isoformat()
            }
            
            saved_schemes_table.put_item(Item=item)
            logger.info(f"Scheme saved: {scheme_id} for user: {user_id}")
            
            return success_response({
                "message": "Scheme saved successfully",
                "scheme_id": scheme_id
            })
            
        elif action == 'unsave':
            # Remove saved scheme
            saved_schemes_table.delete_item(
                Key={
                    'user_id': user_id,
                    'scheme_id': scheme_id
                }
            )
            logger.info(f"Scheme unsaved: {scheme_id} for user: {user_id}")
            
            return success_response({
                "message": "Scheme removed successfully",
                "scheme_id": scheme_id
            })
        else:
            return error_response(400, "Invalid action. Use 'save' or 'unsave'")
        
    except Exception as e:
        logger.error(f"Error saving/unsaving scheme: {str(e)}", exc_info=True)
        return error_response(500, "Failed to process request")


def success_response(data: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
    """Create a successful API response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps(data)
    }


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Create an error API response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps({'error': message})
    }
