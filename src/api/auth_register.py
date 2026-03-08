"""Lambda handler for user registration with Cognito and DynamoDB."""

import json
import os
import logging
import uuid
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError

from src.models.user import UserProfile
from src.models.location import Location
from src.core.user_repository import UserRepository
from src.core.profile_repository import ProfileRepository

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize AWS clients
cognito_client = boto3.client('cognito-idp')
USER_POOL_ID = os.environ.get('USER_POOL_ID')
USERS_TABLE = os.environ.get('USERS_TABLE', 'bharatsahayak-users-dev')
PROFILES_TABLE = os.environ.get('PROFILES_TABLE', 'bharatsahayak-user-profiles-dev')
AWS_REGION = os.environ.get('AWS_REGION', 'ap-south-1')

# Initialize repositories
user_repo = UserRepository(table_name=USERS_TABLE, region_name=AWS_REGION)
profile_repo = ProfileRepository(table_name=PROFILES_TABLE, region_name=AWS_REGION)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle user registration requests.
    
    POST /auth/register
    Request body:
    {
        "phone_number": "+919876543210",
        "language": "hi",
        "location": {
            "state": "Maharashtra",
            "district": "Pune",
            "pincode": "411014"
        }
    }
    
    Response:
    {
        "user_id": "uuid",
        "message": "OTP sent to phone number",
        "session": "cognito_session_token"
    }
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        phone_number = body.get('phone_number')
        language = body.get('language', 'hi')
        location_data = body.get('location', {})
        
        # Validate required fields
        if not phone_number:
            return error_response(400, "phone_number is required")
        
        if not location_data.get('state') or not location_data.get('district') or not location_data.get('pincode'):
            return error_response(400, "location with state, district, and pincode is required")
        
        # Normalize phone number
        phone_number = normalize_phone_number(phone_number)
        
        # Check if user already exists
        existing_user = user_repo.get_by_phone_number(phone_number)
        if existing_user:
            return error_response(409, "User with this phone number already exists")
        
        # Create user in Cognito
        user_id = str(uuid.uuid4())
        cognito_response = create_cognito_user(phone_number, user_id, language)
        
        # Create location object
        location = Location(
            state=location_data['state'],
            district=location_data['district'],
            block=location_data.get('block'),
            village=location_data.get('village'),
            pincode=location_data['pincode'],
            latitude=location_data.get('latitude'),
            longitude=location_data.get('longitude')
        )
        
        # Create user profile
        user_profile = UserProfile(
            user_id=user_id,
            phone_number=phone_number,
            language=language,
            location=location,
            age=body.get('age'),
            gender=body.get('gender'),
            education_level=body.get('education_level'),
            occupation=body.get('occupation'),
            income_bracket=body.get('income_bracket'),
            household_size=body.get('household_size')
        )
        
        # Store user profile in DynamoDB (both tables)
        user_repo.create(user_profile)
        profile_repo.create_profile(user_profile)
        
        logger.info(f"User registered successfully: {user_id}")
        
        return success_response({
            "user_id": user_id,
            "message": "OTP sent to phone number. Please verify to complete registration.",
            "session": cognito_response.get('Session', '')
        })
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return error_response(400, str(e))
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"AWS error: {error_code} - {str(e)}")
        
        if error_code == 'UsernameExistsException':
            return error_response(409, "User already exists")
        elif error_code == 'InvalidParameterException':
            return error_response(400, "Invalid phone number format")
        else:
            return error_response(500, "Registration failed. Please try again.")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return error_response(500, "Internal server error")


def create_cognito_user(phone_number: str, user_id: str, language: str) -> Dict[str, Any]:
    """
    Create user in Cognito and send OTP.
    
    Args:
        phone_number: User's phone number
        user_id: Generated user ID
        language: User's preferred language
        
    Returns:
        Cognito response with session token
    """
    try:
        response = cognito_client.sign_up(
            ClientId=os.environ.get('USER_POOL_CLIENT_ID'),
            Username=phone_number,
            Password=generate_temp_password(),
            UserAttributes=[
                {'Name': 'phone_number', 'Value': phone_number},
                {'Name': 'custom:user_id', 'Value': user_id},
                {'Name': 'custom:language', 'Value': language}
            ]
        )
        
        logger.info(f"Cognito user created: {phone_number}")
        return response
        
    except ClientError as e:
        logger.error(f"Cognito sign up failed: {str(e)}")
        raise


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


def generate_temp_password() -> str:
    """
    Generate a temporary password for Cognito.
    This is required by Cognito but won't be used since we use OTP.
    
    Returns:
        Temporary password string
    """
    import secrets
    import string
    
    # Generate a random password that meets Cognito requirements
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(16))
    return password


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
