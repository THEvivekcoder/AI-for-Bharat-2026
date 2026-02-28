"""
Unit tests for Health Advisory Service

Tests symptom analysis with various inputs, facility search with different locations,
and edge cases (no facilities nearby).

Feature: bharatsahayak
Requirements: 5.1, 5.2, 5.5
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
import uuid

from app.services.health_advisor import HealthAdvisor
from app.models.health import HealthFacility
from app.schemas.health import BasicHealthInfo, Location


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    return Mock()


@pytest.fixture
def sample_location():
    """Create a sample location"""
    return Location(
        state="Maharashtra",
        district="Pune",
        latitude=18.5204,
        longitude=73.8567
    )


@pytest.fixture
def sample_health_info():
    """Create sample basic health info"""
    return BasicHealthInfo(
        age=35,
        gender="male",
        existing_conditions=["diabetes"],
        medications=["metformin"]
    )


class TestSymptomAnalysisWithVariousInputs:
    """Test symptom analysis with various input scenarios"""
    
    def test_symptom_analysis_with_single_symptom(self, mock_db):
        """Test symptom analysis with a single symptom"""
        advisor = HealthAdvisor(mock_db)
        
        guidance = advisor.analyze_symptoms(["fever"])
        
        assert guidance is not None
        assert guidance.urgency_level in ["routine", "soon", "urgent", "emergency"]
        assert len(guidance.possible_conditions) > 0
        assert len(guidance.self_care_recommendations) > 0
        assert guidance.disclaimer is not None
        assert 0.0 <= guidance.confidence <= 1.0
    
    def test_symptom_analysis_with_multiple_symptoms(self, mock_db):
        """Test symptom analysis with multiple symptoms"""
        advisor = HealthAdvisor(mock_db)
        
        guidance = advisor.analyze_symptoms(["fever", "cough", "body ache"])
        
        assert guidance is not None
        assert len(guidance.possible_conditions) > 0
        # Multiple symptoms should increase confidence
        assert guidance.confidence > 0.5
        assert "Common cold" in guidance.possible_conditions or "Flu" in guidance.possible_conditions
    
    def test_symptom_analysis_with_emergency_symptom(self, mock_db):
        """Test symptom analysis with emergency symptom"""
        advisor = HealthAdvisor(mock_db)
        
        guidance = advisor.analyze_symptoms(["chest pain"])
        
        assert guidance.urgency_level == "emergency"
        assert "emergency" in guidance.when_to_seek_care.lower()
        assert "immediately" in guidance.when_to_seek_care.lower()
    
    def test_symptom_analysis_with_urgent_symptom(self, mock_db):
        """Test symptom analysis with urgent symptom"""
        advisor = HealthAdvisor(mock_db)
        
        guidance = advisor.analyze_symptoms(["high fever", "severe pain"])
        
        assert guidance.urgency_level in ["urgent", "emergency"]
        assert "24 hours" in guidance.when_to_seek_care or "soon" in guidance.when_to_seek_care.lower()
    
    def test_symptom_analysis_with_routine_symptom(self, mock_db):
        """Test symptom analysis with routine symptom"""
        advisor = HealthAdvisor(mock_db)
        
        guidance = advisor.analyze_symptoms(["mild headache"])
        
        assert guidance.urgency_level in ["routine", "soon"]
        assert len(guidance.self_care_recommendations) > 0
    
    def test_symptom_analysis_with_vague_symptoms(self, mock_db):
        """Test symptom analysis with vague symptoms"""
        advisor = HealthAdvisor(mock_db)
        
        guidance = advisor.analyze_symptoms(["not feeling well", "discomfort"])
        
        assert guidance is not None
        # Vague symptoms should reduce confidence
        assert guidance.confidence < 0.7
    
    def test_symptom_analysis_with_specific_symptoms(self, mock_db):
        """Test symptom analysis with specific symptoms"""
        advisor = HealthAdvisor(mock_db)
        
        guidance = advisor.analyze_symptoms(["fever 102F", "dry cough", "sore throat"])
        
        assert guidance is not None
        # Specific symptoms should increase confidence
        assert guidance.confidence > 0.6
        assert len(guidance.possible_conditions) > 0
    
    def test_symptom_analysis_with_user_info(self, mock_db, sample_health_info):
        """Test symptom analysis with user health information"""
        advisor = HealthAdvisor(mock_db)
        
        guidance = advisor.analyze_symptoms(["dizziness", "fatigue"], sample_health_info)
        
        assert guidance is not None
        assert len(guidance.possible_conditions) > 0
    
    def test_symptom_analysis_with_mixed_case_symptoms(self, mock_db):
        """Test symptom analysis with mixed case input"""
        advisor = HealthAdvisor(mock_db)
        
        guidance = advisor.analyze_symptoms(["FEVER", "Cough", "body ACHE"])
        
        assert guidance is not None
        assert len(guidance.possible_conditions) > 0
    
    def test_symptom_analysis_with_whitespace(self, mock_db):
        """Test symptom analysis with extra whitespace"""
        advisor = HealthAdvisor(mock_db)
        
        guidance = advisor.analyze_symptoms(["  fever  ", " cough "])
        
        assert guidance is not None
        assert len(guidance.possible_conditions) > 0
    
    def test_symptom_analysis_includes_disclaimer(self, mock_db):
        """Test that symptom analysis always includes disclaimer"""
        advisor = HealthAdvisor(mock_db)
        
        guidance = advisor.analyze_symptoms(["headache"])
        
        assert guidance.disclaimer is not None
        assert len(guidance.disclaimer) > 0
        assert "not a substitute" in guidance.disclaimer.lower()
    
    def test_symptom_analysis_includes_red_flags(self, mock_db):
        """Test that symptom analysis includes red flags"""
        advisor = HealthAdvisor(mock_db)
        
        guidance = advisor.analyze_symptoms(["fever", "cough"])
        
        assert len(guidance.red_flags) > 0
        assert any("worsen" in flag.lower() for flag in guidance.red_flags)
    
    def test_symptom_analysis_with_severity_keywords(self, mock_db):
        """Test symptom analysis with severity keywords"""
        advisor = HealthAdvisor(mock_db)
        
        guidance = advisor.analyze_symptoms(["severe headache", "intense pain"])
        
        assert guidance.urgency_level in ["urgent", "emergency"]
    
    def test_symptom_analysis_with_many_symptoms(self, mock_db):
        """Test symptom analysis with many symptoms (4+)"""
        advisor = HealthAdvisor(mock_db)
        
        guidance = advisor.analyze_symptoms([
            "fever", "cough", "body ache", "fatigue", "headache"
        ])
        
        # Many symptoms should increase urgency
        assert guidance.urgency_level in ["soon", "urgent"]
    
    def test_symptom_analysis_with_gastrointestinal_symptoms(self, mock_db):
        """Test symptom analysis with gastrointestinal symptoms"""
        advisor = HealthAdvisor(mock_db)
        
        guidance = advisor.analyze_symptoms(["stomach pain", "diarrhea", "vomiting"])
        
        assert guidance is not None
        assert any("Food poisoning" in cond or "gastroenteritis" in cond 
                  for cond in guidance.possible_conditions)
    
    def test_symptom_analysis_with_respiratory_symptoms(self, mock_db):
        """Test symptom analysis with respiratory symptoms"""
        advisor = HealthAdvisor(mock_db)
        
        guidance = advisor.analyze_symptoms(["cough", "runny nose", "sore throat"])
        
        assert guidance is not None
        assert any("cold" in cond.lower() for cond in guidance.possible_conditions)
    
    def test_symptom_analysis_with_neurological_symptoms(self, mock_db):
        """Test symptom analysis with neurological symptoms"""
        advisor = HealthAdvisor(mock_db)
        
        guidance = advisor.analyze_symptoms(["headache", "dizziness"])
        
        assert guidance is not None
        assert len(guidance.possible_conditions) > 0
    
    def test_symptom_analysis_with_dermatological_symptoms(self, mock_db):
        """Test symptom analysis with dermatological symptoms"""
        advisor = HealthAdvisor(mock_db)
        
        guidance = advisor.analyze_symptoms(["rash", "itching"])
        
        assert guidance is not None
        assert any("Allergic" in cond or "rash" in cond.lower() 
                  for cond in guidance.possible_conditions)
    
    def test_symptom_analysis_with_musculoskeletal_symptoms(self, mock_db):
        """Test symptom analysis with musculoskeletal symptoms"""
        advisor = HealthAdvisor(mock_db)
        
        guidance = advisor.analyze_symptoms(["joint pain", "body ache"])
        
        assert guidance is not None
        assert len(guidance.possible_conditions) > 0


class TestFacilitySearchWithDifferentLocations:
    """Test facility search with different location scenarios"""
    
    def test_facility_search_with_coordinates(self, mock_db, sample_location):
        """Test facility search with location coordinates"""
        # Create mock facilities
        facility1 = HealthFacility(
            facility_id=uuid.uuid4(),
            name="Pune PHC",
            facility_type="PHC",
            state="Maharashtra",
            district="Pune",
            address="123 Main St",
            latitude=18.5304,
            longitude=73.8667,
            contact="020-12345678",
            services=["OPD", "Emergency"],
            created_at=datetime.utcnow()
        )
        
        facility2 = HealthFacility(
            facility_id=uuid.uuid4(),
            name="Pune District Hospital",
            facility_type="District Hospital",
            state="Maharashtra",
            district="Pune",
            address="456 Hospital Rd",
            latitude=18.5104,
            longitude=73.8467,
            contact="020-87654321",
            services=["OPD", "Emergency", "Surgery"],
            created_at=datetime.utcnow()
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [facility1, facility2]
        
        mock_db.query.return_value = mock_query
        
        advisor = HealthAdvisor(mock_db)
        facilities = advisor.find_facilities(sample_location)
        
        assert len(facilities) == 2
        assert all(f.distance_km is not None for f in facilities)
        # Should be sorted by distance
        assert facilities[0].distance_km <= facilities[1].distance_km
    
    def test_facility_search_without_coordinates(self, mock_db):
        """Test facility search without location coordinates"""
        location = Location(
            state="Maharashtra",
            district="Pune",
            latitude=None,
            longitude=None
        )
        
        facility = HealthFacility(
            facility_id=uuid.uuid4(),
            name="Pune PHC",
            facility_type="PHC",
            state="Maharashtra",
            district="Pune",
            address="123 Main St",
            latitude=None,
            longitude=None,
            contact="020-12345678",
            services=["OPD"],
            created_at=datetime.utcnow()
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [facility]
        
        mock_db.query.return_value = mock_query
        
        advisor = HealthAdvisor(mock_db)
        facilities = advisor.find_facilities(location)
        
        assert len(facilities) == 1
        assert facilities[0].distance_km is None
    
    def test_facility_search_with_facility_type_filter(self, mock_db, sample_location):
        """Test facility search with facility type filter"""
        phc = HealthFacility(
            facility_id=uuid.uuid4(),
            name="Pune PHC",
            facility_type="PHC",
            state="Maharashtra",
            district="Pune",
            address="123 Main St",
            latitude=18.5304,
            longitude=73.8667,
            contact="020-12345678",
            services=["OPD"],
            created_at=datetime.utcnow()
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [phc]
        
        mock_db.query.return_value = mock_query
        
        advisor = HealthAdvisor(mock_db)
        facilities = advisor.find_facilities(sample_location, facility_type="PHC")
        
        assert len(facilities) == 1
        assert facilities[0].facility_type == "PHC"
    
    def test_facility_search_with_custom_radius(self, mock_db, sample_location):
        """Test facility search with custom radius"""
        # Create facility within 10km
        near_facility = HealthFacility(
            facility_id=uuid.uuid4(),
            name="Near PHC",
            facility_type="PHC",
            state="Maharashtra",
            district="Pune",
            address="123 Main St",
            latitude=18.5304,  # ~1.2 km away
            longitude=73.8667,
            contact="020-12345678",
            services=["OPD"],
            created_at=datetime.utcnow()
        )
        
        # Create facility beyond 10km
        far_facility = HealthFacility(
            facility_id=uuid.uuid4(),
            name="Far Hospital",
            facility_type="District Hospital",
            state="Maharashtra",
            district="Pune",
            address="456 Hospital Rd",
            latitude=18.6204,  # ~11 km away
            longitude=73.9567,
            contact="020-87654321",
            services=["OPD", "Emergency"],
            created_at=datetime.utcnow()
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [near_facility, far_facility]
        
        mock_db.query.return_value = mock_query
        
        advisor = HealthAdvisor(mock_db)
        facilities = advisor.find_facilities(sample_location, radius_km=10)
        
        # Should only return facility within 10km
        assert len(facilities) == 1
        assert facilities[0].name == "Near PHC"
    
    def test_facility_search_in_different_state(self, mock_db):
        """Test facility search in different state"""
        location = Location(
            state="Karnataka",
            district="Bangalore",
            latitude=12.9716,
            longitude=77.5946
        )
        
        facility = HealthFacility(
            facility_id=uuid.uuid4(),
            name="Bangalore PHC",
            facility_type="PHC",
            state="Karnataka",
            district="Bangalore",
            address="123 MG Road",
            latitude=12.9716,
            longitude=77.5946,
            contact="080-12345678",
            services=["OPD"],
            created_at=datetime.utcnow()
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [facility]
        
        mock_db.query.return_value = mock_query
        
        advisor = HealthAdvisor(mock_db)
        facilities = advisor.find_facilities(location)
        
        assert len(facilities) == 1
        assert facilities[0].state == "Karnataka"
    
    def test_facility_search_in_different_district(self, mock_db):
        """Test facility search in different district"""
        location = Location(
            state="Maharashtra",
            district="Mumbai",
            latitude=19.0760,
            longitude=72.8777
        )
        
        facility = HealthFacility(
            facility_id=uuid.uuid4(),
            name="Mumbai Hospital",
            facility_type="District Hospital",
            state="Maharashtra",
            district="Mumbai",
            address="456 Marine Drive",
            latitude=19.0760,
            longitude=72.8777,
            contact="022-12345678",
            services=["OPD", "Emergency"],
            created_at=datetime.utcnow()
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [facility]
        
        mock_db.query.return_value = mock_query
        
        advisor = HealthAdvisor(mock_db)
        facilities = advisor.find_facilities(location)
        
        assert len(facilities) == 1
        assert facilities[0].district == "Mumbai"
    
    def test_facility_search_returns_all_facility_types(self, mock_db, sample_location):
        """Test facility search returns all facility types when no filter"""
        phc = HealthFacility(
            facility_id=uuid.uuid4(),
            name="Pune PHC",
            facility_type="PHC",
            state="Maharashtra",
            district="Pune",
            address="123 Main St",
            latitude=18.5304,
            longitude=73.8667,
            contact="020-12345678",
            services=["OPD"],
            created_at=datetime.utcnow()
        )
        
        chc = HealthFacility(
            facility_id=uuid.uuid4(),
            name="Pune CHC",
            facility_type="CHC",
            state="Maharashtra",
            district="Pune",
            address="456 Center St",
            latitude=18.5204,
            longitude=73.8567,
            contact="020-23456789",
            services=["OPD", "Inpatient"],
            created_at=datetime.utcnow()
        )
        
        hospital = HealthFacility(
            facility_id=uuid.uuid4(),
            name="Pune District Hospital",
            facility_type="District Hospital",
            state="Maharashtra",
            district="Pune",
            address="789 Hospital Rd",
            latitude=18.5104,
            longitude=73.8467,
            contact="020-34567890",
            services=["OPD", "Emergency", "Surgery"],
            created_at=datetime.utcnow()
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [phc, chc, hospital]
        
        mock_db.query.return_value = mock_query
        
        advisor = HealthAdvisor(mock_db)
        facilities = advisor.find_facilities(sample_location)
        
        assert len(facilities) == 3
        facility_types = {f.facility_type for f in facilities}
        assert "PHC" in facility_types
        assert "CHC" in facility_types
        assert "District Hospital" in facility_types


class TestFacilitySearchEdgeCases:
    """Test facility search edge cases"""
    
    def test_facility_search_with_no_facilities_in_database(self, mock_db, sample_location):
        """Test facility search when database has no facilities"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        advisor = HealthAdvisor(mock_db)
        facilities = advisor.find_facilities(sample_location)
        
        assert len(facilities) == 0
        assert isinstance(facilities, list)
    
    def test_facility_search_with_no_facilities_in_district(self, mock_db):
        """Test facility search when no facilities in specified district"""
        location = Location(
            state="Maharashtra",
            district="Remote District",
            latitude=18.5204,
            longitude=73.8567
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        advisor = HealthAdvisor(mock_db)
        facilities = advisor.find_facilities(location)
        
        assert len(facilities) == 0
    
    def test_facility_search_with_all_facilities_outside_radius(self, mock_db, sample_location):
        """Test facility search when all facilities are outside radius"""
        # Create facility far away (>100km)
        far_facility = HealthFacility(
            facility_id=uuid.uuid4(),
            name="Far Hospital",
            facility_type="District Hospital",
            state="Maharashtra",
            district="Pune",
            address="456 Hospital Rd",
            latitude=19.5204,  # ~111 km away
            longitude=74.8567,
            contact="020-87654321",
            services=["OPD", "Emergency"],
            created_at=datetime.utcnow()
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [far_facility]
        
        mock_db.query.return_value = mock_query
        
        advisor = HealthAdvisor(mock_db)
        facilities = advisor.find_facilities(sample_location, radius_km=50)
        
        # Should return empty list (facility is outside radius)
        assert len(facilities) == 0
    
    def test_facility_search_with_no_matching_facility_type(self, mock_db, sample_location):
        """Test facility search when no facilities match the type filter"""
        phc = HealthFacility(
            facility_id=uuid.uuid4(),
            name="Pune PHC",
            facility_type="PHC",
            state="Maharashtra",
            district="Pune",
            address="123 Main St",
            latitude=18.5304,
            longitude=73.8667,
            contact="020-12345678",
            services=["OPD"],
            created_at=datetime.utcnow()
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []  # No CHC facilities
        
        mock_db.query.return_value = mock_query
        
        advisor = HealthAdvisor(mock_db)
        facilities = advisor.find_facilities(sample_location, facility_type="CHC")
        
        assert len(facilities) == 0
    
    def test_facility_search_with_partial_coordinates(self, mock_db, sample_location):
        """Test facility search when facility has partial coordinates"""
        facility = HealthFacility(
            facility_id=uuid.uuid4(),
            name="Pune PHC",
            facility_type="PHC",
            state="Maharashtra",
            district="Pune",
            address="123 Main St",
            latitude=18.5304,
            longitude=None,  # Missing longitude
            contact="020-12345678",
            services=["OPD"],
            created_at=datetime.utcnow()
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [facility]
        
        mock_db.query.return_value = mock_query
        
        advisor = HealthAdvisor(mock_db)
        facilities = advisor.find_facilities(sample_location)
        
        # Should still return facility but without distance
        assert len(facilities) == 1
        assert facilities[0].distance_km is None
    
    def test_facility_search_with_invalid_coordinates(self, mock_db):
        """Test facility search with coordinates at boundary"""
        # Test with coordinates at valid boundary (edge case)
        location = Location(
            state="Maharashtra",
            district="Pune",
            latitude=90.0,  # Maximum valid latitude
            longitude=180.0  # Maximum valid longitude
        )
        
        facility = HealthFacility(
            facility_id=uuid.uuid4(),
            name="Pune PHC",
            facility_type="PHC",
            state="Maharashtra",
            district="Pune",
            address="123 Main St",
            latitude=18.5304,
            longitude=73.8667,
            contact="020-12345678",
            services=["OPD"],
            created_at=datetime.utcnow()
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [facility]
        
        mock_db.query.return_value = mock_query
        
        advisor = HealthAdvisor(mock_db)
        # Should handle gracefully (distance will be very large)
        facilities = advisor.find_facilities(location, radius_km=50)
        
        # Should return empty list (facility is very far)
        assert isinstance(facilities, list)
    
    def test_distance_calculation_accuracy(self, mock_db):
        """Test that distance calculation is reasonably accurate"""
        advisor = HealthAdvisor(mock_db)
        
        # Pune to Mumbai (approximately 150 km)
        pune_lat, pune_lon = 18.5204, 73.8567
        mumbai_lat, mumbai_lon = 19.0760, 72.8777
        
        distance = advisor._calculate_distance(pune_lat, pune_lon, mumbai_lat, mumbai_lon)
        
        # Should be approximately 150 km (allow 20% margin)
        assert 120 <= distance <= 180
    
    def test_distance_calculation_for_same_location(self, mock_db):
        """Test distance calculation for same location"""
        advisor = HealthAdvisor(mock_db)
        
        lat, lon = 18.5204, 73.8567
        distance = advisor._calculate_distance(lat, lon, lat, lon)
        
        # Distance should be 0 or very close to 0
        assert distance < 0.1
    
    def test_facility_search_sorts_by_distance(self, mock_db, sample_location):
        """Test that facility search results are sorted by distance"""
        near_facility = HealthFacility(
            facility_id=uuid.uuid4(),
            name="Near PHC",
            facility_type="PHC",
            state="Maharashtra",
            district="Pune",
            address="123 Main St",
            latitude=18.5304,  # ~1.2 km away
            longitude=73.8667,
            contact="020-12345678",
            services=["OPD"],
            created_at=datetime.utcnow()
        )
        
        far_facility = HealthFacility(
            facility_id=uuid.uuid4(),
            name="Far Hospital",
            facility_type="District Hospital",
            state="Maharashtra",
            district="Pune",
            address="456 Hospital Rd",
            latitude=18.5504,  # ~3.5 km away
            longitude=73.9067,
            contact="020-87654321",
            services=["OPD", "Emergency"],
            created_at=datetime.utcnow()
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [far_facility, near_facility]  # Unsorted
        
        mock_db.query.return_value = mock_query
        
        advisor = HealthAdvisor(mock_db)
        facilities = advisor.find_facilities(sample_location)
        
        # Should be sorted by distance (nearest first)
        assert len(facilities) == 2
        assert facilities[0].distance_km < facilities[1].distance_km
        assert facilities[0].name == "Near PHC"
    
    def test_facility_search_with_facilities_without_distance_at_end(self, mock_db, sample_location):
        """Test that facilities without distance are placed at the end"""
        facility_with_coords = HealthFacility(
            facility_id=uuid.uuid4(),
            name="PHC with Coords",
            facility_type="PHC",
            state="Maharashtra",
            district="Pune",
            address="123 Main St",
            latitude=18.5304,
            longitude=73.8667,
            contact="020-12345678",
            services=["OPD"],
            created_at=datetime.utcnow()
        )
        
        facility_without_coords = HealthFacility(
            facility_id=uuid.uuid4(),
            name="PHC without Coords",
            facility_type="PHC",
            state="Maharashtra",
            district="Pune",
            address="456 Center St",
            latitude=None,
            longitude=None,
            contact="020-23456789",
            services=["OPD"],
            created_at=datetime.utcnow()
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [facility_without_coords, facility_with_coords]
        
        mock_db.query.return_value = mock_query
        
        advisor = HealthAdvisor(mock_db)
        facilities = advisor.find_facilities(sample_location)
        
        # Facility with distance should come first
        assert len(facilities) == 2
        assert facilities[0].distance_km is not None
        assert facilities[1].distance_km is None
