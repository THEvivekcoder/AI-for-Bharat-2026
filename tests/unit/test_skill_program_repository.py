"""Unit tests for SkillProgramRepository."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from src.core.skill_program_repository import (
    SkillProgramRepository,
    SkillProgramFilters
)
from src.core.base_repository import ItemNotFoundError, DynamoDBRepositoryError
from src.models.skill import SkillProgram
from src.models.eligibility import EligibilityCriteria
from src.models.location import Location


@pytest.fixture
def mock_table():
    """Create a mock DynamoDB table."""
    return Mock()


@pytest.fixture
def repository(mock_table):
    """Create a SkillProgramRepository with mocked table."""
    with patch('boto3.resource') as mock_resource:
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb
        
        with patch('boto3.client'):
            repo = SkillProgramRepository(table_name="test-skill-programs")
            repo.table = mock_table
            return repo


@pytest.fixture
def sample_program():
    """Create a sample skill program."""
    return SkillProgram(
        program_id="TEST-PROG-001",
        name="Test Electrician Program",
        provider="Test Provider",
        category="technical",
        description="Test program description",
        duration_weeks=12,
        cost=0.0,
        location=Location(
            state="Maharashtra",
            district="Pune",
            pincode="411014"
        ),
        mode="in-person",
        eligibility_criteria=EligibilityCriteria(
            age_min=18,
            age_max=35
        ),
        certification=True,
        placement_support=True,
        registration_url="https://test.com",
        contact="1800-123-4567"
    )


def test_create_program_success(repository, mock_table, sample_program):
    """Test successful program creation."""
    mock_table.put_item.return_value = {}
    
    result = repository.create(sample_program)
    
    assert result == sample_program
    mock_table.put_item.assert_called_once()
    call_args = mock_table.put_item.call_args
    assert call_args[1]['Item']['program_id'] == "TEST-PROG-001"


def test_create_program_duplicate(repository, mock_table, sample_program):
    """Test creating duplicate program raises error."""
    mock_table.put_item.side_effect = ClientError(
        {'Error': {'Code': 'ConditionalCheckFailedException', 'Message': 'Item exists'}},
        'PutItem'
    )
    
    with pytest.raises(DynamoDBRepositoryError, match="already exists"):
        repository.create(sample_program)


def test_get_program_success(repository, mock_table, sample_program):
    """Test successful program retrieval."""
    mock_table.get_item.return_value = {
        'Item': sample_program.model_dump()
    }
    
    result = repository.get("TEST-PROG-001")
    
    assert result.program_id == sample_program.program_id
    assert result.name == sample_program.name
    mock_table.get_item.assert_called_once_with(Key={'program_id': 'TEST-PROG-001'})


def test_get_program_not_found(repository, mock_table):
    """Test getting non-existent program raises error."""
    mock_table.get_item.return_value = {}
    
    with pytest.raises(ItemNotFoundError, match="not found"):
        repository.get("NONEXISTENT")


def test_search_programs_by_category(repository, mock_table, sample_program):
    """Test searching programs by category."""
    mock_table.query.return_value = {
        'Items': [sample_program.model_dump()]
    }
    
    filters = SkillProgramFilters(category="technical")
    results = repository.search_programs(filters=filters)
    
    assert len(results) == 1
    assert results[0].program_id == sample_program.program_id
    mock_table.query.assert_called_once()


def test_search_programs_with_filters(repository, mock_table, sample_program):
    """Test searching programs with multiple filters."""
    mock_table.query.return_value = {
        'Items': [sample_program.model_dump()]
    }
    
    filters = SkillProgramFilters(
        category="technical",
        state="Maharashtra",
        max_cost=5000.0,
        certification=True
    )
    results = repository.search_programs(filters=filters, limit=10)
    
    assert len(results) == 1
    mock_table.query.assert_called_once()


def test_search_programs_with_query(repository, mock_table, sample_program):
    """Test searching programs with keyword query."""
    mock_table.scan.return_value = {
        'Items': [sample_program.model_dump()]
    }
    
    results = repository.search_programs(query="Electrician")
    
    assert len(results) == 1
    assert results[0].name == sample_program.name
    mock_table.scan.assert_called_once()


def test_search_programs_fallback_to_scan(repository, mock_table, sample_program):
    """Test fallback to scan when GSI not available."""
    mock_table.query.side_effect = ClientError(
        {'Error': {'Code': 'ValidationException', 'Message': 'GSI not found'}},
        'Query'
    )
    mock_table.scan.return_value = {
        'Items': [sample_program.model_dump()]
    }
    
    filters = SkillProgramFilters(category="technical")
    results = repository.search_programs(filters=filters)
    
    assert len(results) == 1
    mock_table.scan.assert_called_once()


def test_search_programs_empty_results(repository, mock_table):
    """Test searching with no matching results."""
    mock_table.scan.return_value = {'Items': []}
    
    results = repository.search_programs(query="NonexistentProgram")
    
    assert len(results) == 0


def test_search_programs_with_placement_filter(repository, mock_table, sample_program):
    """Test filtering by placement support."""
    mock_table.scan.return_value = {
        'Items': [sample_program.model_dump()]
    }
    
    filters = SkillProgramFilters(placement_support=True)
    results = repository.search_programs(filters=filters)
    
    assert len(results) == 1
    assert results[0].placement_support is True
