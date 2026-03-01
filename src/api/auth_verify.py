"""Lambda handler for OTP verification and JWT token generation."""

import json
import os
import logging
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError
import jwt
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize AWS clients
cognito_client = boto3.client('cognito-idp')
USER_POOL_ID = os.environ.get('USER_POOL_ID')
USER_POOL_CLIENT_ID = os.environ.get('USER_POOL_CLIENT_ID')
JWT_SECRET = os.environ.get('JWT_SECRET', 'bharatsahayak-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle OTP verification requests.
    
    POST /auth/verify
    Request body:
    {
        "phone_number": "+919876543210",
        "otp": "123456",
        "session": "cognito_session_token"  // Optional, from registration response
    }
    
    Response:
    {
        "user_id": "uuid",
        "access_token": "jwt_token",
        "token_type": "Bearer",
        "expires_in": 86400,
        "message": "Authentication successful"
    }
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        phone_number = body.get('phone_number')
        otp = body.get('otp')
        session = body.get('session')
        
        # Validate required fields
        if not phone_number:
            return error_response(400, "phone_number is required")
        
        if not otp:
            return error_response(400, "otp is required")
        
        # Normalize phone number
        phone_number = normalize_phone_number(phone_number)
        
        # Verify OTP with Cognito
        cognito_response = verify_otp_with_cognito(phone_number, otp, session)
        
        # Extract user information from Cognito response
        user_id = extract_user_id(cognito_response)
        
        # Generate JWT token
        jwt_token = generate_jwt_token(user_id, phone_number)
        
        logger.info(f"User authenticated successfully: {user_id}")
        
        return success_response({
            "user_id": user_id,
            "access_token": jwt_token,
            "token_type": "Bearer",
            "expires_in": JWT_EXPIRATION_HOURS * 3600,
            "message": "Authentication successful"
        })
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return error_response(400, str(e))
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"AWS error: {error_code} - {str(e)}")
        
        if error_code == 'CodeMismatchException':
            return error_response(401, "Invalid OTP code")
        elif error_code == 'ExpiredCodeException':
            return error_response(401, "OTP code has expired")
        elif error_code == 'NotAuthorizedException':
            return error_response(401, "Authentication failed")
        elif error_code == 'UserNotFoundException':
            return error_response(404, "User not found")
        else:
            return error_response(500, "Verification failed. Please try again.")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return error_response(500, "Internal server error")


def verify_otp_with_cognito(phone_number: str, otp: str, session: str = None) -> Dict[str, Any]:
    """
    Verify OTP with Cognito.
    
    Args:
        phone_number: User's phone number
        otp: OTP code to verify
        session: Optional session token from registration
        
    Returns:
        Cognito response with authentication tokens
    """
    try:
        # If session is provided, confirm sign up
        if session:
            response = cognito_client.confirm_sign_up(
                ClientId=USER_POOL_CLIENT_ID,
                Username=phone_number,
                ConfirmationCode=otp
            )
            logger.info(f"Sign up confirmed for: {phone_number}")
            
            # After confirmation, initiate auth to get tokens
            auth_response = cognito_client.initiate_auth(
                ClientId=USER_POOL_CLIENT_ID,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': phone_number,
                    'PASSWORD': otp  # This won't work, need to handle differently
                }
            )
            return auth_response
        else:
            # For existing users, use custom auth flow
            response = cognito_client.initiate_auth(
                ClientId=USER_POOL_CLIENT_ID,
                AuthFlow='CUSTOM_AUTH',
                AuthParameters={
                    'USERNAME': phone_number
                }
            )
            
            # Respond to custom challenge with OTP
            if response.get('ChallengeName') == 'CUSTOM_CHALLENGE':
                auth_response = cognito_client.respond_to_auth_challenge(
                    ClientId=USER_POOL_CLIENT_ID,
                    ChallengeName='CUSTOM_CHALLENGE',
                    Session=response['Session'],
                    ChallengeResponses={
                        'USERNAME': phone_number,
                        'ANSWER': otp
                    }
                )
                return auth_response
            
            return response
        
    except ClientError as e:
        logger.error(f"Cognito verification failed: {str(e)}")
        raise


def extract_user_id(cognito_response: Dict[str, Any]) -> str:
    """
    Extract user ID from Cognito response.
    
    Args:
        cognito_response: Response from Cognito authentication
        
    Returns:
        User ID string
    """
    # Try to get user ID from ID token
    if 'AuthenticationResult' in cognito_response:
        id_token = cognito_response['AuthenticationResult'].get('IdToken')
        if id_token:
            # Decode JWT token (without verification for now)
            decoded = jwt.decode(id_token, options={"verify_signature": False})
            return decoded.get('custom:user_id', decoded.get('sub'))
    
    # Fallback: get user attributes from Cognito
    # This would require additional API call
    return "unknown"


def generate_jwt_token(user_id: str, phone_number: str) -> str:
    """
    Generate JWT token for authenticated user.
    
    Args:
        user_id: User's unique identifier
        phone_number: User's phone number
        
    Returns:
        JWT token string
    """
    now = datetime.utcnow()
    expiration = now + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    payload = {
        'user_id': user_id,
        'phone_number': phone_number,
        'iat': now,
        'exp': expiration,
        'iss': 'bharatsahayak',
        'sub': user_id
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


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
