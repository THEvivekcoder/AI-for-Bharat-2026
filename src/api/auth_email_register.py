"""Lambda handler for email/password registration."""

import json
import os
import logging
import uuid
import hashlib
import hmac
import base64
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

# JWT secret (in production, use AWS Secrets Manager)
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle user registration with email and password.
    
    POST /auth/email/register
    Request body:
    {
        "email": "user@example.com",
        "password": "SecurePassword123!",
        "name": "User Name"
    }
    """
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email', '').strip().lower()
        password = body.get('password', '')
        name = body.get('name', '').strip()
        
        # Validate inputs
        if not email or not password:
            return error_response(400, "Email and password are required")
        
        if not is_valid_email(email):
            return error_response(400, "Invalid email format")
        
        if len(password) < 8:
            return error_response(400, "Password must be at least 8 characters")
        
        # Check if user already exists
        try:
            response = users_table.get_item(Key={'email': email})
            if 'Item' in response:
                return error_response(409, "User with this email already exists")
        except ClientError as e:
            logger.error(f"DynamoDB error: {str(e)}")
            return error_response(500, "Database error")
        
        # Create user
        user_id = str(uuid.uuid4())
        password_hash = hash_password(password)
        
        user_data = {
            'user_id': user_id,
            'email': email,
            'password_hash': password_hash,
            'name': name,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'profile_completed': False
        }
        
        users_table.put_item(Item=user_data)
        
        logger.info(f"User registered successfully: {user_id}")
        
        return success_response({
            "user_id": user_id,
            "email": email,
            "name": name,
            "message": "Registration successful. Please login."
        }, 201)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return error_response(500, "Internal server error")


def hash_password(password: str) -> str:
    """Hash password using PBKDF2."""
    import hashlib
    salt = os.urandom(32)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return base64.b64encode(salt + pwdhash).decode('utf-8')


def is_valid_email(email: str) -> bool:
    """Basic email validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


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
