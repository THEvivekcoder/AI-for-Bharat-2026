"""Lambda handler for user login (existing users) with OTP."""

import json
import os
import logging
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError

from src.core.user_repository import UserRepository

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize AWS clients
cognito_client = boto3.client('cognito-idp')
USER_POOL_ID = os.environ.get('USER_POOL_ID')
USER_POOL_CLIENT_ID = os.environ.get('USER_POOL_CLIENT_ID')
USERS_TABLE = os.environ.get('USERS_TABLE', 'bharatsahayak-users-dev')
AWS_REGION = os.environ.get('AWS_REGION', 'ap-south-1')

# Initialize repository
user_repo = UserRepository(table_name=USERS_TABLE, region_name=AWS_REGION)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle user login requests for existing users.
    
    POST /auth/login
    Request body:
    {
        "phone_number": "+919876543210"
    }
    
    Response:
    {
        "message": "OTP sent to phone number",
        "session": "cognito_session_token",
        "user_exists": true
    }
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        phone_number = body.get('phone_number')
        
        # Validate required fields
        if not phone_number:
            return error_response(400, "phone_number is required")
        
        # Normalize phone number
        phone_number = normalize_phone_number(phone_number)
        
        # Check if user exists
        existing_user = user_repo.get_by_phone_number(phone_number)
        
        if not existing_user:
            return error_response(404, "User not found. Please register first.")
        
        # Initiate authentication with Cognito
        try:
            # Use CUSTOM_AUTH flow for OTP
            response = cognito_client.initiate_auth(
                ClientId=USER_POOL_CLIENT_ID,
                AuthFlow='CUSTOM_AUTH',
                AuthParameters={
                    'USERNAME': phone_number
                }
            )
            
            session = response.get('Session', '')
            
            logger.info(f"OTP sent to existing user: {phone_number}")
            
            return success_response({
                "message": "OTP sent to your phone number",
                "session": session,
                "user_exists": True,
                "user_id": existing_user.user_id
            })
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"Cognito error: {error_code} - {str(e)}")
            
            if error_code == 'UserNotFoundException':
                # User exists in DynamoDB but not in Cognito
                # This is a data inconsistency issue
                logger.error(f"User exists in DB but not in Cognito: {phone_number}")
                return error_response(500, "Account error. Please contact support.")
            elif error_code == 'NotAuthorizedException':
                return error_response(401, "Account is disabled or not confirmed")
            else:
                return error_response(500, "Failed to send OTP. Please try again.")
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return error_response(400, str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return error_response(500, "Internal server error")


def normalize_phone_number(phone_number: str) -> str:
    """
    Normalize phone number to E.164 format.
    
    Args:
        phone_number: Raw phone number
        
    Returns:
        Normalized phone number with country code
    """
    # Remove spaces, dashes, and parentheses
    cleaned = phone_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    
    # Add +91 for Indian numbers if not present
    if not cleaned.startswith("+"):
        if cleaned.startswith("91") and len(cleaned) == 12:
            cleaned = "+" + cleaned
        elif len(cleaned) == 10:
            cleaned = "+91" + cleaned
        else:
            raise ValueError("Invalid phone number format")
    
    return cleaned


def success_response(data: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
    """Create a successful API response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
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
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps({
            'error': message
        })
    }
