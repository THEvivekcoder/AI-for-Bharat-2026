"""Unit tests for distance calculator."""

import pytest
import math

from src.utils.distance_calculator import DistanceCalculator


def test_haversine_distance_same_point():
    """Test distance between same point is zero."""
    distance = DistanceCalculator.haversine_distance(
        18.5204, 73.8567,  # Pune
        18.5204, 73.8567   # Pune
    )
    
    assert distance == 0.0


def test_haversine_distance_known_cities():
    """Test distance calculation between known cities."""
    # Pune to Mumbai (approximate distance ~120 km)
    distance = DistanceCalculator.haversine_distance(
        18.5204, 73.8567,  # Pune
        19.0760, 72.8777   # Mumbai
    )
    
    # Should be approximately 120 km (allow 15% margin)
    assert 100 <= distance <= 140


def test_haversine_distance_long_distance():
    """Test distance calculation for long distances."""
    # Mumbai to Bangalore (approximate distance ~840 km)
    distance = DistanceCalculator.haversine_distance(
        19.0760, 72.8777,  # Mumbai
        12.9716, 77.5946   # Bangalore
    )
    
    # Should be approximately 840 km (allow 10% margin)
    assert 750 <= distance <= 930


def test_get_coordinates_valid_district():
    """Test getting coordinates for valid district."""
    coords = DistanceCalculator.get_coordinates('Maharashtra', 'Pune')
    
    assert coords is not None
    assert len(coords) == 2
    assert coords == (18.5204, 73.8567)


def test_get_coordinates_invalid_state():
    """Test getting coordinates for invalid state."""
    coords = DistanceCalculator.get_coordinates('InvalidState', 'SomeDistrict')
    
    assert coords is None


def test_get_coordinates_invalid_district():
    """Test getting coordinates for invalid district."""
    coords = DistanceCalculator.get_coordinates('Maharashtra', 'InvalidDistrict')
    
    assert coords is None


def test_calculate_distance_same_district():
    """Test distance calculation for same district."""
    distance = DistanceCalculator.calculate_distance(
        'Maharashtra', 'Pune',
        'Maharashtra', 'Pune'
    )
    
    assert distance == 0.0


def test_calculate_distance_different_districts():
    """Test distance calculation between different districts."""
    distance = DistanceCalculator.calculate_distance(
        'Maharashtra', 'Pune',
        'Maharashtra', 'Mumbai'
    )
    
    assert distance is not None
    assert distance > 0
    # Pune to Mumbai is approximately 120 km
    assert 100 <= distance <= 140


def test_calculate_distance_unknown_coordinates():
    """Test distance calculation with unknown coordinates."""
    distance = DistanceCalculator.calculate_distance(
        'Maharashtra', 'Pune',
        'UnknownState', 'UnknownDistrict'
    )
    
    # Should return None when coordinates not found
    assert distance is None


def test_is_within_radius_same_district():
    """Test that same district is always within radius."""
    result = DistanceCalculator.is_within_radius(
        'Maharashtra', 'Pune',
        'Maharashtra', 'Pune',
        radius_km=10
    )
    
    assert result is True


def test_is_within_radius_nearby_district():
    """Test radius check for nearby districts."""
    # Pune to Mumbai is ~120 km
    result = DistanceCalculator.is_within_radius(
        'Maharashtra', 'Pune',
        'Maharashtra', 'Mumbai',
        radius_km=150
    )
    
    assert result is True


def test_is_within_radius_far_district():
    """Test radius check for far districts."""
    # Pune to Mumbai is ~120 km
    result = DistanceCalculator.is_within_radius(
        'Maharashtra', 'Pune',
        'Maharashtra', 'Mumbai',
        radius_km=80
    )
    
    assert result is False


def test_is_within_radius_unknown_coordinates_same_state():
    """Test radius check with unknown coordinates in same state."""
    # When coordinates not found but same state, assume within radius
    result = DistanceCalculator.is_within_radius(
        'Maharashtra', 'Pune',
        'Maharashtra', 'UnknownDistrict',
        radius_km=50
    )
    
    assert result is True


def test_is_within_radius_unknown_coordinates_different_state():
    """Test radius check with unknown coordinates in different state."""
    # When coordinates not found and different state, assume not within radius
    result = DistanceCalculator.is_within_radius(
        'Maharashtra', 'Pune',
        'UnknownState', 'UnknownDistrict',
        radius_km=50
    )
    
    assert result is False


def test_coordinates_coverage():
    """Test that major states and districts have coordinates."""
    major_states = [
        'Maharashtra', 'Karnataka', 'Gujarat', 'Tamil Nadu',
        'Rajasthan', 'Uttar Pradesh', 'Madhya Pradesh'
    ]
    
    for state in major_states:
        state_data = DistanceCalculator.DISTRICT_COORDINATES.get(state)
        assert state_data is not None, f"Missing coordinates for {state}"
        assert len(state_data) > 0, f"No districts for {state}"


def test_haversine_formula_accuracy():
    """Test Haversine formula accuracy with known distances."""
    # Test cases with known distances
    test_cases = [
        # (lat1, lon1, lat2, lon2, expected_distance_km)
        (0, 0, 0, 1, 111.19),  # 1 degree longitude at equator ≈ 111 km
        (0, 0, 1, 0, 111.19),  # 1 degree latitude ≈ 111 km
    ]
    
    for lat1, lon1, lat2, lon2, expected in test_cases:
        distance = DistanceCalculator.haversine_distance(lat1, lon1, lat2, lon2)
        # Allow 1% margin of error
        assert abs(distance - expected) / expected < 0.01


def test_distance_symmetry():
    """Test that distance calculation is symmetric."""
    # Distance from A to B should equal distance from B to A
    distance_ab = DistanceCalculator.calculate_distance(
        'Maharashtra', 'Pune',
        'Maharashtra', 'Mumbai'
    )
    
    distance_ba = DistanceCalculator.calculate_distance(
        'Maharashtra', 'Mumbai',
        'Maharashtra', 'Pune'
    )
    
    assert distance_ab == distance_ba


def test_earth_radius_constant():
    """Test that Earth radius constant is reasonable."""
    # Earth radius should be approximately 6371 km
    assert DistanceCalculator.EARTH_RADIUS_KM == 6371.0
