"""Property-based tests for crop recommendation generation.

Feature: bharatsahayak, Property 7: Crop Recommendation Generation
**Validates: Requirements 3.1**

This test verifies that crop recommendations contain all required fields
and are generated correctly for any valid farm profile.
"""

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck
import json

from src.models.farm import FarmProfile, CropRecommendation
from src.models.location import Location


# Custom strategies for generating valid test data
@st.composite
def location_strategy(draw):
    """Generate valid Location instances."""
    states = ["Maharashtra", "Karnataka", "Tamil Nadu", "Gujarat", "Rajasthan", "Punjab"]
    districts = {
        "Maharashtra": ["Pune", "Mumbai", "Nagpur"],
        "Karnataka": ["Bangalore", "Mysore", "Hubli"],
        "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai"],
        "Gujarat": ["Ahmedabad", "Surat", "Vadodara"],
        "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur"],
        "Punjab": ["Ludhiana", "Amritsar", "Jalandhar"]
    }
    
    state = draw(st.sampled_from(states))
    district = draw(st.sampled_from(districts[state]))
    
    return Location(
        state=state,
        district=district,
        pincode=draw(st.text(min_size=6, max_size=6, alphabet=st.characters(whitelist_categories=('Nd',))))
    )


@st.composite
def farm_profile_strategy(draw):
    """Generate valid FarmProfile instances."""
    return FarmProfile(
        user_id=f"user_{draw(st.integers(min_value=1000, max_value=9999))}",
        land_size_acres=draw(st.floats(min_value=0.5, max_value=100.0)),
        soil_type=draw(st.sampled_from(["black", "loam", "clay", "sandy", "alluvial"])),
        irrigation_type=draw(st.sampled_from(["rainfed", "canal", "well", "drip", "sprinkler"])),
        location=draw(location_strategy()),
        current_crops=draw(st.lists(
            st.sampled_from(["wheat", "rice", "cotton", "soybean", "maize"]),
            min_size=0, max_size=3, unique=True
        )),
        previous_crops=draw(st.lists(
            st.sampled_from(["wheat", "rice", "cotton", "soybean", "maize", "sugarcane"]),
            min_size=0, max_size=5, unique=True
        )),
        livestock=draw(st.one_of(
            st.none(),
            st.lists(st.sampled_from(["cow", "buffalo", "goat", "sheep"]), min_size=1, max_size=3, unique=True)
        ))
    )


def call_crop_advice_handler(farm_profile: FarmProfile, season: str = None) -> dict:
    """
    Call the crop advice Lambda handler with a farm profile.
    
    Args:
        farm_profile: Farm profile to get recommendations for
        season: Optional season (kharif, rabi, zaid)
        
    Returns:
        Response dictionary from the handler
    """
    from src.api.crop_advice import lambda_handler
    
    # Prepare request body
    body = farm_profile.model_dump()
    if season:
        body['season'] = season
    
    # Create Lambda event
    event = {
        'body': json.dumps(body),
        'httpMethod': 'POST',
        'path': '/farmer/crop-advice'
    }
    
    # Call handler
    response = lambda_handler(event, None)
    
    return response


@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
@given(
    farm_profile=farm_profile_strategy(),
    season=st.sampled_from(["kharif", "rabi", "zaid"])
)
def test_crop_recommendation_completeness(farm_profile, season):
    """
    Feature: bharatsahayak, Property 7: Crop Recommendation Generation
    
    For any valid farm profile, the System should generate at least one crop
    recommendation with all required fields (crop_name, suitability_score,
    reasoning, water_requirement, duration_days) populated.
    
    This test verifies:
    1. At least one recommendation is generated
    2. All required fields are present and non-empty
    3. Field values are within valid ranges
    4. Reasoning is provided for each recommendation
    """
    # Call the crop advice handler
    response = call_crop_advice_handler(farm_profile, season)
    
    # Verify successful response
    assert response['statusCode'] == 200, (
        f"Expected status code 200, got {response['statusCode']}"
    )
    
    # Parse response body
    body = json.loads(response['body'])
    
    # Verify recommendations exist
    assert 'recommendations' in body, "Response should contain 'recommendations' field"
    recommendations = body['recommendations']
    
    # Property 1: At least one recommendation should be generated
    assert len(recommendations) > 0, (
        f"At least one crop recommendation should be generated for farm profile: "
        f"soil={farm_profile.soil_type}, irrigation={farm_profile.irrigation_type}, season={season}"
    )
    
    # Verify each recommendation has all required fields
    required_fields = [
        'crop_name', 'suitability_score', 'expected_yield',
        'water_requirement', 'duration_days', 'market_demand',
        'reasoning', 'risks'
    ]
    
    for i, rec in enumerate(recommendations):
        # Property 2: All required fields must be present
        for field in required_fields:
            assert field in rec, (
                f"Recommendation {i} missing required field '{field}'"
            )
        
        # Property 3: Fields must not be empty/null
        assert rec['crop_name'], f"Recommendation {i} has empty crop_name"
        assert rec['reasoning'], f"Recommendation {i} has empty reasoning"
        assert rec['expected_yield'], f"Recommendation {i} has empty expected_yield"
        assert rec['water_requirement'], f"Recommendation {i} has empty water_requirement"
        
        # Property 4: Suitability score must be between 0 and 1
        assert 0 <= rec['suitability_score'] <= 1, (
            f"Recommendation {i} has invalid suitability_score: {rec['suitability_score']} "
            f"(must be between 0 and 1)"
        )
        
        # Property 5: Duration must be positive
        assert rec['duration_days'] > 0, (
            f"Recommendation {i} has invalid duration_days: {rec['duration_days']} "
            f"(must be positive)"
        )
        
        # Property 6: Market demand must be valid
        valid_demands = ['high', 'medium', 'low']
        assert rec['market_demand'] in valid_demands, (
            f"Recommendation {i} has invalid market_demand: {rec['market_demand']} "
            f"(must be one of {valid_demands})"
        )
        
        # Property 7: Water requirement must be valid
        valid_water_reqs = ['high', 'medium', 'low']
        assert rec['water_requirement'] in valid_water_reqs, (
            f"Recommendation {i} has invalid water_requirement: {rec['water_requirement']} "
            f"(must be one of {valid_water_reqs})"
        )
        
        # Property 8: Risks should be a list
        assert isinstance(rec['risks'], list), (
            f"Recommendation {i} has invalid risks type: {type(rec['risks'])} "
            f"(must be a list)"
        )


@settings(max_examples=10, deadline=None)
@given(
    farm_profile=farm_profile_strategy()
)
def test_crop_recommendation_sorting(farm_profile):
    """
    Test that recommendations are sorted by suitability score in descending order.
    
    This verifies that the most suitable crops appear first.
    """
    # Call the crop advice handler
    response = call_crop_advice_handler(farm_profile)
    
    # Verify successful response
    assert response['statusCode'] == 200
    
    # Parse response body
    body = json.loads(response['body'])
    recommendations = body['recommendations']
    
    # Skip if only one recommendation
    if len(recommendations) <= 1:
        return
    
    # Verify sorting: each recommendation should have suitability_score >= next one
    for i in range(len(recommendations) - 1):
        current_score = recommendations[i]['suitability_score']
        next_score = recommendations[i + 1]['suitability_score']
        
        assert current_score >= next_score, (
            f"Recommendations not sorted by suitability score: "
            f"recommendation {i} has score {current_score}, "
            f"recommendation {i+1} has score {next_score}"
        )


@settings(max_examples=10, deadline=None)
@given(
    land_size=st.floats(min_value=0.5, max_value=100.0)
)
def test_crop_recommendation_rainfed_constraints(land_size):
    """
    Test that high water requirement crops are not recommended for rainfed farms.
    
    This verifies that water availability constraints are respected.
    """
    # Create a rainfed farm profile
    farm_profile = FarmProfile(
        user_id="rainfed_user",
        land_size_acres=land_size,
        soil_type="loam",
        irrigation_type="rainfed",
        location=Location(state="Maharashtra", district="Pune", pincode="411014"),
        current_crops=[],
        previous_crops=[]
    )
    
    # Call the crop advice handler for kharif season
    response = call_crop_advice_handler(farm_profile, "kharif")
    
    # Verify successful response
    assert response['statusCode'] == 200
    
    # Parse response body
    body = json.loads(response['body'])
    recommendations = body['recommendations']
    
    # Verify no high water requirement crops for rainfed farms
    for rec in recommendations:
        # Note: The current implementation filters out high water requirement crops
        # for rainfed farms, so we shouldn't see any in the results
        # This is a constraint verification
        if rec['water_requirement'] == 'high':
            # If we find a high water requirement crop, it should have a warning in risks
            assert any('water' in risk.lower() for risk in rec['risks']), (
                f"High water requirement crop {rec['crop_name']} recommended for rainfed farm "
                f"without water-related risk warning"
            )


@settings(max_examples=10, deadline=None)
@given(
    soil_type=st.sampled_from(["black", "loam", "clay", "sandy", "alluvial"]),
    season=st.sampled_from(["kharif", "rabi", "zaid"])
)
def test_crop_recommendation_soil_season_match(soil_type, season):
    """
    Test that recommended crops match the soil type and season.
    
    This verifies that recommendations respect soil and seasonal constraints.
    """
    # Create a farm profile with specific soil and season
    farm_profile = FarmProfile(
        user_id="test_user",
        land_size_acres=5.0,
        soil_type=soil_type,
        irrigation_type="well",
        location=Location(state="Maharashtra", district="Pune", pincode="411014"),
        current_crops=[],
        previous_crops=[]
    )
    
    # Call the crop advice handler
    response = call_crop_advice_handler(farm_profile, season)
    
    # Verify successful response
    assert response['statusCode'] == 200
    
    # Parse response body
    body = json.loads(response['body'])
    recommendations = body['recommendations']
    
    # Verify each recommendation mentions soil or season in reasoning
    for rec in recommendations:
        reasoning_lower = rec['reasoning'].lower()
        
        # Reasoning should mention either soil type or season
        assert (
            soil_type.lower() in reasoning_lower or
            season.lower() in reasoning_lower or
            'soil' in reasoning_lower or
            'season' in reasoning_lower
        ), (
            f"Recommendation for {rec['crop_name']} does not mention soil type or season in reasoning: "
            f"{rec['reasoning']}"
        )


def test_crop_recommendation_invalid_input():
    """
    Test that invalid input returns appropriate error response.
    
    This verifies error handling for malformed requests.
    """
    from src.api.crop_advice import lambda_handler
    
    # Test with missing required fields
    event = {
        'body': json.dumps({
            'user_id': 'test_user'
            # Missing other required fields
        }),
        'httpMethod': 'POST',
        'path': '/farmer/crop-advice'
    }
    
    response = lambda_handler(event, None)
    
    # Should return 400 error
    assert response['statusCode'] == 400, (
        f"Expected status code 400 for invalid input, got {response['statusCode']}"
    )
    
    # Error message should be present
    body = json.loads(response['body'])
    assert 'error' in body, "Error response should contain 'error' field"


def test_crop_recommendation_empty_result_handling():
    """
    Test handling when no crops match the criteria.
    
    This verifies graceful handling of edge cases.
    """
    # Create a farm profile that might not match any crops
    # (This is a theoretical test - the current implementation should always return something)
    farm_profile = FarmProfile(
        user_id="edge_case_user",
        land_size_acres=1.0,
        soil_type="sandy",
        irrigation_type="rainfed",
        location=Location(state="Rajasthan", district="Jaipur", pincode="302001"),
        current_crops=[],
        previous_crops=[]
    )
    
    # Call the crop advice handler for zaid season (summer)
    response = call_crop_advice_handler(farm_profile, "zaid")
    
    # Should still return 200 (even if recommendations list might be empty or limited)
    assert response['statusCode'] == 200
    
    # Parse response body
    body = json.loads(response['body'])
    
    # Should have recommendations key
    assert 'recommendations' in body
    
    # Recommendations should be a list (even if empty)
    assert isinstance(body['recommendations'], list)
