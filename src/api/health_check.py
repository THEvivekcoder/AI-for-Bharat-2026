"""Lambda handler for health symptom checking."""

import json
import os
import logging
from typing import Dict, Any, List

from src.services.health_advisor import HealthAdvisor

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize health advisor
health_advisor = HealthAdvisor()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle POST /health/check requests.
    
    Request Body:
    {
        "symptoms": ["fever", "cough", "headache"],
        "user_info": {
            "age": 35,
            "gender": "male"
        }
    }
    
    Response:
    {
        "urgency_level": "soon",
        "possible_conditions": ["Common cold", "Viral fever"],
        "self_care_recommendations": [...],
        "when_to_seek_care": "...",
        "red_flags": [...],
        "disclaimer": "...",
        "confidence": 0.75
    }
    
    Error Responses:
    - 400: Invalid request body
    - 500: Internal server error
    """
    try:
        # Parse request body
        body = event.get('body')
        if not body:
            return error_response(400, "Request body is required")
        
        try:
            if isinstance(body, str):
                data = json.loads(body)
            else:
                data = body
        except json.JSONDecodeError:
            return error_response(400, "Invalid JSON in request body")
        
        # Extract symptoms
        symptoms = data.get('symptoms', [])
        
        if not isinstance(symptoms, list):
            return error_response(400, "symptoms must be a list")
        
        # Validate symptoms
        if not symptoms:
            return error_response(400, "At least one symptom is required")
        
        # Validate each symptom is a string
        for i, symptom in enumerate(symptoms):
            if not isinstance(symptom, str):
                return error_response(400, f"Symptom {i} must be a string")
            if not symptom.strip():
                return error_response(400, f"Symptom {i} cannot be empty")
        
        # Extract optional user info
        user_info = data.get('user_info', {})
        
        logger.info(f"Analyzing symptoms: {symptoms}")
        
        # Analyze symptoms
        guidance = health_advisor.analyze_symptoms(symptoms, user_info)
        
        # Convert to response format
        response_data = guidance.model_dump()
        
        logger.info(f"Generated guidance with urgency level: {guidance.urgency_level}")
        return success_response(response_data)
        
    except ValueError as e:
        logger.error(f"Invalid parameter value: {str(e)}")
        return error_response(400, f"Invalid parameter value: {str(e)}")
    
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
