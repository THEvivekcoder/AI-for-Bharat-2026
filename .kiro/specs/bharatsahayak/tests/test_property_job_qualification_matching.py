"""
Property-Based Test: Job Search Qualification Matching
Feature: bharatsahayak, Property 11: Job Search Qualification Matching

For any job search with specified qualifications, all returned job postings 
should have qualification requirements that the user meets or are within one 
level of the user's education.

Validates: Requirements 4.3
"""
import pytest
import os
from hypothesis import given, settings, strategies as st, HealthCheck, assume
from hypothesis.strategies import composite
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.skills import JobPosting
from app.services.job_matcher import JobMatcher
from app.schemas.skills import Qualifications, JobPreferences
import uuid


# Strategy for generating job qualifications
@composite
def job_qualifications_strategy(draw):
    """Generate valid job qualification requirements"""
    education_levels = ['10th', '12th', 'diploma', 'graduate', 'postgraduate', 'doctorate']
    
    qualifications = {}
    
    # Education requirement
    if draw(st.booleans()):
        qualifications['education_level'] = draw(st.sampled_from(education_levels))
    
    # Experience requirement
    if draw(st.booleans()):
        qualifications['experience_years'] = draw(st.integers(min_value=0, max_value=15))
    
    # Skills requirement
    if draw(st.booleans()):
        all_skills = [
            'computer skills', 'communication', 'leadership', 'management',
            'accounting', 'data entry', 'typing', 'driving', 'teaching',
            'engineering', 'medical', 'legal', 'administrative'
        ]
        qualifications['skills'] = draw(st.lists(
            st.sampled_from(all_skills),
            min_size=1, max_size=4, unique=True
        ))
    
    return qualifications


# Strategy for generating job postings
@composite
def job_posting_strategy(draw):
    """Generate a valid government job posting"""
    departments = [
        'Ministry of Education',
        'Ministry of Health',
        'Ministry of Agriculture',
        'Ministry of Rural Development',
        'Ministry of Finance',
        'State Government',
        'District Administration',
        'Public Works Department'
    ]
    
    job_titles = [
        'Junior Clerk',
        'Data Entry Operator',
        'Assistant Teacher',
        'Health Worker',
        'Agricultural Extension Officer',
        'Accountant',
        'Stenographer',
        'Technical Assistant',
        'Lab Technician',
        'Driver',
        'Peon',
        'Office Assistant'
    ]
    
    states = ['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh', 'Bihar', 'Gujarat']
    districts = ['District A', 'District B', 'District C', 'District D']
    
    # Generate location
    location = None
    if draw(st.booleans()):
        location = {
            'state': draw(st.sampled_from(states)),
            'district': draw(st.sampled_from(districts))
        }
    
    # Generate deadline (some jobs have deadlines, some don't)
    deadline = None
    if draw(st.booleans()):
        days_ahead = draw(st.integers(min_value=1, max_value=90))
        deadline = date.today() + timedelta(days=days_ahead)
    
    # Generate posted date
    days_ago = draw(st.integers(min_value=0, max_value=60))
    posted_date = date.today() - timedelta(days=days_ago)
    
    return {
        'job_id': uuid.uuid4(),
        'title': draw(st.sampled_from(job_titles)),
        'department': draw(st.sampled_from(departments)),
        'description': f'Government job posting for {draw(st.sampled_from(job_titles))}',
        'qualifications': draw(job_qualifications_strategy()),
        'location': location,
        'application_deadline': deadline,
        'application_url': f'https://jobs.gov.in/apply/{uuid.uuid4()}',
        'posted_date': posted_date,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }


# Strategy for generating user qualifications
@composite
def user_qualifications_strategy(draw):
    """Generate user qualifications for job matching"""
    education_levels = ['below_10th', '10th', '12th', 'diploma', 'graduate', 'postgraduate', 'doctorate']
    
    all_skills = [
        'computer skills', 'communication', 'leadership', 'management',
        'accounting', 'data entry', 'typing', 'driving', 'teaching',
        'engineering', 'medical', 'legal', 'administrative'
    ]
    
    return Qualifications(
        education_level=draw(st.sampled_from(education_levels)),
        degree=draw(st.one_of(st.none(), st.sampled_from(['BA', 'BSc', 'BCom', 'MA', 'MSc', 'MBA', 'PhD']))),
        experience_years=draw(st.integers(min_value=0, max_value=20)),
        skills=draw(st.lists(
            st.sampled_from(all_skills),
            min_size=0, max_size=5, unique=True
        )),
        certifications=draw(st.lists(
            st.sampled_from(['CCC', 'Typing Certificate', 'Driving License', 'First Aid']),
            min_size=0, max_size=3, unique=True
        ))
    )


# Strategy for generating job preferences
@composite
def job_preferences_strategy(draw):
    """Generate job search preferences"""
    departments = [
        'Ministry of Education',
        'Ministry of Health',
        'Ministry of Agriculture',
        'State Government'
    ]
    
    locations = ['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Bihar']
    
    return JobPreferences(
        departments=draw(st.lists(
            st.sampled_from(departments),
            min_size=0, max_size=3, unique=True
        )),
        locations=draw(st.lists(
            st.sampled_from(locations),
            min_size=0, max_size=3, unique=True
        ))
    )


@pytest.fixture(scope="function")
def test_db_session():
    """Create a test database session"""
    from sqlalchemy.types import TypeDecorator, CHAR
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    from sqlalchemy import Table, Column, String, DateTime, Text, Date
    from sqlalchemy import JSON
    import uuid as uuid_module
    
    class UUID(TypeDecorator):
        """Platform-independent UUID type."""
        impl = CHAR
        cache_ok = True
        
        def load_dialect_impl(self, dialect):
            if dialect.name == 'postgresql':
                return dialect.type_descriptor(PG_UUID())
            else:
                return dialect.type_descriptor(CHAR(36))
        
        def process_bind_param(self, value, dialect):
            if value is None:
                return value
            elif not isinstance(value, uuid_module.UUID):
                return str(uuid_module.UUID(value)) if value else None
            else:
                return str(value)
        
        def process_result_value(self, value, dialect):
            if value is None:
                return value
            return uuid_module.UUID(value) if value else None
    
    # Create engine
    engine = create_engine('sqlite:///:memory:', echo=False)
    
    # Create job postings table manually for SQLite compatibility
    from sqlalchemy import MetaData
    metadata = MetaData()
    
    job_postings_table = Table(
        'job_postings', metadata,
        Column('job_id', UUID(), primary_key=True),
        Column('title', String(255), nullable=False),
        Column('department', String(100), nullable=True),
        Column('description', Text, nullable=True),
        Column('qualifications', JSON, nullable=True),
        Column('location', JSON, nullable=True),
        Column('application_deadline', Date, nullable=True),
        Column('application_url', String(500), nullable=True),
        Column('posted_date', Date, nullable=True),
        Column('created_at', DateTime, nullable=False),
        Column('updated_at', DateTime, nullable=False)
    )
    
    metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


def add_jobs_to_db(session, jobs_data):
    """Helper to add job postings to test database"""
    # Clear existing jobs first
    session.query(JobPosting).delete()
    session.commit()
    
    jobs = []
    for job_data in jobs_data:
        job = JobPosting(**job_data)
        session.add(job)
        jobs.append(job)
    
    session.commit()
    return jobs


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    jobs=st.lists(job_posting_strategy(), min_size=5, max_size=20),
    qualifications=user_qualifications_strategy(),
    preferences=job_preferences_strategy()
)
def test_job_qualification_matching_education_level(jobs, qualifications, preferences, test_db_session):
    """
    Feature: bharatsahayak, Property 11: Job Search Qualification Matching
    
    For any job search with specified qualifications, all returned job postings 
    should have qualification requirements that the user meets or are within one 
    level of the user's education.
    
    This is the core property test validating education level matching.
    """
    # Add jobs to database
    add_jobs_to_db(test_db_session, jobs)
    
    # Create matcher and search jobs
    matcher = JobMatcher(test_db_session)
    results = matcher.search_jobs(qualifications, preferences, limit=50)
    
    # Define education level hierarchy
    education_hierarchy = {
        'below_10th': 0,
        '10th': 1,
        '12th': 2,
        'diploma': 3,
        'graduate': 4,
        'postgraduate': 5,
        'doctorate': 6
    }
    
    user_level = education_hierarchy.get(
        qualifications.education_level.lower() if qualifications.education_level else 'below_10th',
        0
    )
    
    # Property: All returned jobs should have education requirements the user meets
    # or are within one level below user's education
    for job_response in results:
        if job_response.qualifications and job_response.qualifications.get('education_level'):
            required_education = job_response.qualifications['education_level'].lower()
            required_level = education_hierarchy.get(required_education, 0)
            
            # User should meet requirement or be within one level
            assert user_level >= required_level - 1, \
                f"Job '{job_response.title}' requires {required_education} (level {required_level}), " \
                f"but user has {qualifications.education_level} (level {user_level}). " \
                f"User should be within one level of requirement."


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    jobs=st.lists(job_posting_strategy(), min_size=5, max_size=15),
    qualifications=user_qualifications_strategy(),
    preferences=job_preferences_strategy()
)
def test_job_qualification_matching_no_expired_jobs(jobs, qualifications, preferences, test_db_session):
    """
    Feature: bharatsahayak, Property 11: Job Search Qualification Matching
    
    Returned jobs should not include expired postings (past application deadline).
    """
    # Add jobs to database
    add_jobs_to_db(test_db_session, jobs)
    
    # Create matcher and search jobs
    matcher = JobMatcher(test_db_session)
    results = matcher.search_jobs(qualifications, preferences, limit=50)
    
    # Property: No expired jobs should be returned
    today = date.today()
    for job_response in results:
        if job_response.application_deadline:
            assert job_response.application_deadline >= today, \
                f"Job '{job_response.title}' has expired deadline {job_response.application_deadline}"


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    jobs=st.lists(job_posting_strategy(), min_size=5, max_size=15),
    qualifications=user_qualifications_strategy(),
    preferences=job_preferences_strategy()
)
def test_job_qualification_matching_department_filter(jobs, qualifications, preferences, test_db_session):
    """
    Feature: bharatsahayak, Property 11: Job Search Qualification Matching
    
    When department preferences are specified, only jobs from those departments should be returned.
    """
    # Add jobs to database
    add_jobs_to_db(test_db_session, jobs)
    
    # Create matcher and search jobs
    matcher = JobMatcher(test_db_session)
    results = matcher.search_jobs(qualifications, preferences, limit=50)
    
    # Property: If department filter is specified, all results should match
    if preferences.departments:
        for job_response in results:
            assert job_response.department in preferences.departments, \
                f"Job department '{job_response.department}' should be in preferred departments {preferences.departments}"


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    jobs=st.lists(job_posting_strategy(), min_size=5, max_size=15),
    qualifications=user_qualifications_strategy(),
    preferences=job_preferences_strategy()
)
def test_job_qualification_matching_location_filter(jobs, qualifications, preferences, test_db_session):
    """
    Feature: bharatsahayak, Property 11: Job Search Qualification Matching
    
    When location preferences are specified, only jobs in those locations should be returned.
    """
    # Add jobs to database
    add_jobs_to_db(test_db_session, jobs)
    
    # Create matcher and search jobs
    matcher = JobMatcher(test_db_session)
    results = matcher.search_jobs(qualifications, preferences, limit=50)
    
    # Property: If location filter is specified, all results should match
    if preferences.locations:
        for job_response in results:
            if job_response.location:
                # Check if job location matches any preferred location
                job_state = job_response.location.get('state', '').lower()
                job_district = job_response.location.get('district', '').lower()
                
                location_match = False
                for pref_loc in preferences.locations:
                    pref_loc_lower = pref_loc.lower()
                    if pref_loc_lower in job_state or pref_loc_lower in job_district:
                        location_match = True
                        break
                
                assert location_match, \
                    f"Job location {job_response.location} should match preferred locations {preferences.locations}"


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    jobs=st.lists(job_posting_strategy(), min_size=5, max_size=15),
    qualifications=user_qualifications_strategy(),
    preferences=job_preferences_strategy()
)
def test_job_qualification_matching_score_ordering(jobs, qualifications, preferences, test_db_session):
    """
    Feature: bharatsahayak, Property 11: Job Search Qualification Matching
    
    Jobs should be ranked by match score, with higher scores appearing first.
    """
    # Add jobs to database
    add_jobs_to_db(test_db_session, jobs)
    
    # Create matcher and search jobs
    matcher = JobMatcher(test_db_session)
    results = matcher.search_jobs(qualifications, preferences, limit=50)
    
    # Property: Results should be sorted by match_score descending
    for i in range(len(results) - 1):
        assert results[i].match_score >= results[i+1].match_score, \
            f"Jobs should be sorted by match score descending. " \
            f"Job {i} score: {results[i].match_score}, " \
            f"Job {i+1} score: {results[i+1].match_score}"
    
    # Property: All match scores should be between 0 and 1
    for job in results:
        assert 0.0 <= job.match_score <= 1.0, \
            f"Match score should be between 0 and 1, got {job.match_score}"


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    jobs=st.lists(job_posting_strategy(), min_size=5, max_size=15),
    qualifications=user_qualifications_strategy(),
    preferences=job_preferences_strategy()
)
def test_job_qualification_matching_reason_presence(jobs, qualifications, preferences, test_db_session):
    """
    Feature: bharatsahayak, Property 11: Job Search Qualification Matching
    
    All matched jobs should include a match_reason explaining why they were recommended.
    """
    # Add jobs to database
    add_jobs_to_db(test_db_session, jobs)
    
    # Create matcher and search jobs
    matcher = JobMatcher(test_db_session)
    results = matcher.search_jobs(qualifications, preferences, limit=50)
    
    # Property: All results should have a match_reason
    for job in results:
        assert job.match_reason is not None, \
            f"Job '{job.title}' should have a match_reason"
        assert len(job.match_reason) > 0, \
            f"Job '{job.title}' match_reason should not be empty"
        assert isinstance(job.match_reason, str), \
            f"Job '{job.title}' match_reason should be a string"


# Concrete example tests to complement property-based tests

def test_job_qualification_matching_exact_education_match(test_db_session):
    """
    Specific example: User with graduate degree should match graduate-level jobs.
    """
    jobs_data = [
        {
            'job_id': uuid.uuid4(),
            'title': 'Assistant Teacher',
            'department': 'Ministry of Education',
            'description': 'Teaching position in government school',
            'qualifications': {
                'education_level': 'graduate',
                'experience_years': 0
            },
            'location': {'state': 'Maharashtra', 'district': 'Mumbai'},
            'application_deadline': date.today() + timedelta(days=30),
            'application_url': 'https://jobs.gov.in/apply/123',
            'posted_date': date.today() - timedelta(days=5),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'job_id': uuid.uuid4(),
            'title': 'Senior Officer',
            'department': 'Ministry of Finance',
            'description': 'Senior administrative position',
            'qualifications': {
                'education_level': 'postgraduate',
                'experience_years': 5
            },
            'location': {'state': 'Maharashtra', 'district': 'Mumbai'},
            'application_deadline': date.today() + timedelta(days=30),
            'application_url': 'https://jobs.gov.in/apply/124',
            'posted_date': date.today() - timedelta(days=5),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ]
    
    add_jobs_to_db(test_db_session, jobs_data)
    
    # User with graduate degree
    qualifications = Qualifications(
        education_level='graduate',
        experience_years=0,
        skills=['teaching', 'communication']
    )
    
    preferences = JobPreferences(
        departments=[],
        locations=['Maharashtra']
    )
    
    matcher = JobMatcher(test_db_session)
    results = matcher.search_jobs(qualifications, preferences, limit=10)
    
    # Should find both jobs (graduate matches graduate, and is within one level of postgraduate)
    assert len(results) >= 1, "Should find matching jobs"
    
    # Assistant Teacher should be in results
    teacher_job = next((j for j in results if 'Teacher' in j.title), None)
    assert teacher_job is not None, "Should find teacher job for graduate"


def test_job_qualification_matching_one_level_below(test_db_session):
    """
    Specific example: User with diploma should match jobs requiring graduate (one level below).
    """
    jobs_data = [
        {
            'job_id': uuid.uuid4(),
            'title': 'Junior Clerk',
            'department': 'State Government',
            'description': 'Clerical position',
            'qualifications': {
                'education_level': 'graduate',
                'experience_years': 0
            },
            'location': {'state': 'Karnataka', 'district': 'Bangalore'},
            'application_deadline': date.today() + timedelta(days=30),
            'application_url': 'https://jobs.gov.in/apply/125',
            'posted_date': date.today() - timedelta(days=3),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ]
    
    add_jobs_to_db(test_db_session, jobs_data)
    
    # User with diploma (one level below graduate: diploma=3, graduate=4)
    qualifications = Qualifications(
        education_level='diploma',
        experience_years=0,
        skills=['computer skills', 'typing']
    )
    
    preferences = JobPreferences(
        departments=[],
        locations=['Karnataka']
    )
    
    matcher = JobMatcher(test_db_session)
    results = matcher.search_jobs(qualifications, preferences, limit=10)
    
    # Should find the job (diploma is within one level of graduate)
    assert len(results) >= 1, "Should find jobs within one education level"
    assert 'Clerk' in results[0].title, "Should find clerk job"


def test_job_qualification_matching_expired_jobs_excluded(test_db_session):
    """
    Test that expired jobs are not returned.
    """
    jobs_data = [
        {
            'job_id': uuid.uuid4(),
            'title': 'Active Job',
            'department': 'Ministry of Health',
            'description': 'Active job posting',
            'qualifications': {'education_level': '12th'},
            'location': {'state': 'Tamil Nadu', 'district': 'Chennai'},
            'application_deadline': date.today() + timedelta(days=15),  # Future deadline
            'application_url': 'https://jobs.gov.in/apply/126',
            'posted_date': date.today() - timedelta(days=5),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'job_id': uuid.uuid4(),
            'title': 'Expired Job',
            'department': 'Ministry of Health',
            'description': 'Expired job posting',
            'qualifications': {'education_level': '12th'},
            'location': {'state': 'Tamil Nadu', 'district': 'Chennai'},
            'application_deadline': date.today() - timedelta(days=5),  # Past deadline
            'application_url': 'https://jobs.gov.in/apply/127',
            'posted_date': date.today() - timedelta(days=30),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ]
    
    add_jobs_to_db(test_db_session, jobs_data)
    
    qualifications = Qualifications(
        education_level='12th',
        experience_years=0,
        skills=[]
    )
    
    preferences = JobPreferences(
        departments=[],
        locations=['Tamil Nadu']
    )
    
    matcher = JobMatcher(test_db_session)
    results = matcher.search_jobs(qualifications, preferences, limit=10)
    
    # Should only return active job
    assert len(results) == 1, "Should only return active jobs"
    assert 'Active' in results[0].title, "Should return the active job"
    assert 'Expired' not in results[0].title, "Should not return expired job"


def test_job_qualification_matching_department_filter_applied(test_db_session):
    """
    Test that department filter is properly applied.
    """
    jobs_data = [
        {
            'job_id': uuid.uuid4(),
            'title': 'Education Job',
            'department': 'Ministry of Education',
            'description': 'Job in education department',
            'qualifications': {'education_level': 'graduate'},
            'location': {'state': 'Bihar', 'district': 'Patna'},
            'application_deadline': date.today() + timedelta(days=30),
            'application_url': 'https://jobs.gov.in/apply/128',
            'posted_date': date.today() - timedelta(days=5),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'job_id': uuid.uuid4(),
            'title': 'Health Job',
            'department': 'Ministry of Health',
            'description': 'Job in health department',
            'qualifications': {'education_level': 'graduate'},
            'location': {'state': 'Bihar', 'district': 'Patna'},
            'application_deadline': date.today() + timedelta(days=30),
            'application_url': 'https://jobs.gov.in/apply/129',
            'posted_date': date.today() - timedelta(days=5),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ]
    
    add_jobs_to_db(test_db_session, jobs_data)
    
    qualifications = Qualifications(
        education_level='graduate',
        experience_years=0,
        skills=[]
    )
    
    # Filter by education department only
    preferences = JobPreferences(
        departments=['Ministry of Education'],
        locations=[]
    )
    
    matcher = JobMatcher(test_db_session)
    results = matcher.search_jobs(qualifications, preferences, limit=10)
    
    # Should only return education job
    assert len(results) == 1, "Should only return jobs from specified department"
    assert 'Education' in results[0].title, "Should return education job"
    assert results[0].department == 'Ministry of Education', "Should match department filter"


def test_job_qualification_matching_no_results(test_db_session):
    """
    Edge case: No matching jobs should return empty list.
    """
    jobs_data = [
        {
            'job_id': uuid.uuid4(),
            'title': 'Senior Position',
            'department': 'Ministry of Finance',
            'description': 'Senior level position',
            'qualifications': {
                'education_level': 'postgraduate',
                'experience_years': 10
            },
            'location': {'state': 'Maharashtra', 'district': 'Mumbai'},
            'application_deadline': date.today() + timedelta(days=30),
            'application_url': 'https://jobs.gov.in/apply/130',
            'posted_date': date.today() - timedelta(days=5),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ]
    
    add_jobs_to_db(test_db_session, jobs_data)
    
    # User with much lower qualifications (more than one level below)
    qualifications = Qualifications(
        education_level='10th',  # Two levels below postgraduate
        experience_years=0,
        skills=[]
    )
    
    preferences = JobPreferences(
        departments=[],
        locations=['Maharashtra']
    )
    
    matcher = JobMatcher(test_db_session)
    results = matcher.search_jobs(qualifications, preferences, limit=10)
    
    # Should return empty list (10th is two levels below postgraduate)
    assert len(results) == 0, "Should return empty list when qualifications don't match"
    assert isinstance(results, list), "Should return a list"


def test_job_qualification_matching_limit_parameter(test_db_session):
    """
    Test that limit parameter is respected.
    """
    # Create 15 jobs
    jobs_data = []
    for i in range(15):
        jobs_data.append({
            'job_id': uuid.uuid4(),
            'title': f'Job Position {i}',
            'department': 'State Government',
            'description': 'Government job posting',
            'qualifications': {'education_level': 'graduate'},
            'location': {'state': 'Gujarat', 'district': 'Ahmedabad'},
            'application_deadline': date.today() + timedelta(days=30),
            'application_url': f'https://jobs.gov.in/apply/{i}',
            'posted_date': date.today() - timedelta(days=5),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
    
    add_jobs_to_db(test_db_session, jobs_data)
    
    qualifications = Qualifications(
        education_level='graduate',
        experience_years=0,
        skills=[]
    )
    
    preferences = JobPreferences(
        departments=[],
        locations=['Gujarat']
    )
    
    matcher = JobMatcher(test_db_session)
    
    # Test with limit=5
    results = matcher.search_jobs(qualifications, preferences, limit=5)
    assert len(results) == 5, "Should respect limit parameter"
    
    # Test with limit=10
    results = matcher.search_jobs(qualifications, preferences, limit=10)
    assert len(results) == 10, "Should respect limit parameter"
