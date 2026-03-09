"""Lambda handler for fetching user dashboard data."""

import json
import os
import logging
from typing import Dict, Any
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

from src.utils.jwt_auth import require_jwt_auth

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
USERS_TABLE = os.environ.get('USERS_TABLE', 'bharatsahayak-users-dev')
SAVED_SCHEMES_TABLE = os.environ.get('SAVED_SCHEMES_TABLE', 'bharatsahayak-saved-schemes-dev')
PROFILES_TABLE = os.environ.get('PROFILES_TABLE', 'bharatsahayak-user-profiles-dev')

users_table = dynamodb.Table(USERS_TABLE)
saved_schemes_table = dynamodb.Table(SAVED_SCHEMES_TABLE)
profiles_table = dynamodb.Table(PROFILES_TABLE)


@require_jwt_auth
def lambda_handler(event: Dict[str, Any], context: Any, user_id: str, email: str) -> Dict[str, Any]:
    """
    Get dashboard data for authenticated user.
    
    GET /dashboard/data
    Headers:
        Authorization: Bearer <jwt_token>
    
    Response:
    {
        "user": {...},
        "profile": {...},
        "saved_schemes": [...],
        "stats": {
            "total_schemes": 400,
            "eligible_schemes": 12,
            "saved_schemes": 8,
            "applications_pending": 3
        }
    }
    """
    try:
        # Get user data
        user_data = get_user_data(email)
        
        # Get profile data
        profile_data = get_profile_data(user_id)
        
        # Get saved schemes
        saved_schemes = get_saved_schemes(user_id)
        
        # Calculate stats
        stats = {
            "total_schemes": 400,  # This could be dynamic from schemes table
            "eligible_schemes": len(saved_schemes),  # Simplified
            "saved_schemes": len(saved_schemes),
            "applications_pending": 0  # This would come from applications table
        }
        
        logger.info(f"Dashboard data loaded for user: {user_id}")
        
        return success_response({
            "user": user_data,
            "profile": profile_data,
            "saved_schemes": saved_schemes,
            "stats": stats
        })
        
    except Exception as e:
        logger.error(f"Error loading dashboard data: {str(e)}", exc_info=True)
        return error_response(500, "Failed to load dashboard data")


def get_user_data(email: str) -> Dict[str, Any]:
    """Get user data from users table."""
    try:
        response = users_table.get_item(Key={'email': email})
        if 'Item' in response:
            user = response['Item']
            # Remove sensitive data
            user.pop('password_hash', None)
            return user
        return {}
    except ClientError as e:
        logger.error(f"Error fetching user data: {str(e)}")
        return {}


def get_profile_data(user_id: str) -> Dict[str, Any]:
    """Get profile data from profiles table."""
    try:
        response = profiles_table.get_item(Key={'user_id': user_id})
        if 'Item' in response:
            return response['Item']
        return {}
    except ClientError as e:
        logger.error(f"Error fetching profile data: {str(e)}")
        return {}


def get_saved_schemes(user_id: str) -> list:
    """Get saved schemes for user."""
    try:
        response = saved_schemes_table.query(
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id}
        )
        return response.get('Items', [])
    except ClientError as e:
        logger.error(f"Error fetching saved schemes: {str(e)}")
        return []


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
        'body': json.dumps(data, default=str)
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
        'body': json.dumps({'error': message})
    }
