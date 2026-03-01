"""Lambda handler for retrieving scheme details by ID."""

import json
import os
import logging
from typing import Dict, Any

from src.core.scheme_repository import SchemeRepository, ItemNotFoundError, DynamoDBRepositoryError
from src.models.scheme import Scheme

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize repository
SCHEMES_TABLE = os.environ.get('SCHEMES_TABLE', 'bharatsahayak-schemes-dev')
scheme_repo = SchemeRepository(table_name=SCHEMES_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle GET /schemes/{scheme_id} requests.
    
    Path Parameters:
        scheme_id: Unique scheme identifier
    
    Response:
    {
        "scheme_id": "...",
        "name": "...",
        "name_translations": {...},
        "category": "...",
        "description": "...",
        "description_translations": {...},
        "benefits": [...],
        "eligibility_criteria": {...},
        "required_documents": [...],
        "application_process": [...],
        "application_url": "...",
        "department": "...",
        "state": "...",
        "last_updated": "...",
        "source_url": "..."
    }
    
    Error Responses:
    - 400: Invalid scheme_id parameter
    - 404: Scheme not found
    - 500: Internal server error
    """
    try:
        # Extract scheme_id from path parameters
        path_params = event.get('pathParameters') or {}
        scheme_id = path_params.get('scheme_id')
        
        # Validate scheme_id
        if not scheme_id:
            return error_response(400, "Missing scheme_id parameter")
        
        if not scheme_id.strip():
            return error_response(400, "Invalid scheme_id: cannot be empty")
        
        # Retrieve scheme from repository
        logger.info(f"Retrieving scheme details: scheme_id={scheme_id}")
        scheme = scheme_repo.get(scheme_id)
        
        # Convert scheme to complete dictionary (all fields)
        scheme_dict = _scheme_to_dict(scheme)
        
        logger.info(f"Successfully retrieved scheme: {scheme_id}")
        return success_response(scheme_dict)
        
    except ItemNotFoundError as e:
        logger.warning(f"Scheme not found: {str(e)}")
        return error_response(404, f"Scheme not found: {scheme_id}")
    
    except DynamoDBRepositoryError as e:
        logger.error(f"Database error: {str(e)}")
        return error_response(500, "Failed to retrieve scheme details")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return error_response(500, "Internal server error")


def _scheme_to_dict(scheme: Scheme) -> Dict[str, Any]:
    """
    Convert a Scheme object to a complete dictionary with all fields.
    
    This includes:
    - Basic information (name, category, description)
    - Translations (name_translations, description_translations)
    - Benefits list
    - Complete eligibility criteria with all conditions
    - Required documents list
    - Step-by-step application process
    - Application URL and department
    - State (for state-specific schemes)
    - Last updated timestamp
    - Source URL for verification
    
    Args:
        scheme: Scheme object
        
    Returns:
        Dictionary with complete scheme information
    """
    return {
        'scheme_id': scheme.scheme_id,
        'name': scheme.name,
        'name_translations': scheme.name_translations,
        'category': scheme.category,
        'description': scheme.description,
        'description_translations': scheme.description_translations,
        'benefits': scheme.benefits,
        'eligibility_criteria': scheme.eligibility_criteria.model_dump(),
        'required_documents': scheme.required_documents,
        'application_process': scheme.application_process,
        'application_url': scheme.application_url,
        'department': scheme.department,
        'state': scheme.state,
        'last_updated': scheme.last_updated.isoformat(),
        'source_url': scheme.source_url
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
