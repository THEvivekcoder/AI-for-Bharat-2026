"""Test script for Scheme Service"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Scheme, SchemeTranslation
from app.services.scheme_repository import SchemeRepository
from app.services.eligibility_checker import EligibilityChecker
from app.schemas.scheme import SchemeCreate, EligibilityCriteria, SchemeFilters
from datetime import datetime
import uuid


def test_scheme_service():
    """Test scheme service functionality"""
    db: Session = SessionLocal()
    
    try:
        print("=" * 60)
        print("Testing Scheme Service")
        print("=" * 60)
        
        # Create a test scheme
        print("\n1. Creating test scheme...")
        repository = SchemeRepository(db)
        
        scheme_data = SchemeCreate(
            name="Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
            category="agriculture",
            description="Income support scheme for farmers providing ₹6000 per year in three installments",
            benefits=[
                "₹2000 per installment (3 times a year)",
                "Direct bank transfer",
                "No application fee"
            ],
            eligibility_criteria=EligibilityCriteria(
                occupation=["farmer", "agriculture"],
                income_max=200000,
                custom_criteria={"land_ownership": "yes"}
            ),
            required_documents=[
                "Aadhaar card",
                "Bank account details",
                "Land ownership documents"
            ],
            application_process=[
                "Visit PM-KISAN portal",
                "Register with Aadhaar",
                "Fill application form",
                "Upload documents",
                "Submit for verification"
            ],
            application_url="https://pmkisan.gov.in",
            department="Ministry of Agriculture",
            state=None,  # Central scheme
            source_url="https://pmkisan.gov.in"
        )
        
        scheme = repository.create_scheme(scheme_data)
        print(f"✓ Created scheme: {scheme.name}")
        print(f"  Scheme ID: {scheme.scheme_id}")
        
        # Test search
        print("\n2. Testing scheme search...")
        filters = SchemeFilters(category="agriculture")
        schemes = repository.search_schemes(filters)
        print(f"✓ Found {len(schemes)} agriculture schemes")
        
        # Test get by ID
        print("\n3. Testing get scheme by ID...")
        retrieved_scheme = repository.get_scheme_by_id(str(scheme.scheme_id))
        if retrieved_scheme:
            print(f"✓ Retrieved scheme: {retrieved_scheme.name}")
        else:
            print("✗ Failed to retrieve scheme")
        
        # Test eligibility checker
        print("\n4. Testing eligibility checker...")
        checker = EligibilityChecker(db)
        
        # Test eligible user
        eligible_profile = {
            "age": 45,
            "occupation": "farmer",
            "income_bracket": "50000-100000",
            "location": {"state": "Punjab", "district": "Ludhiana"},
            "land_ownership": "yes"
        }
        
        result = checker.check_eligibility(eligible_profile, scheme)
        print(f"  Eligible user: {result.is_eligible}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Explanation: {result.explanation}")
        
        # Test ineligible user
        ineligible_profile = {
            "age": 45,
            "occupation": "teacher",
            "income_bracket": "50000-100000",
            "location": {"state": "Punjab", "district": "Ludhiana"}
        }
        
        result = checker.check_eligibility(ineligible_profile, scheme)
        print(f"\n  Ineligible user: {result.is_eligible}")
        print(f"  Missing criteria: {result.missing_criteria}")
        print(f"  Explanation: {result.explanation}")
        
        # Test get eligible schemes
        print("\n5. Testing get eligible schemes...")
        eligible_schemes = checker.get_eligible_schemes(eligible_profile)
        print(f"✓ Found {len(eligible_schemes)} eligible schemes for user")
        
        # Cleanup
        print("\n6. Cleaning up test data...")
        repository.delete_scheme(str(scheme.scheme_id))
        print("✓ Test scheme deleted")
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_scheme_service()
