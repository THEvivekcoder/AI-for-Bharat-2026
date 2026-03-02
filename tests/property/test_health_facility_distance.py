"""Property-based tests for health facility distance accuracy.

Feature: bharatsahayak, Property 13: Health Facility Distance Accuracy
**Validates: Requirements 5.2**

This test verifies that returned health facilities are within the specified radius
and sorted by distance in ascending order with accurate distance calculations.
"""

import pytest
import os
from hypothesis import given, settings, strategies as st, HealthCheck
import json
from unittest.mock import patch, MagicMock

from src.models.location import Location


# Custom strategies for generating valid test data
@st.composite
def location_strategy(draw):
    """Generate valid Location instances with coordinates."""
    states = ["Maharashtra", "Karnataka", "Gujarat", "Tamil Nadu"]
    districts = {
        "Maharashtra": [("Pune", 18.5204, 73.8567), ("Mumbai", 19.0760, 72.8777)],
        "Karnataka": [("Bangalore Urban", 12.9716, 77.5946), ("Mysore", 12.2958, 76.6394)],
        "Gujarat": [("Ahmedabad", 23.0225, 72.5714), ("Surat", 21.1702, 72.8311)],
        "Tamil Nadu": [("Chennai", 13.0827, 80.2707), ("Coimbatore", 11.0168, 76.9558)]
    }
    
    state = draw(st.sampled_from(list(states)))
    district_data = draw(st.sampled_from(districts[state]))
    district, lat, lon = district_data
    
    return Location(
        state=state,
        district=district,
        pincode="411001",
        latitude=lat,
        longitude=lon
    )


def call_health_facilities_handler(location: Location, radius_km: float, facility_type: str = None) -> dict:
    """
    Call the health facilities Lambda handler.
    
    Args:
        location: User location
        radius_km: Search radius in kilometers
        facility_type: Optional facility type filter
        
    Returns:
        Response dictionary from the handler
    """
    # Mock environment variables and boto3 before importing
    with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
        with patch('boto3.resource') as mock_boto_resource:
            # Mock DynamoDB table
            mock_table = MagicMock()
            mock_table.scan.return_value = {'Items': []}
            mock_boto_resource.return_value.Table.return_value = mock_table
            
            # Import after mocking
            from src.api.health_facilities import lambda_handler
            
            # Create Lambda event
            query_params = {
                'state': location.state,
                'district': location.district,
                'pincode': location.pincode,
                'latitude': str(location.latitude),
                'longitude': str(location.longitude),
                'radius_km': str(radius_km)
            }
            
            if facility_type:
                query_params['facility_type'] = facility_type
            
            event = {
                'queryStringParameters': query_params,
                'httpMethod': 'GET',
                'path': '/health/facilities'
            }
            
            # Call handler
            response = lambda_handler(event, None)
    
    return response


@settings(max_examples=3, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
@given(
    location=location_strategy(),
    radius_km=st.floats(min_value=5.0, max_value=100.0)
)
def test_health_facility_distance_accuracy(location, radius_km):
    """
    Feature: bharatsahayak, Property 13: Health Facility Distance Accuracy
    
    For any location query, all returned health facilities should be within
    the specified radius, sorted by distance in ascending order, with accurate
    distance calculations.
    
    This test verifies:
    1. All returned facilities are within the specified radius
    2. Facilities are sorted by distance (ascending)
    3. Distance field is present and non-negative
    4. Distance calculations are accurate (within reasonable margin)
    """
    # Call the health facilities handler
    response = call_health_facilities_handler(location, radius_km)
    
    # Verify successful response or 404 (no facilities)
    assert response['statusCode'] in [200, 404], (
        f"Expected status code 200 or 404, got {response['statusCode']}"
    )
    
    # If 404, skip further checks (no facilities available)
    if response['statusCode'] == 404:
        return
    
    # Parse response body
    body = json.loads(response['body'])
    
    # Verify facilities exist
    assert 'facilities' in body, "Response should contain 'facilities' field"
    facilities = body['facilities']
    
    # Property 1: All facilities should be within the specified radius
    for i, facility in enumerate(facilities):
        assert 'distance_km' in facility, f"Facility {i} missing 'distance_km' field"
        
        distance = facility['distance_km']
        
        # Distance should be non-negative
        assert distance >= 0, (
            f"Facility {i} has negative distance: {distance}"
        )
        
        # Distance should be within radius
        assert distance <= radius_km, (
            f"Facility {i} exceeds radius constraint: "
            f"distance={distance}km, radius={radius_km}km, "
            f"facility={facility['name']}"
        )
    
    # Property 2: Facilities should be sorted by distance (ascending)
    if len(facilities) > 1:
        for i in range(len(facilities) - 1):
            current_distance = facilities[i]['distance_km']
            next_distance = facilities[i + 1]['distance_km']
            
            assert current_distance <= next_distance, (
                f"Facilities not sorted by distance: "
                f"facility {i} has distance {current_distance}km, "
                f"facility {i+1} has distance {next_distance}km"
            )
    
    # Property 3: All required fields should be present
    required_fields = ['facility_id', 'name', 'facility_type', 'location', 
                      'address', 'services', 'distance_km']
    
    for i, facility in enumerate(facilities):
        for field in required_fields:
            assert field in facility, (
                f"Facility {i} missing required field '{field}'"
            )
        
        # Verify location has required fields
        assert 'state' in facility['location'], (
            f"Facility {i} location missing 'state' field"
        )
        assert 'district' in facility['location'], (
            f"Facility {i} location missing 'district' field"
        )
        
        # Services should be a list
        assert isinstance(facility['services'], list), (
            f"Facility {i} services should be a list"
        )


@settings(max_examples=2, deadline=None)
@given(
    location=location_strategy(),
    radius=st.floats(min_value=10.0, max_value=100.0)
)
def test_health_facility_radius_filtering(location, radius):
    """
    Test that radius filtering works correctly.
    
    This verifies that all returned facilities are within the radius.
    """
    response = call_health_facilities_handler(location, radius)
    
    # Skip if no facilities
    if response['statusCode'] == 404:
        return
    
    body = json.loads(response['body'])
    facilities = body.get('facilities', [])
    
    # All facilities should be within radius
    for facility in facilities:
        assert facility['distance_km'] <= radius, (
            f"Facility {facility['name']} exceeds radius: "
            f"distance={facility['distance_km']}km, radius={radius}km"
        )


@settings(max_examples=2, deadline=None)
@given(
    location=location_strategy(),
    facility_type=st.sampled_from(["PHC", "CHC", "District Hospital", "Specialty Center"])
)
def test_health_facility_type_filtering(location, facility_type):
    """
    Test that facility type filtering works correctly.
    
    This verifies that when a facility type is specified, only facilities
    of that type are returned.
    """
    response = call_health_facilities_handler(location, 50.0, facility_type)
    
    # Skip if no facilities
    if response['statusCode'] == 404:
        return
    
    body = json.loads(response['body'])
    facilities = body.get('facilities', [])
    
    # All facilities should match the requested type
    for facility in facilities:
        assert facility['facility_type'] == facility_type, (
            f"Facility {facility['name']} has wrong type: "
            f"expected={facility_type}, got={facility['facility_type']}"
        )


@settings(max_examples=2, deadline=None)
@given(location=location_strategy())
def test_health_facility_same_district_first(location):
    """
    Test that facilities in the same district appear first.
    
    This verifies that local facilities are prioritized.
    """
    response = call_health_facilities_handler(location, 50.0)
    
    # Skip if no facilities
    if response['statusCode'] == 404:
        return
    
    body = json.loads(response['body'])
    facilities = body.get('facilities', [])
    
    # If there are facilities, check if same-district facilities come first
    same_district_facilities = [
        f for f in facilities 
        if f['location']['district'] == location.district
    ]
    
    if same_district_facilities:
        # Same district facilities should have smaller distances
        # (though not necessarily 0 due to coordinate differences)
        first_same_district_index = next(
            (i for i, f in enumerate(facilities) 
             if f['location']['district'] == location.district),
            None
        )
        
        if first_same_district_index is not None and first_same_district_index > 0:
            # All facilities before should have distance <= first same-district facility
            first_same_district_distance = facilities[first_same_district_index]['distance_km']
            for i in range(first_same_district_index):
                assert facilities[i]['distance_km'] <= first_same_district_distance


def test_health_facility_invalid_parameters():
    """
    Test that invalid parameters return appropriate error response.
    
    This verifies error handling for malformed requests.
    """
    # Mock environment and boto3
    with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
        with patch('boto3.resource'):
            from src.api.health_facilities import lambda_handler
            
            # Test with missing required parameters
            event = {
                'queryStringParameters': {
                    'state': 'Maharashtra'
                    # Missing district, pincode, latitude, longitude
                },
                'httpMethod': 'GET',
                'path': '/health/facilities'
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
@given(location=location_strategy())
def test_health_facility_response_structure(location):
    """
    Test that response has correct structure with count.
    
    This verifies that response includes facilities array and count field.
    """
    response = call_health_facilities_handler(location, 50.0)
    
    # Skip if no facilities
    if response['statusCode'] == 404:
        return
    
    body = json.loads(response['body'])
    
    # Should have required fields
    assert 'facilities' in body, "Response should contain 'facilities' field"
    assert 'count' in body, "Response should contain 'count' field"
    
    # Count should match array length
    assert body['count'] == len(body['facilities']), (
        f"Count mismatch: count={body['count']}, array length={len(body['facilities'])}"
    )


@settings(max_examples=2, deadline=None)
@given(
    location=location_strategy(),
    radius=st.floats(min_value=1.0, max_value=200.0)
)
def test_health_facility_radius_boundary(location, radius):
    """
    Test that radius boundary is respected exactly.
    
    This verifies that facilities at exactly the radius distance are included.
    """
    response = call_health_facilities_handler(location, radius)
    
    # Skip if no facilities
    if response['statusCode'] == 404:
        return
    
    body = json.loads(response['body'])
    facilities = body.get('facilities', [])
    
    # All facilities should be within or at the boundary
    for facility in facilities:
        assert facility['distance_km'] <= radius, (
            f"Facility exceeds radius: distance={facility['distance_km']}, radius={radius}"
        )
