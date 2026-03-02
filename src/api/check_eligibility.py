"""Lambda handler for checking user eligibility for a specific scheme."""

import json
import os
import logging
from typing import Dict, Any

from src.core.scheme_repository import SchemeRepository, ItemNotFoundError, DynamoDBRepositoryError
from src.core.eligibility_checker import EligibilityChecker
from src.models.user import UserProfile
from src.models.location import Location

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize repository and checker
SCHEMES_TABLE = os.environ.get('SCHEMES_TABLE', 'bharatsahayak-schemes-dev')
scheme_repo = SchemeRepository(table_name=SCHEMES_TABLE)
eligibility_checker = EligibilityChecker()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle POST /schemes/check-eligibility requests.
    
    Request Body:
    {
        "scheme_id": "PM-KISAN-2024",
        "language": "hi",  // Optional: language code for translated scheme name (default: 'en')
        "user_profile": {
            "user_id": "user_123",
            "phone_number": "+919876543210",
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
            "income_bracket": "100000-300000"
        }
    }
    
    Response:
    {
        "is_eligible": true,
        "reasoning": [
            "Age 35 meets requirement (minimum 18, maximum 60)",
            "Income ₹300,000 is within limit of ₹500,000",
            "Occupation 'farmer' is eligible"
        ],
        "missing_criteria": [],
        "confidence": 1.0,
        "scheme_id": "PM-KISAN-2024",
        "scheme_name": "प्रधानमंत्री किसान सम्मान निधि"  // Translated if language specified
    }
    
    Error Responses:
    - 400: Invalid request body or missing required fields
    - 404: Scheme not found
    - 500: Internal server error
    """
    try:
        # Parse request body
        body = _parse_request_body(event)
        if isinstance(body, dict) and 'error' in body:
            return error_response(400, body['error'])
        
        # Extract and validate required fields
        scheme_id = body.get('scheme_id')
        user_profile_data = body.get('user_profile')
        language = body.get('language', 'en')  # Optional language parameter
        
        if not scheme_id:
            return error_response(400, "Missing required field: scheme_id")
        
        if not user_profile_data:
            return error_response(400, "Missing required field: user_profile")
        
        # Validate and parse user profile
        try:
            user_profile = _parse_user_profile(user_profile_data)
        except ValueError as e:
            return error_response(400, f"Invalid user_profile: {str(e)}")
        
        # Retrieve scheme from repository
        logger.info(f"Checking eligibility: scheme_id={scheme_id}, user_id={user_profile.user_id}")
        scheme = scheme_repo.get(scheme_id)
        
        # Check eligibility
        result = eligibility_checker.check_eligibility(user_profile, scheme)
        
        # Get translated scheme name if available
        scheme_name = scheme.name_translations.get(language, scheme.name) if language != 'en' else scheme.name
        
        # Build response
        response_data = {
            'is_eligible': result.is_eligible,
            'reasoning': result.reasoning,
            'missing_criteria': result.missing_criteria,
            'confidence': result.confidence,
            'scheme_id': scheme.scheme_id,
            'scheme_name': scheme_name
        }
        
        logger.info(f"Eligibility check complete: eligible={result.is_eligible}, confidence={result.confidence}")
        return success_response(response_data)
        
    except ItemNotFoundError as e:
        logger.warning(f"Scheme not found: {str(e)}")
        return error_response(404, f"Scheme not found: {scheme_id}")
    
    except DynamoDBRepositoryError as e:
        logger.error(f"Database error: {str(e)}")
        return error_response(500, "Failed to retrieve scheme information")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return error_response(500, "Internal server error")


def _parse_request_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and validate request body from API Gateway event.
    
    Args:
        event: API Gateway event
        
    Returns:
        Parsed request body as dictionary
    """
    try:
        body = event.get('body')
        if not body:
            return {'error': 'Request body is required'}
        
        # Parse JSON if body is string
        if isinstance(body, str):
            body = json.loads(body)
        
        return body
        
    except json.JSONDecodeError as e:
        return {'error': f'Invalid JSON in request body: {str(e)}'}


def _parse_user_profile(profile_data: Dict[str, Any]) -> UserProfile:
    """
    Parse and validate user profile data.
    
    Args:
        profile_data: User profile dictionary
        
    Returns:
        UserProfile object
        
    Raises:
        ValueError: If profile data is invalid
    """
    try:
        # Extract location data
        location_data = profile_data.get('location')
        if not location_data:
            raise ValueError("Missing required field: location")
        
        # Create Location object
        location = Location(**location_data)
        
        # Create UserProfile object
        profile_data['location'] = location
        user_profile = UserProfile(**profile_data)
        
        return user_profile
        
    except Exception as e:
        raise ValueError(f"Failed to parse user profile: {str(e)}")


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
