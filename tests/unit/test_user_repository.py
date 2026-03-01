"""Unit tests for UserRepository."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from src.core.user_repository import UserRepository
from src.core.base_repository import ItemNotFoundError, DynamoDBRepositoryError
from src.models.user import UserProfile, UserPreferences
from src.models.location import Location


@pytest.fixture
def mock_table():
    """Create a mock DynamoDB table."""
    return Mock()


@pytest.fixture
def user_repository(mock_table):
    """Create a UserRepository with mocked DynamoDB table."""
    with patch('boto3.resource') as mock_resource:
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb
        
        with patch('boto3.client'):
            repo = UserRepository(table_name="TestUsers")
            repo.table = mock_table
            return repo


@pytest.fixture
def sample_user_profile():
    """Create a sample user profile for testing."""
    return UserProfile(
        user_id="test_user_123",
        phone_number="+919876543210",
        language="hi",
        location=Location(
            state="Maharashtra",
            district="Pune",
            pincode="411014"
        ),
        age=35,
        gender="male",
        education_level="secondary",
        occupation="farmer",
        income_bracket="100000-300000",
        household_size=5
    )


def test_create_user_success(user_repository, mock_table, sample_user_profile):
    """Test successful user creation."""
    mock_table.put_item.return_value = {}
    
    result = user_repository.create(sample_user_profile)
    
    assert result == sample_user_profile
    mock_table.put_item.assert_called_once()
    call_args = mock_table.put_item.call_args
    assert 'Item' in call_args.kwargs
    assert call_args.kwargs['Item']['user_id'] == "test_user_123"


def test_create_user_already_exists(user_repository, mock_table, sample_user_profile):
    """Test creating a user that already exists."""
    mock_table.put_item.side_effect = ClientError(
        {'Error': {'Code': 'ConditionalCheckFailedException', 'Message': 'Item exists'}},
        'PutItem'
    )
    
    with pytest.raises(DynamoDBRepositoryError, match="already exists"):
        user_repository.create(sample_user_profile)


def test_get_user_success(user_repository, mock_table, sample_user_profile):
    """Test successful user retrieval."""
    mock_table.get_item.return_value = {
        'Item': {
            'user_id': 'test_user_123',
            'phone_number': '+919876543210',
            'language': 'hi',
            'location': {
                'state': 'Maharashtra',
                'district': 'Pune',
                'pincode': '411014'
            },
            'age': 35,
            'gender': 'male',
            'education_level': 'secondary',
            'occupation': 'farmer',
            'income_bracket': '100000-300000',
            'household_size': 5,
            'preferences': {
                'notification_enabled': True,
                'preferred_categories': [],
                'voice_enabled': True,
                'data_sharing_consent': False
            },
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-01T00:00:00'
        }
    }
    
    result = user_repository.get('test_user_123')
    
    assert result.user_id == 'test_user_123'
    assert result.phone_number == '+919876543210'
    assert result.age == 35
    mock_table.get_item.assert_called_once_with(Key={'user_id': 'test_user_123'})


def test_get_user_not_found(user_repository, mock_table):
    """Test retrieving a non-existent user."""
    mock_table.get_item.return_value = {}
    
    with pytest.raises(ItemNotFoundError, match="not found"):
        user_repository.get('nonexistent_user')


def test_update_user_success(user_repository, mock_table, sample_user_profile):
    """Test successful user update."""
    mock_table.put_item.return_value = {}
    
    sample_user_profile.age = 36
    result = user_repository.update(sample_user_profile)
    
    assert result.age == 36
    mock_table.put_item.assert_called_once()


def test_update_user_not_found(user_repository, mock_table, sample_user_profile):
    """Test updating a non-existent user."""
    mock_table.put_item.side_effect = ClientError(
        {'Error': {'Code': 'ConditionalCheckFailedException', 'Message': 'Item not found'}},
        'PutItem'
    )
    
    with pytest.raises(ItemNotFoundError, match="not found"):
        user_repository.update(sample_user_profile)


def test_delete_user_success(user_repository, mock_table):
    """Test successful user deletion."""
    mock_table.delete_item.return_value = {}
    
    user_repository.delete('test_user_123')
    
    mock_table.delete_item.assert_called_once_with(
        Key={'user_id': 'test_user_123'},
        ConditionExpression='attribute_exists(user_id)'
    )


def test_delete_user_not_found(user_repository, mock_table):
    """Test deleting a non-existent user."""
    mock_table.delete_item.side_effect = ClientError(
        {'Error': {'Code': 'ConditionalCheckFailedException', 'Message': 'Item not found'}},
        'DeleteItem'
    )
    
    with pytest.raises(ItemNotFoundError, match="not found"):
        user_repository.delete('nonexistent_user')


def test_get_by_phone_number_success(user_repository, mock_table):
    """Test retrieving user by phone number."""
    mock_table.query.return_value = {
        'Items': [{
            'user_id': 'test_user_123',
            'phone_number': '+919876543210',
            'language': 'hi',
            'location': {
                'state': 'Maharashtra',
                'district': 'Pune',
                'pincode': '411014'
            },
            'preferences': {
                'notification_enabled': True,
                'preferred_categories': [],
                'voice_enabled': True,
                'data_sharing_consent': False
            },
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-01T00:00:00'
        }]
    }
    
    result = user_repository.get_by_phone_number('+919876543210')
    
    assert result is not None
    assert result.phone_number == '+919876543210'


def test_get_by_phone_number_not_found(user_repository, mock_table):
    """Test retrieving user by phone number when not found."""
    mock_table.query.return_value = {'Items': []}
    
    result = user_repository.get_by_phone_number('+919999999999')
    
    assert result is None


def test_get_by_phone_number_fallback_to_scan(user_repository, mock_table):
    """Test fallback to scan when GSI is not available."""
    # First call to query raises ValidationException (GSI not found)
    mock_table.query.side_effect = ClientError(
        {'Error': {'Code': 'ValidationException', 'Message': 'GSI not found'}},
        'Query'
    )
    
    # Scan should be called as fallback
    mock_table.scan.return_value = {
        'Items': [{
            'user_id': 'test_user_123',
            'phone_number': '+919876543210',
            'language': 'hi',
            'location': {
                'state': 'Maharashtra',
                'district': 'Pune',
                'pincode': '411014'
            },
            'preferences': {
                'notification_enabled': True,
                'preferred_categories': [],
                'voice_enabled': True,
                'data_sharing_consent': False
            },
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-01T00:00:00'
        }]
    }
    
    result = user_repository.get_by_phone_number('+919876543210')
    
    assert result is not None
    assert result.phone_number == '+919876543210'
    mock_table.scan.assert_called_once()
