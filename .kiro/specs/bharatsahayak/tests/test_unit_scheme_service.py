"""
Unit tests for Scheme Service

Tests scheme search with various filters, eligibility with edge cases,
and scheme not found error handling.

Feature: bharatsahayak
Requirements: 2.1, 2.2, 2.3
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
import uuid

from app.services.scheme_repository import SchemeRepository
from app.services.eligibility_checker import EligibilityChecker
from app.models.scheme import Scheme, SchemeTranslation
from app.schemas.scheme import SchemeFilters, EligibilityResult


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    return Mock()


@pytest.fixture
def sample_schemes():
    """Create sample schemes for testing"""
    scheme1_id = uuid.uuid4()
    scheme2_id = uuid.uuid4()
    scheme3_id = uuid.uuid4()
    
    scheme1 = Scheme(
        scheme_id=scheme1_id,
        name="PM-KISAN",
        category="agriculture",
        description="Income support for farmer families",
        benefits=["Rs 6000 per year", "Direct bank transfer"],
        eligibility_criteria={
            "occupation": ["farmer"],
            "age_min": 18,
            "income_max": 200000
        },
        required_documents=["Aadhaar", "Bank account"],
        application_process=["Visit portal", "Fill form", "Submit"],
        application_url="https://pmkisan.gov.in",
        department="Agriculture",
        state=None,  # Central scheme
        source_url="https://pmkisan.gov.in",
        last_updated=datetime.utcnow(),
        created_at=datetime.utcnow(),
        translations=[]
    )
    
    scheme2 = Scheme(
        scheme_id=scheme2_id,
        name="Ayushman Bharat",
        category="health",
        description="Health insurance for poor families",
        benefits=["Rs 5 lakh coverage", "Cashless treatment"],
        eligibility_criteria={
            "income_max": 100000,
            "location": ["All India"]
        },
        required_documents=["Aadhaar", "Ration card"],
        application_process=["Visit hospital", "Show card"],
        application_url="https://pmjay.gov.in",
        department="Health",
        state=None,
        source_url="https://pmjay.gov.in",
        last_updated=datetime.utcnow(),
        created_at=datetime.utcnow(),
        translations=[]
    )
    
    scheme3 = Scheme(
        scheme_id=scheme3_id,
        name="Maharashtra Skill Development",
        category="employment",
        description="Skill training for youth in Maharashtra",
        benefits=["Free training", "Certification"],
        eligibility_criteria={
            "age_min": 18,
            "age_max": 35,
            "location": ["Maharashtra"],
            "education": ["10th pass", "12th pass"]
        },
        required_documents=["Aadhaar", "Education certificate"],
        application_process=["Apply online", "Attend interview"],
        application_url="https://maharashtra.gov.in/skills",
        department="Skill Development",
        state="Maharashtra",
        source_url="https://maharashtra.gov.in",
        last_updated=datetime.utcnow(),
        created_at=datetime.utcnow(),
        translations=[]
    )
    
    return [scheme1, scheme2, scheme3]


class TestSchemeSearch:
    """Test scheme search with various filters"""
    
    def test_search_without_filters(self, mock_db, sample_schemes):
        """Test searching schemes without any filters"""
        # Mock query chain
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = sample_schemes
        
        mock_db.query.return_value = mock_query
        
        repository = SchemeRepository(mock_db)
        filters = SchemeFilters()
        
        results = repository.search_schemes(filters)
        
        assert len(results) == 3
        assert results[0].name == "PM-KISAN"
    
    def test_search_by_category(self, mock_db, sample_schemes):
        """Test searching schemes by category"""
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = [sample_schemes[0]]  # Only agriculture
        
        mock_db.query.return_value = mock_query
        
        repository = SchemeRepository(mock_db)
        filters = SchemeFilters(category="agriculture")
        
        results = repository.search_schemes(filters)
        
        assert len(results) == 1
        assert results[0].category == "agriculture"
        # Verify filter was called
        mock_query.filter.assert_called()
    
    def test_search_by_state(self, mock_db, sample_schemes):
        """Test searching schemes by state (includes central schemes)"""
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        # Should return Maharashtra scheme + central schemes
        mock_query.all.return_value = [sample_schemes[0], sample_schemes[2]]
        
        mock_db.query.return_value = mock_query
        
        repository = SchemeRepository(mock_db)
        filters = SchemeFilters(state="Maharashtra")
        
        results = repository.search_schemes(filters)
        
        assert len(results) == 2
        # Verify filter was called for state
        mock_query.filter.assert_called()
    
    def test_search_by_department(self, mock_db, sample_schemes):
        """Test searching schemes by department"""
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = [sample_schemes[1]]  # Health department
        
        mock_db.query.return_value = mock_query
        
        repository = SchemeRepository(mock_db)
        filters = SchemeFilters(department="Health")
        
        results = repository.search_schemes(filters)
        
        assert len(results) == 1
        assert results[0].department == "Health"
    
    def test_search_by_text_query(self, mock_db, sample_schemes):
        """Test searching schemes by text query in name/description"""
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = [sample_schemes[0]]  # PM-KISAN matches "farmer"
        
        mock_db.query.return_value = mock_query
        
        repository = SchemeRepository(mock_db)
        filters = SchemeFilters(query="farmer")
        
        results = repository.search_schemes(filters)
        
        assert len(results) == 1
        assert "farmer" in results[0].description.lower()
    
    def test_search_with_multiple_filters(self, mock_db, sample_schemes):
        """Test searching schemes with multiple filters combined"""
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = [sample_schemes[2]]  # Maharashtra + employment
        
        mock_db.query.return_value = mock_query
        
        repository = SchemeRepository(mock_db)
        filters = SchemeFilters(
            category="employment",
            state="Maharashtra"
        )
        
        results = repository.search_schemes(filters)
        
        assert len(results) == 1
        assert results[0].category == "employment"
        assert results[0].state == "Maharashtra"
        # Verify multiple filters were applied
        assert mock_query.filter.call_count >= 2
    
    def test_search_with_pagination(self, mock_db, sample_schemes):
        """Test searching schemes with limit and offset"""
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = [sample_schemes[1]]  # Second page
        
        mock_db.query.return_value = mock_query
        
        repository = SchemeRepository(mock_db)
        filters = SchemeFilters()
        
        results = repository.search_schemes(filters, limit=1, offset=1)
        
        # Verify pagination was applied
        mock_query.limit.assert_called_with(1)
        mock_query.offset.assert_called_with(1)
    
    def test_search_returns_empty_list_when_no_matches(self, mock_db):
        """Test searching schemes returns empty list when no matches"""
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        repository = SchemeRepository(mock_db)
        filters = SchemeFilters(category="nonexistent")
        
        results = repository.search_schemes(filters)
        
        assert len(results) == 0
        assert isinstance(results, list)
    
    def test_search_orders_by_created_at_desc(self, mock_db, sample_schemes):
        """Test that search results are ordered by created_at descending"""
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = sample_schemes
        
        mock_db.query.return_value = mock_query
        
        repository = SchemeRepository(mock_db)
        filters = SchemeFilters()
        
        repository.search_schemes(filters)
        
        # Verify order_by was called
        mock_query.order_by.assert_called()


class TestSchemeNotFound:
    """Test scheme not found error handling"""
    
    def test_get_scheme_by_id_not_found(self, mock_db):
        """Test getting scheme by ID when scheme doesn't exist"""
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        mock_db.query.return_value = mock_query
        
        repository = SchemeRepository(mock_db)
        result = repository.get_scheme_by_id(str(uuid.uuid4()))
        
        assert result is None
    
    def test_get_scheme_by_invalid_uuid(self, mock_db):
        """Test getting scheme with invalid UUID format"""
        repository = SchemeRepository(mock_db)
        result = repository.get_scheme_by_id("invalid-uuid")
        
        assert result is None
    
    def test_get_scheme_by_id_found(self, mock_db, sample_schemes):
        """Test getting scheme by ID when scheme exists"""
        scheme = sample_schemes[0]
        
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = scheme
        
        mock_db.query.return_value = mock_query
        
        repository = SchemeRepository(mock_db)
        result = repository.get_scheme_by_id(str(scheme.scheme_id))
        
        assert result is not None
        assert result.scheme_id == scheme.scheme_id
        assert result.name == "PM-KISAN"
    
    def test_update_scheme_not_found(self, mock_db):
        """Test updating scheme that doesn't exist"""
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        mock_db.query.return_value = mock_query
        
        repository = SchemeRepository(mock_db)
        from app.schemas.scheme import SchemeUpdate
        
        result = repository.update_scheme(
            str(uuid.uuid4()),
            SchemeUpdate(name="Updated Name")
        )
        
        assert result is None
    
    def test_delete_scheme_not_found(self, mock_db):
        """Test deleting scheme that doesn't exist"""
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        mock_db.query.return_value = mock_query
        
        repository = SchemeRepository(mock_db)
        result = repository.delete_scheme(str(uuid.uuid4()))
        
        assert result is False


class TestEligibilityEdgeCases:
    """Test eligibility checking with edge cases (missing criteria)"""
    
    def test_eligibility_with_missing_age(self, mock_db, sample_schemes):
        """Test eligibility check when user age is missing"""
        checker = EligibilityChecker(mock_db)
        scheme = sample_schemes[0]  # PM-KISAN requires age_min: 18
        
        user_profile = {
            "occupation": "farmer",
            "income_bracket": "0-100000"
            # age is missing
        }
        
        result = checker.check_eligibility(user_profile, scheme)
        
        assert result.is_eligible is False
        assert "age" in result.missing_criteria
        assert result.confidence < 1.0
    
    def test_eligibility_with_missing_income(self, mock_db, sample_schemes):
        """Test eligibility check when user income is missing"""
        checker = EligibilityChecker(mock_db)
        scheme = sample_schemes[0]  # PM-KISAN requires income_max
        
        user_profile = {
            "age": 30,
            "occupation": "farmer"
            # income_bracket is missing
        }
        
        result = checker.check_eligibility(user_profile, scheme)
        
        assert result.is_eligible is False
        assert "income_bracket" in result.missing_criteria
        assert result.confidence < 1.0
    
    def test_eligibility_with_missing_occupation(self, mock_db, sample_schemes):
        """Test eligibility check when user occupation is missing"""
        checker = EligibilityChecker(mock_db)
        scheme = sample_schemes[0]  # PM-KISAN requires occupation: farmer
        
        user_profile = {
            "age": 30,
            "income_bracket": "0-100000"
            # occupation is missing
        }
        
        result = checker.check_eligibility(user_profile, scheme)
        
        assert result.is_eligible is False
        assert "occupation" in result.missing_criteria
        assert result.confidence < 1.0
    
    def test_eligibility_with_missing_location(self, mock_db, sample_schemes):
        """Test eligibility check when user location is missing"""
        checker = EligibilityChecker(mock_db)
        scheme = sample_schemes[2]  # Maharashtra scheme requires location
        
        user_profile = {
            "age": 25,
            "education_level": "12th pass"
            # location/state is missing
        }
        
        result = checker.check_eligibility(user_profile, scheme)
        
        assert result.is_eligible is False
        assert any("location" in criterion for criterion in result.missing_criteria)
        assert result.confidence < 1.0
    
    def test_eligibility_with_missing_education(self, mock_db, sample_schemes):
        """Test eligibility check when user education is missing"""
        checker = EligibilityChecker(mock_db)
        scheme = sample_schemes[2]  # Maharashtra scheme requires education
        
        user_profile = {
            "age": 25,
            "state": "Maharashtra"
            # education_level is missing
        }
        
        result = checker.check_eligibility(user_profile, scheme)
        
        assert result.is_eligible is False
        assert "education_level" in result.missing_criteria
        assert result.confidence < 1.0
    
    def test_eligibility_with_all_criteria_missing(self, mock_db, sample_schemes):
        """Test eligibility check when all criteria are missing"""
        checker = EligibilityChecker(mock_db)
        scheme = sample_schemes[0]
        
        user_profile = {}  # Empty profile
        
        result = checker.check_eligibility(user_profile, scheme)
        
        assert result.is_eligible is False
        assert len(result.missing_criteria) > 0
        assert result.confidence < 1.0
    
    def test_eligibility_with_age_below_minimum(self, mock_db, sample_schemes):
        """Test eligibility when user age is below minimum"""
        checker = EligibilityChecker(mock_db)
        scheme = sample_schemes[0]  # PM-KISAN requires age_min: 18
        
        user_profile = {
            "age": 16,  # Below minimum
            "occupation": "farmer",
            "income_bracket": "0-100000"
        }
        
        result = checker.check_eligibility(user_profile, scheme)
        
        assert result.is_eligible is False
        assert any("age" in criterion and "minimum" in criterion for criterion in result.missing_criteria)
    
    def test_eligibility_with_age_above_maximum(self, mock_db, sample_schemes):
        """Test eligibility when user age is above maximum"""
        checker = EligibilityChecker(mock_db)
        scheme = sample_schemes[2]  # Maharashtra scheme has age_max: 35
        
        user_profile = {
            "age": 40,  # Above maximum
            "state": "Maharashtra",
            "education_level": "12th pass"
        }
        
        result = checker.check_eligibility(user_profile, scheme)
        
        assert result.is_eligible is False
        assert any("age" in criterion and "maximum" in criterion for criterion in result.missing_criteria)
    
    def test_eligibility_with_income_above_maximum(self, mock_db, sample_schemes):
        """Test eligibility when user income is above maximum"""
        checker = EligibilityChecker(mock_db)
        scheme = sample_schemes[0]  # PM-KISAN has income_max: 200000
        
        user_profile = {
            "age": 30,
            "occupation": "farmer",
            "income_bracket": "200000-500000"  # Above maximum
        }
        
        result = checker.check_eligibility(user_profile, scheme)
        
        assert result.is_eligible is False
        assert any("income" in criterion for criterion in result.missing_criteria)
    
    def test_eligibility_with_wrong_occupation(self, mock_db, sample_schemes):
        """Test eligibility when user has wrong occupation"""
        checker = EligibilityChecker(mock_db)
        scheme = sample_schemes[0]  # PM-KISAN requires occupation: farmer
        
        user_profile = {
            "age": 30,
            "occupation": "teacher",  # Wrong occupation
            "income_bracket": "0-100000"
        }
        
        result = checker.check_eligibility(user_profile, scheme)
        
        assert result.is_eligible is False
        assert any("occupation" in criterion for criterion in result.missing_criteria)
    
    def test_eligibility_with_wrong_location(self, mock_db, sample_schemes):
        """Test eligibility when user is in wrong location"""
        checker = EligibilityChecker(mock_db)
        scheme = sample_schemes[2]  # Maharashtra scheme
        
        user_profile = {
            "age": 25,
            "state": "Karnataka",  # Wrong state
            "education_level": "12th pass"
        }
        
        result = checker.check_eligibility(user_profile, scheme)
        
        assert result.is_eligible is False
        assert any("location" in criterion for criterion in result.missing_criteria)
    
    def test_eligibility_with_all_criteria_met(self, mock_db, sample_schemes):
        """Test eligibility when all criteria are met"""
        checker = EligibilityChecker(mock_db)
        scheme = sample_schemes[0]  # PM-KISAN
        
        user_profile = {
            "age": 30,
            "occupation": "farmer",
            "income_bracket": "0-100000"
        }
        
        result = checker.check_eligibility(user_profile, scheme)
        
        assert result.is_eligible is True
        assert len(result.missing_criteria) == 0
        assert result.confidence == 1.0
    
    def test_eligibility_with_partial_criteria_met(self, mock_db, sample_schemes):
        """Test eligibility with some criteria met and some missing"""
        checker = EligibilityChecker(mock_db)
        scheme = sample_schemes[2]  # Maharashtra scheme
        
        user_profile = {
            "age": 25,
            "state": "Maharashtra"
            # education_level is missing
        }
        
        result = checker.check_eligibility(user_profile, scheme)
        
        assert result.is_eligible is False
        assert len(result.missing_criteria) > 0
        assert 0 < result.confidence < 1.0
    
    def test_eligibility_explanation_in_english(self, mock_db, sample_schemes):
        """Test eligibility explanation is generated in English"""
        checker = EligibilityChecker(mock_db)
        scheme = sample_schemes[0]
        
        user_profile = {
            "age": 16,  # Below minimum
            "occupation": "farmer",
            "income_bracket": "0-100000"
        }
        
        result = checker.check_eligibility(user_profile, scheme)
        
        assert result.explanation is not None
        assert len(result.explanation) > 0
        assert "PM-KISAN" in result.explanation
    
    def test_eligibility_explanation_in_hindi(self, mock_db, sample_schemes):
        """Test eligibility explanation can be generated in Hindi"""
        checker = EligibilityChecker(mock_db)
        
        explanation = checker.explain_eligibility(
            is_eligible=False,
            missing_criteria=["age"],
            scheme_name="PM-KISAN",
            language="hi"
        )
        
        assert explanation is not None
        assert len(explanation) > 0
        # Should contain Hindi text
        assert "पात्र" in explanation or "योजना" in explanation
    
    def test_get_eligible_schemes_with_empty_list(self, mock_db):
        """Test getting eligible schemes when no schemes match"""
        mock_db.query.return_value.all.return_value = []
        
        checker = EligibilityChecker(mock_db)
        user_profile = {"age": 30}
        
        results = checker.get_eligible_schemes(user_profile)
        
        assert len(results) == 0
        assert isinstance(results, list)
    
    def test_get_eligible_schemes_filters_ineligible(self, mock_db, sample_schemes):
        """Test that get_eligible_schemes only returns eligible schemes"""
        mock_db.query.return_value.all.return_value = sample_schemes
        
        checker = EligibilityChecker(mock_db)
        user_profile = {
            "age": 30,
            "occupation": "farmer",
            "income_bracket": "0-100000"
        }
        
        results = checker.get_eligible_schemes(user_profile)
        
        # Should only return PM-KISAN (scheme1) which matches farmer occupation
        assert len(results) >= 1
        for scheme, eligibility in results:
            assert eligibility.is_eligible is True
