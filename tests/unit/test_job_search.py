"""Unit tests for job search Lambda handler."""

import json
import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.api.job_search import lambda_handler
from src.models.skill import JobPosting
from src.models.location import Location


@pytest.fixture
def sample_jobs():
    """Create sample job postings for testing."""
    return [
        JobPosting(
            job_id="MAHA-PWD-2024-001",
            title="Junior Engineer (Civil)",
            department="Maharashtra Public Works Department",
            description="Junior Engineer position for civil engineering projects",
            qualifications={
                "education": ["Diploma in Civil Engineering", "B.E./B.Tech in Civil Engineering"],
                "experience": ["Freshers welcome", "0-2 years experience"],
                "skills": ["AutoCAD", "Site supervision"]
            },
            location=Location(
                state="Maharashtra",
                district="Pune",
                pincode="411001"
            ),
            application_deadline=date.today() + timedelta(days=30),
            application_url="https://mahapwd.gov.in/recruitment",
            posted_date=date.today() - timedelta(days=15),
            salary_range="Rs. 35,000 - 50,000 per month",
            vacancies=25
        ),
        JobPosting(
            job_id="UP-POLICE-2024-001",
            title="Constable",
            department="Uttar Pradesh Police",
            description="Police constable recruitment for law enforcement duties",
            qualifications={
                "education": ["10th pass", "12th pass"],
                "experience": ["Freshers welcome"],
                "skills": ["Physical fitness", "Basic computer knowledge"]
            },
            location=Location(
                state="Uttar Pradesh",
                district="Lucknow",
                pincode="226001"
            ),
            application_deadline=date.today() + timedelta(days=45),
            application_url="https://uppbpb.gov.in/recruitment",
            posted_date=date.today() - timedelta(days=10),
            salary_range="Rs. 21,700 - 69,100 per month",
            vacancies=50000
        ),
        JobPosting(
            job_id="MAHA-HEALTH-2024-001",
            title="Staff Nurse",
            department="Maharashtra Health Department",
            description="Staff nurse position in government hospitals",
            qualifications={
                "education": ["B.Sc Nursing", "GNM"],
                "experience": ["Freshers welcome", "0-3 years experience"],
                "skills": ["Patient care", "Medical procedures"]
            },
            location=Location(
                state="Maharashtra",
                district="Mumbai",
                pincode="400001"
            ),
            application_deadline=date.today() + timedelta(days=20),
            application_url="https://mahahealth.gov.in/recruitment",
            posted_date=date.today() - timedelta(days=5),
            salary_range="Rs. 25,000 - 45,000 per month",
            vacancies=100
        )
    ]


@patch('src.api.job_search.job_repo')
def test_job_search_no_filters(mock_repo, sample_jobs):
    """Test job search without any filters."""
    mock_repo.search_jobs.return_value = sample_jobs
    
    event = {
        'queryStringParameters': {}
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    assert 'jobs' in body
    assert len(body['jobs']) == 3
    assert body['total_count'] == 3
    assert body['filters_applied']['active_only'] is True


@patch('src.api.job_search.job_repo')
def test_job_search_with_education_filter(mock_repo, sample_jobs):
    """Test job search filtered by education qualifications."""
    # Return only jobs matching 10th/12th pass
    filtered_jobs = [job for job in sample_jobs if job.job_id == "UP-POLICE-2024-001"]
    mock_repo.search_jobs.return_value = filtered_jobs
    
    event = {
        'queryStringParameters': {
            'education': '10th pass,12th pass'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    assert len(body['jobs']) == 1
    assert body['jobs'][0]['job_id'] == "UP-POLICE-2024-001"
    assert body['filters_applied']['education'] == ['10th pass', '12th pass']


@patch('src.api.job_search.job_repo')
def test_job_search_with_state_filter(mock_repo, sample_jobs):
    """Test job search filtered by state."""
    # Return only Maharashtra jobs
    filtered_jobs = [job for job in sample_jobs if job.location.state == "Maharashtra"]
    mock_repo.search_jobs.return_value = filtered_jobs
    
    event = {
        'queryStringParameters': {
            'state': 'Maharashtra'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    assert len(body['jobs']) == 2
    assert all(job['location']['state'] == 'Maharashtra' for job in body['jobs'])
    assert body['filters_applied']['state'] == 'Maharashtra'


@patch('src.api.job_search.job_repo')
def test_job_search_with_department_filter(mock_repo, sample_jobs):
    """Test job search filtered by department."""
    filtered_jobs = [job for job in sample_jobs if job.department == "Maharashtra Public Works Department"]
    mock_repo.search_jobs.return_value = filtered_jobs
    
    event = {
        'queryStringParameters': {
            'department': 'Maharashtra Public Works Department'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    assert len(body['jobs']) == 1
    assert body['jobs'][0]['department'] == 'Maharashtra Public Works Department'
    assert body['filters_applied']['department'] == 'Maharashtra Public Works Department'


@patch('src.api.job_search.job_repo')
def test_job_search_with_keyword_query(mock_repo, sample_jobs):
    """Test job search with keyword query."""
    # Return jobs matching "engineer"
    filtered_jobs = [job for job in sample_jobs if "engineer" in job.title.lower()]
    mock_repo.search_jobs.return_value = filtered_jobs
    
    event = {
        'queryStringParameters': {
            'query': 'engineer'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    assert len(body['jobs']) == 1
    assert 'Engineer' in body['jobs'][0]['title']
    assert body['filters_applied']['query'] == 'engineer'


@patch('src.api.job_search.job_repo')
def test_job_search_with_multiple_filters(mock_repo, sample_jobs):
    """Test job search with multiple filters combined."""
    filtered_jobs = [job for job in sample_jobs 
                     if job.location.state == "Maharashtra" 
                     and "B.Sc Nursing" in job.qualifications.get("education", [])]
    mock_repo.search_jobs.return_value = filtered_jobs
    
    event = {
        'queryStringParameters': {
            'state': 'Maharashtra',
            'education': 'B.Sc Nursing,GNM'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    assert len(body['jobs']) == 1
    assert body['jobs'][0]['job_id'] == 'MAHA-HEALTH-2024-001'


@patch('src.api.job_search.job_repo')
def test_job_search_active_only_true(mock_repo, sample_jobs):
    """Test job search with active_only=true (default)."""
    mock_repo.search_jobs.return_value = sample_jobs
    
    event = {
        'queryStringParameters': {
            'active_only': 'true'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Verify that deadline_after filter was applied
    mock_repo.search_jobs.assert_called_once()
    call_args = mock_repo.search_jobs.call_args
    filters = call_args.kwargs['filters']
    assert filters.deadline_after == date.today()


@patch('src.api.job_search.job_repo')
def test_job_search_active_only_false(mock_repo, sample_jobs):
    """Test job search with active_only=false."""
    mock_repo.search_jobs.return_value = sample_jobs
    
    event = {
        'queryStringParameters': {
            'active_only': 'false'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    
    # Verify that deadline_after filter was NOT applied
    call_args = mock_repo.search_jobs.call_args
    filters = call_args.kwargs['filters']
    assert filters.deadline_after is None


@patch('src.api.job_search.job_repo')
def test_job_search_with_limit(mock_repo, sample_jobs):
    """Test job search with custom limit."""
    mock_repo.search_jobs.return_value = sample_jobs[:2]
    
    event = {
        'queryStringParameters': {
            'limit': '2'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    assert len(body['jobs']) == 2
    
    # Verify limit was passed to repository
    call_args = mock_repo.search_jobs.call_args
    assert call_args.kwargs['limit'] == 2


def test_job_search_invalid_limit_too_low():
    """Test job search with invalid limit (too low)."""
    event = {
        'queryStringParameters': {
            'limit': '0'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'Invalid limit' in body['error']


def test_job_search_invalid_limit_too_high():
    """Test job search with invalid limit (too high)."""
    event = {
        'queryStringParameters': {
            'limit': '100'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'Invalid limit' in body['error']


@patch('src.api.job_search.job_repo')
def test_job_search_no_results(mock_repo):
    """Test job search with no matching results."""
    mock_repo.search_jobs.return_value = []
    
    event = {
        'queryStringParameters': {
            'query': 'nonexistent job'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    assert body['jobs'] == []
    assert body['total_count'] == 0


@patch('src.api.job_search.job_repo')
def test_job_search_repository_error(mock_repo):
    """Test job search when repository raises an error."""
    mock_repo.search_jobs.side_effect = Exception("Database connection failed")
    
    event = {
        'queryStringParameters': {}
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert 'Internal server error' in body['error']


@patch('src.api.job_search.job_repo')
def test_job_search_response_structure(mock_repo, sample_jobs):
    """Test that job search response has correct structure."""
    mock_repo.search_jobs.return_value = [sample_jobs[0]]
    
    event = {
        'queryStringParameters': {}
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Verify response structure
    assert 'jobs' in body
    assert 'total_count' in body
    assert 'filters_applied' in body
    
    # Verify job structure
    job = body['jobs'][0]
    assert 'job_id' in job
    assert 'title' in job
    assert 'department' in job
    assert 'description' in job
    assert 'qualifications' in job
    assert 'location' in job
    assert 'application_deadline' in job
    assert 'application_url' in job
    assert 'posted_date' in job
    
    # Verify location structure
    assert 'state' in job['location']
    assert 'district' in job['location']
    assert 'pincode' in job['location']


@patch('src.api.job_search.job_repo')
def test_job_search_null_query_parameters(mock_repo, sample_jobs):
    """Test job search when queryStringParameters is None."""
    mock_repo.search_jobs.return_value = sample_jobs
    
    event = {
        'queryStringParameters': None
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    assert len(body['jobs']) == 3
    assert body['filters_applied']['active_only'] is True
