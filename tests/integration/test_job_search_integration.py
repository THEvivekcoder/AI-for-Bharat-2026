"""Integration tests for job search Lambda handler."""

import json
import pytest
from datetime import date, timedelta
from moto import mock_aws
import boto3

from src.api.job_search import lambda_handler
from src.models.skill import JobPosting
from src.models.location import Location
from src.core.job_posting_repository import JobPostingRepository


@pytest.fixture
def dynamodb_table():
    """Create a mock DynamoDB table for testing."""
    with mock_aws():
        # Create DynamoDB resource
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create table
        table = dynamodb.create_table(
            TableName='bharatsahayak-job-postings-dev',
            KeySchema=[
                {'AttributeName': 'job_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'job_id', 'AttributeType': 'S'},
                {'AttributeName': 'department', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'department-index',
                    'KeySchema': [
                        {'AttributeName': 'department', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            BillingMode='PROVISIONED',
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        
        yield table


@pytest.fixture
def sample_jobs_in_db(dynamodb_table):
    """Load sample job postings into the mock database."""
    repo = JobPostingRepository(table_name='bharatsahayak-job-postings-dev')
    
    jobs = [
        JobPosting(
            job_id="MAHA-PWD-2024-001",
            title="Junior Engineer (Civil)",
            department="Maharashtra Public Works Department",
            description="Junior Engineer position for civil engineering projects including road construction",
            qualifications={
                "education": ["Diploma in Civil Engineering", "B.E./B.Tech in Civil Engineering"],
                "experience": ["Freshers welcome", "0-2 years experience"],
                "skills": ["AutoCAD", "Site supervision", "Quality control"]
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
                "skills": ["Patient care", "Medical procedures", "Emergency response"]
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
        ),
        JobPosting(
            job_id="MAHA-EDUCATION-2024-001",
            title="Primary Teacher",
            department="Maharashtra Education Department",
            description="Primary school teacher position for government schools",
            qualifications={
                "education": ["B.Ed", "D.Ed", "B.A. with B.Ed"],
                "experience": ["Freshers welcome"],
                "skills": ["Teaching", "Child psychology", "Classroom management"]
            },
            location=Location(
                state="Maharashtra",
                district="Nagpur",
                pincode="440001"
            ),
            application_deadline=date.today() - timedelta(days=5),  # Expired
            application_url="https://mahaedu.gov.in/recruitment",
            posted_date=date.today() - timedelta(days=60),
            salary_range="Rs. 30,000 - 55,000 per month",
            vacancies=500
        )
    ]
    
    for job in jobs:
        repo.create(job)
    
    return jobs


def test_job_search_integration_no_filters(dynamodb_table, sample_jobs_in_db):
    """Test job search with no filters (active jobs only by default)."""
    event = {
        'queryStringParameters': {}
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Should return 3 active jobs (excluding expired one)
    assert len(body['jobs']) == 3
    assert body['total_count'] == 3
    
    # Verify expired job is not included
    job_ids = [job['job_id'] for job in body['jobs']]
    assert 'MAHA-EDUCATION-2024-001' not in job_ids


def test_job_search_integration_with_education_filter(dynamodb_table, sample_jobs_in_db):
    """Test job search filtered by education qualifications."""
    event = {
        'queryStringParameters': {
            'education': '10th pass,12th pass'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Should return only the police constable job
    assert len(body['jobs']) >= 1
    
    # Verify at least one job matches the education criteria
    found_constable = any(job['job_id'] == 'UP-POLICE-2024-001' for job in body['jobs'])
    assert found_constable


def test_job_search_integration_with_state_filter(dynamodb_table, sample_jobs_in_db):
    """Test job search filtered by state."""
    event = {
        'queryStringParameters': {
            'state': 'Maharashtra'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Should return 2 active Maharashtra jobs (PWD and Health)
    assert len(body['jobs']) == 2
    
    # Verify all jobs are from Maharashtra
    for job in body['jobs']:
        assert job['location']['state'] == 'Maharashtra'


def test_job_search_integration_with_department_filter(dynamodb_table, sample_jobs_in_db):
    """Test job search filtered by department."""
    event = {
        'queryStringParameters': {
            'department': 'Maharashtra Public Works Department'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Should return only the PWD job
    assert len(body['jobs']) == 1
    assert body['jobs'][0]['job_id'] == 'MAHA-PWD-2024-001'
    assert body['jobs'][0]['department'] == 'Maharashtra Public Works Department'


def test_job_search_integration_with_keyword_query(dynamodb_table, sample_jobs_in_db):
    """Test job search with keyword query."""
    event = {
        'queryStringParameters': {
            'query': 'engineer'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Should return jobs with "engineer" in title or description
    assert len(body['jobs']) >= 1
    
    # Verify at least one job contains "engineer"
    found_engineer = any('engineer' in job['title'].lower() or 'engineer' in job['description'].lower() 
                         for job in body['jobs'])
    assert found_engineer


def test_job_search_integration_active_only_false(dynamodb_table, sample_jobs_in_db):
    """Test job search with active_only=false to include expired jobs."""
    event = {
        'queryStringParameters': {
            'active_only': 'false'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Should return all 4 jobs including expired one
    assert len(body['jobs']) == 4
    
    # Verify expired job is included
    job_ids = [job['job_id'] for job in body['jobs']]
    assert 'MAHA-EDUCATION-2024-001' in job_ids


def test_job_search_integration_with_limit(dynamodb_table, sample_jobs_in_db):
    """Test job search with custom limit."""
    event = {
        'queryStringParameters': {
            'limit': '2'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Should return at most 2 jobs
    assert len(body['jobs']) <= 2


def test_job_search_integration_multiple_filters(dynamodb_table, sample_jobs_in_db):
    """Test job search with multiple filters combined."""
    event = {
        'queryStringParameters': {
            'state': 'Maharashtra',
            'education': 'B.Sc Nursing,GNM',
            'active_only': 'true'
        }
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    
    # Should return only the Staff Nurse job
    assert len(body['jobs']) >= 1
    
    # Verify the nurse job is included
    found_nurse = any(job['job_id'] == 'MAHA-HEALTH-2024-001' for job in body['jobs'])
    assert found_nurse


def test_job_search_integration_response_structure(dynamodb_table, sample_jobs_in_db):
    """Test that job search response has correct structure."""
    event = {
        'queryStringParameters': {}
    }
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    assert 'headers' in response
    assert 'Content-Type' in response['headers']
    assert 'Access-Control-Allow-Origin' in response['headers']
    
    body = json.loads(response['body'])
    
    # Verify response structure
    assert 'jobs' in body
    assert 'total_count' in body
    assert 'filters_applied' in body
    
    # Verify job structure
    if body['jobs']:
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
