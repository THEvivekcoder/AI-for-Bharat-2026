"""Authorization middleware for JWT token verification."""

import os
import logging
from typing import Dict, Any, Optional
import jwt
from functools import wraps

logger = logging.getLogger()

JWT_SECRET = os.environ.get('JWT_SECRET', 'bharatsahayak-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        jwt.InvalidTokenError: If token is invalid or expired
    """
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        # Decode and verify token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        raise
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {str(e)}")
        raise


def extract_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user ID from JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        User ID if token is valid, None otherwise
    """
    try:
        payload = verify_jwt_token(token)
        return payload.get('user_id')
    except jwt.InvalidTokenError:
        return None


def get_authorization_header(event: Dict[str, Any]) -> Optional[str]:
    """
    Extract authorization header from API Gateway event.
    
    Args:
        event: API Gateway event
        
    Returns:
        Authorization header value or None
    """
    headers = event.get('headers', {})
    
    # Check both 'Authorization' and 'authorization' (case-insensitive)
    auth_header = headers.get('Authorization') or headers.get('authorization')
    
    return auth_header


def extract_user_id(event: Dict[str, Any]) -> Optional[str]:
    """
    Extract user ID from API Gateway event JWT token.
    
    Args:
        event: API Gateway event
        
    Returns:
        User ID if token is valid, None otherwise
    """
    auth_header = get_authorization_header(event)
    
    if not auth_header:
        return None
    
    return extract_user_id_from_token(auth_header)


def require_auth(handler_func):
    """
    Decorator to require authentication for Lambda handlers.
    
    Usage:
        @require_auth
        def lambda_handler(event, context, user_id):
            # user_id is automatically extracted from token
            pass
    """
    @wraps(handler_func)
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        try:
            # Extract authorization header
            auth_header = get_authorization_header(event)
            
            if not auth_header:
                return unauthorized_response("Missing authorization header")
            
            # Verify token and extract user ID
            payload = verify_jwt_token(auth_header)
            user_id = payload.get('user_id')
            
            if not user_id:
                return unauthorized_response("Invalid token: missing user_id")
            
            # Call the original handler with user_id
            return handler_func(event, context, user_id)
            
        except jwt.ExpiredSignatureError:
            return unauthorized_response("Token has expired")
        except jwt.InvalidTokenError:
            return unauthorized_response("Invalid token")
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}", exc_info=True)
            return error_response(500, "Internal server error")
    
    return wrapper


def unauthorized_response(message: str) -> Dict[str, Any]:
    """Create an unauthorized (401) response."""
    import json
    return {
        'statusCode': 401,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': message
        })
    }


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Create an error API response."""
    import json
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
