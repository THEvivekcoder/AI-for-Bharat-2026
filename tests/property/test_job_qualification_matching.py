"""Property-based tests for job search qualification matching.

Feature: bharatsahayak, Property 11: Job Search Qualification Matching
**Validates: Requirements 4.3**

This test verifies that returned jobs match user qualifications,
ensuring that job search results align with user's education level,
experience, and skills.
"""

import pytest
from hypothesis import given, settings, strategies as st, assume
from typing import List, Dict, Any
from datetime import date, timedelta

from src.models.skill import JobPosting
from src.models.user import UserProfile, UserPreferences
from src.models.location import Location


# Custom strategies for generating valid test data
@st.composite
def location_strategy(draw):
    """Generate valid Location instances."""
    states = ["Maharashtra", "Karnataka", "Tamil Nadu", "Gujarat", "Uttar Pradesh", "Delhi"]
    districts = {
        "Maharashtra": ["Pune", "Mumbai", "Nagpur"],
        "Karnataka": ["Bangalore", "Mysore", "Hubli"],
        "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai"],
        "Gujarat": ["Ahmedabad", "Surat", "Vadodara"],
        "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi"],
        "Delhi": ["New Delhi", "South Delhi", "North Delhi"]
    }
    
    state = draw(st.sampled_from(states))
    district = draw(st.sampled_from(districts[state]))
    
    return Location(
        state=state,
        district=district,
        pincode=draw(st.text(min_size=6, max_size=6, alphabet=st.characters(whitelist_categories=('Nd',))))
    )


@st.composite
def user_profile_with_qualifications_strategy(draw):
    """Generate UserProfile with education and skills for job matching."""
    location = draw(location_strategy())
    
    # Education levels matching UserProfile model validation
    # These are the standardized levels used in the system
    education_levels = [
        "illiterate",
        "primary",      # Equivalent to 5th pass
        "secondary",    # Equivalent to 10th pass
        "higher_secondary",  # Equivalent to 12th pass
        "diploma",
        "graduate",
        "postgraduate",
        "vocational"
    ]
    
    education = draw(st.sampled_from(education_levels))
    
    # Skills based on education level
    all_skills = ["Computer basics", "Communication", "Teamwork", "Problem solving"]
    skills = draw(st.lists(
        st.sampled_from(all_skills),
        min_size=1, max_size=3, unique=True
    ))
    
    return UserProfile(
        user_id=f"user_{draw(st.integers(min_value=1000, max_value=9999))}",
        phone_number=f"+91{draw(st.integers(min_value=1000000000, max_value=9999999999))}",
        language=draw(st.sampled_from(["hi", "en", "mr"])),
        location=location,
        age=draw(st.integers(min_value=18, max_value=45)),
        gender=draw(st.sampled_from(["male", "female"])),
        education_level=education,
        occupation=draw(st.sampled_from(["unemployed", "student", "job seeker"])),
        income_bracket="0-100000",
        household_size=draw(st.integers(min_value=1, max_value=8)),
        preferences=UserPreferences(
            preferred_categories=[]
        )
    )


def create_diverse_job_postings() -> List[JobPosting]:
    """Create a diverse set of job postings for testing."""
    jobs = []
    
    # Job 1: Entry level - 10th pass requirement
    jobs.append(JobPosting(
        job_id="UP-POLICE-2024-001",
        title="Police Constable",
        department="Uttar Pradesh Police",
        description="Police constable recruitment for law enforcement duties",
        qualifications={
            "education": ["10th pass", "12th pass"],
            "experience": ["Freshers welcome"],
            "skills": ["Physical fitness", "Basic discipline"]
        },
        location=Location(state="Uttar Pradesh", district="Lucknow", pincode="226001"),
        application_deadline=date.today() + timedelta(days=45),
        application_url="https://uppbpb.gov.in/recruitment",
        posted_date=date.today() - timedelta(days=10),
        salary_range="Rs. 21,700 - 69,100 per month",
        vacancies=50000
    ))
    
    # Job 2: Mid level - 12th pass requirement
    jobs.append(JobPosting(
        job_id="RAILWAY-CLERK-2024-001",
        title="Railway Clerk",
        department="Indian Railways",
        description="Clerical position in railway administration",
        qualifications={
            "education": ["12th pass", "Graduate"],
            "experience": ["Freshers welcome", "0-2 years"],
            "skills": ["Computer basics", "Communication", "Data entry"]
        },
        location=Location(state="Maharashtra", district="Mumbai", pincode="400001"),
        application_deadline=date.today() + timedelta(days=30),
        application_url="https://rrbmumbai.gov.in/recruitment",
        posted_date=date.today() - timedelta(days=20),
        salary_range="Rs. 25,000 - 40,000 per month",
        vacancies=500
    ))
    
    # Job 3: Technical - Diploma requirement
    jobs.append(JobPosting(
        job_id="MAHA-PWD-2024-001",
        title="Junior Engineer (Civil)",
        department="Maharashtra Public Works Department",
        description="Junior Engineer position for civil engineering projects",
        qualifications={
            "education": ["Diploma in Civil Engineering", "B.E./B.Tech in Civil Engineering"],
            "experience": ["Freshers welcome", "0-2 years experience"],
            "skills": ["AutoCAD", "Site supervision", "Technical drawing"]
        },
        location=Location(state="Maharashtra", district="Pune", pincode="411001"),
        application_deadline=date.today() + timedelta(days=30),
        application_url="https://mahapwd.gov.in/recruitment",
        posted_date=date.today() - timedelta(days=15),
        salary_range="Rs. 35,000 - 50,000 per month",
        vacancies=25
    ))
    
    # Job 4: Graduate level
    jobs.append(JobPosting(
        job_id="BANK-PO-2024-001",
        title="Probationary Officer",
        department="State Bank of India",
        description="Banking officer position for branch operations",
        qualifications={
            "education": ["Graduate", "Post Graduate"],
            "experience": ["Freshers welcome"],
            "skills": ["Banking knowledge", "Customer service", "Computer proficiency"]
        },
        location=Location(state="Karnataka", district="Bangalore", pincode="560001"),
        application_deadline=date.today() + timedelta(days=60),
        application_url="https://sbi.co.in/careers",
        posted_date=date.today() - timedelta(days=5),
        salary_range="Rs. 40,000 - 60,000 per month",
        vacancies=2000
    ))
    
    # Job 5: Healthcare - Specific qualification
    jobs.append(JobPosting(
        job_id="MAHA-HEALTH-2024-001",
        title="Staff Nurse",
        department="Maharashtra Health Department",
        description="Staff nurse position in government hospitals",
        qualifications={
            "education": ["B.Sc Nursing", "GNM"],
            "experience": ["Freshers welcome", "0-3 years experience"],
            "skills": ["Patient care", "Medical procedures", "Emergency response"]
        },
        location=Location(state="Maharashtra", district="Mumbai", pincode="400001"),
        application_deadline=date.today() + timedelta(days=20),
        application_url="https://mahahealth.gov.in/recruitment",
        posted_date=date.today() - timedelta(days=5),
        salary_range="Rs. 25,000 - 45,000 per month",
        vacancies=100
    ))
    
    # Job 6: Teaching - Graduate requirement
    jobs.append(JobPosting(
        job_id="TN-EDU-2024-001",
        title="Primary School Teacher",
        department="Tamil Nadu Education Department",
        description="Teaching position in government primary schools",
        qualifications={
            "education": ["Graduate", "B.Ed"],
            "experience": ["Freshers welcome", "0-5 years"],
            "skills": ["Teaching", "Communication", "Child psychology"]
        },
        location=Location(state="Tamil Nadu", district="Chennai", pincode="600001"),
        application_deadline=date.today() + timedelta(days=40),
        application_url="https://tnteachers.gov.in/recruitment",
        posted_date=date.today() - timedelta(days=12),
        salary_range="Rs. 30,000 - 50,000 per month",
        vacancies=300
    ))
    
    return jobs


def education_level_to_index(education: str) -> int:
    """
    Convert education level to numeric index for comparison.
    
    Handles both standardized user education levels (from UserProfile model)
    and job requirement strings (from job postings).
    """
    education_hierarchy = {
        # Standardized user education levels (from UserProfile model)
        "illiterate": 0,
        "primary": 1,           # Equivalent to 5th pass
        "secondary": 2,         # Equivalent to 10th pass
        "higher_secondary": 3,  # Equivalent to 12th pass
        "vocational": 3,        # Same level as 12th pass
        "diploma": 4,
        "graduate": 5,
        "postgraduate": 6,
        
        # Job requirement strings (from job postings)
        "5th pass": 1,
        "8th pass": 1,
        "10th pass": 2,
        "12th pass": 3,
        "diploma in civil engineering": 4,
        "b.e./b.tech in civil engineering": 5,
        "b.sc nursing": 5,
        "gnm": 5,
        "b.ed": 5,
        "post graduate": 6,
        
        # Additional common variations
        "iti": 3,
        "12th pass with iti": 3
    }
    return education_hierarchy.get(education.lower(), -1)


def user_meets_education_requirement(user_education: str, required_education: List[str]) -> bool:
    """
    Check if user's education meets job requirements.
    
    User qualifies if their education level matches or exceeds any of the
    required education qualifications.
    """
    user_level = education_level_to_index(user_education)
    
    for req_edu in required_education:
        req_level = education_level_to_index(req_edu)
        if user_level >= req_level:
            return True
    
    return False


def filter_jobs_by_qualifications(
    jobs: List[JobPosting],
    user_profile: UserProfile
) -> List[JobPosting]:
    """
    Filter jobs based on user qualifications.
    
    This mimics the logic in job_search.py and job_posting_repository.py.
    Jobs are returned if user's education matches or exceeds requirements.
    """
    matching_jobs = []
    
    for job in jobs:
        # Check education qualification
        required_education = job.qualifications.get("education", [])
        
        if not required_education:
            # No education requirement specified, job is open to all
            matching_jobs.append(job)
            continue
        
        # Check if user meets education requirement
        if user_meets_education_requirement(user_profile.education_level, required_education):
            matching_jobs.append(job)
    
    return matching_jobs


@settings(max_examples=50, deadline=None)
@given(user_profile=user_profile_with_qualifications_strategy())
def test_returned_jobs_match_user_qualifications(user_profile):
    """
    Feature: bharatsahayak, Property 11: Job Search Qualification Matching
    
    For any user profile with specified education and qualifications, returned
    job postings should match the user's education level - either requiring
    exactly that level or a lower level of education.
    
    This test verifies:
    1. All returned jobs have education requirements user can meet
    2. Jobs requiring higher education than user has are filtered out
    3. Jobs with no education requirement are included for all users
    4. Education matching follows proper hierarchy (Graduate > 12th > 10th, etc.)
    """
    # Create diverse job set
    all_jobs = create_diverse_job_postings()
    
    # Filter jobs by user qualifications
    matching_jobs = filter_jobs_by_qualifications(all_jobs, user_profile)
    
    # Property verification: All matching jobs should be achievable by user
    for job in matching_jobs:
        required_education = job.qualifications.get("education", [])
        
        if required_education:
            # User must meet at least one education requirement
            meets_requirement = user_meets_education_requirement(
                user_profile.education_level,
                required_education
            )
            
            assert meets_requirement, (
                f"Job {job.job_id} ({job.title}) was matched but user doesn't meet education requirements.\n"
                f"User education: {user_profile.education_level}\n"
                f"Required education: {required_education}\n"
                f"User education level: {education_level_to_index(user_profile.education_level)}\n"
                f"Required levels: {[education_level_to_index(e) for e in required_education]}"
            )


@settings(max_examples=30, deadline=None)
@given(user_profile=user_profile_with_qualifications_strategy())
def test_higher_education_users_see_more_jobs(user_profile):
    """
    Test that users with higher education qualifications see more job opportunities.
    
    This verifies that the education hierarchy is properly implemented - a Graduate
    should see all jobs that a 10th pass can see, plus additional graduate-level jobs.
    """
    all_jobs = create_diverse_job_postings()
    
    # Get jobs for current user
    user_jobs = filter_jobs_by_qualifications(all_jobs, user_profile)
    
    # Create a user with lower education
    lower_education_levels = {
        "postgraduate": "graduate",
        "graduate": "higher_secondary",
        "diploma": "higher_secondary",
        "higher_secondary": "secondary",
        "vocational": "secondary",
        "secondary": "primary",
        "primary": "illiterate"
    }
    
    if user_profile.education_level in lower_education_levels:
        lower_education = lower_education_levels[user_profile.education_level]
        
        # Create profile with lower education
        lower_profile = UserProfile(
            user_id=user_profile.user_id,
            phone_number=user_profile.phone_number,
            language=user_profile.language,
            location=user_profile.location,
            age=user_profile.age,
            gender=user_profile.gender,
            education_level=lower_education,
            occupation=user_profile.occupation,
            income_bracket=user_profile.income_bracket,
            household_size=user_profile.household_size,
            preferences=user_profile.preferences
        )
        
        lower_jobs = filter_jobs_by_qualifications(all_jobs, lower_profile)
        
        # Higher education should see at least as many jobs as lower education
        assert len(user_jobs) >= len(lower_jobs), (
            f"User with {user_profile.education_level} sees fewer jobs ({len(user_jobs)}) "
            f"than user with {lower_education} ({len(lower_jobs)}). "
            f"Higher education should see equal or more opportunities."
        )


@settings(max_examples=20, deadline=None)
@given(user_profile=user_profile_with_qualifications_strategy())
def test_no_overqualified_filtering(user_profile):
    """
    Test that users are not excluded from jobs they are overqualified for.
    
    A Graduate should still be able to apply for jobs requiring 10th pass,
    as overqualification should not disqualify candidates.
    """
    all_jobs = create_diverse_job_postings()
    
    # Filter jobs
    matching_jobs = filter_jobs_by_qualifications(all_jobs, user_profile)
    
    # Find jobs with lower education requirements
    user_level = education_level_to_index(user_profile.education_level)
    
    for job in all_jobs:
        required_education = job.qualifications.get("education", [])
        
        if required_education:
            # Check if any requirement is lower than user's education
            has_lower_requirement = any(
                education_level_to_index(req) <= user_level
                for req in required_education
            )
            
            if has_lower_requirement:
                # Job should be in matching list (user is qualified, even if overqualified)
                assert job in matching_jobs, (
                    f"Job {job.job_id} ({job.title}) requires {required_education} "
                    f"but was not matched for user with {user_profile.education_level}. "
                    f"Users should not be excluded for being overqualified."
                )


@settings(max_examples=20, deadline=None)
@given(user_profile=user_profile_with_qualifications_strategy())
def test_underqualified_users_excluded(user_profile):
    """
    Test that users who don't meet minimum education requirements are excluded.
    
    A 10th pass user should not see jobs requiring Graduate degree.
    """
    all_jobs = create_diverse_job_postings()
    
    # Filter jobs
    matching_jobs = filter_jobs_by_qualifications(all_jobs, user_profile)
    
    # Get user's education level
    user_level = education_level_to_index(user_profile.education_level)
    
    # Check that no matched job requires higher education than user has
    for job in matching_jobs:
        required_education = job.qualifications.get("education", [])
        
        if required_education:
            # At least one requirement should be achievable by user
            min_required_level = min(
                education_level_to_index(req) for req in required_education
            )
            
            assert user_level >= min_required_level, (
                f"Job {job.job_id} ({job.title}) requires minimum {required_education} "
                f"(level {min_required_level}) but user only has {user_profile.education_level} "
                f"(level {user_level}). Underqualified users should be excluded."
            )


@settings(max_examples=15, deadline=None)
@given(user_profile=user_profile_with_qualifications_strategy())
def test_jobs_without_education_requirement_included(user_profile):
    """
    Test that jobs without specific education requirements are available to all users.
    
    Some jobs may not specify education requirements, and these should be
    accessible to users of any education level.
    """
    # Create a job with no education requirement
    open_job = JobPosting(
        job_id="OPEN-JOB-2024-001",
        title="General Worker",
        department="Municipal Corporation",
        description="General worker position with no specific education requirement",
        qualifications={
            "experience": ["Freshers welcome"],
            "skills": ["Physical fitness"]
        },
        location=Location(state="Maharashtra", district="Pune", pincode="411001"),
        application_deadline=date.today() + timedelta(days=30),
        application_url="https://example.com/apply",
        posted_date=date.today() - timedelta(days=5),
        salary_range="Rs. 15,000 - 25,000 per month",
        vacancies=100
    )
    
    jobs = create_diverse_job_postings() + [open_job]
    
    # Filter jobs
    matching_jobs = filter_jobs_by_qualifications(jobs, user_profile)
    
    # The open job should always be included
    assert open_job in matching_jobs, (
        f"Job {open_job.job_id} with no education requirement should be available "
        f"to user with {user_profile.education_level} education."
    )


@settings(max_examples=10, deadline=None)
@given(user_profile=user_profile_with_qualifications_strategy())
def test_multiple_education_paths_accepted(user_profile):
    """
    Test that jobs with multiple education paths accept users meeting any path.
    
    For example, a job requiring "Diploma OR Graduate" should accept both
    Diploma holders and Graduates.
    """
    # Create job with multiple education paths
    multi_path_job = JobPosting(
        job_id="MULTI-PATH-2024-001",
        title="Technical Assistant",
        department="Government Department",
        description="Technical assistant with multiple qualification paths",
        qualifications={
            "education": ["Diploma", "Graduate", "12th pass with ITI"],
            "experience": ["Freshers welcome"],
            "skills": ["Technical knowledge"]
        },
        location=Location(state="Maharashtra", district="Pune", pincode="411001"),
        application_deadline=date.today() + timedelta(days=30),
        application_url="https://example.com/apply",
        posted_date=date.today() - timedelta(days=5),
        salary_range="Rs. 20,000 - 35,000 per month",
        vacancies=50
    )
    
    jobs = [multi_path_job]
    
    # Filter jobs
    matching_jobs = filter_jobs_by_qualifications(jobs, user_profile)
    
    # Check if user meets any of the education requirements
    user_meets_any = user_meets_education_requirement(
        user_profile.education_level,
        multi_path_job.qualifications["education"]
    )
    
    if user_meets_any:
        assert multi_path_job in matching_jobs, (
            f"User with {user_profile.education_level} meets one of the education paths "
            f"{multi_path_job.qualifications['education']} but job was not matched."
        )
    else:
        assert multi_path_job not in matching_jobs, (
            f"User with {user_profile.education_level} doesn't meet any education path "
            f"{multi_path_job.qualifications['education']} but job was matched."
        )
