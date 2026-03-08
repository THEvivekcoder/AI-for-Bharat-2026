"""Lambda handler for querying impact analytics."""

import json
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from src.core.impact_repository import ImpactRepository, DynamoDBRepositoryError

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize repository
INTERACTIONS_TABLE = os.environ.get('INTERACTIONS_TABLE', 'bharatsahayak-interactions-dev')
AWS_REGION = os.environ.get('AWS_REGION', 'ap-south-1')
impact_repo = ImpactRepository(table_name=INTERACTIONS_TABLE, region_name=AWS_REGION)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle GET /impact requests to retrieve analytics data.
    
    Query Parameters:
        start_date: Start date for filtering (ISO format: YYYY-MM-DD)
        end_date: End date for filtering (ISO format: YYYY-MM-DD)
        category: Filter by category (agriculture, health, education, employment, social_welfare)
        limit: Maximum number of events to scan (default: 10000)
    
    Response:
    {
        "metrics": {
            "total_users": 1234,
            "total_queries": 5678,
            "schemes_accessed": 890,
            "schemes_applied": 234,
            "jobs_discovered": 123,
            "facilities_located": 45,
            "success_rate": 26.29,
            "by_category": {
                "agriculture": 2000,
                "health": 1500,
                "education": 1000
            },
            "by_language": {
                "hi": 3000,
                "en": 1500,
                "mr": 1178
            }
        },
        "filters": {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "category": "agriculture"
        }
    }
    
    Note: All user data is anonymized - no PII is included in the response.
    """
    try:
        # Parse query parameters
        query_params = event.get('queryStringParameters') or {}
        
        # Parse date filters
        start_date = None
        end_date = None
        
        start_date_str = query_params.get('start_date')
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
            except ValueError:
                return error_response(400, "Invalid start_date format. Use YYYY-MM-DD")
        
        end_date_str = query_params.get('end_date')
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str)
            except ValueError:
                return error_response(400, "Invalid end_date format. Use YYYY-MM-DD")
        
        # Validate date range
        if start_date and end_date and start_date > end_date:
            return error_response(400, "start_date must be before end_date")
        
        # Parse category filter
        category = query_params.get('category')
        if category:
            valid_categories = ['agriculture', 'health', 'education', 'employment', 'social_welfare']
            if category not in valid_categories:
                return error_response(400, f"Invalid category. Must be one of: {', '.join(valid_categories)}")
        
        # Parse limit
        limit = int(query_params.get('limit', '10000'))
        if limit < 1 or limit > 50000:
            return error_response(400, "Limit must be between 1 and 50000")
        
        # Get analytics data
        logger.info(f"Fetching analytics: start_date={start_date}, end_date={end_date}, category={category}, limit={limit}")
        
        metrics = impact_repo.get_analytics_data(
            start_date=start_date,
            end_date=end_date,
            category=category,
            limit=limit
        )
        
        # Build response with filters applied
        response_data = {
            'metrics': metrics,
            'filters': {
                'start_date': start_date_str,
                'end_date': end_date_str,
                'category': category
            }
        }
        
        logger.info(f"Analytics retrieved: {metrics['total_users']} users, {metrics['total_queries']} queries")
        
        return success_response(response_data)
        
    except ValueError as e:
        logger.error(f"Invalid parameter: {str(e)}")
        return error_response(400, f"Invalid parameter: {str(e)}")
    
    except DynamoDBRepositoryError as e:
        logger.error(f"Database error: {str(e)}")
        return error_response(500, "Failed to retrieve analytics data")
    
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
