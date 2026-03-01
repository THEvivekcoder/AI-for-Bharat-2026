"""Lambda handler for updating user profile."""

import json
import os
import logging
from typing import Dict, Any

from src.core.profile_repository import ProfileRepository, ItemNotFoundError
from src.models.location import Location
from src.models.user import UserPreferences
from src.utils.auth_middleware import require_auth

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize repository
PROFILES_TABLE = os.environ.get('PROFILES_TABLE', 'bharatsahayak-user-profiles-dev')
profile_repo = ProfileRepository(table_name=PROFILES_TABLE)


@require_auth
def lambda_handler(event: Dict[str, Any], context: Any, user_id: str) -> Dict[str, Any]:
    """
    Handle PUT user profile update requests.
    
    PUT /user/profile
    Headers:
        Authorization: Bearer <jwt_token>
    
    Request body (all fields optional):
    {
        "language": "hi",
        "location": {
            "state": "Maharashtra",
            "district": "Pune",
            "pincode": "411014"
        },
        "age": 35,
        "gender": "male",
        "education_level": "secondary",
        "occupation": "farmer",
        "income_bracket": "100000-300000",
        "household_size": 5,
        "preferences": {
            "notification_enabled": true,
            "preferred_categories": ["agriculture", "health"]
        }
    }
    
    Response:
    {
        "user_id": "uuid",
        "message": "Profile updated successfully",
        "profile": {...}
    }
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        if not body:
            return error_response(400, "Request body is required")
        
        # Check if updating own profile
        path_params = event.get('pathParameters', {})
        requested_user_id = path_params.get('user_id', user_id)
        
        if requested_user_id != user_id:
            return error_response(403, "Access denied: You can only update your own profile")
        
        # Validate and prepare updates
        updates = {}
        
        # Simple string fields
        if 'language' in body:
            updates['language'] = body['language']
        
        if 'education_level' in body:
            updates['education_level'] = body['education_level']
        
        if 'occupation' in body:
            updates['occupation'] = body['occupation']
        
        if 'income_bracket' in body:
            updates['income_bracket'] = body['income_bracket']
        
        if 'gender' in body:
            updates['gender'] = body['gender']
        
        # Numeric fields
        if 'age' in body:
            age = body['age']
            if not isinstance(age, int) or age < 0 or age > 120:
                return error_response(400, "Age must be between 0 and 120")
            updates['age'] = age
        
        if 'household_size' in body:
            household_size = body['household_size']
            if not isinstance(household_size, int) or household_size < 1:
                return error_response(400, "Household size must be at least 1")
            updates['household_size'] = household_size
        
        # Location object
        if 'location' in body:
            try:
                location = Location(**body['location'])
                updates['location'] = location.model_dump()
            except Exception as e:
                return error_response(400, f"Invalid location data: {str(e)}")
        
        # Preferences object
        if 'preferences' in body:
            try:
                preferences = UserPreferences(**body['preferences'])
                updates['preferences'] = preferences.model_dump()
            except Exception as e:
                return error_response(400, f"Invalid preferences data: {str(e)}")
        
        if not updates:
            return error_response(400, "No valid fields to update")
        
        # Update profile in DynamoDB
        updated_profile = profile_repo.update_profile(user_id, updates)
        
        # Convert to dict
        profile_dict = updated_profile.model_dump()
        profile_dict['created_at'] = profile_dict['created_at'].isoformat()
        profile_dict['updated_at'] = profile_dict['updated_at'].isoformat()
        
        logger.info(f"Profile updated successfully: {user_id}")
        
        return success_response({
            "user_id": user_id,
            "message": "Profile updated successfully",
            "profile": profile_dict
        })
        
    except ItemNotFoundError as e:
        logger.error(f"Profile not found: {str(e)}")
        return error_response(404, "Profile not found")
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return error_response(400, str(e))
    
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
