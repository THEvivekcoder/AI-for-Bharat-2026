"""Test script for Skills and Employment Service"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.skills import SkillProgram, JobPosting
from app.services.skills_matcher import SkillsMatcher
from app.services.job_matcher import JobMatcher
from app.schemas.skills import SkillPreferences, Qualifications, JobPreferences
from datetime import date, timedelta
import uuid
from decimal import Decimal


def create_test_data(db: Session):
    """Create test skill programs and job postings"""
    print("Creating test data...")
    
    # Create skill programs
    programs = [
        SkillProgram(
            program_id=uuid.uuid4(),
            name="Digital Marketing Certification",
            provider="National Skill Development Corporation",
            category="digital",
            description="Learn digital marketing, SEO, social media marketing, and analytics",
            duration_weeks=12,
            cost=Decimal("5000.00"),
            state="Maharashtra",
            district="Mumbai",
            mode="hybrid",
            eligibility_criteria={"education": ["12th", "graduate"]},
            certification=True,
            placement_support=True,
            registration_url="https://example.com/digital-marketing",
            contact="contact@nsdc.gov.in"
        ),
        SkillProgram(
            program_id=uuid.uuid4(),
            name="Plumbing and Electrical Work",
            provider="Ministry of Skill Development",
            category="vocational",
            description="Hands-on training in plumbing and electrical installations",
            duration_weeks=8,
            cost=Decimal("2000.00"),
            state="Maharashtra",
            district="Pune",
            mode="in-person",
            eligibility_criteria={"education": ["10th", "12th"]},
            certification=True,
            placement_support=False,
            registration_url="https://example.com/plumbing",
            contact="contact@msde.gov.in"
        ),
        SkillProgram(
            program_id=uuid.uuid4(),
            name="Python Programming for Beginners",
            provider="NIELIT",
            category="technical",
            description="Learn Python programming from scratch with hands-on projects",
            duration_weeks=16,
            cost=Decimal("8000.00"),
            state=None,  # Online, available everywhere
            district=None,
            mode="online",
            eligibility_criteria={"education": ["12th", "graduate", "postgraduate"]},
            certification=True,
            placement_support=True,
            registration_url="https://example.com/python",
            contact="contact@nielit.gov.in"
        ),
        SkillProgram(
            program_id=uuid.uuid4(),
            name="Entrepreneurship Development Program",
            provider="Ministry of MSME",
            category="entrepreneurship",
            description="Learn how to start and manage your own business",
            duration_weeks=6,
            cost=Decimal("3000.00"),
            state="Maharashtra",
            district="Mumbai",
            mode="in-person",
            eligibility_criteria={"education": ["graduate", "postgraduate"]},
            certification=False,
            placement_support=False,
            registration_url="https://example.com/entrepreneurship",
            contact="contact@msme.gov.in"
        )
    ]
    
    for program in programs:
        db.add(program)
    
    # Create job postings
    jobs = [
        JobPosting(
            job_id=uuid.uuid4(),
            title="Junior Software Developer",
            department="Department of Electronics and IT",
            description="Develop and maintain government web applications",
            qualifications={
                "education_level": "graduate",
                "degree": "Computer Science or IT",
                "experience_years": 0,
                "skills": ["Python", "JavaScript", "SQL"]
            },
            location={
                "state": "Maharashtra",
                "district": "Mumbai"
            },
            application_deadline=date.today() + timedelta(days=30),
            application_url="https://example.com/apply/software-dev",
            posted_date=date.today() - timedelta(days=5)
        ),
        JobPosting(
            job_id=uuid.uuid4(),
            title="Data Entry Operator",
            department="Ministry of Statistics",
            description="Enter and verify data in government databases",
            qualifications={
                "education_level": "12th",
                "experience_years": 0,
                "skills": ["Typing", "MS Office"]
            },
            location={
                "state": "Maharashtra",
                "district": "Pune"
            },
            application_deadline=date.today() + timedelta(days=15),
            application_url="https://example.com/apply/data-entry",
            posted_date=date.today() - timedelta(days=2)
        ),
        JobPosting(
            job_id=uuid.uuid4(),
            title="Agricultural Extension Officer",
            department="Ministry of Agriculture",
            description="Provide agricultural guidance to farmers in rural areas",
            qualifications={
                "education_level": "graduate",
                "degree": "Agriculture or related field",
                "experience_years": 2,
                "skills": ["Agriculture", "Communication"]
            },
            location={
                "state": "Maharashtra",
                "locations": [
                    {"state": "Maharashtra", "district": "Nashik"},
                    {"state": "Maharashtra", "district": "Ahmednagar"}
                ]
            },
            application_deadline=date.today() + timedelta(days=45),
            application_url="https://example.com/apply/agri-officer",
            posted_date=date.today() - timedelta(days=10)
        ),
        JobPosting(
            job_id=uuid.uuid4(),
            title="Primary School Teacher",
            department="Ministry of Education",
            description="Teach primary school students in government schools",
            qualifications={
                "education_level": "graduate",
                "degree": "B.Ed or equivalent",
                "experience_years": 0,
                "skills": ["Teaching", "Child Psychology"]
            },
            location={
                "state": "Maharashtra",
                "district": "Mumbai"
            },
            application_deadline=date.today() + timedelta(days=20),
            application_url="https://example.com/apply/teacher",
            posted_date=date.today() - timedelta(days=7)
        )
    ]
    
    for job in jobs:
        db.add(job)
    
    db.commit()
    print(f"Created {len(programs)} skill programs and {len(jobs)} job postings")


def test_skills_matcher(db: Session):
    """Test skills matcher functionality"""
    print("\n=== Testing Skills Matcher ===")
    
    matcher = SkillsMatcher(db)
    
    # Test 1: Match programs for a user interested in digital skills
    print("\nTest 1: User interested in digital marketing")
    user_profile = {
        "state": "Maharashtra",
        "district": "Mumbai",
        "education_level": "graduate"
    }
    preferences = SkillPreferences(
        interests=["digital marketing", "social media"],
        career_goals=["marketing career"],
        max_cost=Decimal("10000.00"),
        location_state="Maharashtra"
    )
    
    matched_programs = matcher.match_programs(user_profile, preferences, limit=5)
    print(f"Found {len(matched_programs)} matching programs:")
    for program in matched_programs:
        print(f"  - {program.name} (Score: {program.relevance_score:.2f})")
        print(f"    Reason: {program.match_reason}")
    
    # Test 2: Match programs for a user interested in technical skills
    print("\nTest 2: User interested in programming")
    preferences = SkillPreferences(
        interests=["programming", "software development"],
        current_skills=["basic computer"],
        max_duration_weeks=20,
        preferred_mode="online"
    )
    
    matched_programs = matcher.match_programs(user_profile, preferences, limit=5)
    print(f"Found {len(matched_programs)} matching programs:")
    for program in matched_programs:
        print(f"  - {program.name} (Score: {program.relevance_score:.2f})")
        print(f"    Reason: {program.match_reason}")
    
    # Test 3: Get all programs
    print("\nTest 3: Get all programs")
    all_programs = matcher.get_all_programs(limit=10)
    print(f"Total programs: {len(all_programs)}")


def test_job_matcher(db: Session):
    """Test job matcher functionality"""
    print("\n=== Testing Job Matcher ===")
    
    matcher = JobMatcher(db)
    
    # Test 1: Search jobs for a fresh graduate
    print("\nTest 1: Fresh graduate looking for software jobs")
    qualifications = Qualifications(
        education_level="graduate",
        degree="Computer Science",
        experience_years=0,
        skills=["Python", "JavaScript"]
    )
    preferences = JobPreferences(
        departments=["Department of Electronics and IT"],
        locations=["Maharashtra"]
    )
    
    matched_jobs = matcher.search_jobs(qualifications, preferences, limit=5)
    print(f"Found {len(matched_jobs)} matching jobs:")
    for job in matched_jobs:
        print(f"  - {job.title} (Score: {job.match_score:.2f})")
        print(f"    Department: {job.department}")
        print(f"    Reason: {job.match_reason}")
        print(f"    Deadline: {job.application_deadline}")
    
    # Test 2: Search jobs for 12th pass candidate
    print("\nTest 2: 12th pass candidate looking for entry-level jobs")
    qualifications = Qualifications(
        education_level="12th",
        experience_years=0,
        skills=["Typing", "MS Office"]
    )
    preferences = JobPreferences(
        locations=["Maharashtra", "Pune"]
    )
    
    matched_jobs = matcher.search_jobs(qualifications, preferences, limit=5)
    print(f"Found {len(matched_jobs)} matching jobs:")
    for job in matched_jobs:
        print(f"  - {job.title} (Score: {job.match_score:.2f})")
        print(f"    Reason: {job.match_reason}")
    
    # Test 3: Get job alerts (recent postings)
    print("\nTest 3: Job alerts for experienced agriculture graduate")
    user_profile = {
        "education_level": "graduate",
        "occupation": "farmer"
    }
    qualifications = Qualifications(
        education_level="graduate",
        degree="Agriculture",
        experience_years=2,
        skills=["Agriculture", "Communication"]
    )
    preferences = JobPreferences(
        departments=["Ministry of Agriculture"],
        locations=["Maharashtra"]
    )
    
    job_alerts = matcher.get_job_alerts(
        user_profile, qualifications, preferences, days_back=30
    )
    print(f"Found {len(job_alerts)} recent job postings:")
    for job in job_alerts:
        print(f"  - {job.title} (Score: {job.match_score:.2f})")
        print(f"    Posted: {job.posted_date}")
        print(f"    Reason: {job.match_reason}")


def main():
    """Main test function"""
    print("Skills and Employment Service Test")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Create test data
        create_test_data(db)
        
        # Test skills matcher
        test_skills_matcher(db)
        
        # Test job matcher
        test_job_matcher(db)
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
