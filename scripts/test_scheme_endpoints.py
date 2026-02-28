"""Test Scheme Service API endpoints"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.services.scheme_repository import SchemeRepository
from app.schemas.scheme import SchemeCreate, EligibilityCriteria
import uuid

client = TestClient(app)


def setup_test_scheme():
    """Create a test scheme in the database"""
    db = SessionLocal()
    try:
        repository = SchemeRepository(db)
        
        scheme_data = SchemeCreate(
            name="Test Agriculture Scheme",
            category="agriculture",
            description="Test scheme for farmers",
            benefits=["Benefit 1", "Benefit 2"],
            eligibility_criteria=EligibilityCriteria(
                age_min=18,
                age_max=60,
                occupation=["farmer"],
                income_max=200000
            ),
            required_documents=["Aadhaar", "Bank details"],
            application_process=["Step 1", "Step 2"],
            application_url="https://example.com",
            department="Agriculture",
            state="Punjab",
            source_url="https://example.com"
        )
        
        scheme = repository.create_scheme(scheme_data)
        return str(scheme.scheme_id)
    finally:
        db.close()


def cleanup_test_scheme(scheme_id: str):
    """Delete test scheme"""
    db = SessionLocal()
    try:
        repository = SchemeRepository(db)
        repository.delete_scheme(scheme_id)
    finally:
        db.close()


def test_endpoints():
    """Test all scheme endpoints"""
    print("=" * 60)
    print("Testing Scheme Service API Endpoints")
    print("=" * 60)
    
    # Setup
    print("\nSetting up test data...")
    scheme_id = setup_test_scheme()
    print(f"✓ Created test scheme: {scheme_id}")
    
    try:
        # Test 1: List schemes
        print("\n1. Testing GET /api/schemes")
        response = client.get("/api/schemes")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        schemes = response.json()
        assert len(schemes) > 0, "Expected at least one scheme"
        print(f"✓ Retrieved {len(schemes)} schemes")
        
        # Test 2: List schemes with filters
        print("\n2. Testing GET /api/schemes with category filter")
        response = client.get("/api/schemes?category=agriculture")
        assert response.status_code == 200
        schemes = response.json()
        assert all(s["category"] == "agriculture" for s in schemes), "All schemes should be agriculture"
        print(f"✓ Retrieved {len(schemes)} agriculture schemes")
        
        # Test 3: Get scheme by ID
        print("\n3. Testing GET /api/schemes/{id}")
        response = client.get(f"/api/schemes/{scheme_id}")
        assert response.status_code == 200
        scheme = response.json()
        assert scheme["scheme_id"] == scheme_id
        print(f"✓ Retrieved scheme: {scheme['name']}")
        
        # Test 4: Get non-existent scheme
        print("\n4. Testing GET /api/schemes/{id} with invalid ID")
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/schemes/{fake_id}")
        assert response.status_code == 404
        print("✓ Correctly returned 404 for non-existent scheme")
        
        # Test 5: Check eligibility - eligible user
        print("\n5. Testing POST /api/schemes/check-eligibility (eligible user)")
        response = client.post(
            "/api/schemes/check-eligibility",
            json={
                "scheme_id": scheme_id,
                "user_profile": {
                    "age": 35,
                    "occupation": "farmer",
                    "income_bracket": "50000-100000",
                    "location": {"state": "Punjab", "district": "Ludhiana"}
                }
            }
        )
        assert response.status_code == 200
        result = response.json()
        assert result["is_eligible"] == True
        print(f"✓ User is eligible: {result['explanation']}")
        
        # Test 6: Check eligibility - ineligible user
        print("\n6. Testing POST /api/schemes/check-eligibility (ineligible user)")
        response = client.post(
            "/api/schemes/check-eligibility",
            json={
                "scheme_id": scheme_id,
                "user_profile": {
                    "age": 35,
                    "occupation": "teacher",
                    "income_bracket": "50000-100000",
                    "location": {"state": "Punjab", "district": "Ludhiana"}
                }
            }
        )
        assert response.status_code == 200
        result = response.json()
        assert result["is_eligible"] == False
        assert len(result["missing_criteria"]) > 0
        print(f"✓ User is not eligible: {result['missing_criteria']}")
        
        # Test 7: Get eligible schemes
        print("\n7. Testing POST /api/schemes/eligible")
        response = client.post(
            "/api/schemes/eligible",
            json={
                "user_profile": {
                    "age": 35,
                    "occupation": "farmer",
                    "income_bracket": "50000-100000",
                    "location": {"state": "Punjab", "district": "Ludhiana"}
                },
                "category": "agriculture"
            }
        )
        assert response.status_code == 200
        eligible_schemes = response.json()
        print(f"✓ Found {len(eligible_schemes)} eligible schemes")
        if eligible_schemes:
            print(f"  First scheme: {eligible_schemes[0]['scheme']['name']}")
        
        print("\n" + "=" * 60)
        print("All API endpoint tests passed! ✓")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Cleanup
        print("\nCleaning up test data...")
        cleanup_test_scheme(scheme_id)
        print("✓ Test data cleaned up")


if __name__ == "__main__":
    test_endpoints()
