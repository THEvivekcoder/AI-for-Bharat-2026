"""Lambda handler for searching government schemes."""

import json
import os
import logging
from typing import Dict, Any, Optional

from src.core.scheme_repository import SchemeRepository, SchemeFilters, DynamoDBRepositoryError
from src.models.scheme import Scheme

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize repository
SCHEMES_TABLE = os.environ.get('SCHEMES_TABLE', 'bharatsahayak-schemes-dev')
scheme_repo = SchemeRepository(table_name=SCHEMES_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle GET /schemes requests with query parameters.
    
    Query Parameters:
        q: Keyword search query (searches in name and description)
        category: Filter by category (agriculture, health, education, employment, social_welfare)
        state: Filter by state (empty string or omit for central schemes)
        department: Filter by government department
        lang: Language code for translated content (hi, ta, te, bn). Falls back to English if unavailable.
        page: Page number for pagination (default: 1)
        limit: Results per page (default: 20, max: 100)
    
    Response:
    {
        "schemes": [
            {
                "scheme_id": "...",
                "name": "...",
                "category": "...",
                "description": "...",
                "department": "...",
                "state": "...",
                ...
            }
        ],
        "pagination": {
            "page": 1,
            "limit": 20,
            "total": 45,
            "has_more": true
        }
    }
    """
    try:
        # Parse query parameters
        query_params = event.get('queryStringParameters') or {}
        
        # Extract search query
        search_query = query_params.get('q')
        
        # Extract filters
        category = query_params.get('category')
        state = query_params.get('state')
        department = query_params.get('department')
        
        # Extract language parameter
        language = query_params.get('lang', 'en')
        
        # Extract pagination parameters
        page = int(query_params.get('page', '1'))
        limit = int(query_params.get('limit', '20'))
        
        # Validate pagination parameters
        if page < 1:
            return error_response(400, "Page number must be >= 1")
        
        if limit < 1 or limit > 100:
            return error_response(400, "Limit must be between 1 and 100")
        
        # Build filters
        filters = SchemeFilters(
            category=category,
            state=state,
            department=department
        )
        
        # Calculate fetch limit (fetch more to support pagination)
        # Since DynamoDB doesn't support offset-based pagination efficiently,
        # we'll fetch up to page * limit items and slice
        fetch_limit = page * limit
        
        # Search schemes
        logger.info(f"Searching schemes: query={search_query}, filters={filters.__dict__}, limit={fetch_limit}")
        all_schemes = scheme_repo.search_schemes(
            query=search_query,
            filters=filters,
            limit=fetch_limit
        )
        
        # Calculate pagination
        total_fetched = len(all_schemes)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        # Slice results for current page
        page_schemes = all_schemes[start_idx:end_idx]
        
        # Convert schemes to summary format (exclude some verbose fields)
        scheme_summaries = [
            _scheme_to_summary(scheme, language) for scheme in page_schemes
        ]
        
        # Build pagination metadata
        pagination = {
            'page': page,
            'limit': limit,
            'total': total_fetched,
            'has_more': end_idx < total_fetched
        }
        
        logger.info(f"Found {len(scheme_summaries)} schemes for page {page}")
        
        return success_response({
            'schemes': scheme_summaries,
            'pagination': pagination
        })
        
    except ValueError as e:
        logger.error(f"Invalid parameter: {str(e)}")
        return error_response(400, f"Invalid parameter: {str(e)}")
    
    except DynamoDBRepositoryError as e:
        logger.error(f"Database error: {str(e)}")
        return error_response(500, "Failed to search schemes")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return error_response(500, "Internal server error")


def _scheme_to_summary(scheme: Scheme, language: str = 'en') -> Dict[str, Any]:
    """
    Convert a Scheme object to a summary dictionary.
    Excludes verbose fields like translations and detailed application process.
    
    If a language is specified and translations are available, the name and description
    will be replaced with the translated versions. Falls back to English if translation unavailable.
    
    Args:
        scheme: Scheme object
        language: Language code for translated content (default: 'en')
        
    Returns:
        Dictionary with scheme summary
    """
    # Get translated name and description if available
    name = scheme.name_translations.get(language, scheme.name) if language != 'en' else scheme.name
    description = scheme.description_translations.get(language, scheme.description) if language != 'en' else scheme.description
    
    return {
        'scheme_id': scheme.scheme_id,
        'name': name,
        'category': scheme.category,
        'description': description,
        'department': scheme.department,
        'state': scheme.state,
        'benefits': scheme.benefits,
        'application_url': scheme.application_url,
        'last_updated': scheme.last_updated.isoformat()
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
