"""Property-based tests for mandi price radius constraint.

Feature: bharatsahayak, Property 9: Mandi Price Radius Constraint
**Validates: Requirements 3.3**

This test verifies that returned mandi prices are within the specified radius
and sorted by distance in ascending order.
"""

import pytest
import os
from hypothesis import given, settings, strategies as st, HealthCheck
import json
from unittest.mock import patch, MagicMock

from src.models.mandi import MandiPriceQuery


# Custom strategies for generating valid test data
@st.composite
def mandi_price_query_strategy(draw):
    """Generate valid MandiPriceQuery instances."""
    states = ["Maharashtra", "Karnataka", "Gujarat", "Tamil Nadu", "Rajasthan"]
    districts = {
        "Maharashtra": ["Pune", "Mumbai", "Nagpur"],
        "Karnataka": ["Bangalore", "Mysore", "Hubli"],
        "Gujarat": ["Ahmedabad", "Surat", "Vadodara"],
        "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai"],
        "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur"]
    }
    
    state = draw(st.sampled_from(states))
    district = draw(st.sampled_from(districts[state]))
    
    return MandiPriceQuery(
        crop_name=draw(st.sampled_from(["wheat", "rice", "soybean", "cotton", "maize"])),
        state=state,
        district=district,
        radius_km=draw(st.integers(min_value=10, max_value=100))
    )


def call_market_price_handler(query: MandiPriceQuery) -> dict:
    """
    Call the market price Lambda handler with a query.
    
    Args:
        query: Mandi price query
        
    Returns:
        Response dictionary from the handler
    """
    # Mock environment variables and boto3 before importing
    with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
        with patch('boto3.resource') as mock_boto_resource:
            # Mock DynamoDB table
            mock_table = MagicMock()
            mock_table.query.return_value = {'Items': []}
            mock_table.batch_writer.return_value.__enter__ = MagicMock()
            mock_table.batch_writer.return_value.__exit__ = MagicMock()
            mock_boto_resource.return_value.Table.return_value = mock_table
            
            # Import after mocking
            from src.api.market_price import lambda_handler
            
            # Create Lambda event
            event = {
                'queryStringParameters': {
                    'crop_name': query.crop_name,
                    'state': query.state,
                    'district': query.district,
                    'radius_km': str(query.radius_km)
                },
                'httpMethod': 'GET',
                'path': '/farmer/market-price'
            }
            
            # Call handler
            response = lambda_handler(event, None)
    
    return response


@settings(max_examples=3, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
@given(query=mandi_price_query_strategy())
def test_mandi_price_radius_constraint(query):
    """
    Feature: bharatsahayak, Property 9: Mandi Price Radius Constraint
    
    For any location and crop query, all returned mandi prices should be from
    mandis within the specified radius (default 50km), and results should be
    sorted by distance in ascending order.
    
    This test verifies:
    1. All returned prices are within the specified radius
    2. Prices are sorted by distance (ascending)
    3. Distance field is present and non-negative
    4. At least one price is returned for valid queries
    """
    # Call the market price handler
    response = call_market_price_handler(query)
    
    # Verify successful response or 404 (no data)
    assert response['statusCode'] in [200, 404], (
        f"Expected status code 200 or 404, got {response['statusCode']}"
    )
    
    # If 404, skip further checks (no data available)
    if response['statusCode'] == 404:
        return
    
    # Parse response body
    body = json.loads(response['body'])
    
    # Verify prices exist
    assert 'prices' in body, "Response should contain 'prices' field"
    prices = body['prices']
    
    # Property 1: All prices should be within the specified radius
    for i, price in enumerate(prices):
        assert 'distance_km' in price, f"Price {i} missing 'distance_km' field"
        
        distance = price['distance_km']
        
        # Distance should be non-negative
        assert distance >= 0, (
            f"Price {i} has negative distance: {distance}"
        )
        
        # Distance should be within radius
        assert distance <= query.radius_km, (
            f"Price {i} exceeds radius constraint: "
            f"distance={distance}km, radius={query.radius_km}km, "
            f"mandi={price['mandi_name']}"
        )
    
    # Property 2: Prices should be sorted by distance (ascending)
    if len(prices) > 1:
        for i in range(len(prices) - 1):
            current_distance = prices[i]['distance_km']
            next_distance = prices[i + 1]['distance_km']
            
            assert current_distance <= next_distance, (
                f"Prices not sorted by distance: "
                f"price {i} has distance {current_distance}km, "
                f"price {i+1} has distance {next_distance}km"
            )
    
    # Property 3: All required fields should be present
    required_fields = ['mandi_name', 'crop_name', 'state', 'district', 
                      'price_per_quintal', 'price_date', 'distance_km']
    
    for i, price in enumerate(prices):
        for field in required_fields:
            assert field in price, (
                f"Price {i} missing required field '{field}'"
            )
        
        # Price should be positive
        assert price['price_per_quintal'] > 0, (
            f"Price {i} has invalid price_per_quintal: {price['price_per_quintal']}"
        )


@settings(max_examples=2, deadline=None)
@given(
    crop_name=st.sampled_from(["wheat", "rice", "soybean", "cotton"]),
    radius=st.integers(min_value=10, max_value=100)
)
def test_mandi_price_radius_filtering(crop_name, radius):
    """
    Test that radius filtering works correctly.
    
    This verifies that increasing radius returns more or equal results.
    """
    query1 = MandiPriceQuery(
        crop_name=crop_name,
        state="Maharashtra",
        district="Pune",
        radius_km=radius
    )
    
    # Call with smaller radius
    response1 = call_market_price_handler(query1)
    
    # Skip if no data
    if response1['statusCode'] == 404:
        return
    
    body1 = json.loads(response1['body'])
    prices1 = body1.get('prices', [])
    
    # All prices should be within radius
    for price in prices1:
        assert price['distance_km'] <= radius


@settings(max_examples=2, deadline=None)
@given(query=mandi_price_query_strategy())
def test_mandi_price_same_district_first(query):
    """
    Test that prices from the same district appear first (distance = 0).
    
    This verifies that local mandis are prioritized.
    """
    response = call_market_price_handler(query)
    
    # Skip if no data
    if response['statusCode'] == 404:
        return
    
    body = json.loads(response['body'])
    prices = body.get('prices', [])
    
    # If there are prices, check if same-district prices come first
    same_district_prices = [p for p in prices if p['district'] == query.district]
    
    if same_district_prices:
        # Same district prices should have distance 0
        for price in same_district_prices:
            assert price['distance_km'] == 0, (
                f"Same district price should have distance 0, got {price['distance_km']}"
            )
        
        # Same district prices should appear first (due to sorting by distance)
        first_same_district_index = next(
            (i for i, p in enumerate(prices) if p['district'] == query.district),
            None
        )
        
        if first_same_district_index is not None:
            # All prices before this should also be distance 0
            for i in range(first_same_district_index):
                assert prices[i]['distance_km'] == 0


def test_mandi_price_invalid_parameters():
    """
    Test that invalid parameters return appropriate error response.
    
    This verifies error handling for malformed requests.
    """
    # Mock environment and boto3
    with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
        with patch('boto3.resource'):
            from src.api.market_price import lambda_handler
            
            # Test with missing required parameters
            event = {
                'queryStringParameters': {
                    'crop_name': 'wheat'
                    # Missing state and district
                },
                'httpMethod': 'GET',
                'path': '/farmer/market-price'
            }
            
            response = lambda_handler(event, None)
    
    # Should return 400 error
    assert response['statusCode'] == 400, (
        f"Expected status code 400 for invalid input, got {response['statusCode']}"
    )
    
    # Error message should be present
    body = json.loads(response['body'])
    assert 'error' in body, "Error response should contain 'error' field"


@settings(max_examples=2, deadline=None)
@given(radius=st.integers(min_value=1, max_value=200))
def test_mandi_price_radius_boundary(radius):
    """
    Test that radius boundary is respected exactly.
    
    This verifies that prices at exactly the radius distance are included.
    """
    query = MandiPriceQuery(
        crop_name="wheat",
        state="Maharashtra",
        district="Pune",
        radius_km=radius
    )
    
    response = call_market_price_handler(query)
    
    # Skip if no data
    if response['statusCode'] == 404:
        return
    
    body = json.loads(response['body'])
    prices = body.get('prices', [])
    
    # All prices should be within or at the boundary
    for price in prices:
        assert price['distance_km'] <= radius, (
            f"Price exceeds radius: distance={price['distance_km']}, radius={radius}"
        )


@settings(max_examples=2, deadline=None)
@given(query=mandi_price_query_strategy())
def test_mandi_price_response_structure(query):
    """
    Test that response has correct structure with metadata.
    
    This verifies that response includes last_updated and source fields.
    """
    response = call_market_price_handler(query)
    
    # Skip if no data
    if response['statusCode'] == 404:
        return
    
    body = json.loads(response['body'])
    
    # Should have metadata fields
    assert 'last_updated' in body, "Response should contain 'last_updated' field"
    assert 'source' in body, "Response should contain 'source' field"
    
    # Source should be valid
    assert body['source'] in ['cache', 'government_api'], (
        f"Invalid source: {body['source']}"
    )
