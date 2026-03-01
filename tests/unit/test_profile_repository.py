"""Unit tests for ProfileRepository."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError

from src.core.profile_repository import ProfileRepository
from src.core.base_repository import ItemNotFoundError, DynamoDBRepositoryError
from src.models.user import UserProfile, UserPreferences
from src.models.location import Location


@pytest.fixture
def mock_table():
    """Create a mock DynamoDB table."""
    return Mock()


@pytest.fixture
def profile_repository(mock_table):
    """Create a ProfileRepository with mocked DynamoDB table."""
    with patch('boto3.resource') as mock_resource:
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb
        
        with patch('boto3.client'):
            repo = ProfileRepository(table_name="TestProfiles")
            repo.table = mock_table
            return repo


@pytest.fixture
def sample_profile():
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
        gender="male"
    )


def test_get_profile_success(profile_repository, mock_table):
    """Test successful profile retrieval."""
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
    
    result = profile_repository.get_profile('test_user_123')
    
    assert result.user_id == 'test_user_123'
    assert result.age == 35
    mock_table.get_item.assert_called_once_with(Key={'user_id': 'test_user_123'})


def test_get_profile_not_found(profile_repository, mock_table):
    """Test retrieving a non-existent profile."""
    mock_table.get_item.return_value = {}
    
    with pytest.raises(ItemNotFoundError, match="not found"):
        profile_repository.get_profile('nonexistent_user')


def test_update_profile_success(profile_repository, mock_table):
    """Test successful profile update."""
    mock_table.update_item.return_value = {
        'Attributes': {
            'user_id': 'test_user_123',
            'phone_number': '+919876543210',
            'language': 'hi',
            'location': {
                'state': 'Maharashtra',
                'district': 'Pune',
                'pincode': '411014'
            },
            'age': 36,
            'gender': 'male',
            'preferences': {
                'notification_enabled': True,
                'preferred_categories': [],
                'voice_enabled': True,
                'data_sharing_consent': False
            },
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-15T10:30:00'
        }
    }
    
    result = profile_repository.update_profile('test_user_123', {'age': 36})
    
    assert result.age == 36
    mock_table.update_item.assert_called_once()


def test_update_profile_not_found(profile_repository, mock_table):
    """Test updating a non-existent profile."""
    mock_table.update_item.side_effect = ClientError(
        {'Error': {'Code': 'ConditionalCheckFailedException', 'Message': 'Item not found'}},
        'UpdateItem'
    )
    
    with pytest.raises(ItemNotFoundError, match="not found"):
        profile_repository.update_profile('nonexistent_user', {'age': 36})


def test_update_profile_create_if_not_exists(profile_repository, mock_table):
    """Test updating profile with create_if_not_exists flag."""
    mock_table.update_item.return_value = {
        'Attributes': {
            'user_id': 'new_user_123',
            'phone_number': '+919876543210',
            'language': 'hi',
            'location': {
                'state': 'Maharashtra',
                'district': 'Pune',
                'pincode': '411014'
            },
            'age': 30,
            'preferences': {
                'notification_enabled': True,
                'preferred_categories': [],
                'voice_enabled': True,
                'data_sharing_consent': False
            },
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-15T10:30:00'
        }
    }
    
    result = profile_repository.update_profile(
        'new_user_123',
        {'age': 30},
        create_if_not_exists=True
    )
    
    assert result.age == 30
    # Verify that ConditionExpression was not set
    call_kwargs = mock_table.update_item.call_args.kwargs
    assert 'ConditionExpression' not in call_kwargs


def test_create_profile_success(profile_repository, mock_table, sample_profile):
    """Test successful profile creation."""
    mock_table.put_item.return_value = {}
    
    result = profile_repository.create_profile(sample_profile)
    
    assert result == sample_profile
    mock_table.put_item.assert_called_once()


def test_create_profile_already_exists(profile_repository, mock_table, sample_profile):
    """Test creating a profile that already exists."""
    mock_table.put_item.side_effect = ClientError(
        {'Error': {'Code': 'ConditionalCheckFailedException', 'Message': 'Item exists'}},
        'PutItem'
    )
    
    with pytest.raises(DynamoDBRepositoryError, match="already exists"):
        profile_repository.create_profile(sample_profile)


def test_delete_profile_success(profile_repository, mock_table):
    """Test successful profile deletion."""
    mock_table.delete_item.return_value = {}
    
    profile_repository.delete_profile('test_user_123')
    
    mock_table.delete_item.assert_called_once_with(
        Key={'user_id': 'test_user_123'},
        ConditionExpression='attribute_exists(user_id)'
    )


def test_delete_profile_not_found(profile_repository, mock_table):
    """Test deleting a non-existent profile."""
    mock_table.delete_item.side_effect = ClientError(
        {'Error': {'Code': 'ConditionalCheckFailedException', 'Message': 'Item not found'}},
        'DeleteItem'
    )
    
    with pytest.raises(ItemNotFoundError, match="not found"):
        profile_repository.delete_profile('nonexistent_user')


def test_update_location(profile_repository, mock_table):
    """Test updating user location."""
    mock_table.update_item.return_value = {
        'Attributes': {
            'user_id': 'test_user_123',
            'phone_number': '+919876543210',
            'language': 'hi',
            'location': {
                'state': 'Karnataka',
                'district': 'Bangalore',
                'pincode': '560001'
            },
            'preferences': {
                'notification_enabled': True,
                'preferred_categories': [],
                'voice_enabled': True,
                'data_sharing_consent': False
            },
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-15T10:30:00'
        }
    }
    
    new_location = {
        'state': 'Karnataka',
        'district': 'Bangalore',
        'pincode': '560001'
    }
    
    result = profile_repository.update_location('test_user_123', new_location)
    
    assert result.location.state == 'Karnataka'
    assert result.location.district == 'Bangalore'


def test_update_preferences(profile_repository, mock_table):
    """Test updating user preferences."""
    mock_table.update_item.return_value = {
        'Attributes': {
            'user_id': 'test_user_123',
            'phone_number': '+919876543210',
            'language': 'hi',
            'location': {
                'state': 'Maharashtra',
                'district': 'Pune',
                'pincode': '411014'
            },
            'preferences': {
                'notification_enabled': False,
                'preferred_categories': ['agriculture', 'health'],
                'voice_enabled': True,
                'data_sharing_consent': True
            },
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-15T10:30:00'
        }
    }
    
    new_preferences = {
        'notification_enabled': False,
        'preferred_categories': ['agriculture', 'health'],
        'data_sharing_consent': True
    }
    
    result = profile_repository.update_preferences('test_user_123', new_preferences)
    
    assert result.preferences.notification_enabled is False
    assert 'agriculture' in result.preferences.preferred_categories


def test_profile_exists_true(profile_repository, mock_table):
    """Test checking if profile exists (returns True)."""
    mock_table.get_item.return_value = {
        'Item': {'user_id': 'test_user_123'}
    }
    
    result = profile_repository.profile_exists('test_user_123')
    
    assert result is True


def test_profile_exists_false(profile_repository, mock_table):
    """Test checking if profile exists (returns False)."""
    mock_table.get_item.return_value = {}
    
    result = profile_repository.profile_exists('nonexistent_user')
    
    assert result is False


def test_profile_exists_error_handling(profile_repository, mock_table):
    """Test profile_exists handles errors gracefully."""
    mock_table.get_item.side_effect = ClientError(
        {'Error': {'Code': 'InternalServerError', 'Message': 'Server error'}},
        'GetItem'
    )
    
    result = profile_repository.profile_exists('test_user_123')
    
    assert result is False
