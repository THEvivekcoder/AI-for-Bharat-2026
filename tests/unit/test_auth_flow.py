"""Unit tests for authentication flow (registration, OTP verification, JWT)."""

import os
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError
import jwt as pyjwt

# Set environment variables before importing modules
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['USER_POOL_ID'] = 'test_pool_id'
os.environ['USER_POOL_CLIENT_ID'] = 'test_client_id'
os.environ['JWT_SECRET'] = 'test-jwt-secret-key-for-testing'
os.environ['USERS_TABLE'] = 'test-users-table'
os.environ['PROFILES_TABLE'] = 'test-profiles-table'

# Mock boto3 before importing modules that use it
with patch('boto3.client'), patch('boto3.resource'):
    from src.api.auth_register import (
        lambda_handler as register_handler,
        normalize_phone_number,
        generate_temp_password,
        create_cognito_user
    )
    from src.api.auth_verify import (
        lambda_handler as verify_handler,
        verify_otp_with_cognito,
        generate_jwt_token,
        extract_user_id
    )
    from src.utils.auth_middleware import (
        verify_jwt_token,
        extract_user_id_from_token,
        get_authorization_header,
        require_auth
    )


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def valid_registration_event():
    """Create a valid registration event."""
    return {
        'body': json.dumps({
            'phone_number': '+919876543210',
            'language': 'hi',
            'location': {
                'state': 'Maharashtra',
                'district': 'Pune',
                'pincode': '411014'
            },
            'age': 35,
            'gender': 'male'
        })
    }


@pytest.fixture
def valid_verification_event():
    """Create a valid OTP verification event."""
    return {
        'body': json.dumps({
            'phone_number': '+919876543210',
            'otp': '123456',
            'session': 'test_session_token'
        })
    }


@pytest.fixture
def mock_cognito_client():
    """Create a mock Cognito client."""
    with patch('src.api.auth_register.cognito_client') as mock_client:
        yield mock_client


@pytest.fixture
def mock_verify_cognito_client():
    """Create a mock Cognito client for verification."""
    with patch('src.api.auth_verify.cognito_client') as mock_client:
        yield mock_client


@pytest.fixture
def mock_repositories():
    """Mock user and profile repositories."""
    with patch('src.api.auth_register.user_repo') as mock_user_repo, \
         patch('src.api.auth_register.profile_repo') as mock_profile_repo:
        mock_user_repo.get_by_phone_number.return_value = None
        mock_user_repo.create.return_value = None
        mock_profile_repo.create_profile.return_value = None
        yield mock_user_repo, mock_profile_repo


# ============================================================================
# REGISTRATION TESTS - VALID PHONE NUMBERS
# ============================================================================

def test_register_with_valid_phone_number_with_country_code(
    valid_registration_event, mock_cognito_client, mock_repositories
):
    """Test registration with valid phone number including country code."""
    mock_cognito_client.sign_up.return_value = {
        'UserSub': 'test_user_sub',
        'Session': 'test_session'
    }
    
    response = register_handler(valid_registration_event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert 'user_id' in body
    assert 'session' in body
    assert body['message'] == 'OTP sent to phone number. Please verify to complete registration.'


def test_register_with_valid_phone_number_without_country_code(
    mock_cognito_client, mock_repositories
):
    """Test registration with 10-digit phone number (auto-adds +91)."""
    event = {
        'body': json.dumps({
            'phone_number': '9876543210',
            'language': 'hi',
            'location': {
                'state': 'Maharashtra',
                'district': 'Pune',
                'pincode': '411014'
            }
        })
    }
    
    mock_cognito_client.sign_up.return_value = {
        'UserSub': 'test_user_sub',
        'Session': 'test_session'
    }
    
    response = register_handler(event, None)
    
    assert response['statusCode'] == 200
    # Verify that phone number was normalized to +919876543210
    call_args = mock_cognito_client.sign_up.call_args
    assert call_args.kwargs['Username'] == '+919876543210'


def test_register_with_phone_number_with_spaces_and_dashes(
    mock_cognito_client, mock_repositories
):
    """Test registration with phone number containing spaces and dashes."""
    event = {
        'body': json.dumps({
            'phone_number': '+91 987-654-3210',
            'language': 'hi',
            'location': {
                'state': 'Maharashtra',
                'district': 'Pune',
                'pincode': '411014'
            }
        })
    }
    
    mock_cognito_client.sign_up.return_value = {
        'UserSub': 'test_user_sub',
        'Session': 'test_session'
    }
    
    response = register_handler(event, None)
    
    assert response['statusCode'] == 200
    # Verify normalization removed spaces and dashes
    call_args = mock_cognito_client.sign_up.call_args
    assert call_args.kwargs['Username'] == '+919876543210'


# ============================================================================
# REGISTRATION TESTS - INVALID PHONE NUMBERS
# ============================================================================

def test_register_with_missing_phone_number(mock_cognito_client, mock_repositories):
    """Test registration fails when phone number is missing."""
    event = {
        'body': json.dumps({
            'language': 'hi',
            'location': {
                'state': 'Maharashtra',
                'district': 'Pune',
                'pincode': '411014'
            }
        })
    }
    
    response = register_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'phone_number is required' in body['error']


def test_register_with_invalid_phone_number_format(mock_cognito_client, mock_repositories):
    """Test registration fails with invalid phone number format."""
    event = {
        'body': json.dumps({
            'phone_number': '12345',  # Too short
            'language': 'hi',
            'location': {
                'state': 'Maharashtra',
                'district': 'Pune',
                'pincode': '411014'
            }
        })
    }
    
    response = register_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'Invalid phone number format' in body['error']


def test_register_with_existing_phone_number(mock_cognito_client, mock_repositories):
    """Test registration fails when phone number already exists."""
    mock_user_repo, _ = mock_repositories
    mock_user_repo.get_by_phone_number.return_value = Mock(user_id='existing_user')
    
    event = {
        'body': json.dumps({
            'phone_number': '+919876543210',
            'language': 'hi',
            'location': {
                'state': 'Maharashtra',
                'district': 'Pune',
                'pincode': '411014'
            }
        })
    }
    
    response = register_handler(event, None)
    
    assert response['statusCode'] == 409
    body = json.loads(response['body'])
    assert 'already exists' in body['error']


def test_register_cognito_username_exists_exception(
    valid_registration_event, mock_cognito_client, mock_repositories
):
    """Test registration handles Cognito UsernameExistsException."""
    mock_cognito_client.sign_up.side_effect = ClientError(
        {'Error': {'Code': 'UsernameExistsException', 'Message': 'User exists'}},
        'SignUp'
    )
    
    response = register_handler(valid_registration_event, None)
    
    assert response['statusCode'] == 409
    body = json.loads(response['body'])
    assert 'already exists' in body['error']


def test_register_cognito_invalid_parameter_exception(
    mock_cognito_client, mock_repositories
):
    """Test registration handles Cognito InvalidParameterException."""
    event = {
        'body': json.dumps({
            'phone_number': 'invalid',
            'language': 'hi',
            'location': {
                'state': 'Maharashtra',
                'district': 'Pune',
                'pincode': '411014'
            }
        })
    }
    
    mock_cognito_client.sign_up.side_effect = ClientError(
        {'Error': {'Code': 'InvalidParameterException', 'Message': 'Invalid phone'}},
        'SignUp'
    )
    
    response = register_handler(event, None)
    
    assert response['statusCode'] == 400


# ============================================================================
# OTP VERIFICATION TESTS - SUCCESS CASES
# ============================================================================

def test_verify_otp_success(valid_verification_event, mock_verify_cognito_client):
    """Test successful OTP verification."""
    mock_verify_cognito_client.confirm_sign_up.return_value = {}
    mock_verify_cognito_client.initiate_auth.return_value = {
        'AuthenticationResult': {
            'IdToken': create_test_cognito_token('test_user_123'),
            'AccessToken': 'test_access_token',
            'RefreshToken': 'test_refresh_token'
        }
    }
    
    response = verify_handler(valid_verification_event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert 'access_token' in body
    assert 'user_id' in body
    assert body['token_type'] == 'Bearer'
    assert body['message'] == 'Authentication successful'


def test_verify_otp_without_session(mock_verify_cognito_client):
    """Test OTP verification for existing user (without session)."""
    event = {
        'body': json.dumps({
            'phone_number': '+919876543210',
            'otp': '123456'
        })
    }
    
    mock_verify_cognito_client.initiate_auth.return_value = {
        'ChallengeName': 'CUSTOM_CHALLENGE',
        'Session': 'challenge_session'
    }
    
    mock_verify_cognito_client.respond_to_auth_challenge.return_value = {
        'AuthenticationResult': {
            'IdToken': create_test_cognito_token('test_user_123'),
            'AccessToken': 'test_access_token'
        }
    }
    
    response = verify_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert 'access_token' in body


# ============================================================================
# OTP VERIFICATION TESTS - FAILURE CASES
# ============================================================================

def test_verify_otp_missing_phone_number(mock_verify_cognito_client):
    """Test OTP verification fails when phone number is missing."""
    event = {
        'body': json.dumps({
            'otp': '123456'
        })
    }
    
    response = verify_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'phone_number is required' in body['error']


def test_verify_otp_missing_otp_code(mock_verify_cognito_client):
    """Test OTP verification fails when OTP is missing."""
    event = {
        'body': json.dumps({
            'phone_number': '+919876543210'
        })
    }
    
    response = verify_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'otp is required' in body['error']


def test_verify_otp_code_mismatch(valid_verification_event, mock_verify_cognito_client):
    """Test OTP verification fails with incorrect OTP."""
    mock_verify_cognito_client.confirm_sign_up.side_effect = ClientError(
        {'Error': {'Code': 'CodeMismatchException', 'Message': 'Invalid code'}},
        'ConfirmSignUp'
    )
    
    response = verify_handler(valid_verification_event, None)
    
    assert response['statusCode'] == 401
    body = json.loads(response['body'])
    assert 'Invalid OTP code' in body['error']


def test_verify_otp_expired_code(valid_verification_event, mock_verify_cognito_client):
    """Test OTP verification fails with expired OTP."""
    mock_verify_cognito_client.confirm_sign_up.side_effect = ClientError(
        {'Error': {'Code': 'ExpiredCodeException', 'Message': 'Code expired'}},
        'ConfirmSignUp'
    )
    
    response = verify_handler(valid_verification_event, None)
    
    assert response['statusCode'] == 401
    body = json.loads(response['body'])
    assert 'expired' in body['error'].lower()


def test_verify_otp_user_not_found(valid_verification_event, mock_verify_cognito_client):
    """Test OTP verification fails when user doesn't exist."""
    mock_verify_cognito_client.confirm_sign_up.side_effect = ClientError(
        {'Error': {'Code': 'UserNotFoundException', 'Message': 'User not found'}},
        'ConfirmSignUp'
    )
    
    response = verify_handler(valid_verification_event, None)
    
    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert 'not found' in body['error'].lower()


def test_verify_otp_not_authorized(valid_verification_event, mock_verify_cognito_client):
    """Test OTP verification fails with NotAuthorizedException."""
    mock_verify_cognito_client.confirm_sign_up.side_effect = ClientError(
        {'Error': {'Code': 'NotAuthorizedException', 'Message': 'Not authorized'}},
        'ConfirmSignUp'
    )
    
    response = verify_handler(valid_verification_event, None)
    
    assert response['statusCode'] == 401
    body = json.loads(response['body'])
    assert 'Authentication failed' in body['error']


# ============================================================================
# JWT TOKEN GENERATION TESTS
# ============================================================================

def test_generate_jwt_token_contains_required_fields():
    """Test JWT token contains all required fields."""
    user_id = 'test_user_123'
    phone_number = '+919876543210'
    
    token = generate_jwt_token(user_id, phone_number)
    
    # Decode without verification to check payload
    payload = pyjwt.decode(token, options={"verify_signature": False})
    
    assert payload['user_id'] == user_id
    assert payload['phone_number'] == phone_number
    assert payload['sub'] == user_id
    assert payload['iss'] == 'bharatsahayak'
    assert 'iat' in payload
    assert 'exp' in payload


def test_generate_jwt_token_expiration():
    """Test JWT token has correct expiration time."""
    user_id = 'test_user_123'
    phone_number = '+919876543210'
    
    before_time = datetime.utcnow()
    token = generate_jwt_token(user_id, phone_number)
    after_time = datetime.utcnow()
    
    payload = pyjwt.decode(token, options={"verify_signature": False})
    
    exp_time = datetime.fromtimestamp(payload['exp'])
    iat_time = datetime.fromtimestamp(payload['iat'])
    
    # Token should expire 24 hours after issuance
    expected_duration = timedelta(hours=24)
    actual_duration = exp_time - iat_time
    
    assert abs((actual_duration - expected_duration).total_seconds()) < 2


def test_generate_jwt_token_is_valid():
    """Test generated JWT token can be verified."""
    user_id = 'test_user_123'
    phone_number = '+919876543210'
    
    token = generate_jwt_token(user_id, phone_number)
    
    # Should not raise exception
    payload = verify_jwt_token(token)
    assert payload['user_id'] == user_id


# ============================================================================
# JWT TOKEN VALIDATION TESTS
# ============================================================================

def test_verify_jwt_token_success():
    """Test successful JWT token verification."""
    user_id = 'test_user_123'
    phone_number = '+919876543210'
    
    token = generate_jwt_token(user_id, phone_number)
    payload = verify_jwt_token(token)
    
    assert payload['user_id'] == user_id
    assert payload['phone_number'] == phone_number


def test_verify_jwt_token_with_bearer_prefix():
    """Test JWT verification handles Bearer prefix."""
    user_id = 'test_user_123'
    phone_number = '+919876543210'
    
    token = generate_jwt_token(user_id, phone_number)
    bearer_token = f'Bearer {token}'
    
    payload = verify_jwt_token(bearer_token)
    assert payload['user_id'] == user_id


def test_verify_jwt_token_expired():
    """Test JWT verification fails with expired token."""
    # Create an expired token
    import os
    jwt_secret = os.environ.get('JWT_SECRET', 'bharatsahayak-secret-key-change-in-production')
    
    expired_payload = {
        'user_id': 'test_user_123',
        'phone_number': '+919876543210',
        'iat': datetime.utcnow() - timedelta(days=2),
        'exp': datetime.utcnow() - timedelta(days=1),
        'iss': 'bharatsahayak',
        'sub': 'test_user_123'
    }
    
    expired_token = pyjwt.encode(expired_payload, jwt_secret, algorithm='HS256')
    
    with pytest.raises(pyjwt.ExpiredSignatureError):
        verify_jwt_token(expired_token)


def test_verify_jwt_token_invalid_signature():
    """Test JWT verification fails with invalid signature."""
    # Create token with wrong secret
    wrong_payload = {
        'user_id': 'test_user_123',
        'phone_number': '+919876543210',
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iss': 'bharatsahayak',
        'sub': 'test_user_123'
    }
    
    invalid_token = pyjwt.encode(wrong_payload, 'wrong_secret', algorithm='HS256')
    
    with pytest.raises(pyjwt.InvalidTokenError):
        verify_jwt_token(invalid_token)


def test_verify_jwt_token_malformed():
    """Test JWT verification fails with malformed token."""
    malformed_token = 'not.a.valid.jwt.token'
    
    with pytest.raises(pyjwt.InvalidTokenError):
        verify_jwt_token(malformed_token)


def test_extract_user_id_from_token_success():
    """Test extracting user ID from valid token."""
    user_id = 'test_user_123'
    phone_number = '+919876543210'
    
    token = generate_jwt_token(user_id, phone_number)
    extracted_id = extract_user_id_from_token(token)
    
    assert extracted_id == user_id


def test_extract_user_id_from_token_invalid():
    """Test extracting user ID from invalid token returns None."""
    invalid_token = 'invalid.token.here'
    
    extracted_id = extract_user_id_from_token(invalid_token)
    
    assert extracted_id is None


# ============================================================================
# AUTHORIZATION HEADER TESTS
# ============================================================================

def test_get_authorization_header_success():
    """Test extracting authorization header from event."""
    event = {
        'headers': {
            'Authorization': 'Bearer test_token_123'
        }
    }
    
    auth_header = get_authorization_header(event)
    
    assert auth_header == 'Bearer test_token_123'


def test_get_authorization_header_lowercase():
    """Test extracting authorization header with lowercase key."""
    event = {
        'headers': {
            'authorization': 'Bearer test_token_123'
        }
    }
    
    auth_header = get_authorization_header(event)
    
    assert auth_header == 'Bearer test_token_123'


def test_get_authorization_header_missing():
    """Test extracting authorization header when missing."""
    event = {
        'headers': {}
    }
    
    auth_header = get_authorization_header(event)
    
    assert auth_header is None


# ============================================================================
# REQUIRE_AUTH DECORATOR TESTS
# ============================================================================

def test_require_auth_decorator_success():
    """Test require_auth decorator with valid token."""
    @require_auth
    def test_handler(event, context, user_id):
        return {
            'statusCode': 200,
            'body': json.dumps({'user_id': user_id})
        }
    
    token = generate_jwt_token('test_user_123', '+919876543210')
    event = {
        'headers': {
            'Authorization': f'Bearer {token}'
        }
    }
    
    response = test_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['user_id'] == 'test_user_123'


def test_require_auth_decorator_missing_header():
    """Test require_auth decorator fails without authorization header."""
    @require_auth
    def test_handler(event, context, user_id):
        return {'statusCode': 200}
    
    event = {'headers': {}}
    
    response = test_handler(event, None)
    
    assert response['statusCode'] == 401
    body = json.loads(response['body'])
    assert 'Missing authorization header' in body['error']


def test_require_auth_decorator_invalid_token():
    """Test require_auth decorator fails with invalid token."""
    @require_auth
    def test_handler(event, context, user_id):
        return {'statusCode': 200}
    
    event = {
        'headers': {
            'Authorization': 'Bearer invalid.token.here'
        }
    }
    
    response = test_handler(event, None)
    
    assert response['statusCode'] == 401
    body = json.loads(response['body'])
    assert 'Invalid token' in body['error']


def test_require_auth_decorator_expired_token():
    """Test require_auth decorator fails with expired token."""
    @require_auth
    def test_handler(event, context, user_id):
        return {'statusCode': 200}
    
    import os
    jwt_secret = os.environ.get('JWT_SECRET', 'bharatsahayak-secret-key-change-in-production')
    
    expired_payload = {
        'user_id': 'test_user_123',
        'phone_number': '+919876543210',
        'iat': datetime.utcnow() - timedelta(days=2),
        'exp': datetime.utcnow() - timedelta(days=1),
        'iss': 'bharatsahayak',
        'sub': 'test_user_123'
    }
    
    expired_token = pyjwt.encode(expired_payload, jwt_secret, algorithm='HS256')
    
    event = {
        'headers': {
            'Authorization': f'Bearer {expired_token}'
        }
    }
    
    response = test_handler(event, None)
    
    assert response['statusCode'] == 401
    body = json.loads(response['body'])
    assert 'expired' in body['error'].lower()


# ============================================================================
# PHONE NUMBER NORMALIZATION TESTS
# ============================================================================

def test_normalize_phone_number_with_country_code():
    """Test normalizing phone number with country code."""
    result = normalize_phone_number('+919876543210')
    assert result == '+919876543210'


def test_normalize_phone_number_without_country_code():
    """Test normalizing 10-digit phone number."""
    result = normalize_phone_number('9876543210')
    assert result == '+919876543210'


def test_normalize_phone_number_with_91_prefix():
    """Test normalizing phone number with 91 prefix."""
    result = normalize_phone_number('919876543210')
    assert result == '+919876543210'


def test_normalize_phone_number_with_spaces():
    """Test normalizing phone number with spaces."""
    result = normalize_phone_number('+91 987 654 3210')
    assert result == '+919876543210'


def test_normalize_phone_number_with_dashes():
    """Test normalizing phone number with dashes."""
    result = normalize_phone_number('+91-987-654-3210')
    assert result == '+919876543210'


def test_normalize_phone_number_with_parentheses():
    """Test normalizing phone number with parentheses."""
    result = normalize_phone_number('+91 (987) 654-3210')
    assert result == '+919876543210'


def test_normalize_phone_number_invalid_length():
    """Test normalizing phone number with invalid length."""
    with pytest.raises(ValueError, match="Invalid phone number format"):
        normalize_phone_number('12345')


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_test_cognito_token(user_id: str) -> str:
    """Create a test Cognito ID token."""
    import os
    jwt_secret = os.environ.get('JWT_SECRET', 'bharatsahayak-secret-key-change-in-production')
    
    payload = {
        'custom:user_id': user_id,
        'sub': user_id,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    
    return pyjwt.encode(payload, jwt_secret, algorithm='HS256')
