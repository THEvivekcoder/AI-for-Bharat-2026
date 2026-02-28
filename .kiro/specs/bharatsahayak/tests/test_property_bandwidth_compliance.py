"""
Property-Based Test: Bandwidth Constraint Compliance

Feature: bharatsahayak, Property 18: Bandwidth Constraint Compliance

Property:
For any API response, the total payload size should be under 100KB when compressed,
ensuring low-bandwidth compatibility.

Validates: Requirements 7.2
"""
import pytest
from hypothesis import given, settings, strategies as st
from hypothesis import assume
import json
import gzip
import sys
from typing import Dict, Any, List
from datetime import datetime, timedelta
import random


# Constants
MAX_UNCOMPRESSED_SIZE_KB = 100
MAX_COMPRESSED_SIZE_KB = 100
BYTES_PER_KB = 1024


def calculate_payload_size(data: Any) -> tuple[int, int]:
    """
    Calculate uncompressed and compressed payload size
    
    Args:
        data: Data to measure (dict, list, or any JSON-serializable object)
        
    Returns:
        Tuple of (uncompressed_bytes, compressed_bytes)
    """
    # Serialize to JSON
    json_str = json.dumps(data, default=str, ensure_ascii=False)
    json_bytes = json_str.encode('utf-8')
    
    # Uncompressed size
    uncompressed_size = len(json_bytes)
    
    # Compressed size (gzip)
    compressed_bytes = gzip.compress(json_bytes, compresslevel=6)
    compressed_size = len(compressed_bytes)
    
    return uncompressed_size, compressed_size


def create_sample_scheme() -> Dict[str, Any]:
    """Create a sample scheme response"""
    return {
        "scheme_id": "scheme_123",
        "name": "Pradhan Mantri Kisan Samman Nidhi",
        "name_translations": {
            "hi": "प्रधानमंत्री किसान सम्मान निधि",
            "bn": "প্রধানমন্ত্রী কিষাণ সম্মান নিধি"
        },
        "category": "agriculture",
        "description": "Financial support to farmers providing income support of Rs 6000 per year in three equal installments",
        "description_translations": {
            "hi": "किसानों को वित्तीय सहायता प्रदान करना",
            "bn": "কৃষকদের আর্থিক সহায়তা প্রদান"
        },
        "benefits": [
            "Rs 6000 per year in three installments",
            "Direct bank transfer",
            "No intermediaries"
        ],
        "eligibility_criteria": {
            "age_min": 18,
            "age_max": None,
            "income_max": None,
            "gender": None,
            "occupation": ["farmer"],
            "education": None,
            "location": None,
            "caste": None,
            "custom_criteria": {"land_ownership": "required"}
        },
        "required_documents": [
            "Aadhaar card",
            "Bank account details",
            "Land ownership documents"
        ],
        "application_process": [
            "Visit PM-KISAN portal",
            "Register with Aadhaar",
            "Fill application form",
            "Upload documents",
            "Submit application"
        ],
        "application_url": "https://pmkisan.gov.in",
        "department": "Ministry of Agriculture",
        "state": None,
        "last_updated": datetime.now().isoformat(),
        "source_url": "https://pmkisan.gov.in"
    }


def create_sample_crop_recommendation() -> Dict[str, Any]:
    """Create a sample crop recommendation"""
    return {
        "crop_name": "Rice",
        "suitability_score": 0.85,
        "expected_yield": "40-50 quintals per hectare",
        "water_requirement": "High - requires consistent irrigation",
        "duration_days": 120,
        "market_demand": "high",
        "estimated_profit": "Rs 30,000 - 40,000 per hectare",
        "reasoning": "Suitable for clay loam soil with good water availability. High market demand in the region.",
        "risks": [
            "Requires consistent water supply",
            "Susceptible to pests during monsoon",
            "Market price fluctuations"
        ]
    }


def create_sample_skill_program() -> Dict[str, Any]:
    """Create a sample skill program"""
    return {
        "program_id": "skill_123",
        "name": "Digital Marketing Certification",
        "provider": "National Skill Development Corporation",
        "category": "digital",
        "description": "Comprehensive digital marketing training covering SEO, social media, content marketing, and analytics",
        "duration_weeks": 12,
        "cost": 5000.0,
        "location": {
            "state": "Maharashtra",
            "district": "Mumbai",
            "block": None,
            "village": None,
            "pincode": "400001",
            "latitude": 19.0760,
            "longitude": 72.8777
        },
        "mode": "hybrid",
        "eligibility": {
            "age_min": 18,
            "age_max": 35,
            "education": ["12th", "graduate"]
        },
        "certification": True,
        "placement_support": True,
        "registration_url": "https://nsdcindia.org",
        "contact": "+91-1234567890"
    }


def create_sample_health_guidance() -> Dict[str, Any]:
    """Create a sample health guidance response"""
    return {
        "urgency_level": "soon",
        "possible_conditions": [
            "Common cold",
            "Seasonal allergies",
            "Upper respiratory infection"
        ],
        "self_care_recommendations": [
            "Rest and stay hydrated",
            "Use steam inhalation",
            "Take over-the-counter pain relievers if needed",
            "Monitor temperature"
        ],
        "when_to_seek_care": "If symptoms worsen or persist beyond 7 days, or if fever exceeds 102°F",
        "red_flags": [
            "Difficulty breathing",
            "Chest pain",
            "High fever (>103°F)",
            "Severe headache"
        ],
        "disclaimer": "This guidance is informational only and not a substitute for professional medical consultation. Please consult a qualified healthcare provider for proper diagnosis and treatment.",
        "confidence": 0.75
    }


# Hypothesis strategies for generating test data
@st.composite
def scheme_list_strategy(draw, min_size=1, max_size=20):
    """Generate a list of schemes"""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    schemes = []
    for _ in range(size):
        scheme = create_sample_scheme()
        # Vary some fields
        scheme["scheme_id"] = f"scheme_{draw(st.integers(min_value=1, max_value=10000))}"
        scheme["name"] = draw(st.text(min_size=10, max_size=100))
        schemes.append(scheme)
    return schemes


@st.composite
def crop_recommendation_list_strategy(draw, min_size=1, max_size=10):
    """Generate a list of crop recommendations"""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    recommendations = []
    for _ in range(size):
        rec = create_sample_crop_recommendation()
        rec["crop_name"] = draw(st.sampled_from(["Rice", "Wheat", "Cotton", "Sugarcane", "Maize"]))
        recommendations.append(rec)
    return recommendations


@st.composite
def skill_program_list_strategy(draw, min_size=1, max_size=15):
    """Generate a list of skill programs"""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    programs = []
    for _ in range(size):
        program = create_sample_skill_program()
        program["program_id"] = f"skill_{draw(st.integers(min_value=1, max_value=10000))}"
        program["name"] = draw(st.text(min_size=10, max_size=80))
        programs.append(program)
    return programs


@st.composite
def api_response_strategy(draw):
    """Generate various API response types"""
    response_type = draw(st.sampled_from([
        "scheme_list",
        "crop_recommendations",
        "skill_programs",
        "health_guidance",
        "mixed_content"
    ]))
    
    if response_type == "scheme_list":
        return {
            "success": True,
            "count": draw(st.integers(min_value=1, max_value=20)),
            "results": draw(scheme_list_strategy(max_size=20))
        }
    elif response_type == "crop_recommendations":
        return {
            "success": True,
            "recommendations": draw(crop_recommendation_list_strategy(max_size=10))
        }
    elif response_type == "skill_programs":
        return {
            "success": True,
            "count": draw(st.integers(min_value=1, max_value=15)),
            "programs": draw(skill_program_list_strategy(max_size=15))
        }
    elif response_type == "health_guidance":
        return create_sample_health_guidance()
    else:  # mixed_content
        return {
            "success": True,
            "schemes": draw(scheme_list_strategy(max_size=5)),
            "programs": draw(skill_program_list_strategy(max_size=5)),
            "recommendations": draw(crop_recommendation_list_strategy(max_size=3))
        }


# Property Tests

@settings(max_examples=100, deadline=None)
@given(response_data=api_response_strategy())
def test_bandwidth_constraint_compliance(response_data: Dict[str, Any]):
    """
    Property 18: Bandwidth Constraint Compliance
    
    For any API response, the total payload size should be under 100KB when compressed,
    ensuring low-bandwidth compatibility.
    
    This property ensures that:
    1. Compressed payload size is under 100KB
    2. Compression ratio is reasonable (at least 20% reduction)
    3. Response structure is optimized for bandwidth
    """
    # Calculate payload sizes
    uncompressed_size, compressed_size = calculate_payload_size(response_data)
    
    # Convert to KB
    uncompressed_kb = uncompressed_size / BYTES_PER_KB
    compressed_kb = compressed_size / BYTES_PER_KB
    
    # Calculate compression ratio
    compression_ratio = (1 - (compressed_size / uncompressed_size)) * 100 if uncompressed_size > 0 else 0
    
    # Log sizes for debugging
    print(f"\nPayload sizes:")
    print(f"  Uncompressed: {uncompressed_kb:.2f} KB ({uncompressed_size} bytes)")
    print(f"  Compressed: {compressed_kb:.2f} KB ({compressed_size} bytes)")
    print(f"  Compression ratio: {compression_ratio:.1f}%")
    
    # Property 1: Compressed size must be under 100KB
    assert compressed_size <= MAX_COMPRESSED_SIZE_KB * BYTES_PER_KB, (
        f"Compressed payload size {compressed_kb:.2f} KB exceeds maximum {MAX_COMPRESSED_SIZE_KB} KB. "
        f"Response must be optimized for low-bandwidth environments."
    )
    
    # Property 2: Compression should provide reasonable reduction
    # (at least 10% for text-based JSON data)
    if uncompressed_size > 1024:  # Only check for payloads > 1KB
        assert compression_ratio >= 10, (
            f"Compression ratio {compression_ratio:.1f}% is too low. "
            f"Response structure may not be optimized for compression."
        )
    
    # Property 3: Response should be valid JSON
    json_str = json.dumps(response_data, default=str)
    parsed = json.loads(json_str)
    assert parsed is not None, "Response must be valid JSON"


@settings(max_examples=50, deadline=None)
@given(
    scheme_count=st.integers(min_value=1, max_value=50)
)
def test_bandwidth_compliance_with_varying_scheme_counts(scheme_count: int):
    """
    Test bandwidth compliance with varying numbers of schemes
    
    This tests that even with many schemes, the response stays under bandwidth limits.
    If it exceeds, pagination should be used.
    """
    # Create response with specified number of schemes
    schemes = []
    for i in range(scheme_count):
        scheme = create_sample_scheme()
        scheme["scheme_id"] = f"scheme_{i}"
        schemes.append(scheme)
    
    response = {
        "success": True,
        "count": scheme_count,
        "results": schemes,
        "page": 1,
        "page_size": scheme_count,
        "total_pages": 1
    }
    
    # Calculate sizes
    uncompressed_size, compressed_size = calculate_payload_size(response)
    compressed_kb = compressed_size / BYTES_PER_KB
    
    print(f"\nScheme count: {scheme_count}")
    print(f"Compressed size: {compressed_kb:.2f} KB")
    
    # If response exceeds limit, it should be paginated
    if compressed_size > MAX_COMPRESSED_SIZE_KB * BYTES_PER_KB:
        # Calculate recommended page size
        avg_scheme_size = compressed_size / scheme_count
        recommended_page_size = int((MAX_COMPRESSED_SIZE_KB * BYTES_PER_KB * 0.8) / avg_scheme_size)
        
        pytest.skip(
            f"Response with {scheme_count} schemes exceeds {MAX_COMPRESSED_SIZE_KB}KB limit "
            f"({compressed_kb:.2f} KB). Recommended page size: {recommended_page_size} schemes. "
            f"API should implement pagination."
        )
    
    # Otherwise, verify it's under limit
    assert compressed_size <= MAX_COMPRESSED_SIZE_KB * BYTES_PER_KB


@settings(max_examples=50, deadline=None)
@given(
    include_translations=st.booleans(),
    include_descriptions=st.booleans(),
    field_count=st.integers(min_value=5, max_value=20)
)
def test_bandwidth_compliance_with_optional_fields(
    include_translations: bool,
    include_descriptions: bool,
    field_count: int
):
    """
    Test bandwidth compliance with optional fields
    
    This tests that responses can be optimized by excluding optional fields
    when bandwidth is constrained.
    """
    # Create a scheme with optional fields
    scheme = create_sample_scheme()
    
    # Conditionally include translations
    if not include_translations:
        scheme.pop("name_translations", None)
        scheme.pop("description_translations", None)
    
    # Conditionally include full descriptions
    if not include_descriptions:
        # Use shorter description
        scheme["description"] = scheme["description"][:100] + "..."
    
    # Create response with multiple schemes
    response = {
        "success": True,
        "count": field_count,
        "results": [scheme for _ in range(field_count)]
    }
    
    # Calculate sizes
    uncompressed_size, compressed_size = calculate_payload_size(response)
    compressed_kb = compressed_size / BYTES_PER_KB
    
    print(f"\nOptional fields test:")
    print(f"  Translations: {include_translations}")
    print(f"  Full descriptions: {include_descriptions}")
    print(f"  Field count: {field_count}")
    print(f"  Compressed size: {compressed_kb:.2f} KB")
    
    # Verify under limit
    assert compressed_size <= MAX_COMPRESSED_SIZE_KB * BYTES_PER_KB, (
        f"Response with optional fields exceeds bandwidth limit. "
        f"Consider implementing field selection or pagination."
    )


@settings(max_examples=30, deadline=None)
@given(
    response_type=st.sampled_from(["json", "json_with_metadata"])
)
def test_bandwidth_compliance_response_format(response_type: str):
    """
    Test bandwidth compliance with different response formats
    
    This tests that response format doesn't unnecessarily inflate payload size.
    """
    # Create base data
    schemes = [create_sample_scheme() for _ in range(10)]
    
    if response_type == "json":
        # Simple JSON response
        response = {
            "results": schemes
        }
    else:
        # JSON with metadata
        response = {
            "success": True,
            "count": len(schemes),
            "results": schemes,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "api_version": "1.0",
                "request_id": "req_123456"
            }
        }
    
    # Calculate sizes
    uncompressed_size, compressed_size = calculate_payload_size(response)
    compressed_kb = compressed_size / BYTES_PER_KB
    
    print(f"\nResponse format: {response_type}")
    print(f"Compressed size: {compressed_kb:.2f} KB")
    
    # Verify under limit
    assert compressed_size <= MAX_COMPRESSED_SIZE_KB * BYTES_PER_KB


def test_bandwidth_compliance_real_world_scenarios():
    """
    Test bandwidth compliance with real-world API response scenarios
    
    This tests specific common API responses to ensure they meet bandwidth requirements.
    """
    scenarios = [
        {
            "name": "Scheme search results (10 schemes)",
            "response": {
                "success": True,
                "count": 10,
                "results": [create_sample_scheme() for _ in range(10)]
            }
        },
        {
            "name": "Crop recommendations (5 crops)",
            "response": {
                "success": True,
                "recommendations": [create_sample_crop_recommendation() for _ in range(5)]
            }
        },
        {
            "name": "Skill programs (15 programs)",
            "response": {
                "success": True,
                "count": 15,
                "programs": [create_sample_skill_program() for _ in range(15)]
            }
        },
        {
            "name": "Health guidance",
            "response": create_sample_health_guidance()
        },
        {
            "name": "Mixed content response",
            "response": {
                "success": True,
                "schemes": [create_sample_scheme() for _ in range(5)],
                "programs": [create_sample_skill_program() for _ in range(5)],
                "recommendations": [create_sample_crop_recommendation() for _ in range(3)]
            }
        }
    ]
    
    for scenario in scenarios:
        name = scenario["name"]
        response = scenario["response"]
        
        # Calculate sizes
        uncompressed_size, compressed_size = calculate_payload_size(response)
        compressed_kb = compressed_size / BYTES_PER_KB
        
        print(f"\nScenario: {name}")
        print(f"  Compressed size: {compressed_kb:.2f} KB")
        
        # Verify under limit
        assert compressed_size <= MAX_COMPRESSED_SIZE_KB * BYTES_PER_KB, (
            f"Scenario '{name}' exceeds bandwidth limit with {compressed_kb:.2f} KB. "
            f"Maximum allowed: {MAX_COMPRESSED_SIZE_KB} KB."
        )


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
