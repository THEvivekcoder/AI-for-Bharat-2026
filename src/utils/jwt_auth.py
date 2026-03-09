"""JWT authentication middleware for Lambda functions."""

import json
import os
import logging
from typing import Dict, Any, Callable
from functools import wraps

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# JWT secret
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')


def require_jwt_auth(handler: Callable) -> Callable:
    """
    Decorator to require JWT authentication for Lambda handlers.
    Extracts user_id and email from JWT and passes them to the handler.
    """
    @wraps(handler)
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        try:
            # Get Authorization header
            headers = event.get('headers', {})
            auth_header = headers.get('Authorization') or headers.get('authorization')
            
            if not auth_header:
                return error_response(401, "Authorization header missing")
            
            # Extract token
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return error_response(401, "Invalid authorization header format")
            
            token = parts[1]
            
            # Verify and decode JWT
            payload = verify_jwt(token)
            
            if not payload:
                return error_response(401, "Invalid or expired token")
            
            # Extract user info
            user_id = payload.get('user_id')
            email = payload.get('email')
            
            if not user_id or not email:
                return error_response(401, "Invalid token payload")
            
            # Call the original handler with user info
            return handler(event, context, user_id, email)
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}", exc_info=True)
            return error_response(401, "Authentication failed")
    
    return wrapper


def verify_jwt(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token."""
    try:
        import jwt
        from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
        
    except ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"JWT verification error: {str(e)}")
        return None


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Create an error API response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps({'error': message})
    }
