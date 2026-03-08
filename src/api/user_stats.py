"""Lambda handler for getting user statistics."""

import json
import os
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError

from src.utils.auth_middleware import extract_user_id

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
PROFILES_TABLE = os.environ.get('PROFILES_TABLE', 'bharatsahayak-user-profiles-dev')
INTERACTIONS_TABLE = os.environ.get('INTERACTIONS_TABLE', 'bharatsahayak-interactions-dev')

profiles_table = dynamodb.Table(PROFILES_TABLE)
interactions_table = dynamodb.Table(INTERACTIONS_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle user statistics requests.
    
    GET /user/stats
    
    Response:
    {
        "schemes_viewed": 15,
        "schemes_applied": 3,
        "queries_made": 25,
        "last_active": "2024-01-20T10:00:00Z",
        "member_since": "2024-01-01T00:00:00Z",
        "eligible_schemes_count": 8,
        "profile_completion": 85
    }
    """
    try:
        # Extract user ID from JWT token
        user_id = extract_user_id(event)
        if not user_id:
            return error_response(401, "Authentication required")
        
        logger.info(f"Getting stats for user: {user_id}")
        
        # Get user profile
        try:
            profile_response = profiles_table.get_item(Key={'user_id': user_id})
            profile = profile_response.get('Item')
            
            if not profile:
                return error_response(404, "User profile not found")
        except ClientError as e:
            logger.error(f"Error getting profile: {str(e)}")
            return error_response(500, "Failed to get user profile")
        
        # Calculate profile completion
        profile_completion = calculate_profile_completion(profile)
        
        # Get interaction statistics
        stats = get_interaction_stats(user_id)
        
        # Get member since date
        member_since = profile.get('created_at', datetime.utcnow().isoformat())
        
        # Build response
        response_data = {
            "schemes_viewed": stats.get('schemes_viewed', 0),
            "schemes_applied": stats.get('schemes_applied', 0),
            "queries_made": stats.get('queries_made', 0),
            "last_active": stats.get('last_active', datetime.utcnow().isoformat()),
            "member_since": member_since,
            "eligible_schemes_count": stats.get('eligible_schemes_count', 0),
            "profile_completion": profile_completion,
            "total_interactions": stats.get('total_interactions', 0),
            "voice_queries": stats.get('voice_queries', 0),
            "text_queries": stats.get('text_queries', 0)
        }
        
        logger.info(f"Stats retrieved successfully for user: {user_id}")
        
        return success_response(response_data)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return error_response(500, "Internal server error")


def calculate_profile_completion(profile: Dict[str, Any]) -> int:
    """
    Calculate profile completion percentage.
    
    Args:
        profile: User profile dictionary
        
    Returns:
        Completion percentage (0-100)
    """
    required_fields = [
        'phone_number',
        'language',
        'location',
        'age',
        'gender',
        'education_level',
        'occupation',
        'income_bracket',
        'household_size'
    ]
    
    completed_fields = 0
    for field in required_fields:
        if field in profile and profile[field]:
            if field == 'location':
                # Check if location has required sub-fields
                location = profile[field]
                if isinstance(location, dict):
                    if location.get('state') and location.get('district') and location.get('pincode'):
                        completed_fields += 1
            else:
                completed_fields += 1
    
    return int((completed_fields / len(required_fields)) * 100)


def get_interaction_stats(user_id: str) -> Dict[str, Any]:
    """
    Get user interaction statistics from DynamoDB.
    
    Args:
        user_id: User's unique identifier
        
    Returns:
        Dictionary with interaction statistics
    """
    try:
        # Query interactions for the last 30 days
        thirty_days_ago = int((datetime.utcnow() - timedelta(days=30)).timestamp())
        
        response = interactions_table.query(
            KeyConditionExpression='user_id = :uid AND #ts >= :start_time',
            ExpressionAttributeNames={
                '#ts': 'timestamp'
            },
            ExpressionAttributeValues={
                ':uid': user_id,
                ':start_time': thirty_days_ago
            }
        )
        
        interactions = response.get('Items', [])
        
        # Calculate statistics
        stats = {
            'total_interactions': len(interactions),
            'schemes_viewed': 0,
            'schemes_applied': 0,
            'queries_made': 0,
            'voice_queries': 0,
            'text_queries': 0,
            'eligible_schemes_count': 0,
            'last_active': None
        }
        
        for interaction in interactions:
            interaction_type = interaction.get('interaction_type', '')
            
            if interaction_type == 'scheme_viewed':
                stats['schemes_viewed'] += 1
            elif interaction_type == 'scheme_applied':
                stats['schemes_applied'] += 1
            elif interaction_type == 'query':
                stats['queries_made'] += 1
                if interaction.get('query_type') == 'voice':
                    stats['voice_queries'] += 1
                else:
                    stats['text_queries'] += 1
            elif interaction_type == 'eligible_schemes_checked':
                stats['eligible_schemes_count'] = interaction.get('count', 0)
            
            # Update last active
            timestamp = interaction.get('timestamp', 0)
            if not stats['last_active'] or timestamp > stats['last_active']:
                stats['last_active'] = timestamp
        
        # Convert last_active timestamp to ISO format
        if stats['last_active']:
            stats['last_active'] = datetime.fromtimestamp(stats['last_active']).isoformat() + 'Z'
        
        return stats
        
    except ClientError as e:
        logger.error(f"Error querying interactions: {str(e)}")
        return {
            'total_interactions': 0,
            'schemes_viewed': 0,
            'schemes_applied': 0,
            'queries_made': 0,
            'voice_queries': 0,
            'text_queries': 0,
            'eligible_schemes_count': 0,
            'last_active': None
        }
    except Exception as e:
        logger.error(f"Unexpected error in get_interaction_stats: {str(e)}")
        return {
            'total_interactions': 0,
            'schemes_viewed': 0,
            'schemes_applied': 0,
            'queries_made': 0,
            'voice_queries': 0,
            'text_queries': 0,
            'eligible_schemes_count': 0,
            'last_active': None
        }


def success_response(data: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
    """Create a successful API response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps(data)
    }


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Create an error API response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps({
            'error': message
        })
    }
