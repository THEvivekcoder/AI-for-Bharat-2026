"""Lambda handler for finding all eligible schemes for a user profile."""

import json
import os
import logging
from typing import Dict, Any, List, Tuple

from src.core.scheme_repository import SchemeRepository, DynamoDBRepositoryError
from src.core.eligibility_checker import EligibilityChecker, EligibilityResult
from src.models.user import UserProfile
from src.models.location import Location
from src.models.scheme import Scheme

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize repository and checker
SCHEMES_TABLE = os.environ.get('SCHEMES_TABLE', 'bharatsahayak-schemes-dev')
scheme_repo = SchemeRepository(table_name=SCHEMES_TABLE)
eligibility_checker = EligibilityChecker()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle POST /schemes/eligible requests.
    
    Returns all schemes that the user is eligible for, ranked by relevance.
    
    Request Body:
    {
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
        },
        "category": "agriculture",  // Optional: filter by category
        "limit": 20  // Optional: max results (default 50)
    }
    
    Response:
    {
        "eligible_schemes": [
            {
                "scheme_id": "PM-KISAN-2024",
                "name": "Pradhan Mantri Kisan Samman Nidhi",
                "category": "agriculture",
                "description": "Income support scheme...",
                "benefits": [...],
                "eligibility_explanation": {
                    "is_eligible": true,
                    "reasoning": [
                        "Age 35 meets requirement",
                        "Occupation 'farmer' is eligible"
                    ],
                    "confidence": 1.0
                },
                "relevance_score": 0.95
            }
        ],
        "total_count": 5,
        "user_location": "Maharashtra/Pune"
    }
    
    Error Responses:
    - 400: Invalid request body or missing required fields
    - 500: Internal server error
    """
    try:
        # Parse request body
        body = _parse_request_body(event)
        if isinstance(body, dict) and 'error' in body:
            return error_response(400, body['error'])
        
        # Extract and validate required fields
        user_profile_data = body.get('user_profile')
        category_filter = body.get('category')
        limit = body.get('limit', 50)
        
        if not user_profile_data:
            return error_response(400, "Missing required field: user_profile")
        
        # Validate limit
        if not isinstance(limit, int) or limit < 1 or limit > 100:
            return error_response(400, "Invalid limit: must be between 1 and 100")
        
        # Validate and parse user profile
        try:
            user_profile = _parse_user_profile(user_profile_data)
        except ValueError as e:
            return error_response(400, f"Invalid user_profile: {str(e)}")
        
        # Retrieve all schemes (with optional category filter)
        logger.info(f"Finding eligible schemes: user_id={user_profile.user_id}, category={category_filter}")
        
        # Get schemes from repository
        all_schemes = scheme_repo.get_all_schemes(category=category_filter, limit=200)
        
        logger.info(f"Retrieved {len(all_schemes)} schemes to check")
        
        # Check eligibility for each scheme
        eligible_schemes_with_results = []
        for scheme in all_schemes:
            result = eligibility_checker.check_eligibility(user_profile, scheme)
            
            if result.is_eligible:
                eligible_schemes_with_results.append((scheme, result))
        
        logger.info(f"Found {len(eligible_schemes_with_results)} eligible schemes")
        
        # Rank schemes by relevance
        ranked_schemes = _rank_schemes_by_relevance(
            eligible_schemes_with_results,
            user_profile
        )
        
        # Limit results
        ranked_schemes = ranked_schemes[:limit]
        
        # Build response
        response_data = {
            'eligible_schemes': [
                _build_scheme_response(scheme, result, relevance_score)
                for scheme, result, relevance_score in ranked_schemes
            ],
            'total_count': len(ranked_schemes),
            'user_location': f"{user_profile.location.state}/{user_profile.location.district}"
        }
        
        logger.info(f"Returning {len(ranked_schemes)} eligible schemes")
        return success_response(response_data)
        
    except DynamoDBRepositoryError as e:
        logger.error(f"Database error: {str(e)}")
        return error_response(500, "Failed to retrieve schemes")
    
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


def _rank_schemes_by_relevance(
    eligible_schemes: List[Tuple[Scheme, EligibilityResult]],
    user_profile: UserProfile
) -> List[Tuple[Scheme, EligibilityResult, float]]:
    """
    Rank eligible schemes by relevance to user profile.
    
    Relevance factors:
    - Confidence score (higher is better)
    - Location match (state-specific schemes ranked higher for that state)
    - Category preference (if user has preferred categories)
    - Occupation match (schemes for user's occupation ranked higher)
    
    Args:
        eligible_schemes: List of (Scheme, EligibilityResult) tuples
        user_profile: User profile
        
    Returns:
        List of (Scheme, EligibilityResult, relevance_score) tuples, sorted by relevance
    """
    ranked = []
    
    for scheme, result in eligible_schemes:
        relevance_score = 0.0
        
        # Base score from confidence
        relevance_score += result.confidence * 0.4
        
        # Location match bonus
        if scheme.state:
            if scheme.state.lower() == user_profile.location.state.lower():
                relevance_score += 0.3  # State-specific scheme for user's state
        else:
            relevance_score += 0.2  # Central scheme (available everywhere)
        
        # Category preference bonus
        if user_profile.preferences.preferred_categories:
            if scheme.category in user_profile.preferences.preferred_categories:
                relevance_score += 0.2
        
        # Occupation match bonus
        if user_profile.occupation and scheme.eligibility_criteria.occupation:
            if user_profile.occupation.lower() in [
                occ.lower() for occ in scheme.eligibility_criteria.occupation
            ]:
                relevance_score += 0.1
        
        # Normalize score to 0-1 range
        relevance_score = min(1.0, relevance_score)
        
        ranked.append((scheme, result, relevance_score))
    
    # Sort by relevance score (descending)
    ranked.sort(key=lambda x: x[2], reverse=True)
    
    return ranked


def _build_scheme_response(
    scheme: Scheme,
    result: EligibilityResult,
    relevance_score: float
) -> Dict[str, Any]:
    """
    Build response object for a single eligible scheme.
    
    Args:
        scheme: Scheme object
        result: EligibilityResult
        relevance_score: Relevance score (0-1)
        
    Returns:
        Dictionary with scheme information and eligibility explanation
    """
    return {
        'scheme_id': scheme.scheme_id,
        'name': scheme.name,
        'name_translations': scheme.name_translations,
        'category': scheme.category,
        'description': scheme.description,
        'description_translations': scheme.description_translations,
        'benefits': scheme.benefits,
        'required_documents': scheme.required_documents,
        'application_process': scheme.application_process,
        'application_url': scheme.application_url,
        'department': scheme.department,
        'state': scheme.state,
        'eligibility_explanation': {
            'is_eligible': result.is_eligible,
            'reasoning': result.reasoning,
            'confidence': result.confidence
        },
        'relevance_score': round(relevance_score, 2)
    }


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
