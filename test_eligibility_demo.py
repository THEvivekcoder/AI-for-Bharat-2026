"""
Demonstration script for eligibility checking with various user profiles.
This script tests the eligibility checker with different user scenarios.
"""

from datetime import datetime
from src.models.user import UserProfile, Location
from src.models.scheme import Scheme, EligibilityCriteria
from src.core.eligibility_checker import EligibilityChecker

def create_sample_schemes():
    """Create sample schemes for testing"""
    schemes = []
    
    # Scheme 1: PM-KISAN (Farmer scheme)
    schemes.append(Scheme(
        scheme_id="pm-kisan-001",
        name="PM-KISAN",
        category="agriculture",
        description="Income support for farmers",
        benefits=["₹6000 per year in 3 installments"],
        eligibility_criteria=EligibilityCriteria(
            occupation=["farmer", "agricultural worker"]
        ),
        required_documents=["Land records", "Aadhaar"],
        application_process=["Visit PM-KISAN portal", "Register with Aadhaar"],
        department="Ministry of Agriculture",
        last_updated=datetime.now(),
        source_url="https://pmkisan.gov.in"
    ))
    
    # Scheme 2: Beti Bachao Beti Padhao (Girl child scheme)
    schemes.append(Scheme(
        scheme_id="bbbp-001",
        name="Beti Bachao Beti Padhao",
        category="social_welfare",
        description="Scheme for girl child welfare and education",
        benefits=["Educational support", "Financial assistance"],
        eligibility_criteria=EligibilityCriteria(
            gender="female",
            age_max=21
        ),
        required_documents=["Birth certificate", "School enrollment"],
        application_process=["Apply through school", "Submit documents"],
        department="Ministry of Women and Child Development",
        last_updated=datetime.now(),
        source_url="https://wcd.nic.in"
    ))
    
    # Scheme 3: Pradhan Mantri Awas Yojana (Housing scheme)
    schemes.append(Scheme(
        scheme_id="pmay-001",
        name="Pradhan Mantri Awas Yojana",
        category="housing",
        description="Affordable housing for economically weaker sections",
        benefits=["Subsidy on home loan", "Financial assistance"],
        eligibility_criteria=EligibilityCriteria(
            income_max=300000,
            age_min=21,
            age_max=55
        ),
        required_documents=["Income certificate", "Aadhaar", "Bank details"],
        application_process=["Apply online", "Submit documents"],
        department="Ministry of Housing and Urban Affairs",
        last_updated=datetime.now(),
        source_url="https://pmaymis.gov.in"
    ))
    
    # Scheme 4: State-specific scheme (Uttar Pradesh)
    schemes.append(Scheme(
        scheme_id="up-pension-001",
        name="UP Old Age Pension",
        category="social_welfare",
        description="Pension for senior citizens in Uttar Pradesh",
        benefits=["₹1000 per month"],
        eligibility_criteria=EligibilityCriteria(
            age_min=60,
            location=["Uttar Pradesh"],
            income_max=200000
        ),
        required_documents=["Age proof", "Income certificate", "Aadhaar"],
        application_process=["Apply at district office", "Submit documents"],
        department="Social Welfare Department, UP",
        state="Uttar Pradesh",
        last_updated=datetime.now(),
        source_url="https://sspy-up.gov.in"
    ))
    
    return schemes

def create_test_profiles():
    """Create various user profiles for testing"""
    profiles = []
    
    # Profile 1: Young farmer from Bihar
    profiles.append({
        "name": "Young Farmer from Bihar",
        "profile": UserProfile(
            user_id="user-001",
            phone_number="+919876543210",
            language="hi",
            location=Location(
                state="Bihar",
                district="Patna",
                pincode="800001"
            ),
            age=35,
            gender="male",
            occupation="farmer",
            income_bracket="0-100000"
        )
    })
    
    # Profile 2: Female student from Uttar Pradesh
    profiles.append({
        "name": "Female Student from UP",
        "profile": UserProfile(
            user_id="user-002",
            phone_number="+919876543211",
            language="hi",
            location=Location(
                state="Uttar Pradesh",
                district="Lucknow",
                pincode="226001"
            ),
            age=18,
            gender="female",
            occupation="student",
            income_bracket="0-100000"
        )
    })
    
    # Profile 3: Middle-aged worker seeking housing
    profiles.append({
        "name": "Middle-aged Worker",
        "profile": UserProfile(
            user_id="user-003",
            phone_number="+919876543212",
            language="hi",
            location=Location(
                state="Maharashtra",
                district="Mumbai",
                pincode="400001"
            ),
            age=40,
            gender="male",
            occupation="daily wage worker",
            income_bracket="200000-300000"
        )
    })
    
    # Profile 4: Senior citizen from Uttar Pradesh
    profiles.append({
        "name": "Senior Citizen from UP",
        "profile": UserProfile(
            user_id="user-004",
            phone_number="+919876543213",
            language="hi",
            location=Location(
                state="Uttar Pradesh",
                district="Varanasi",
                pincode="221001"
            ),
            age=65,
            gender="male",
            occupation="retired",
            income_bracket="0-100000"
        )
    })
    
    # Profile 5: Young professional (high income)
    profiles.append({
        "name": "Young Professional (High Income)",
        "profile": UserProfile(
            user_id="user-005",
            phone_number="+919876543214",
            language="en",
            location=Location(
                state="Karnataka",
                district="Bangalore",
                pincode="560001"
            ),
            age=28,
            gender="female",
            occupation="software engineer",
            income_bracket="500000+"
        )
    })
    
    return profiles

def main():
    """Run eligibility checking demonstration"""
    print("=" * 80)
    print("ELIGIBILITY CHECKING DEMONSTRATION")
    print("=" * 80)
    print()
    
    # Create checker and test data
    checker = EligibilityChecker()
    schemes = create_sample_schemes()
    profiles = create_test_profiles()
    
    print(f"Testing with {len(schemes)} schemes and {len(profiles)} user profiles\n")
    
    # Test each profile against all schemes
    for profile_data in profiles:
        profile_name = profile_data["name"]
        profile = profile_data["profile"]
        
        print("-" * 80)
        print(f"USER PROFILE: {profile_name}")
        print(f"  Location: {profile.location.district}, {profile.location.state}")
        print(f"  Age: {profile.age}, Gender: {profile.gender}")
        print(f"  Occupation: {profile.occupation}")
        print(f"  Income: {profile.income_bracket}")
        print()
        
        eligible_count = 0
        
        for scheme in schemes:
            result = checker.check_eligibility(profile, scheme)
            
            if result.is_eligible:
                eligible_count += 1
                print(f"  ✓ ELIGIBLE: {scheme.name}")
                print(f"    Category: {scheme.category}")
                print(f"    Confidence: {result.confidence:.2f}")
                if result.reasoning:
                    print(f"    Reason: {result.reasoning}")
            else:
                print(f"  ✗ NOT ELIGIBLE: {scheme.name}")
                if result.missing_criteria:
                    print(f"    Missing: {', '.join(result.missing_criteria)}")
        
        print(f"\n  Summary: Eligible for {eligible_count}/{len(schemes)} schemes")
        print()
    
    print("=" * 80)
    print("BULK ELIGIBILITY CHECK TEST")
    print("=" * 80)
    print()
    
    # Test bulk eligibility check for one profile
    test_profile = profiles[3]["profile"]  # Senior citizen from UP
    print(f"Testing bulk eligibility for: {profiles[3]['name']}")
    print()
    
    # Check all schemes and collect eligible ones
    eligible_schemes = []
    for scheme in schemes:
        result = checker.check_eligibility(test_profile, scheme)
        if result.is_eligible:
            eligible_schemes.append((scheme, result))
    
    print(f"Found {len(eligible_schemes)} eligible schemes:")
    for scheme, result in eligible_schemes:
        print(f"  • {scheme.name}")
        print(f"    Category: {scheme.category}")
        print(f"    Confidence: {result.confidence:.2f}")
        print()
    
    print("=" * 80)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    main()
