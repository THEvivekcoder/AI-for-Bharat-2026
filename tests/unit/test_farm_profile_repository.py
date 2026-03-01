"""Unit tests for FarmProfileRepository."""

import pytest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError

from src.core.farm_profile_repository import FarmProfileRepository
from src.core.base_repository import ItemNotFoundError, DynamoDBRepositoryError
from src.models.farm import FarmProfile
from src.models.location import Location


@pytest.fixture
def mock_table():
    """Create a mock DynamoDB table."""
    return Mock()


@pytest.fixture
def farm_profile_repository(mock_table):
    """Create a FarmProfileRepository with mocked DynamoDB table."""
    with patch('boto3.resource') as mock_resource:
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb
        
        with patch('boto3.client'):
            repo = FarmProfileRepository(table_name="TestFarmProfiles")
            repo.table = mock_table
            return repo


@pytest.fixture
def sample_farm_profile():
    """Create a sample farm profile for testing."""
    return FarmProfile(
        user_id="farmer_123",
        land_size_acres=5.0,
        soil_type="black",
        irrigation_type="well",
        location=Location(
            state="Maharashtra",
            district="Pune",
            block="Haveli",
            village="Kharadi",
            pincode="411014",
            latitude=18.5511,
            longitude=73.9467
        ),
        current_crops=["wheat", "sugarcane"],
        previous_crops=["cotton", "soybean"],
        livestock=["cow", "buffalo"]
    )


def test_get_farm_profile_success(farm_profile_repository, mock_table):
    """Test successful farm profile retrieval."""
    mock_table.get_item.return_value = {
        'Item': {
            'user_id': 'farmer_123',
            'land_size_acres': 5.0,
            'soil_type': 'black',
            'irrigation_type': 'well',
            'location': {
                'state': 'Maharashtra',
                'district': 'Pune',
                'block': 'Haveli',
                'village': 'Kharadi',
                'pincode': '411014',
                'latitude': 18.5511,
                'longitude': 73.9467
            },
            'current_crops': ['wheat', 'sugarcane'],
            'previous_crops': ['cotton', 'soybean'],
            'livestock': ['cow', 'buffalo'],
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-01T00:00:00'
        }
    }
    
    result = farm_profile_repository.get_farm_profile('farmer_123')
    
    assert result.user_id == 'farmer_123'
    assert result.land_size_acres == 5.0
    assert result.soil_type == 'black'
    assert 'wheat' in result.current_crops
    mock_table.get_item.assert_called_once_with(Key={'user_id': 'farmer_123'})


def test_get_farm_profile_not_found(farm_profile_repository, mock_table):
    """Test retrieving a non-existent farm profile."""
    mock_table.get_item.return_value = {}
    
    with pytest.raises(ItemNotFoundError, match="not found"):
        farm_profile_repository.get_farm_profile('nonexistent_farmer')


def test_create_farm_profile_success(farm_profile_repository, mock_table, sample_farm_profile):
    """Test successful farm profile creation."""
    mock_table.put_item.return_value = {}
    
    result = farm_profile_repository.create_farm_profile(sample_farm_profile)
    
    assert result == sample_farm_profile
    mock_table.put_item.assert_called_once()


def test_create_farm_profile_already_exists(farm_profile_repository, mock_table, sample_farm_profile):
    """Test creating a farm profile that already exists."""
    mock_table.put_item.side_effect = ClientError(
        {'Error': {'Code': 'ConditionalCheckFailedException', 'Message': 'Item exists'}},
        'PutItem'
    )
    
    with pytest.raises(DynamoDBRepositoryError, match="already exists"):
        farm_profile_repository.create_farm_profile(sample_farm_profile)


def test_update_farm_profile_success(farm_profile_repository, mock_table, sample_farm_profile):
    """Test successful farm profile update."""
    mock_table.put_item.return_value = {}
    
    # Update the farm profile
    sample_farm_profile.current_crops = ["rice", "wheat"]
    result = farm_profile_repository.update_farm_profile(sample_farm_profile)
    
    assert result == sample_farm_profile
    mock_table.put_item.assert_called_once()


def test_update_farm_profile_not_found(farm_profile_repository, mock_table, sample_farm_profile):
    """Test updating a non-existent farm profile."""
    mock_table.put_item.side_effect = ClientError(
        {'Error': {'Code': 'ConditionalCheckFailedException', 'Message': 'Item not found'}},
        'PutItem'
    )
    
    with pytest.raises(ItemNotFoundError, match="not found"):
        farm_profile_repository.update_farm_profile(sample_farm_profile)


def test_delete_farm_profile_success(farm_profile_repository, mock_table):
    """Test successful farm profile deletion."""
    mock_table.delete_item.return_value = {}
    
    farm_profile_repository.delete_farm_profile('farmer_123')
    
    mock_table.delete_item.assert_called_once_with(
        Key={'user_id': 'farmer_123'},
        ConditionExpression='attribute_exists(user_id)'
    )


def test_delete_farm_profile_not_found(farm_profile_repository, mock_table):
    """Test deleting a non-existent farm profile."""
    mock_table.delete_item.side_effect = ClientError(
        {'Error': {'Code': 'ConditionalCheckFailedException', 'Message': 'Item not found'}},
        'DeleteItem'
    )
    
    with pytest.raises(ItemNotFoundError, match="not found"):
        farm_profile_repository.delete_farm_profile('nonexistent_farmer')


def test_farm_profile_exists_true(farm_profile_repository, mock_table):
    """Test checking if farm profile exists (returns True)."""
    mock_table.get_item.return_value = {
        'Item': {'user_id': 'farmer_123'}
    }
    
    result = farm_profile_repository.farm_profile_exists('farmer_123')
    
    assert result is True


def test_farm_profile_exists_false(farm_profile_repository, mock_table):
    """Test checking if farm profile exists (returns False)."""
    mock_table.get_item.return_value = {}
    
    result = farm_profile_repository.farm_profile_exists('nonexistent_farmer')
    
    assert result is False


def test_farm_profile_exists_error_handling(farm_profile_repository, mock_table):
    """Test farm_profile_exists handles errors gracefully."""
    mock_table.get_item.side_effect = ClientError(
        {'Error': {'Code': 'InternalServerError', 'Message': 'Server error'}},
        'GetItem'
    )
    
    result = farm_profile_repository.farm_profile_exists('farmer_123')
    
    assert result is False


# Error Handling Tests for Network Failures

def test_get_farm_profile_network_error(farm_profile_repository, mock_table):
    """Test handling of network errors during farm profile retrieval."""
    mock_table.get_item.side_effect = ClientError(
        {'Error': {'Code': 'RequestTimeout', 'Message': 'Request timed out'}},
        'GetItem'
    )
    
    with pytest.raises(DynamoDBRepositoryError, match="DynamoDB error"):
        farm_profile_repository.get_farm_profile('farmer_123')


def test_create_farm_profile_network_error(farm_profile_repository, mock_table, sample_farm_profile):
    """Test handling of network errors during farm profile creation."""
    mock_table.put_item.side_effect = ClientError(
        {'Error': {'Code': 'InternalServerError', 'Message': 'Internal server error'}},
        'PutItem'
    )
    
    with pytest.raises(DynamoDBRepositoryError, match="DynamoDB error"):
        farm_profile_repository.create_farm_profile(sample_farm_profile)


def test_update_farm_profile_network_error(farm_profile_repository, mock_table, sample_farm_profile):
    """Test handling of network errors during farm profile update."""
    mock_table.put_item.side_effect = ClientError(
        {'Error': {'Code': 'ServiceUnavailable', 'Message': 'Service unavailable'}},
        'PutItem'
    )
    
    with pytest.raises(DynamoDBRepositoryError, match="DynamoDB error"):
        farm_profile_repository.update_farm_profile(sample_farm_profile)


def test_delete_farm_profile_network_error(farm_profile_repository, mock_table):
    """Test handling of network errors during farm profile deletion."""
    mock_table.delete_item.side_effect = ClientError(
        {'Error': {'Code': 'ProvisionedThroughputExceededException', 'Message': 'Throughput exceeded'}},
        'DeleteItem'
    )
    
    with pytest.raises(DynamoDBRepositoryError, match="DynamoDB error"):
        farm_profile_repository.delete_farm_profile('farmer_123')


def test_resource_not_found_error(farm_profile_repository, mock_table):
    """Test handling of ResourceNotFoundException (table doesn't exist)."""
    mock_table.get_item.side_effect = ClientError(
        {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Table not found'}},
        'GetItem'
    )
    
    with pytest.raises(ItemNotFoundError, match="Table .* not found"):
        farm_profile_repository.get_farm_profile('farmer_123')


# Edge Case Tests

def test_create_farm_profile_with_minimal_data(farm_profile_repository, mock_table):
    """Test creating farm profile with minimal required data."""
    minimal_profile = FarmProfile(
        user_id="farmer_456",
        land_size_acres=2.5,
        soil_type="loam",
        irrigation_type="rainfed",
        location=Location(
            state="Karnataka",
            district="Bangalore",
            pincode="560001"
        )
    )
    
    mock_table.put_item.return_value = {}
    
    result = farm_profile_repository.create_farm_profile(minimal_profile)
    
    assert result.user_id == "farmer_456"
    assert result.current_crops == []
    assert result.livestock is None


def test_update_farm_profile_with_empty_lists(farm_profile_repository, mock_table):
    """Test updating farm profile with empty crop lists."""
    profile = FarmProfile(
        user_id="farmer_789",
        land_size_acres=3.0,
        soil_type="sandy",
        irrigation_type="drip",
        location=Location(
            state="Punjab",
            district="Ludhiana",
            pincode="141001"
        ),
        current_crops=[],
        previous_crops=[]
    )
    
    mock_table.put_item.return_value = {}
    
    result = farm_profile_repository.update_farm_profile(profile)
    
    assert result.current_crops == []
    assert result.previous_crops == []


def test_farm_profile_with_multiple_livestock(farm_profile_repository, mock_table):
    """Test farm profile with multiple livestock types."""
    profile = FarmProfile(
        user_id="farmer_999",
        land_size_acres=10.0,
        soil_type="black",
        irrigation_type="canal",
        location=Location(
            state="Haryana",
            district="Karnal",
            pincode="132001"
        ),
        livestock=["cow", "buffalo", "goat", "chicken"]
    )
    
    mock_table.put_item.return_value = {}
    
    result = farm_profile_repository.create_farm_profile(profile)
    
    assert len(result.livestock) == 4
    assert "goat" in result.livestock
