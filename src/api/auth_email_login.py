"""Lambda handler for email/password login with JWT."""

import json
import os
import logging
import hashlib
import base64
import hmac
from typing import Dict, Any
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
USERS_TABLE = os.environ.get('USERS_TABLE', 'bharatsahayak-users-dev')
users_table = dynamodb.Table(USERS_TABLE)

# JWT secret
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle user login with email and password.
    
    POST /auth/email/login
    Request body:
    {
        "email": "user@example.com",
        "password": "SecurePassword123!"
    }
    
    Response:
    {
        "access_token": "jwt_token",
        "user_id": "uuid",
        "email": "user@example.com",
        "name": "User Name"
    }
    """
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email', '').strip().lower()
        password = body.get('password', '')
        
        # Validate inputs
        if not email or not password:
            return error_response(400, "Email and password are required")
        
        # Get user from database
        try:
            response = users_table.get_item(Key={'email': email})
            if 'Item' not in response:
                return error_response(401, "Invalid email or password")
            
            user = response['Item']
        except ClientError as e:
            logger.error(f"DynamoDB error: {str(e)}")
            return error_response(500, "Database error")
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            return error_response(401, "Invalid email or password")
        
        # Generate JWT token
        token = generate_jwt(user['user_id'], email)
        
        # Update last login
        try:
            users_table.update_item(
                Key={'email': email},
                UpdateExpression='SET last_login = :login_time',
                ExpressionAttributeValues={':login_time': datetime.utcnow().isoformat()}
            )
        except Exception as e:
            logger.warning(f"Failed to update last login: {str(e)}")
        
        logger.info(f"User logged in successfully: {user['user_id']}")
        
        return success_response({
            "access_token": token,
            "user_id": user['user_id'],
            "email": user['email'],
            "name": user.get('name', ''),
            "profile_completed": user.get('profile_completed', False)
        })
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return error_response(500, "Internal server error")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    try:
        decoded = base64.b64decode(password_hash.encode('utf-8'))
        salt = decoded[:32]
        stored_hash = decoded[32:]
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return hmac.compare_digest(pwdhash, stored_hash)
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False


def generate_jwt(user_id: str, email: str) -> str:
    """Generate JWT token."""
    import jwt
    
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    return token


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
        'body': json.dumps({'error': message})
    }
