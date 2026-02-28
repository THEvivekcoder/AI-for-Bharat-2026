"""
Unit tests for Personalization Service

Tests recommendation scoring with various profiles and explanation generation.

Feature: bharatsahayak
Requirements: 8.2, 8.4
"""

import pytest
from app.services.personalization import PersonalizationEngine


@pytest.fixture
def personalization_engine():
    """Create a PersonalizationEngine instance"""
    return PersonalizationEngine()


@pytest.fixture
def sample_user_profile():
    """Create a sample user profile"""
    return {
        "user_id": "user123",
        "occupation": "farmer",
        "state": "Maharashtra",
        "district": "Pune",
        "age": 35,
        "education_level": "10th",
        "income_bracket": "0-50000",
        "interests": ["agriculture", "technology"],
        "career_goals": ["farming", "agribusiness"],
        "skills": ["crop management"],
        "experience_years": 5,
        "preferred_departments": ["Agriculture", "Rural Development"]
    }


@pytest.fixture
def sample_scheme():
    """Create a sample scheme"""
    return {
        "scheme_id": "scheme123",
        "name": "PM-KISAN",
        "category": "agriculture",
        "state": None,  # Central scheme
        "eligibility_criteria": {
            "occupation": ["farmer"],
            "age_min": 18,
            "age_max": 60,
            "income_max": 100000,
            "education": ["below_10th", "10th", "12th"]
        }
    }


@pytest.fixture
def sample_job():
    """Create a sample job posting"""
    return {
        "job_id": "job123",
        "title": "Agricultural Officer",
        "department": "Agriculture",
        "location": {
            "state": "Maharashtra",
            "district": "Pune"
        },
        "qualifications": {
            "education_level": "graduate",
            "experience_years": 3,
            "skills": ["crop management", "soil testing"]
        }
    }


@pytest.fixture
def sample_skill_program():
    """Create a sample skill program"""
    return {
        "program_id": "prog123",
        "name": "Modern Farming Techniques",
        "category": "agriculture",
        "description": "Learn modern farming and technology",
        "state": "Maharashtra",
        "district": "Pune",
        "mode": "in-person",
        "eligibility_criteria": {
            "education": ["10th", "12th"]
        }
    }


class TestSchemeScoring:
    """Test scheme relevance scoring"""
    
    def test_perfect_match_scheme(self, personalization_engine, sample_user_profile, sample_scheme):
        """Test scoring for a scheme that perfectly matches user profile"""
        score, explanation = personalization_engine.score_scheme_relevance(
            sample_scheme, sample_user_profile
        )
        
        # Should have high score due to occupation, location, income, age, education matches
        assert score > 0.7, f"Expected high score for perfect match, got {score}"
        assert "farmer" in explanation.lower()
        assert isinstance(explanation, str)
        assert len(explanation) > 0
    
    def test_occupation_mismatch(self, personalization_engine, sample_scheme):
        """Test scoring when user occupation doesn't match scheme"""
        user_profile = {
            "occupation": "teacher",
            "state": "Maharashtra",
            "age": 35,
            "income_bracket": "0-50000",
            "education_level": "graduate"
        }
        
        score, explanation = personalization_engine.score_scheme_relevance(
            sample_scheme, user_profile
        )
        
        # Should have lower score due to occupation mismatch
        assert score < 0.7, f"Expected lower score for occupation mismatch, got {score}"
    
    def test_state_specific_scheme_match(self, personalization_engine, sample_user_profile):
        """Test scoring for state-specific scheme in user's state"""
        state_scheme = {
            "scheme_id": "state123",
            "name": "Maharashtra Farmer Scheme",
            "category": "agriculture",
            "state": "Maharashtra",
            "eligibility_criteria": {
                "occupation": ["farmer"],
                "age_min": 18
            }
        }
        
        score, explanation = personalization_engine.score_scheme_relevance(
            state_scheme, sample_user_profile
        )
        
        assert score > 0.5
        assert "maharashtra" in explanation.lower() or "state" in explanation.lower()
    
    def test_state_specific_scheme_mismatch(self, personalization_engine, sample_user_profile):
        """Test scoring for state-specific scheme in different state"""
        other_state_scheme = {
            "scheme_id": "state456",
            "name": "Kerala Farmer Scheme",
            "category": "agriculture",
            "state": "Kerala",
            "eligibility_criteria": {
                "occupation": ["farmer"]
            }
        }
        
        score, explanation = personalization_engine.score_scheme_relevance(
            other_state_scheme, sample_user_profile
        )
        
        # Should have low score due to state mismatch
        assert score < 0.5, f"Expected low score for state mismatch, got {score}"
    
    def test_income_eligibility(self, personalization_engine, sample_scheme):
        """Test income-based eligibility scoring"""
        # User within income limit
        low_income_user = {
            "occupation": "farmer",
            "state": "Maharashtra",
            "age": 35,
            "income_bracket": "0-50000",
            "education_level": "10th"
        }
        
        score1, _ = personalization_engine.score_scheme_relevance(
            sample_scheme, low_income_user
        )
        
        # User exceeding income limit
        high_income_user = {
            "occupation": "farmer",
            "state": "Maharashtra",
            "age": 35,
            "income_bracket": "100000-200000",
            "education_level": "10th"
        }
        
        score2, _ = personalization_engine.score_scheme_relevance(
            sample_scheme, high_income_user
        )
        
        # Low income user should score higher
        assert score1 > score2, "User within income limit should score higher"
    
    def test_age_eligibility(self, personalization_engine, sample_scheme):
        """Test age-based eligibility scoring"""
        # User within age range
        eligible_age_user = {
            "occupation": "farmer",
            "state": "Maharashtra",
            "age": 35,
            "income_bracket": "0-50000",
            "education_level": "10th"
        }
        
        score1, explanation1 = personalization_engine.score_scheme_relevance(
            sample_scheme, eligible_age_user
        )
        
        # User outside age range
        ineligible_age_user = {
            "occupation": "farmer",
            "state": "Maharashtra",
            "age": 70,
            "income_bracket": "0-50000",
            "education_level": "10th"
        }
        
        score2, explanation2 = personalization_engine.score_scheme_relevance(
            sample_scheme, ineligible_age_user
        )
        
        # Eligible age user should score higher
        assert score1 > score2, "User within age range should score higher"
    
    def test_education_level_matching(self, personalization_engine, sample_scheme):
        """Test education level matching in scoring"""
        # Exact match
        exact_match_user = {
            "occupation": "farmer",
            "state": "Maharashtra",
            "age": 35,
            "income_bracket": "0-50000",
            "education_level": "10th"
        }
        
        score1, explanation1 = personalization_engine.score_scheme_relevance(
            sample_scheme, exact_match_user
        )
        
        # Overqualified
        overqualified_user = {
            "occupation": "farmer",
            "state": "Maharashtra",
            "age": 35,
            "income_bracket": "0-50000",
            "education_level": "graduate"
        }
        
        score2, explanation2 = personalization_engine.score_scheme_relevance(
            sample_scheme, overqualified_user
        )
        
        # Both should have reasonable scores, exact match slightly higher
        assert score1 > 0.5
        assert score2 > 0.5
        assert "education" in explanation2.lower()


class TestJobScoring:
    """Test job relevance scoring"""
    
    def test_qualified_candidate(self, personalization_engine, sample_user_profile, sample_job):
        """Test scoring for a candidate who meets job requirements"""
        # Adjust profile to meet job requirements
        qualified_profile = sample_user_profile.copy()
        qualified_profile["education_level"] = "graduate"
        qualified_profile["experience_years"] = 5
        qualified_profile["skills"] = ["crop management", "soil testing"]
        
        score, explanation = personalization_engine.score_job_relevance(
            sample_job, qualified_profile
        )
        
        # Should have high score
        assert score > 0.7, f"Expected high score for qualified candidate, got {score}"
        assert "education" in explanation.lower() or "experience" in explanation.lower()
    
    def test_underqualified_education(self, personalization_engine, sample_user_profile, sample_job):
        """Test scoring when candidate has lower education than required"""
        underqualified_profile = sample_user_profile.copy()
        underqualified_profile["education_level"] = "12th"
        underqualified_profile["experience_years"] = 5
        
        score, explanation = personalization_engine.score_job_relevance(
            sample_job, underqualified_profile
        )
        
        # Should have lower score due to education gap
        assert score < 0.7, f"Expected lower score for underqualified candidate, got {score}"
    
    def test_experience_matching(self, personalization_engine, sample_user_profile, sample_job):
        """Test experience-based scoring"""
        # Sufficient experience
        experienced_profile = sample_user_profile.copy()
        experienced_profile["education_level"] = "graduate"
        experienced_profile["experience_years"] = 5
        
        score1, _ = personalization_engine.score_job_relevance(
            sample_job, experienced_profile
        )
        
        # Insufficient experience
        inexperienced_profile = sample_user_profile.copy()
        inexperienced_profile["education_level"] = "graduate"
        inexperienced_profile["experience_years"] = 1
        
        score2, _ = personalization_engine.score_job_relevance(
            sample_job, inexperienced_profile
        )
        
        # More experienced candidate should score higher
        assert score1 > score2, "Candidate with more experience should score higher"
    
    def test_skills_matching(self, personalization_engine, sample_user_profile, sample_job):
        """Test skills-based scoring"""
        # All required skills
        skilled_profile = sample_user_profile.copy()
        skilled_profile["education_level"] = "graduate"
        skilled_profile["skills"] = ["crop management", "soil testing"]
        
        score1, explanation1 = personalization_engine.score_job_relevance(
            sample_job, skilled_profile
        )
        
        # Partial skills
        partial_skills_profile = sample_user_profile.copy()
        partial_skills_profile["education_level"] = "graduate"
        partial_skills_profile["skills"] = ["crop management"]
        
        score2, explanation2 = personalization_engine.score_job_relevance(
            sample_job, partial_skills_profile
        )
        
        # Candidate with all skills should score higher
        assert score1 > score2, "Candidate with all required skills should score higher"
        assert "skill" in explanation1.lower()
    
    def test_location_preference(self, personalization_engine, sample_user_profile, sample_job):
        """Test location-based scoring"""
        # Same district
        local_profile = sample_user_profile.copy()
        local_profile["education_level"] = "graduate"
        local_profile["state"] = "Maharashtra"
        local_profile["district"] = "Pune"
        
        score1, explanation1 = personalization_engine.score_job_relevance(
            sample_job, local_profile
        )
        
        # Different district, same state
        other_district_profile = sample_user_profile.copy()
        other_district_profile["education_level"] = "graduate"
        other_district_profile["state"] = "Maharashtra"
        other_district_profile["district"] = "Mumbai"
        
        score2, explanation2 = personalization_engine.score_job_relevance(
            sample_job, other_district_profile
        )
        
        # Local candidate should score higher
        assert score1 >= score2, "Candidate in same district should score higher or equal"
    
    def test_explicit_qualifications_parameter(self, personalization_engine, sample_user_profile, sample_job):
        """Test using explicit qualifications parameter"""
        qualifications = {
            "education_level": "graduate",
            "experience_years": 5,
            "skills": ["crop management", "soil testing"]
        }
        
        score, explanation = personalization_engine.score_job_relevance(
            sample_job, sample_user_profile, qualifications
        )
        
        # Should use provided qualifications
        assert score > 0.5
        assert isinstance(explanation, str)


class TestSkillProgramScoring:
    """Test skill program relevance scoring"""
    
    def test_interest_matching(self, personalization_engine, sample_user_profile, sample_skill_program):
        """Test scoring based on user interests"""
        interested_profile = sample_user_profile.copy()
        interested_profile["interests"] = ["agriculture", "farming"]
        
        score, explanation = personalization_engine.score_skill_program_relevance(
            sample_skill_program, interested_profile
        )
        
        # Should have high score due to interest match
        assert score > 0.5, f"Expected high score for interest match, got {score}"
        assert "interest" in explanation.lower()
    
    def test_no_interest_match(self, personalization_engine, sample_user_profile, sample_skill_program):
        """Test scoring when user interests don't match program"""
        uninterested_profile = sample_user_profile.copy()
        uninterested_profile["interests"] = ["music", "art"]
        
        score, explanation = personalization_engine.score_skill_program_relevance(
            sample_skill_program, uninterested_profile
        )
        
        # Should have lower score
        assert score < 0.5, f"Expected lower score for no interest match, got {score}"
    
    def test_career_goal_alignment(self, personalization_engine, sample_user_profile, sample_skill_program):
        """Test scoring based on career goals"""
        goal_aligned_profile = sample_user_profile.copy()
        goal_aligned_profile["career_goals"] = ["farming", "agriculture"]
        
        score, explanation = personalization_engine.score_skill_program_relevance(
            sample_skill_program, goal_aligned_profile
        )
        
        assert score > 0.4
        assert "goal" in explanation.lower() or "interest" in explanation.lower()
    
    def test_online_program_location(self, personalization_engine, sample_user_profile):
        """Test scoring for online programs (location-independent)"""
        online_program = {
            "program_id": "prog456",
            "name": "Digital Agriculture",
            "category": "agriculture",
            "description": "Online course on digital farming",
            "mode": "online",
            "eligibility_criteria": {}
        }
        
        score, explanation = personalization_engine.score_skill_program_relevance(
            online_program, sample_user_profile
        )
        
        # Online programs should get location score
        assert "online" in explanation.lower()
    
    def test_location_based_program(self, personalization_engine, sample_user_profile, sample_skill_program):
        """Test scoring for location-based programs"""
        # Same district
        local_profile = sample_user_profile.copy()
        local_profile["state"] = "Maharashtra"
        local_profile["district"] = "Pune"
        
        score1, explanation1 = personalization_engine.score_skill_program_relevance(
            sample_skill_program, local_profile
        )
        
        # Different state
        remote_profile = sample_user_profile.copy()
        remote_profile["state"] = "Kerala"
        remote_profile["district"] = "Kochi"
        
        score2, explanation2 = personalization_engine.score_skill_program_relevance(
            sample_skill_program, remote_profile
        )
        
        # Local user should score higher
        assert score1 > score2, "User in same location should score higher"
    
    def test_skill_building_on_current_skills(self, personalization_engine, sample_user_profile, sample_skill_program):
        """Test scoring when program builds on current skills"""
        skilled_profile = sample_user_profile.copy()
        skilled_profile["skills"] = ["farming", "agriculture"]
        
        preferences = {
            "interests": ["agriculture"],
            "career_goals": ["farming"],
            "current_skills": ["farming", "agriculture"]
        }
        
        score, explanation = personalization_engine.score_skill_program_relevance(
            sample_skill_program, skilled_profile, preferences
        )
        
        assert score > 0.4
        assert "skill" in explanation.lower() or "interest" in explanation.lower()


class TestRankRecommendations:
    """Test ranking of recommendations"""
    
    def test_rank_schemes(self, personalization_engine, sample_user_profile):
        """Test ranking multiple schemes"""
        schemes = [
            {
                "scheme_id": "s1",
                "name": "Farmer Scheme",
                "category": "agriculture",
                "state": None,
                "eligibility_criteria": {"occupation": ["farmer"], "age_min": 18}
            },
            {
                "scheme_id": "s2",
                "name": "Teacher Scheme",
                "category": "education",
                "state": None,
                "eligibility_criteria": {"occupation": ["teacher"], "age_min": 18}
            },
            {
                "scheme_id": "s3",
                "name": "Maharashtra Farmer Scheme",
                "category": "agriculture",
                "state": "Maharashtra",
                "eligibility_criteria": {"occupation": ["farmer"], "age_min": 18}
            }
        ]
        
        ranked = personalization_engine.rank_recommendations(
            schemes, sample_user_profile, "scheme"
        )
        
        # Should return list of tuples (item, score, explanation)
        assert len(ranked) == 3
        assert all(len(item) == 3 for item in ranked)
        
        # Scores should be in descending order
        scores = [item[1] for item in ranked]
        assert scores == sorted(scores, reverse=True), "Scores should be in descending order"
        
        # Farmer schemes should rank higher than teacher scheme
        farmer_scheme_scores = [item[1] for item in ranked if "farmer" in item[0]["name"].lower()]
        teacher_scheme_score = [item[1] for item in ranked if "teacher" in item[0]["name"].lower()][0]
        assert all(score > teacher_scheme_score for score in farmer_scheme_scores)
    
    def test_rank_jobs(self, personalization_engine, sample_user_profile):
        """Test ranking multiple jobs"""
        jobs = [
            {
                "job_id": "j1",
                "title": "Agricultural Officer",
                "department": "Agriculture",
                "location": {"state": "Maharashtra", "district": "Pune"},
                "qualifications": {"education_level": "graduate", "experience_years": 3}
            },
            {
                "job_id": "j2",
                "title": "Teacher",
                "department": "Education",
                "location": {"state": "Maharashtra", "district": "Mumbai"},
                "qualifications": {"education_level": "graduate", "experience_years": 2}
            }
        ]
        
        qualified_profile = sample_user_profile.copy()
        qualified_profile["education_level"] = "graduate"
        qualified_profile["experience_years"] = 5
        
        ranked = personalization_engine.rank_recommendations(
            jobs, qualified_profile, "job"
        )
        
        assert len(ranked) == 2
        # Agricultural job should rank higher for farmer profile
        assert "agricultural" in ranked[0][0]["title"].lower()
    
    def test_rank_skill_programs(self, personalization_engine, sample_user_profile):
        """Test ranking multiple skill programs"""
        programs = [
            {
                "program_id": "p1",
                "name": "Modern Farming",
                "category": "agriculture",
                "description": "Farming techniques",
                "state": "Maharashtra",
                "mode": "in-person",
                "eligibility_criteria": {}
            },
            {
                "program_id": "p2",
                "name": "Music Production",
                "category": "arts",
                "description": "Music and audio",
                "state": "Maharashtra",
                "mode": "online",
                "eligibility_criteria": {}
            }
        ]
        
        ranked = personalization_engine.rank_recommendations(
            programs, sample_user_profile, "skill_program"
        )
        
        assert len(ranked) == 2
        # Farming program should rank higher for farmer with agriculture interests
        assert "farming" in ranked[0][0]["name"].lower()
    
    def test_invalid_recommendation_type(self, personalization_engine, sample_user_profile, sample_scheme):
        """Test error handling for invalid recommendation type"""
        with pytest.raises(ValueError, match="Unknown recommendation type"):
            personalization_engine.rank_recommendations(
                [sample_scheme], sample_user_profile, "invalid_type"
            )


class TestExplanationGeneration:
    """Test explanation generation"""
    
    def test_high_relevance_explanation(self, personalization_engine, sample_user_profile, sample_scheme):
        """Test explanation for highly relevant recommendation"""
        explanation = personalization_engine.generate_detailed_explanation(
            sample_scheme,
            sample_user_profile,
            "scheme",
            0.85,
            "Recommended because it matches your profile"
        )
        
        assert "highly recommended" in explanation.lower()
        assert "farmer" in explanation.lower()
        assert "maharashtra" in explanation.lower()
        assert len(explanation) > 50
    
    def test_moderate_relevance_explanation(self, personalization_engine, sample_user_profile, sample_scheme):
        """Test explanation for moderately relevant recommendation"""
        explanation = personalization_engine.generate_detailed_explanation(
            sample_scheme,
            sample_user_profile,
            "scheme",
            0.55,
            "May be relevant"
        )
        
        assert "good match" in explanation.lower() or "moderate" in explanation.lower()
        assert isinstance(explanation, str)
    
    def test_low_relevance_explanation(self, personalization_engine, sample_user_profile, sample_scheme):
        """Test explanation for low relevance recommendation"""
        explanation = personalization_engine.generate_detailed_explanation(
            sample_scheme,
            sample_user_profile,
            "scheme",
            0.25,
            "This scheme may be relevant"
        )
        
        assert "may be relevant" in explanation.lower()
        assert len(explanation) > 0
    
    def test_job_explanation_includes_qualifications(self, personalization_engine, sample_user_profile, sample_job):
        """Test job explanation includes education and experience"""
        qualified_profile = sample_user_profile.copy()
        qualified_profile["education_level"] = "graduate"
        qualified_profile["experience_years"] = 5
        
        explanation = personalization_engine.generate_detailed_explanation(
            sample_job,
            qualified_profile,
            "job",
            0.75,
            "Good match for your qualifications"
        )
        
        assert "graduate" in explanation.lower() or "education" in explanation.lower()
        assert "experience" in explanation.lower() or "years" in explanation.lower()
    
    def test_skill_program_explanation_includes_interests(self, personalization_engine, sample_user_profile, sample_skill_program):
        """Test skill program explanation includes interests"""
        interested_profile = sample_user_profile.copy()
        interested_profile["interests"] = ["agriculture", "technology"]
        
        explanation = personalization_engine.generate_detailed_explanation(
            sample_skill_program,
            interested_profile,
            "skill_program",
            0.70,
            "Matches your interests"
        )
        
        assert "interest" in explanation.lower()
        assert "agriculture" in explanation.lower() or "technology" in explanation.lower()
    
    def test_explanation_always_returns_string(self, personalization_engine, sample_user_profile, sample_scheme):
        """Test that explanation generation always returns a valid string"""
        # Test with minimal profile
        minimal_profile = {"user_id": "user123"}
        
        explanation = personalization_engine.generate_detailed_explanation(
            sample_scheme,
            minimal_profile,
            "scheme",
            0.5,
            "May be relevant"
        )
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert explanation.endswith(".")


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_user_profile(self, personalization_engine, sample_scheme):
        """Test scoring with empty user profile"""
        empty_profile = {}
        
        score, explanation = personalization_engine.score_scheme_relevance(
            sample_scheme, empty_profile
        )
        
        # Should return some score without crashing
        assert 0 <= score <= 1
        assert isinstance(explanation, str)
    
    def test_missing_eligibility_criteria(self, personalization_engine, sample_user_profile):
        """Test scoring scheme with no eligibility criteria"""
        scheme_no_criteria = {
            "scheme_id": "s1",
            "name": "Universal Scheme",
            "category": "general",
            "state": None
        }
        
        score, explanation = personalization_engine.score_scheme_relevance(
            scheme_no_criteria, sample_user_profile
        )
        
        assert 0 <= score <= 1
        assert isinstance(explanation, str)
    
    def test_invalid_income_format(self, personalization_engine, sample_scheme):
        """Test handling of invalid income format"""
        invalid_income_profile = {
            "occupation": "farmer",
            "state": "Maharashtra",
            "age": 35,
            "income_bracket": "invalid",
            "education_level": "10th"
        }
        
        score, explanation = personalization_engine.score_scheme_relevance(
            sample_scheme, invalid_income_profile
        )
        
        # Should handle gracefully without crashing
        assert 0 <= score <= 1
    
    def test_score_bounds(self, personalization_engine, sample_user_profile, sample_scheme):
        """Test that scores are always between 0 and 1"""
        score, _ = personalization_engine.score_scheme_relevance(
            sample_scheme, sample_user_profile
        )
        
        assert 0 <= score <= 1, f"Score {score} is out of bounds [0, 1]"
    
    def test_explanation_presence(self, personalization_engine, sample_user_profile, sample_scheme):
        """Test that explanations are always provided"""
        _, explanation = personalization_engine.score_scheme_relevance(
            sample_scheme, sample_user_profile
        )
        
        assert explanation is not None
        assert isinstance(explanation, str)
        assert len(explanation) > 0
