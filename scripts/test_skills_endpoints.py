"""Test script for Skills and Employment API endpoints"""
import requests
import json
from datetime import date, timedelta
from decimal import Decimal

BASE_URL = "http://localhost:8000"


def test_list_skills():
    """Test GET /api/skills endpoint"""
    print("\n=== Test: List Skill Programs ===")
    
    response = requests.get(f"{BASE_URL}/api/skills")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        programs = response.json()
        print(f"Found {len(programs)} programs")
        if programs:
            print(f"First program: {programs[0]['name']}")
    else:
        print(f"Error: {response.text}")


def test_match_skills():
    """Test POST /api/skills/match endpoint"""
    print("\n=== Test: Match Skill Programs ===")
    
    payload = {
        "user_profile": {
            "state": "Maharashtra",
            "district": "Mumbai",
            "education_level": "graduate"
        },
        "preferences": {
            "interests": ["digital marketing", "programming"],
            "career_goals": ["tech career"],
            "max_cost": 10000,
            "location_state": "Maharashtra"
        },
        "limit": 5
    }
    
    response = requests.post(f"{BASE_URL}/api/skills/match", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        programs = response.json()
        print(f"Found {len(programs)} matching programs")
        for program in programs:
            print(f"  - {program['name']} (Score: {program.get('relevance_score', 0):.2f})")
            print(f"    {program.get('match_reason', 'N/A')}")
    else:
        print(f"Error: {response.text}")


def test_list_jobs():
    """Test GET /api/jobs endpoint"""
    print("\n=== Test: List Job Postings ===")
    
    response = requests.get(f"{BASE_URL}/api/jobs")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        jobs = response.json()
        print(f"Found {len(jobs)} jobs")
        if jobs:
            print(f"First job: {jobs[0]['title']}")
    else:
        print(f"Error: {response.text}")


def test_search_jobs():
    """Test POST /api/jobs/search endpoint"""
    print("\n=== Test: Search Jobs with Matching ===")
    
    payload = {
        "qualifications": {
            "education_level": "graduate",
            "degree": "Computer Science",
            "experience_years": 0,
            "skills": ["Python", "JavaScript"]
        },
        "preferences": {
            "departments": ["Department of Electronics and IT"],
            "locations": ["Maharashtra"]
        },
        "limit": 5
    }
    
    response = requests.post(f"{BASE_URL}/api/jobs/search", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        jobs = response.json()
        print(f"Found {len(jobs)} matching jobs")
        for job in jobs:
            print(f"  - {job['title']} (Score: {job.get('match_score', 0):.2f})")
            print(f"    {job.get('match_reason', 'N/A')}")
    else:
        print(f"Error: {response.text}")


def test_job_alerts():
    """Test POST /api/jobs/alerts endpoint"""
    print("\n=== Test: Get Job Alerts ===")
    
    payload = {
        "user_profile": {
            "education_level": "graduate"
        },
        "qualifications": {
            "education_level": "graduate",
            "degree": "Agriculture",
            "experience_years": 2,
            "skills": ["Agriculture"]
        },
        "preferences": {
            "departments": ["Ministry of Agriculture"],
            "locations": ["Maharashtra"]
        },
        "days_back": 30
    }
    
    response = requests.post(f"{BASE_URL}/api/jobs/alerts", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        jobs = response.json()
        print(f"Found {len(jobs)} recent job postings")
        for job in jobs:
            print(f"  - {job['title']} (Score: {job.get('match_score', 0):.2f})")
    else:
        print(f"Error: {response.text}")


def main():
    """Main test function"""
    print("Skills and Employment API Endpoints Test")
    print("=" * 50)
    print("Make sure the server is running on http://localhost:8000")
    print("=" * 50)
    
    try:
        # Test endpoints
        test_list_skills()
        test_match_skills()
        test_list_jobs()
        test_search_jobs()
        test_job_alerts()
        
        print("\n" + "=" * 50)
        print("All endpoint tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to server.")
        print("Please start the server with: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
