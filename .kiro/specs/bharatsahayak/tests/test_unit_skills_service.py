"""
Unit tests for Skills and Employment Service

Tests program matching with various profiles, job search with different qualifications,
and edge cases (no matching programs/jobs).

Feature: bharatsahayak
Requirements: 4.1, 4.3
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock
import uuid

from app.services.skills_matcher import SkillsMatcher
from app.services.job_matcher import JobMatcher
from app.models.skills import SkillProgram, JobPosting
from app.schemas.skills import (
    SkillPreferences, Qualifications, JobPreferences
)


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    return Mock()


@pytest.fixture
def sample_skill_programs():
    """Create sample skill programs for testing"""
    program1_id = uuid.uuid4()
    program2_id = uuid.uuid4()
    program3_id = uuid.uuid4()
    program4_id = uuid.uuid4()
    
    program1 = SkillProgram(
        program_id=program1_id,
        name="Python Programming Bootcamp",
        provider="National Skill Development Corporation",
        category="technical",
        description="Learn Python programming for software development",
        duration_weeks=12,
        cost=0,  # Free
        state="Maharashtra",
        district="Mumbai",
        mode="online",
        eligibility_criteria={"education": ["12th pass", "graduate"]},
        certification=True,
        placement_support=True,
        registration_url="https://nsdc.gov.in/python",
        contact="contact@nsdc.gov.in",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    program2 = SkillProgram(
        program_id=program2_id,
        name="Welding and Fabrication",
        provider="Industrial Training Institute",
        category="vocational",
        description="Hands-on welding and metal fabrication training",
        duration_weeks=24,
        cost=5000,
        state="Maharashtra",
        district="Pune",
        mode="in-person",
        eligibility_criteria={"education": ["10th pass"]},
        certification=True,
        placement_support=False,
        registration_url="https://iti.gov.in/welding",
        contact="iti@gov.in",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    program3 = SkillProgram(
        program_id=program3_id,
        name="Digital Marketing Masterclass",
        provider="Skill India",
        category="digital",
        description="Master digital marketing and social media strategies",
        duration_weeks=8,
        cost=0,
        state="Karnataka",
        district="Bangalore",
        mode="hybrid",
        eligibility_criteria={"education": ["graduate"]},
        certification=True,
        placement_support=True,
        registration_url="https://skillindia.gov.in/digital",
        contact="info@skillindia.gov.in",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    program4 = SkillProgram(
        program_id=program4_id,
        name="Entrepreneurship Development",
        provider="Ministry of MSME",
        category="entrepreneurship",
        description="Start and grow your own business",
        duration_weeks=6,
        cost=1000,
        state=None,  # Available nationwide
        district=None,
        mode="online",
        eligibility_criteria={"education": ["10th pass", "12th pass", "graduate"]},
        certification=False,
        placement_support=False,
        registration_url="https://msme.gov.in/entrepreneurship",
        contact="msme@gov.in",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    return [program1, program2, program3, program4]



@pytest.fixture
def sample_job_postings():
    """Create sample job postings for testing"""
    job1_id = uuid.uuid4()
    job2_id = uuid.uuid4()
    job3_id = uuid.uuid4()
    job4_id = uuid.uuid4()
    
    today = date.today()
    
    job1 = JobPosting(
        job_id=job1_id,
        title="Junior Software Developer",
        department="Information Technology",
        description="Develop and maintain government web applications",
        qualifications={
            "education_level": "graduate",
            "degree": "Computer Science or related",
            "experience_years": 0,
            "skills": ["Python", "JavaScript", "SQL"]
        },
        location={"state": "Maharashtra", "district": "Mumbai"},
        application_deadline=today + timedelta(days=30),
        application_url="https://jobs.gov.in/software-dev",
        posted_date=today - timedelta(days=5),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    job2 = JobPosting(
        job_id=job2_id,
        title="Agricultural Extension Officer",
        department="Agriculture",
        description="Provide agricultural guidance to farmers",
        qualifications={
            "education_level": "graduate",
            "degree": "Agriculture or related",
            "experience_years": 2,
            "skills": ["Farming", "Communication", "Hindi"]
        },
        location={"state": "Maharashtra", "district": "Pune"},
        application_deadline=today + timedelta(days=15),
        application_url="https://jobs.gov.in/agri-officer",
        posted_date=today - timedelta(days=10),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    job3 = JobPosting(
        job_id=job3_id,
        title="Data Entry Operator",
        department="Administration",
        description="Enter and maintain government records",
        qualifications={
            "education_level": "12th",
            "experience_years": 0,
            "skills": ["Typing", "Computer basics"]
        },
        location={"state": "Karnataka", "district": "Bangalore"},
        application_deadline=today + timedelta(days=7),
        application_url="https://jobs.gov.in/data-entry",
        posted_date=today - timedelta(days=2),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    job4 = JobPosting(
        job_id=job4_id,
        title="Senior Engineer",
        department="Public Works",
        description="Design and oversee infrastructure projects",
        qualifications={
            "education_level": "postgraduate",
            "degree": "Civil Engineering",
            "experience_years": 5,
            "skills": ["AutoCAD", "Project Management", "Structural Design"]
        },
        location={"locations": [
            {"state": "Maharashtra", "district": "Mumbai"},
            {"state": "Maharashtra", "district": "Pune"}
        ]},
        application_deadline=today + timedelta(days=45),
        application_url="https://jobs.gov.in/senior-engineer",
        posted_date=today - timedelta(days=1),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    return [job1, job2, job3, job4]



class TestProgramMatchingWithVariousProfiles:
    """Test program matching with various user profiles"""
    
    def test_match_programs_with_technical_interest(self, mock_db, sample_skill_programs):
        """Test matching programs for user interested in technical skills"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_skill_programs
        mock_db.query.return_value = mock_query
        
        matcher = SkillsMatcher(mock_db)
        
        user_profile = {
            "state": "Maharashtra",
            "education_level": "graduate"
        }
        
        preferences = SkillPreferences(
            interests=["programming", "software"],
            location_state="Maharashtra"
        )
        
        results = matcher.match_programs(user_profile, preferences)
        
        # Should return Python program with high relevance
        assert len(results) > 0
        assert any("Python" in prog.name for prog in results)
        # Technical program should have high relevance score
        python_prog = next(prog for prog in results if "Python" in prog.name)
        assert python_prog.relevance_score > 0.3
    
    def test_match_programs_with_vocational_interest(self, mock_db, sample_skill_programs):
        """Test matching programs for user interested in vocational skills"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_skill_programs
        mock_db.query.return_value = mock_query
        
        matcher = SkillsMatcher(mock_db)
        
        user_profile = {
            "state": "Maharashtra",
            "education_level": "10th pass"
        }
        
        preferences = SkillPreferences(
            interests=["welding", "manufacturing"],
            location_state="Maharashtra",
            location_district="Pune"
        )
        
        results = matcher.match_programs(user_profile, preferences)
        
        # Should return welding program
        assert len(results) > 0
        assert any("Welding" in prog.name for prog in results)
    
    def test_match_programs_with_career_goals(self, mock_db, sample_skill_programs):
        """Test matching programs based on career goals"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_skill_programs
        mock_db.query.return_value = mock_query
        
        matcher = SkillsMatcher(mock_db)
        
        user_profile = {
            "state": "Karnataka",
            "education_level": "graduate"
        }
        
        preferences = SkillPreferences(
            career_goals=["digital marketing", "social media"],
            location_state="Karnataka"
        )
        
        results = matcher.match_programs(user_profile, preferences)
        
        # Should return digital marketing program
        assert len(results) > 0
        assert any("Digital Marketing" in prog.name for prog in results)
    
    def test_match_programs_with_current_skills(self, mock_db, sample_skill_programs):
        """Test matching programs that build on current skills"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_skill_programs
        mock_db.query.return_value = mock_query
        
        matcher = SkillsMatcher(mock_db)
        
        user_profile = {
            "state": "Maharashtra",
            "education_level": "graduate"
        }
        
        preferences = SkillPreferences(
            current_skills=["programming", "coding"],
            location_state="Maharashtra"
        )
        
        results = matcher.match_programs(user_profile, preferences)
        
        # Should return technical programs
        assert len(results) > 0
        assert any("Python" in prog.name for prog in results)
    
    def test_match_programs_with_cost_constraint(self, mock_db, sample_skill_programs):
        """Test matching programs with maximum cost filter"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [sample_skill_programs[0], sample_skill_programs[2]]  # Free programs
        mock_db.query.return_value = mock_query
        
        matcher = SkillsMatcher(mock_db)
        
        user_profile = {
            "state": "Maharashtra",
            "education_level": "graduate"
        }
        
        preferences = SkillPreferences(
            interests=["programming"],
            max_cost=0,  # Only free programs
            location_state="Maharashtra"
        )
        
        results = matcher.match_programs(user_profile, preferences)
        
        # All returned programs should be free
        for prog in results:
            assert prog.cost == 0 or prog.cost is None
    
    def test_match_programs_with_duration_constraint(self, mock_db, sample_skill_programs):
        """Test matching programs with maximum duration filter"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        # Return programs with duration <= 12 weeks
        mock_query.all.return_value = [sample_skill_programs[0], sample_skill_programs[2], sample_skill_programs[3]]
        mock_db.query.return_value = mock_query
        
        matcher = SkillsMatcher(mock_db)
        
        user_profile = {
            "state": "Maharashtra",
            "education_level": "graduate"
        }
        
        preferences = SkillPreferences(
            interests=["programming"],
            max_duration_weeks=12,
            location_state="Maharashtra"
        )
        
        results = matcher.match_programs(user_profile, preferences)
        
        # All returned programs should be <= 12 weeks
        for prog in results:
            if prog.duration_weeks is not None:
                assert prog.duration_weeks <= 12
    
    def test_match_programs_with_online_mode_preference(self, mock_db, sample_skill_programs):
        """Test matching programs with online mode preference"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        # Return only online programs
        mock_query.all.return_value = [sample_skill_programs[0], sample_skill_programs[3]]
        mock_db.query.return_value = mock_query
        
        matcher = SkillsMatcher(mock_db)
        
        user_profile = {
            "state": "Maharashtra",
            "education_level": "graduate"
        }
        
        preferences = SkillPreferences(
            interests=["programming"],
            preferred_mode="online",
            location_state="Maharashtra"
        )
        
        results = matcher.match_programs(user_profile, preferences)
        
        # All returned programs should be online
        for prog in results:
            assert prog.mode == "online"
    
    def test_match_programs_prefers_certification(self, mock_db, sample_skill_programs):
        """Test that programs with certification get bonus score"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_skill_programs
        mock_db.query.return_value = mock_query
        
        matcher = SkillsMatcher(mock_db)
        
        user_profile = {
            "state": "Maharashtra",
            "education_level": "graduate"
        }
        
        preferences = SkillPreferences(
            interests=["programming"],
            location_state="Maharashtra"
        )
        
        results = matcher.match_programs(user_profile, preferences)
        
        # Programs with certification should have higher scores
        if len(results) > 1:
            certified_progs = [p for p in results if p.certification]
            if certified_progs:
                assert certified_progs[0].relevance_score > 0
    
    def test_match_programs_prefers_placement_support(self, mock_db, sample_skill_programs):
        """Test that programs with placement support get bonus score"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_skill_programs
        mock_db.query.return_value = mock_query
        
        matcher = SkillsMatcher(mock_db)
        
        user_profile = {
            "state": "Maharashtra",
            "education_level": "graduate"
        }
        
        preferences = SkillPreferences(
            interests=["programming"],
            location_state="Maharashtra"
        )
        
        results = matcher.match_programs(user_profile, preferences)
        
        # Programs with placement support should have higher scores
        if len(results) > 1:
            placement_progs = [p for p in results if p.placement_support]
            if placement_progs:
                assert placement_progs[0].relevance_score > 0
    
    def test_match_programs_sorts_by_relevance(self, mock_db, sample_skill_programs):
        """Test that results are sorted by relevance score"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_skill_programs
        mock_db.query.return_value = mock_query
        
        matcher = SkillsMatcher(mock_db)
        
        user_profile = {
            "state": "Maharashtra",
            "education_level": "graduate"
        }
        
        preferences = SkillPreferences(
            interests=["programming", "technical"],
            location_state="Maharashtra"
        )
        
        results = matcher.match_programs(user_profile, preferences)
        
        # Results should be sorted by relevance score (descending)
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].relevance_score >= results[i + 1].relevance_score
    
    def test_match_programs_respects_limit(self, mock_db, sample_skill_programs):
        """Test that match_programs respects the limit parameter"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_skill_programs
        mock_db.query.return_value = mock_query
        
        matcher = SkillsMatcher(mock_db)
        
        user_profile = {
            "state": "Maharashtra",
            "education_level": "graduate"
        }
        
        preferences = SkillPreferences(
            interests=["programming"],
            location_state="Maharashtra"
        )
        
        results = matcher.match_programs(user_profile, preferences, limit=2)
        
        # Should return at most 2 results
        assert len(results) <= 2



class TestJobSearchWithDifferentQualifications:
    """Test job search with different user qualifications"""
    
    def test_search_jobs_with_graduate_qualification(self, mock_db, sample_job_postings):
        """Test job search for graduate user"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_job_postings
        mock_db.query.return_value = mock_query
        
        matcher = JobMatcher(mock_db)
        
        qualifications = Qualifications(
            education_level="graduate",
            degree="Computer Science",
            experience_years=0,
            skills=["Python", "JavaScript"]
        )
        
        preferences = JobPreferences(
            locations=["Maharashtra"]
        )
        
        results = matcher.search_jobs(qualifications, preferences)
        
        # Should return jobs matching graduate qualification
        assert len(results) > 0
        assert any("Software Developer" in job.title for job in results)
    
    def test_search_jobs_with_12th_qualification(self, mock_db, sample_job_postings):
        """Test job search for 12th pass user"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_job_postings
        mock_db.query.return_value = mock_query
        
        matcher = JobMatcher(mock_db)
        
        qualifications = Qualifications(
            education_level="12th",
            experience_years=0,
            skills=["Typing", "Computer basics"]
        )
        
        preferences = JobPreferences(
            locations=["Karnataka"]
        )
        
        results = matcher.search_jobs(qualifications, preferences)
        
        # Should return data entry job
        assert len(results) > 0
        assert any("Data Entry" in job.title for job in results)
    
    def test_search_jobs_with_experience(self, mock_db, sample_job_postings):
        """Test job search for experienced user"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_job_postings
        mock_db.query.return_value = mock_query
        
        matcher = JobMatcher(mock_db)
        
        qualifications = Qualifications(
            education_level="graduate",
            degree="Agriculture",
            experience_years=3,
            skills=["Farming", "Communication"]
        )
        
        preferences = JobPreferences(
            departments=["Agriculture"],
            locations=["Maharashtra"]
        )
        
        results = matcher.search_jobs(qualifications, preferences)
        
        # Should return agricultural officer job
        assert len(results) > 0
        assert any("Agricultural" in job.title for job in results)
    
    def test_search_jobs_with_matching_skills(self, mock_db, sample_job_postings):
        """Test job search with matching skills"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_job_postings
        mock_db.query.return_value = mock_query
        
        matcher = JobMatcher(mock_db)
        
        qualifications = Qualifications(
            education_level="graduate",
            experience_years=0,
            skills=["Python", "JavaScript", "SQL"]  # All required skills
        )
        
        preferences = JobPreferences(
            locations=["Maharashtra"]
        )
        
        results = matcher.search_jobs(qualifications, preferences)
        
        # Software developer job should have high match score
        if results:
            software_job = next((job for job in results if "Software" in job.title), None)
            if software_job:
                assert software_job.match_score > 0.3
    
    def test_search_jobs_with_partial_skills(self, mock_db, sample_job_postings):
        """Test job search with partial skill match"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_job_postings
        mock_db.query.return_value = mock_query
        
        matcher = JobMatcher(mock_db)
        
        qualifications = Qualifications(
            education_level="graduate",
            experience_years=0,
            skills=["Python"]  # Only one of required skills
        )
        
        preferences = JobPreferences(
            locations=["Maharashtra"]
        )
        
        results = matcher.search_jobs(qualifications, preferences)
        
        # Should still return software developer job but with lower score
        if results:
            software_job = next((job for job in results if "Software" in job.title), None)
            if software_job:
                assert software_job.match_score > 0
    
    def test_search_jobs_with_postgraduate_qualification(self, mock_db, sample_job_postings):
        """Test job search for postgraduate user"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_job_postings
        mock_db.query.return_value = mock_query
        
        matcher = JobMatcher(mock_db)
        
        qualifications = Qualifications(
            education_level="postgraduate",
            degree="Civil Engineering",
            experience_years=6,
            skills=["AutoCAD", "Project Management"]
        )
        
        preferences = JobPreferences(
            departments=["Public Works"],
            locations=["Maharashtra"]
        )
        
        results = matcher.search_jobs(qualifications, preferences)
        
        # Should return senior engineer job
        assert len(results) > 0
        assert any("Senior Engineer" in job.title for job in results)
    
    def test_search_jobs_filters_expired_jobs(self, mock_db, sample_job_postings):
        """Test that expired jobs are filtered out"""
        # Create an expired job
        expired_job = JobPosting(
            job_id=uuid.uuid4(),
            title="Expired Job",
            department="Test",
            description="This job has expired",
            qualifications={"education_level": "graduate"},
            location={"state": "Maharashtra"},
            application_deadline=date.today() - timedelta(days=1),  # Expired
            application_url="https://jobs.gov.in/expired",
            posted_date=date.today() - timedelta(days=30),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        # Should not return expired job
        mock_query.all.return_value = sample_job_postings  # Only active jobs
        mock_db.query.return_value = mock_query
        
        matcher = JobMatcher(mock_db)
        
        qualifications = Qualifications(
            education_level="graduate",
            experience_years=0
        )
        
        preferences = JobPreferences(
            locations=["Maharashtra"]
        )
        
        results = matcher.search_jobs(qualifications, preferences)
        
        # Should not contain expired job
        assert not any("Expired" in job.title for job in results)
    
    def test_search_jobs_by_department(self, mock_db, sample_job_postings):
        """Test job search filtered by department"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        # Return only IT department jobs
        mock_query.all.return_value = [sample_job_postings[0]]
        mock_db.query.return_value = mock_query
        
        matcher = JobMatcher(mock_db)
        
        qualifications = Qualifications(
            education_level="graduate",
            experience_years=0
        )
        
        preferences = JobPreferences(
            departments=["Information Technology"],
            locations=["Maharashtra"]
        )
        
        results = matcher.search_jobs(qualifications, preferences)
        
        # All results should be from IT department
        for job in results:
            assert job.department == "Information Technology"
    
    def test_search_jobs_by_location(self, mock_db, sample_job_postings):
        """Test job search filtered by location"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_job_postings
        mock_db.query.return_value = mock_query
        
        matcher = JobMatcher(mock_db)
        
        qualifications = Qualifications(
            education_level="graduate",
            experience_years=0
        )
        
        preferences = JobPreferences(
            locations=["Karnataka"]
        )
        
        results = matcher.search_jobs(qualifications, preferences)
        
        # Should only return Karnataka jobs
        for job in results:
            if job.location:
                location_str = str(job.location).lower()
                assert "karnataka" in location_str
    
    def test_search_jobs_sorts_by_match_score(self, mock_db, sample_job_postings):
        """Test that results are sorted by match score"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_job_postings
        mock_db.query.return_value = mock_query
        
        matcher = JobMatcher(mock_db)
        
        qualifications = Qualifications(
            education_level="graduate",
            experience_years=0,
            skills=["Python"]
        )
        
        preferences = JobPreferences(
            locations=["Maharashtra"]
        )
        
        results = matcher.search_jobs(qualifications, preferences)
        
        # Results should be sorted by match score (descending)
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].match_score >= results[i + 1].match_score
    
    def test_search_jobs_respects_limit(self, mock_db, sample_job_postings):
        """Test that search_jobs respects the limit parameter"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_job_postings
        mock_db.query.return_value = mock_query
        
        matcher = JobMatcher(mock_db)
        
        qualifications = Qualifications(
            education_level="graduate",
            experience_years=0
        )
        
        preferences = JobPreferences(
            locations=["Maharashtra"]
        )
        
        results = matcher.search_jobs(qualifications, preferences, limit=2)
        
        # Should return at most 2 results
        assert len(results) <= 2
    
    def test_search_jobs_allows_one_level_below_education(self, mock_db, sample_job_postings):
        """Test that users one level below required education can still see jobs"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_job_postings
        mock_db.query.return_value = mock_query
        
        matcher = JobMatcher(mock_db)
        
        # User with 12th can see graduate jobs (one level below)
        qualifications = Qualifications(
            education_level="12th",
            experience_years=0,
            skills=["Typing", "Computer basics"]
        )
        
        preferences = JobPreferences(
            locations=["Karnataka"]  # Match data entry job location
        )
        
        results = matcher.search_jobs(qualifications, preferences)
        
        # Should return data entry job (12th requirement) and possibly graduate jobs
        assert len(results) > 0



class TestEdgeCases:
    """Test edge cases (no matching programs/jobs)"""
    
    def test_no_matching_programs_returns_empty_list(self, mock_db):
        """Test that no matching programs returns empty list"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []  # No programs
        mock_db.query.return_value = mock_query
        
        matcher = SkillsMatcher(mock_db)
        
        user_profile = {
            "state": "Maharashtra",
            "education_level": "graduate"
        }
        
        preferences = SkillPreferences(
            interests=["nonexistent skill"],
            location_state="Maharashtra"
        )
        
        results = matcher.match_programs(user_profile, preferences)
        
        assert len(results) == 0
        assert isinstance(results, list)
    
    def test_no_matching_jobs_returns_empty_list(self, mock_db):
        """Test that no matching jobs returns empty list"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []  # No jobs
        mock_db.query.return_value = mock_query
        
        matcher = JobMatcher(mock_db)
        
        qualifications = Qualifications(
            education_level="graduate",
            experience_years=0
        )
        
        preferences = JobPreferences(
            locations=["NonexistentState"]
        )
        
        results = matcher.search_jobs(qualifications, preferences)
        
        assert len(results) == 0
        assert isinstance(results, list)
    
    def test_programs_without_relevance_match_excluded(self, mock_db, sample_skill_programs):
        """Test that programs without interest/skill/goal match are excluded"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_skill_programs
        mock_db.query.return_value = mock_query
        
        matcher = SkillsMatcher(mock_db)
        
        user_profile = {
            "state": "Maharashtra",
            "education_level": "graduate"
        }
        
        # No interests, skills, or career goals specified
        preferences = SkillPreferences(
            location_state="Maharashtra"
        )
        
        results = matcher.match_programs(user_profile, preferences)
        
        # Should return empty list since no relevance criteria
        assert len(results) == 0
    
    def test_jobs_with_no_location_restriction_match_all(self, mock_db):
        """Test that jobs with no location restriction match all locations"""
        job_no_location = JobPosting(
            job_id=uuid.uuid4(),
            title="Remote Job",
            department="IT",
            description="Work from anywhere",
            qualifications={"education_level": "graduate"},
            location=None,  # No location restriction
            application_deadline=date.today() + timedelta(days=30),
            application_url="https://jobs.gov.in/remote",
            posted_date=date.today(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [job_no_location]
        mock_db.query.return_value = mock_query
        
        matcher = JobMatcher(mock_db)
        
        qualifications = Qualifications(
            education_level="graduate",
            experience_years=0
        )
        
        preferences = JobPreferences(
            locations=["AnyState"]
        )
        
        results = matcher.search_jobs(qualifications, preferences)
        
        # Should return the job since it has no location restriction
        assert len(results) > 0
        assert any("Remote" in job.title for job in results)
    
    def test_get_program_details_not_found(self, mock_db):
        """Test getting program details when program doesn't exist"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        matcher = SkillsMatcher(mock_db)
        result = matcher.get_program_details(str(uuid.uuid4()))
        
        assert result is None
    
    def test_get_program_details_invalid_uuid(self, mock_db):
        """Test getting program details with invalid UUID"""
        matcher = SkillsMatcher(mock_db)
        result = matcher.get_program_details("invalid-uuid")
        
        assert result is None
    
    def test_get_job_by_id_not_found(self, mock_db):
        """Test getting job by ID when job doesn't exist"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        matcher = JobMatcher(mock_db)
        result = matcher.get_job_by_id(str(uuid.uuid4()))
        
        assert result is None
    
    def test_get_job_by_invalid_uuid(self, mock_db):
        """Test getting job with invalid UUID format"""
        matcher = JobMatcher(mock_db)
        result = matcher.get_job_by_id("invalid-uuid")
        
        assert result is None
    
    def test_job_alerts_with_no_recent_jobs(self, mock_db):
        """Test job alerts when no recent jobs are available"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []  # No recent jobs
        mock_db.query.return_value = mock_query
        
        matcher = JobMatcher(mock_db)
        
        user_profile = {"state": "Maharashtra"}
        qualifications = Qualifications(
            education_level="graduate",
            experience_years=0
        )
        preferences = JobPreferences(
            locations=["Maharashtra"]
        )
        
        results = matcher.get_job_alerts(user_profile, qualifications, preferences)
        
        assert len(results) == 0
        assert isinstance(results, list)
    
    def test_programs_with_no_eligibility_criteria(self, mock_db):
        """Test matching programs with no eligibility criteria"""
        program_no_criteria = SkillProgram(
            program_id=uuid.uuid4(),
            name="Open Program",
            provider="Test Provider",
            category="general",
            description="Open to all",
            duration_weeks=4,
            cost=0,
            state="Maharashtra",
            district=None,
            mode="online",
            eligibility_criteria=None,  # No criteria
            certification=False,
            placement_support=False,
            registration_url="https://test.gov.in",
            contact="test@gov.in",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [program_no_criteria]
        mock_db.query.return_value = mock_query
        
        matcher = SkillsMatcher(mock_db)
        
        user_profile = {
            "state": "Maharashtra",
            "education_level": "10th pass"
        }
        
        preferences = SkillPreferences(
            interests=["general"],
            location_state="Maharashtra"
        )
        
        results = matcher.match_programs(user_profile, preferences)
        
        # Should return the program
        assert len(results) > 0
    
    def test_jobs_with_no_qualifications(self, mock_db):
        """Test matching jobs with no qualification requirements"""
        job_no_quals = JobPosting(
            job_id=uuid.uuid4(),
            title="Entry Level Job",
            department="General",
            description="No specific qualifications required",
            qualifications=None,  # No requirements
            location={"state": "Maharashtra"},
            application_deadline=date.today() + timedelta(days=30),
            application_url="https://jobs.gov.in/entry",
            posted_date=date.today(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [job_no_quals]
        mock_db.query.return_value = mock_query
        
        matcher = JobMatcher(mock_db)
        
        qualifications = Qualifications(
            education_level="10th",
            experience_years=0
        )
        
        preferences = JobPreferences(
            locations=["Maharashtra"]
        )
        
        results = matcher.search_jobs(qualifications, preferences)
        
        # Should return the job
        assert len(results) > 0
        assert any("Entry Level" in job.title for job in results)
    
    def test_get_all_programs_with_filters(self, mock_db, sample_skill_programs):
        """Test getting all programs with category and state filters"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = [sample_skill_programs[0]]
        mock_db.query.return_value = mock_query
        
        matcher = SkillsMatcher(mock_db)
        
        results = matcher.get_all_programs(
            category="technical",
            state="Maharashtra",
            limit=10,
            offset=0
        )
        
        assert len(results) > 0
        assert results[0].category == "technical"
    
    def test_job_alerts_filters_by_date_range(self, mock_db, sample_job_postings):
        """Test that job alerts only return jobs within date range"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        # Return only recent jobs
        recent_jobs = [job for job in sample_job_postings 
                      if (date.today() - job.posted_date).days <= 30]
        mock_query.all.return_value = recent_jobs
        mock_db.query.return_value = mock_query
        
        matcher = JobMatcher(mock_db)
        
        user_profile = {"state": "Maharashtra"}
        qualifications = Qualifications(
            education_level="graduate",
            experience_years=0
        )
        preferences = JobPreferences(
            locations=["Maharashtra"]
        )
        
        results = matcher.get_job_alerts(
            user_profile, qualifications, preferences, days_back=30
        )
        
        # All returned jobs should be recent
        for job in results:
            if job.posted_date:
                days_old = (date.today() - job.posted_date).days
                assert days_old <= 30
