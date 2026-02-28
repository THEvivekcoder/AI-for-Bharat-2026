"""Test script for personalization engine"""
import sys
sys.path.insert(0, '.')

from app.services.personalization import PersonalizationEngine


def test_scheme_scoring():
    """Test scheme relevance scoring"""
    print("Testing Scheme Personalization...")
    
    engine = PersonalizationEngine()
    
    # Sample scheme
    scheme = {
        "scheme_id": "test-123",
        "name": "PM-KISAN Farmer Support",
        "category": "agriculture",
        "description": "Financial support for farmers",
        "state": None,  # Central scheme
        "eligibility_criteria": {
            "occupation": ["farmer", "agricultural worker"],
            "income_max": 200000,
            "age_min": 18,
            "age_max": 70
        }
    }
    
    # Sample user profile - farmer
    user_profile = {
        "occupation": "farmer",
        "state": "Maharashtra",
        "income_bracket": "0-100000",
        "age": 45,
        "education_level": "10th"
    }
    
    score, explanation = engine.score_scheme_relevance(scheme, user_profile)
    
    print(f"  Scheme: {scheme['name']}")
    print(f"  User: {user_profile['occupation']} from {user_profile['state']}")
    print(f"  Score: {score:.2f}")
    print(f"  Explanation: {explanation}")
    print()
    
    assert score > 0.5, "Farmer should have high relevance for farmer scheme"
    assert "farmer" in explanation.lower(), "Explanation should mention occupation"
    print("✓ Scheme scoring test passed\n")


def test_job_scoring():
    """Test job relevance scoring"""
    print("Testing Job Personalization...")
    
    engine = PersonalizationEngine()
    
    # Sample job
    job = {
        "job_id": "job-456",
        "title": "Junior Engineer",
        "department": "Public Works",
        "qualifications": {
            "education_level": "graduate",
            "experience_years": 2,
            "skills": ["engineering", "project management"]
        },
        "location": {
            "state": "Karnataka",
            "district": "Bangalore"
        }
    }
    
    # Sample user profile
    user_profile = {
        "education_level": "graduate",
        "experience_years": 3,
        "skills": ["engineering", "design"],
        "state": "Karnataka",
        "district": "Bangalore"
    }
    
    qualifications = {
        "education_level": "graduate",
        "experience_years": 3,
        "skills": ["engineering", "design"]
    }
    
    score, explanation = engine.score_job_relevance(job, user_profile, qualifications)
    
    print(f"  Job: {job['title']}")
    print(f"  User: {user_profile['education_level']}, {user_profile['experience_years']} years exp")
    print(f"  Score: {score:.2f}")
    print(f"  Explanation: {explanation}")
    print()
    
    assert score > 0.5, "Qualified user should have high relevance"
    assert "education" in explanation.lower() or "experience" in explanation.lower(), \
        "Explanation should mention qualifications"
    print("✓ Job scoring test passed\n")


def test_skill_program_scoring():
    """Test skill program relevance scoring"""
    print("Testing Skill Program Personalization...")
    
    engine = PersonalizationEngine()
    
    # Sample program
    program = {
        "program_id": "prog-789",
        "name": "Digital Marketing Course",
        "category": "digital",
        "description": "Learn digital marketing and social media",
        "state": "Tamil Nadu",
        "mode": "online",
        "eligibility_criteria": {
            "education": ["12th", "graduate"]
        }
    }
    
    # Sample user profile
    user_profile = {
        "education_level": "12th",
        "state": "Tamil Nadu",
        "interests": ["marketing", "digital skills"],
        "career_goals": ["digital marketing career"]
    }
    
    preferences = {
        "interests": ["marketing", "digital skills"],
        "career_goals": ["digital marketing career"],
        "current_skills": []
    }
    
    score, explanation = engine.score_skill_program_relevance(program, user_profile, preferences)
    
    print(f"  Program: {program['name']}")
    print(f"  User interests: {', '.join(user_profile['interests'])}")
    print(f"  Score: {score:.2f}")
    print(f"  Explanation: {explanation}")
    print()
    
    assert score > 0.5, "User with matching interests should have high relevance"
    assert "interest" in explanation.lower() or "goal" in explanation.lower(), \
        "Explanation should mention interests or goals"
    print("✓ Skill program scoring test passed\n")


def test_ranking():
    """Test ranking multiple items"""
    print("Testing Ranking...")
    
    engine = PersonalizationEngine()
    
    schemes = [
        {
            "name": "Farmer Scheme",
            "category": "agriculture",
            "state": None,
            "eligibility_criteria": {"occupation": ["farmer"]}
        },
        {
            "name": "Education Scheme",
            "category": "education",
            "state": "Maharashtra",
            "eligibility_criteria": {"education": ["graduate"]}
        },
        {
            "name": "Health Scheme",
            "category": "health",
            "state": "Maharashtra",
            "eligibility_criteria": {"income_max": 100000}
        }
    ]
    
    user_profile = {
        "occupation": "farmer",
        "state": "Maharashtra",
        "income_bracket": "0-50000",
        "education_level": "10th"
    }
    
    ranked = engine.rank_recommendations(schemes, user_profile, "scheme")
    
    print(f"  User: {user_profile['occupation']} from {user_profile['state']}")
    print(f"  Ranked schemes:")
    for i, (item, score, explanation) in enumerate(ranked, 1):
        print(f"    {i}. {item['name']} (score: {score:.2f})")
    print()
    
    # Farmer scheme should rank highest for a farmer
    assert ranked[0][0]["name"] == "Farmer Scheme", "Farmer scheme should rank first for farmer"
    assert ranked[0][1] > ranked[1][1], "Scores should be in descending order"
    print("✓ Ranking test passed\n")


def test_detailed_explanation():
    """Test detailed explanation generation"""
    print("Testing Detailed Explanations...")
    
    engine = PersonalizationEngine()
    
    scheme = {"name": "Test Scheme", "category": "agriculture"}
    user_profile = {
        "occupation": "farmer",
        "state": "Punjab"
    }
    
    detailed = engine.generate_detailed_explanation(
        scheme,
        user_profile,
        "scheme",
        0.85,
        "Recommended because it designed for farmers"
    )
    
    print(f"  Detailed explanation: {detailed}")
    print()
    
    assert "Highly recommended" in detailed, "High score should say 'Highly recommended'"
    assert "farmer" in detailed.lower(), "Should mention occupation"
    print("✓ Detailed explanation test passed\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Personalization Engine Tests")
    print("=" * 60)
    print()
    
    try:
        test_scheme_scoring()
        test_job_scoring()
        test_skill_program_scoring()
        test_ranking()
        test_detailed_explanation()
        
        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
    
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
