"""Lambda handler for matching skill development programs to user profile."""

import json
import os
import logging
from typing import Dict, Any, List, Tuple

import boto3
from botocore.exceptions import ClientError

from src.models.skill import SkillProgram
from src.models.user import UserProfile
from src.models.location import Location
from src.models.eligibility import EligibilityCriteria

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
PROGRAMS_TABLE = os.environ.get('SKILL_PROGRAMS_TABLE', 'bharatsahayak-skill-programs-dev')
programs_table = dynamodb.Table(PROGRAMS_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle POST /skills/match requests.
    
    Matches skill development programs based on user education, interests, and location.
    
    Request Body:
    {
        "user_profile": {
            "user_id": "user_123",
            "education_level": "10th pass",
            "location": {
                "state": "Maharashtra",
                "district": "Pune",
                "pincode": "411014"
            },
            "age": 25,
            "preferences": {
                "interests": ["technical", "digital"],
                "max_cost": 5000,
                "preferred_mode": "in-person"
            }
        },
        "category": "technical",  // Optional filter
        "limit": 10  // Optional: max results (default 10)
    }
    
    Response:
    {
        "matched_programs": [
            {
                "program_id": "PMKVY-ELEC-2024",
                "name": "Electrician Training Program",
                "provider": "NSDC",
                "category": "technical",
                "description": "...",
                "duration_weeks": 12,
                "cost": 0,
                "location": {...},
                "mode": "in-person",
                "certification": true,
                "placement_support": true,
                "match_score": 0.85,
                "match_reasoning": [
                    "Matches interest: technical",
                    "Within budget: Rs. 0",
                    "Preferred mode: in-person"
                ]
            }
        ],
        "total_count": 5
    }
    """
    try:
        # Parse request body
        body = _parse_request_body(event)
        if isinstance(body, dict) and 'error' in body:
            return error_response(400, body['error'])
        
        # Extract required fields
        user_profile_data = body.get('user_profile')
        category_filter = body.get('category')
        limit = body.get('limit', 10)
        
        if not user_profile_data:
            return error_response(400, "Missing required field: user_profile")
        
        # Validate limit
        if not isinstance(limit, int) or limit < 1 or limit > 50:
            return error_response(400, "Invalid limit: must be between 1 and 50")
        
        # Parse user profile
        try:
            user_profile = _parse_user_profile(user_profile_data)
        except ValueError as e:
            return error_response(400, f"Invalid user_profile: {str(e)}")
        
        logger.info(f"Matching programs: user_id={user_profile.user_id}, category={category_filter}")
        
        # Retrieve programs from DynamoDB
        programs = _get_programs(category_filter)
        logger.info(f"Retrieved {len(programs)} programs")
        
        # Match and rank programs
        matched_programs = _match_programs(programs, user_profile)
        logger.info(f"Matched {len(matched_programs)} programs")
        
        # Limit results
        matched_programs = matched_programs[:limit]
        
        # Build response
        response_data = {
            'matched_programs': [
                _build_program_response(program, score, reasoning)
                for program, score, reasoning in matched_programs
            ],
            'total_count': len(matched_programs)
        }
        
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return error_response(500, "Internal server error")



def _parse_request_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """Parse and validate request body from API Gateway event."""
    try:
        body = event.get('body')
        if not body:
            return {'error': 'Request body is required'}
        
        if isinstance(body, str):
            body = json.loads(body)
        
        return body
    except json.JSONDecodeError as e:
        return {'error': f'Invalid JSON in request body: {str(e)}'}


def _parse_user_profile(profile_data: Dict[str, Any]) -> UserProfile:
    """Parse and validate user profile data."""
    try:
        location_data = profile_data.get('location')
        if not location_data:
            raise ValueError("Missing required field: location")
        
        location = Location(**location_data)
        profile_data['location'] = location
        user_profile = UserProfile(**profile_data)
        
        return user_profile
    except Exception as e:
        raise ValueError(f"Failed to parse user profile: {str(e)}")


def _get_programs(category: str = None) -> List[SkillProgram]:
    """Retrieve skill programs from DynamoDB."""
    try:
        if category:
            # Query by category using GSI
            response = programs_table.query(
                IndexName='category-index',
                KeyConditionExpression='category = :cat',
                ExpressionAttributeValues={':cat': category}
            )
        else:
            # Scan all programs
            response = programs_table.scan()
        
        items = response.get('Items', [])
        
        # Convert to SkillProgram objects
        programs = []
        for item in items:
            try:
                # Convert nested dicts to model objects
                item['location'] = Location(**item['location'])
                item['eligibility_criteria'] = EligibilityCriteria(**item['eligibility_criteria'])
                program = SkillProgram(**item)
                programs.append(program)
            except Exception as e:
                logger.warning(f"Failed to parse program {item.get('program_id')}: {e}")
                continue
        
        return programs
        
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        raise


def _match_programs(
    programs: List[SkillProgram],
    user_profile: UserProfile
) -> List[Tuple[SkillProgram, float, List[str]]]:
    """
    Match and rank programs based on user profile.
    
    Matching criteria:
    - Education level compatibility
    - Interest/category match
    - Cost within budget
    - Location proximity
    - Age eligibility
    - Preferred mode
    
    Returns:
        List of (program, match_score, reasoning) tuples, sorted by score
    """
    matched = []
    
    for program in programs:
        score = 0.0
        reasoning = []
        
        # Check basic eligibility
        if not _check_eligibility(program, user_profile):
            continue  # Skip ineligible programs
        
        # Interest/category match (30% weight)
        if user_profile.preferences and user_profile.preferences.interests:
            if program.category in user_profile.preferences.interests:
                score += 0.3
                reasoning.append(f"Matches interest: {program.category}")
        
        # Cost within budget (25% weight)
        max_cost = None
        if user_profile.preferences and hasattr(user_profile.preferences, 'max_cost'):
            max_cost = user_profile.preferences.max_cost
        
        if max_cost is not None:
            if program.cost <= max_cost:
                score += 0.25
                reasoning.append(f"Within budget: Rs. {program.cost}")
            else:
                score += 0.1  # Partial credit if over budget
                reasoning.append(f"Cost Rs. {program.cost} exceeds budget")
        else:
            # No budget specified, prefer free programs
            if program.cost == 0:
                score += 0.25
                reasoning.append("Free program")
            else:
                score += 0.15
        
        # Location match (20% weight)
        if program.location.state.lower() == user_profile.location.state.lower():
            score += 0.15
            reasoning.append(f"Same state: {program.location.state}")
            
            if program.location.district.lower() == user_profile.location.district.lower():
                score += 0.05
                reasoning.append(f"Same district: {program.location.district}")
        
        # Mode preference (15% weight)
        preferred_mode = None
        if user_profile.preferences and hasattr(user_profile.preferences, 'preferred_mode'):
            preferred_mode = user_profile.preferences.preferred_mode
        
        if preferred_mode:
            if program.mode == preferred_mode:
                score += 0.15
                reasoning.append(f"Preferred mode: {program.mode}")
        else:
            # No preference, slight bonus for online (more accessible)
            if program.mode == "online":
                score += 0.1
                reasoning.append("Online mode (accessible)")
        
        # Placement support bonus (10% weight)
        if program.placement_support:
            score += 0.1
            reasoning.append("Placement support available")
        
        # Normalize score to 0-1
        score = min(1.0, score)
        
        if score > 0:  # Only include programs with some match
            matched.append((program, score, reasoning))
    
    # Sort by match score (descending)
    matched.sort(key=lambda x: x[1], reverse=True)
    
    return matched


def _check_eligibility(program: SkillProgram, user_profile: UserProfile) -> bool:
    """Check if user meets basic eligibility criteria for program."""
    criteria = program.eligibility_criteria
    
    # Check age
    if criteria.age_min and user_profile.age:
        if user_profile.age < criteria.age_min:
            return False
    
    if criteria.age_max and user_profile.age:
        if user_profile.age > criteria.age_max:
            return False
    
    # Check education level
    if criteria.education and user_profile.education_level:
        # Simple check: if user's education is in the list, they're eligible
        if user_profile.education_level not in criteria.education:
            return False
    
    # Check gender
    if criteria.gender and user_profile.gender:
        if criteria.gender.lower() != user_profile.gender.lower():
            return False
    
    return True


def _build_program_response(
    program: SkillProgram,
    match_score: float,
    reasoning: List[str]
) -> Dict[str, Any]:
    """Build response object for a matched program."""
    return {
        'program_id': program.program_id,
        'name': program.name,
        'provider': program.provider,
        'category': program.category,
        'description': program.description,
        'duration_weeks': program.duration_weeks,
        'cost': program.cost,
        'location': {
            'state': program.location.state,
            'district': program.location.district,
            'pincode': program.location.pincode
        },
        'mode': program.mode,
        'certification': program.certification,
        'placement_support': program.placement_support,
        'registration_url': program.registration_url,
        'contact': program.contact,
        'match_score': round(match_score, 2),
        'match_reasoning': reasoning
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
