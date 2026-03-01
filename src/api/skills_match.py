"""Lambda handler for skill program matching."""

import json
import os
import logging
import boto3
from typing import Dict, Any, List
from decimal import Decimal

from src.models.skill import SkillProgram
from src.models.eligibility import EligibilityCriteria
from src.models.location import Location
from src.models.user import UserProfile

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('SKILL_PROGRAMS_TABLE', 'SkillPrograms')
table = dynamodb.Table(table_name)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle POST /skills/match requests.
    
    Request Body:
    {
        "user_profile": {
            "age": 25,
            "education_level": "12th pass",
            "location": {"state": "Maharashtra", "district": "Pune", "pincode": "411001"},
            "interests": ["technical", "digital"],
            "current_skills": ["basic computer"],
            "preferred_mode": "hybrid"  // optional
        }
    }
    
    Response:
    {
        "matched_programs": [
            {
                "program_id": "...",
                "name": "...",
                "provider": "...",
                "category": "...",
                "match_score": 0.85,
                "match_reasons": [...]
            }
        ]
    }
    
    Error Responses:
    - 400: Invalid request body
    - 500: Internal server error
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        if 'user_profile' not in body:
            return error_response(400, "Missing required field: user_profile")
        
        user_data = body['user_profile']
        required_fields = ['age', 'education_level', 'location', 'interests']
        missing_fields = [field for field in required_fields if field not in user_data]
        
        if missing_fields:
            return error_response(400, f"Missing required fields in user_profile: {', '.join(missing_fields)}")
        
        logger.info(f"Matching skill programs for user with interests: {user_data.get('interests')}")
        
        # Get all skill programs from DynamoDB
        programs = _get_all_programs()
        
        if not programs:
            logger.warning("No skill programs found in database")
            return success_response({'matched_programs': []})
        
        # Match and rank programs
        matched_programs = _match_programs(user_data, programs)
        
        logger.info(f"Matched {len(matched_programs)} programs")
        return success_response({'matched_programs': matched_programs})
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return error_response(400, "Invalid JSON in request body")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return error_response(500, "Internal server error")


def _get_all_programs() -> List[Dict[str, Any]]:
    """Retrieve all skill programs from DynamoDB."""
    try:
        response = table.scan()
        programs = response.get('Items', [])
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            programs.extend(response.get('Items', []))
        
        logger.info(f"Retrieved {len(programs)} programs from DynamoDB")
        return programs
        
    except Exception as e:
        logger.error(f"Error retrieving programs from DynamoDB: {str(e)}")
        return []



def _match_programs(user_data: Dict[str, Any], programs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Match and rank skill programs based on user profile.
    
    Matching criteria:
    - Category matches user interests
    - User meets eligibility criteria
    - Location proximity
    - Preferred mode (if specified)
    """
    matched = []
    
    user_age = user_data.get('age')
    user_education = user_data.get('education_level', '').lower()
    user_interests = [interest.lower() for interest in user_data.get('interests', [])]
    user_location = user_data.get('location', {})
    user_state = user_location.get('state', '').lower()
    user_district = user_location.get('district', '').lower()
    preferred_mode = user_data.get('preferred_mode', '').lower()
    current_skills = [skill.lower() for skill in user_data.get('current_skills', [])]
    
    for program in programs:
        match_score = 0.0
        match_reasons = []
        
        # Convert Decimal to float for DynamoDB compatibility
        program = _convert_decimals(program)
        
        # Check category match with interests
        program_category = program.get('category', '').lower()
        if program_category in user_interests:
            match_score += 0.4
            match_reasons.append(f"Matches your interest in {program_category}")
        
        # Check eligibility
        eligibility = program.get('eligibility', {})
        is_eligible, eligibility_reason = _check_eligibility(user_age, user_education, eligibility)
        
        if not is_eligible:
            # Skip programs user is not eligible for
            continue
        
        match_score += 0.3
        match_reasons.append("You meet the eligibility criteria")
        
        # Check location match
        program_location = program.get('location', {})
        program_state = program_location.get('state', '').lower()
        program_district = program_location.get('district', '').lower()
        
        if program_state == user_state:
            match_score += 0.15
            if program_district == user_district:
                match_score += 0.1
                match_reasons.append("Program available in your district")
            else:
                match_reasons.append("Program available in your state")
        
        # Check mode preference
        program_mode = program.get('mode', '').lower()
        if preferred_mode and program_mode == preferred_mode:
            match_score += 0.05
            match_reasons.append(f"Matches your preferred {preferred_mode} mode")
        elif program_mode == 'online':
            # Online programs are accessible from anywhere
            match_score += 0.05
            match_reasons.append("Available online from anywhere")
        
        # Bonus for free programs
        if program.get('cost', 0) == 0:
            match_reasons.append("Free training program")
        
        # Bonus for placement support
        if program.get('placement_support', False):
            match_reasons.append("Includes placement assistance")
        
        # Bonus for certification
        if program.get('certification', False):
            match_reasons.append("Provides industry certification")
        
        # Only include programs with reasonable match score
        if match_score >= 0.3:
            matched.append({
                'program_id': program.get('program_id'),
                'name': program.get('name'),
                'provider': program.get('provider'),
                'category': program.get('category'),
                'description': program.get('description'),
                'duration_weeks': program.get('duration_weeks'),
                'cost': program.get('cost'),
                'location': program.get('location'),
                'mode': program.get('mode'),
                'certification': program.get('certification'),
                'placement_support': program.get('placement_support'),
                'registration_url': program.get('registration_url'),
                'contact': program.get('contact'),
                'match_score': round(match_score, 2),
                'match_reasons': match_reasons
            })
    
    # Sort by match score (descending)
    matched.sort(key=lambda x: x['match_score'], reverse=True)
    
    return matched



def _check_eligibility(user_age: int, user_education: str, eligibility: Dict[str, Any]) -> tuple:
    """
    Check if user meets eligibility criteria.
    
    Returns:
        Tuple of (is_eligible: bool, reason: str)
    """
    # Check age
    age_min = eligibility.get('age_min')
    age_max = eligibility.get('age_max')
    
    if age_min and user_age < age_min:
        return False, f"Minimum age requirement is {age_min}"
    
    if age_max and user_age > age_max:
        return False, f"Maximum age limit is {age_max}"
    
    # Check education
    eligible_education = eligibility.get('education', [])
    if eligible_education:
        # Normalize education levels
        education_hierarchy = {
            'primary': 1,
            '8th pass': 2,
            '10th pass': 3,
            'secondary': 3,
            '12th pass': 4,
            'higher_secondary': 4,
            'undergraduate': 5,
            'postgraduate': 6
        }
        
        user_level = education_hierarchy.get(user_education, 0)
        
        # Check if user meets any of the eligible education levels
        meets_education = False
        for edu in eligible_education:
            edu_normalized = edu.lower()
            required_level = education_hierarchy.get(edu_normalized, 0)
            if user_level >= required_level:
                meets_education = True
                break
        
        if not meets_education:
            return False, f"Required education: {', '.join(eligible_education)}"
    
    return True, "Eligible"


def _convert_decimals(obj: Any) -> Any:
    """Convert Decimal objects to float for JSON serialization."""
    if isinstance(obj, list):
        return [_convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: _convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj


def success_response(data: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
    """Generate success response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(data)
    }


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Generate error response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'error': message})
    }
