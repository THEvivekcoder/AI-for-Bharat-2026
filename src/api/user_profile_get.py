"""Lambda handler for retrieving user profile."""

import json
import os
import logging
from typing import Dict, Any

from src.core.profile_repository import ProfileRepository, ItemNotFoundError
from src.utils.jwt_auth import require_jwt_auth

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize repository
PROFILES_TABLE = os.environ.get('PROFILES_TABLE', 'bharatsahayak-user-profiles-dev')
AWS_REGION = os.environ.get('AWS_REGION', 'ap-south-1')
profile_repo = ProfileRepository(table_name=PROFILES_TABLE, region_name=AWS_REGION)


@require_jwt_auth
def lambda_handler(event: Dict[str, Any], context: Any, user_id: str, email: str) -> Dict[str, Any]:
    """
    Handle GET user profile requests.
    
    GET /user/profile
    Headers:
        Authorization: Bearer <jwt_token>
    
    Response:
    {
        "user_id": "uuid",
        "phone_number": "+919876543210",
        "language": "hi",
        "location": {...},
        "age": 35,
        "gender": "male",
        ...
    }
    """
    try:
        # Check if requesting own profile or specific user
        path_params = event.get('pathParameters', {})
        requested_user_id = path_params.get('user_id', user_id)
        
        # For now, users can only access their own profile
        # In future, add admin role check for accessing other profiles
        if requested_user_id != user_id:
            return error_response(403, "Access denied: You can only access your own profile")
        
        # Retrieve profile from DynamoDB
        profile = profile_repo.get_profile(user_id)
        
        # Convert to dict and return
        profile_dict = profile.model_dump()
        
        # Convert datetime objects to ISO format strings
        profile_dict['created_at'] = profile_dict['created_at'].isoformat()
        profile_dict['updated_at'] = profile_dict['updated_at'].isoformat()
        
        logger.info(f"Profile retrieved successfully: {user_id}")
        
        return success_response(profile_dict)
        
    except ItemNotFoundError as e:
        logger.error(f"Profile not found: {str(e)}")
        return error_response(404, "Profile not found")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return error_response(500, "Internal server error")


def success_response(data: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
    """Create a successful API response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(data)
    }


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Create an error API response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': message
        })
    }
