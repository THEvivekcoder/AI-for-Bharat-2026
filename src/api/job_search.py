"""Lambda handler for searching government job postings."""

import json
import os
import logging
from typing import Dict, Any, List
from datetime import date

import boto3
from botocore.exceptions import ClientError

from src.models.skill import JobPosting
from src.models.location import Location
from src.core.job_posting_repository import JobPostingRepository, JobPostingFilters

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize repository
JOBS_TABLE = os.environ.get('JOB_POSTINGS_TABLE', 'bharatsahayak-job-postings-dev')
job_repo = JobPostingRepository(table_name=JOBS_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle GET /jobs requests.
    
    Filters jobs by qualifications, location, and other criteria.
    Returns jobs matching user education level and preferences.
    
    Query Parameters:
    - query: Search keywords (optional)
    - department: Filter by government department (optional)
    - state: Filter by state (optional)
    - education: Comma-separated list of education qualifications (optional)
    - active_only: Return only jobs with deadline not passed (default: true)
    - limit: Maximum number of results (default: 20, max: 50)
    
    Example:
    GET /jobs?education=10th pass,12th pass&state=Maharashtra&active_only=true&limit=10
    
    Response:
    {
        "jobs": [
            {
                "job_id": "MAHA-PWD-2024-001",
                "title": "Junior Engineer (Civil)",
                "department": "Maharashtra Public Works Department",
                "description": "...",
                "qualifications": {
                    "education": ["Diploma in Civil Engineering", "B.E./B.Tech in Civil Engineering"],
                    "experience": ["Freshers welcome"],
                    "skills": ["AutoCAD", "Site supervision"]
                },
                "location": {
                    "state": "Maharashtra",
                    "district": "Pune",
                    "pincode": "411001"
                },
                "application_deadline": "2024-03-31",
                "application_url": "https://mahapwd.gov.in/recruitment",
                "posted_date": "2024-01-15",
                "salary_range": "Rs. 35,000 - 50,000 per month",
                "vacancies": 25
            }
        ],
        "total_count": 5,
        "filters_applied": {
            "education": ["10th pass", "12th pass"],
            "state": "Maharashtra",
            "active_only": true
        }
    }
    """
    try:
        # Parse query parameters
        params = event.get('queryStringParameters') or {}
        
        query = params.get('query')
        department = params.get('department')
        state = params.get('state')
        education_str = params.get('education')
        active_only = params.get('active_only', 'true').lower() == 'true'
        limit = int(params.get('limit', '20'))
        
        # Validate limit
        if limit < 1 or limit > 50:
            return error_response(400, "Invalid limit: must be between 1 and 50")
        
        # Parse education qualifications
        education = None
        if education_str:
            education = [e.strip() for e in education_str.split(',') if e.strip()]
        
        logger.info(f"Job search: query={query}, department={department}, state={state}, "
                   f"education={education}, active_only={active_only}, limit={limit}")
        
        # Build filters
        filters = JobPostingFilters(
            department=department,
            state=state,
            education=education,
            deadline_after=date.today() if active_only else None
        )
        
        # Search jobs
        jobs = job_repo.search_jobs(query=query, filters=filters, limit=limit)
        logger.info(f"Found {len(jobs)} matching jobs")
        
        # Build response
        response_data = {
            'jobs': [_build_job_response(job) for job in jobs],
            'total_count': len(jobs),
            'filters_applied': {
                'query': query,
                'department': department,
                'state': state,
                'education': education,
                'active_only': active_only
            }
        }
        
        return success_response(response_data)
        
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return error_response(400, str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return error_response(500, "Internal server error")


def _build_job_response(job: JobPosting) -> Dict[str, Any]:
    """Build response object for a job posting."""
    return {
        'job_id': job.job_id,
        'title': job.title,
        'department': job.department,
        'description': job.description,
        'qualifications': job.qualifications,
        'location': {
            'state': job.location.state,
            'district': job.location.district,
            'pincode': job.location.pincode
        },
        'application_deadline': job.application_deadline.isoformat(),
        'application_url': job.application_url,
        'posted_date': job.posted_date.isoformat(),
        'salary_range': job.salary_range,
        'vacancies': job.vacancies
    }


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
