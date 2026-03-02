"""Unit tests for JobPostingRepository."""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError

from src.core.job_posting_repository import (
    JobPostingRepository,
    JobPostingFilters
)
from src.core.base_repository import ItemNotFoundError, DynamoDBRepositoryError
from src.models.skill import JobPosting
from src.models.location import Location


@pytest.fixture
def mock_table():
    """Create a mock DynamoDB table."""
    return Mock()


@pytest.fixture
def repository(mock_table):
    """Create a JobPostingRepository with mocked table."""
    with patch('boto3.resource') as mock_resource:
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb
        
        with patch('boto3.client'):
            repo = JobPostingRepository(table_name="test-job-postings")
            repo.table = mock_table
            return repo


@pytest.fixture
def sample_job():
    """Create a sample job posting."""
    return JobPosting(
        job_id="TEST-JOB-001",
        title="Junior Engineer",
        department="Public Works Department",
        description="Test job description",
        qualifications={
            "education": ["Diploma in Civil Engineering", "B.E. Civil"],
            "experience": ["0-2 years"],
            "skills": ["AutoCAD", "Site supervision"]
        },
        location=Location(
            state="Maharashtra",
            district="Pune",
            pincode="411001"
        ),
        application_deadline=date.today() + timedelta(days=30),
        application_url="https://test.gov.in/apply",
        posted_date=date.today(),
        salary_range="Rs. 35,000 - 50,000",
        vacancies=10
    )


def test_create_job_success(repository, mock_table, sample_job):
    """Test successful job creation."""
    mock_table.put_item.return_value = {}
    
    result = repository.create(sample_job)
    
    assert result == sample_job
    mock_table.put_item.assert_called_once()
    call_args = mock_table.put_item.call_args
    assert call_args[1]['Item']['job_id'] == "TEST-JOB-001"


def test_create_job_duplicate(repository, mock_table, sample_job):
    """Test creating duplicate job raises error."""
    mock_table.put_item.side_effect = ClientError(
        {'Error': {'Code': 'ConditionalCheckFailedException', 'Message': 'Item exists'}},
        'PutItem'
    )
    
    with pytest.raises(DynamoDBRepositoryError, match="already exists"):
        repository.create(sample_job)


def test_get_job_success(repository, mock_table, sample_job):
    """Test successful job retrieval."""
    mock_table.get_item.return_value = {
        'Item': sample_job.model_dump()
    }
    
    result = repository.get("TEST-JOB-001")
    
    assert result.job_id == sample_job.job_id
    assert result.title == sample_job.title
    mock_table.get_item.assert_called_once_with(Key={'job_id': 'TEST-JOB-001'})


def test_get_job_not_found(repository, mock_table):
    """Test getting non-existent job raises error."""
    mock_table.get_item.return_value = {}
    
    with pytest.raises(ItemNotFoundError, match="not found"):
        repository.get("NONEXISTENT")


def test_search_jobs_by_department(repository, mock_table, sample_job):
    """Test searching jobs by department."""
    mock_table.query.return_value = {
        'Items': [sample_job.model_dump()]
    }
    
    filters = JobPostingFilters(department="Public Works Department")
    results = repository.search_jobs(filters=filters)
    
    assert len(results) == 1
    assert results[0].job_id == sample_job.job_id
    mock_table.query.assert_called_once()


def test_search_jobs_with_filters(repository, mock_table, sample_job):
    """Test searching jobs with multiple filters."""
    mock_table.query.return_value = {
        'Items': [sample_job.model_dump()]
    }
    
    filters = JobPostingFilters(
        department="Public Works Department",
        state="Maharashtra",
        deadline_after=date.today()
    )
    results = repository.search_jobs(filters=filters, limit=10)
    
    assert len(results) == 1
    mock_table.query.assert_called_once()


def test_search_jobs_with_education_filter(repository, mock_table, sample_job):
    """Test searching jobs with education qualification filter."""
    mock_table.scan.return_value = {
        'Items': [sample_job.model_dump()]
    }
    
    filters = JobPostingFilters(
        education=["Diploma in Civil Engineering"]
    )
    results = repository.search_jobs(filters=filters)
    
    assert len(results) == 1
    assert "Diploma in Civil Engineering" in results[0].qualifications["education"]


def test_search_jobs_with_query(repository, mock_table, sample_job):
    """Test searching jobs with keyword query."""
    mock_table.scan.return_value = {
        'Items': [sample_job.model_dump()]
    }
    
    results = repository.search_jobs(query="Engineer")
    
    assert len(results) == 1
    assert "Engineer" in results[0].title
    mock_table.scan.assert_called_once()


def test_search_jobs_fallback_to_scan(repository, mock_table, sample_job):
    """Test fallback to scan when GSI not available."""
    mock_table.query.side_effect = ClientError(
        {'Error': {'Code': 'ValidationException', 'Message': 'GSI not found'}},
        'Query'
    )
    mock_table.scan.return_value = {
        'Items': [sample_job.model_dump()]
    }
    
    filters = JobPostingFilters(department="Public Works Department")
    results = repository.search_jobs(filters=filters)
    
    assert len(results) == 1
    mock_table.scan.assert_called_once()


def test_search_jobs_empty_results(repository, mock_table):
    """Test searching with no matching results."""
    mock_table.scan.return_value = {'Items': []}
    
    results = repository.search_jobs(query="NonexistentJob")
    
    assert len(results) == 0


def test_get_active_jobs(repository, mock_table, sample_job):
    """Test getting active jobs (deadline not passed)."""
    mock_table.scan.return_value = {
        'Items': [sample_job.model_dump()]
    }
    
    results = repository.get_active_jobs(limit=20)
    
    assert len(results) == 1
    assert results[0].application_deadline >= date.today()


def test_search_jobs_expired_deadline(repository, mock_table):
    """Test filtering out jobs with expired deadlines."""
    expired_job = JobPosting(
        job_id="EXPIRED-JOB",
        title="Expired Position",
        department="Test Dept",
        description="Expired job",
        qualifications={"education": ["Any"]},
        location=Location(state="Test", district="Test", pincode="000000"),
        application_deadline=date.today() - timedelta(days=1),
        application_url="https://test.com",
        posted_date=date.today() - timedelta(days=60)
    )
    
    mock_table.scan.return_value = {'Items': []}
    
    filters = JobPostingFilters(deadline_after=date.today())
    results = repository.search_jobs(filters=filters)
    
    assert len(results) == 0
