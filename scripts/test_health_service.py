"""Test script for Health Advisory Service"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.health_advisor import HealthAdvisor
from app.schemas.health import BasicHealthInfo, Location
from app.models.health import HealthFacility
import uuid


def test_symptom_analysis():
    """Test symptom analysis functionality"""
    print("\n=== Testing Symptom Analysis ===")
    
    db = SessionLocal()
    health_advisor = HealthAdvisor(db)
    
    # Test 1: Emergency symptoms
    print("\n1. Testing emergency symptoms:")
    symptoms = ["chest pain", "difficulty breathing"]
    guidance = health_advisor.analyze_symptoms(symptoms)
    print(f"   Symptoms: {symptoms}")
    print(f"   Urgency: {guidance.urgency_level}")
    print(f"   When to seek care: {guidance.when_to_seek_care}")
    assert guidance.urgency_level == "emergency", "Emergency symptoms should trigger emergency urgency"
    print("   ✓ Emergency detection working")
    
    # Test 2: Urgent symptoms
    print("\n2. Testing urgent symptoms:")
    symptoms = ["high fever", "severe headache"]
    guidance = health_advisor.analyze_symptoms(symptoms)
    print(f"   Symptoms: {symptoms}")
    print(f"   Urgency: {guidance.urgency_level}")
    print(f"   Possible conditions: {guidance.possible_conditions[:3]}")
    assert guidance.urgency_level in ["urgent", "soon"], "Urgent symptoms should trigger urgent/soon urgency"
    print("   ✓ Urgent symptom detection working")
    
    # Test 3: Routine symptoms
    print("\n3. Testing routine symptoms:")
    symptoms = ["mild headache", "fatigue"]
    user_info = BasicHealthInfo(age=30, gender="male")
    guidance = health_advisor.analyze_symptoms(symptoms, user_info)
    print(f"   Symptoms: {symptoms}")
    print(f"   Urgency: {guidance.urgency_level}")
    print(f"   Self-care recommendations: {len(guidance.self_care_recommendations)} items")
    print(f"   Disclaimer present: {len(guidance.disclaimer) > 0}")
    assert guidance.urgency_level in ["routine", "soon"], "Mild symptoms should trigger routine/soon urgency"
    assert len(guidance.disclaimer) > 0, "Disclaimer should always be present"
    print("   ✓ Routine symptom analysis working")
    
    # Test 4: Multiple symptoms
    print("\n4. Testing multiple symptoms:")
    symptoms = ["fever", "cough", "body ache", "sore throat"]
    guidance = health_advisor.analyze_symptoms(symptoms)
    print(f"   Symptoms: {symptoms}")
    print(f"   Urgency: {guidance.urgency_level}")
    print(f"   Possible conditions: {guidance.possible_conditions[:3]}")
    print(f"   Confidence: {guidance.confidence}")
    assert len(guidance.possible_conditions) > 0, "Should identify possible conditions"
    print("   ✓ Multiple symptom analysis working")
    
    db.close()
    print("\n✓ All symptom analysis tests passed!")


def test_facility_search():
    """Test health facility search functionality"""
    print("\n=== Testing Health Facility Search ===")
    
    db = SessionLocal()
    
    # Create test facilities
    print("\n1. Creating test health facilities...")
    test_facilities = [
        HealthFacility(
            facility_id=uuid.uuid4(),
            name="Test Primary Health Center",
            facility_type="PHC",
            state="Maharashtra",
            district="Pune",
            address="Test Address 1",
            latitude=18.5204,
            longitude=73.8567,
            contact="1234567890",
            services=["OPD", "Emergency", "Maternity"]
        ),
        HealthFacility(
            facility_id=uuid.uuid4(),
            name="Test Community Health Center",
            facility_type="CHC",
            state="Maharashtra",
            district="Pune",
            address="Test Address 2",
            latitude=18.5304,
            longitude=73.8667,
            contact="0987654321",
            services=["OPD", "Emergency", "Surgery", "X-Ray"]
        ),
        HealthFacility(
            facility_id=uuid.uuid4(),
            name="Test District Hospital",
            facility_type="District Hospital",
            state="Maharashtra",
            district="Pune",
            address="Test Address 3",
            latitude=18.5404,
            longitude=73.8767,
            contact="1122334455",
            services=["OPD", "Emergency", "ICU", "Surgery", "Maternity"]
        )
    ]
    
    for facility in test_facilities:
        db.add(facility)
    db.commit()
    print(f"   Created {len(test_facilities)} test facilities")
    
    # Test facility search
    health_advisor = HealthAdvisor(db)
    
    print("\n2. Testing facility search by location:")
    location = Location(
        state="Maharashtra",
        district="Pune",
        latitude=18.5204,
        longitude=73.8567
    )
    facilities = health_advisor.find_facilities(location, radius_km=50)
    print(f"   Found {len(facilities)} facilities in Pune, Maharashtra")
    assert len(facilities) >= 3, "Should find at least 3 test facilities"
    print("   ✓ Location-based search working")
    
    print("\n3. Testing facility search with distance calculation:")
    for facility in facilities[:3]:
        print(f"   - {facility.name} ({facility.facility_type})")
        if facility.distance_km:
            print(f"     Distance: {facility.distance_km} km")
    assert facilities[0].distance_km is not None, "Distance should be calculated"
    print("   ✓ Distance calculation working")
    
    print("\n4. Testing facility type filter:")
    phc_facilities = health_advisor.find_facilities(location, facility_type="PHC", radius_km=50)
    print(f"   Found {len(phc_facilities)} PHC facilities")
    assert all(f.facility_type == "PHC" for f in phc_facilities), "Should only return PHC facilities"
    print("   ✓ Facility type filtering working")
    
    # Cleanup
    print("\n5. Cleaning up test data...")
    for facility in test_facilities:
        db.delete(facility)
    db.commit()
    db.close()
    print("   Test facilities removed")
    
    print("\n✓ All facility search tests passed!")


def test_distance_calculation():
    """Test distance calculation accuracy"""
    print("\n=== Testing Distance Calculation ===")
    
    db = SessionLocal()
    health_advisor = HealthAdvisor(db)
    
    # Test known distances
    print("\n1. Testing Haversine formula:")
    
    # Mumbai to Pune (approximately 120-150 km)
    mumbai_lat, mumbai_lon = 19.0760, 72.8777
    pune_lat, pune_lon = 18.5204, 73.8567
    distance = health_advisor._calculate_distance(mumbai_lat, mumbai_lon, pune_lat, pune_lon)
    print(f"   Mumbai to Pune: {distance:.2f} km")
    assert 110 <= distance <= 160, "Distance should be approximately 120-150 km"
    print("   ✓ Long distance calculation accurate")
    
    # Short distance (approximately 1 km)
    lat1, lon1 = 18.5204, 73.8567
    lat2, lon2 = 18.5304, 73.8667
    distance = health_advisor._calculate_distance(lat1, lon1, lat2, lon2)
    print(f"   Short distance: {distance:.2f} km")
    assert distance < 5, "Short distance should be less than 5 km"
    print("   ✓ Short distance calculation accurate")
    
    db.close()
    print("\n✓ All distance calculation tests passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("Health Advisory Service Test Suite")
    print("=" * 60)
    
    try:
        test_symptom_analysis()
        test_distance_calculation()
        test_facility_search()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
