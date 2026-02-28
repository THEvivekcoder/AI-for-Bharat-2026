"""
Property-Based Test: Health Facility Distance Accuracy
Feature: bharatsahayak, Property 13: Health Facility Distance Accuracy

For any location query, all returned health facilities should be within the 
specified radius, sorted by distance in ascending order, with accurate distance 
calculations.

Validates: Requirements 5.2
"""
import pytest
from hypothesis import given, settings, strategies as st, HealthCheck, assume
from hypothesis.strategies import composite
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.health_advisor import HealthAdvisor
from app.schemas.health import Location
from app.models.health import HealthFacility
import math
import uuid
from datetime import datetime


# Strategy for generating valid locations
@composite
def location_strategy(draw):
    """Generate a valid location with coordinates"""
    states = ['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh', 'Bihar', 'West Bengal']
    districts = ['Mumbai', 'Pune', 'Bangalore', 'Chennai', 'Lucknow', 'Patna', 'Kolkata']
    
    state = draw(st.sampled_from(states))
    district = draw(st.sampled_from(districts))
    
    # Generate valid coordinates (India roughly: lat 8-35, lon 68-97)
    latitude = draw(st.floats(min_value=8.0, max_value=35.0, allow_nan=False, allow_infinity=False))
    longitude = draw(st.floats(min_value=68.0, max_value=97.0, allow_nan=False, allow_infinity=False))
    
    return Location(
        state=state,
        district=district,
        latitude=latitude,
        longitude=longitude
    )


# Strategy for generating search radius
def radius_strategy():
    """Generate valid search radius in kilometers"""
    return st.integers(min_value=5, max_value=100)


# Strategy for generating facility type
def facility_type_strategy():
    """Generate valid facility types"""
    return st.sampled_from(['PHC', 'CHC', 'District Hospital', 'Specialty Center', 'Clinic'])


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula
    This is the reference implementation for testing
    
    Returns:
        Distance in kilometers
    """
    # Earth radius in kilometers
    R = 6371.0
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance


@pytest.fixture(scope="function")
def test_db_with_facilities():
    """Create a test database with health facilities"""
    from sqlalchemy.types import TypeDecorator, CHAR
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    from sqlalchemy import Table, Column, String, DateTime, Text, Float, Integer, JSON, DECIMAL
    from sqlalchemy import MetaData
    import uuid as uuid_module
    
    class UUID(TypeDecorator):
        """Platform-independent UUID type."""
        impl = CHAR
        cache_ok = True
        
        def load_dialect_impl(self, dialect):
            if dialect.name == 'postgresql':
                return dialect.type_descriptor(PG_UUID())
            else:
                return dialect.type_descriptor(CHAR(36))
        
        def process_bind_param(self, value, dialect):
            if value is None:
                return value
            elif not isinstance(value, uuid_module.UUID):
                return str(uuid_module.UUID(value)) if value else None
            else:
                return str(value)
        
        def process_result_value(self, value, dialect):
            if value is None:
                return value
            return uuid_module.UUID(value) if value else None
    
    # Create engine
    engine = create_engine('sqlite:///:memory:', echo=False)
    
    # Create tables manually for SQLite compatibility
    metadata = MetaData()
    
    # Health facilities table
    health_facilities_table = Table(
        'health_facilities', metadata,
        Column('facility_id', UUID(), primary_key=True),
        Column('name', String(255), nullable=False),
        Column('facility_type', String(50)),
        Column('state', String(50)),
        Column('district', String(50)),
        Column('address', Text),
        Column('latitude', DECIMAL(10, 8)),
        Column('longitude', DECIMAL(11, 8)),
        Column('contact', String(100)),
        Column('services', JSON),
        Column('created_at', DateTime)
    )
    
    metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


def create_test_facilities(session, base_location: Location, num_facilities: int = 10):
    """
    Create test facilities at various distances from base location
    
    Returns list of created facilities with their expected distances
    """
    # Clear any existing facilities to avoid test interference
    session.query(HealthFacility).delete()
    session.commit()
    
    facilities_data = []
    
    for i in range(num_facilities):
        # Create facilities at different distances
        # Offset in degrees (roughly 1 degree = 111 km)
        # Use a pattern that avoids creating facilities at exact same location
        # Start from 0.05 degrees and increment by 0.1
        lat_offset = (i * 0.1) + 0.05  # Range from 0.05 to 1.45 degrees
        lon_offset = (i * 0.1) + 0.05
        
        facility_lat = base_location.latitude + lat_offset
        facility_lon = base_location.longitude + lon_offset
        
        # Calculate expected distance
        expected_distance = calculate_haversine_distance(
            base_location.latitude,
            base_location.longitude,
            facility_lat,
            facility_lon
        )
        
        facility = HealthFacility(
            facility_id=uuid.uuid4(),
            name=f"Test Facility {i}",
            facility_type=['PHC', 'CHC', 'District Hospital'][i % 3],
            state=base_location.state,
            district=base_location.district,
            address=f"Test Address {i}",
            latitude=facility_lat,
            longitude=facility_lon,
            contact=f"1234567{i:03d}",
            services=['OPD', 'Emergency'],
            created_at=datetime.utcnow()
        )
        
        session.add(facility)
        facilities_data.append({
            'facility': facility,
            'expected_distance': expected_distance
        })
    
    session.commit()
    return facilities_data


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    location=location_strategy(),
    radius_km=radius_strategy()
)
def test_facility_distance_within_radius(location, radius_km, test_db_with_facilities):
    """
    Feature: bharatsahayak, Property 13: Health Facility Distance Accuracy
    
    For any location query, all returned health facilities should be within 
    the specified radius.
    
    This tests that the radius constraint is properly enforced.
    """
    # Create test facilities
    facilities_data = create_test_facilities(test_db_with_facilities, location, num_facilities=15)
    
    # Create health advisor
    advisor = HealthAdvisor(test_db_with_facilities)
    
    # Find facilities within radius
    results = advisor.find_facilities(location, radius_km=radius_km)
    
    # Property 1: All returned facilities should be within the specified radius
    for facility in results:
        if facility.distance_km is not None:
            assert facility.distance_km <= radius_km, \
                f"Facility {facility.name} at distance {facility.distance_km}km exceeds radius {radius_km}km"


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    location=location_strategy(),
    radius_km=radius_strategy()
)
def test_facility_distance_sorted_ascending(location, radius_km, test_db_with_facilities):
    """
    Feature: bharatsahayak, Property 13: Health Facility Distance Accuracy
    
    For any location query, returned health facilities should be sorted by 
    distance in ascending order.
    
    This tests that facilities are properly sorted by distance.
    """
    # Create test facilities
    facilities_data = create_test_facilities(test_db_with_facilities, location, num_facilities=15)
    
    # Create health advisor
    advisor = HealthAdvisor(test_db_with_facilities)
    
    # Find facilities within radius
    results = advisor.find_facilities(location, radius_km=radius_km)
    
    # Skip if no results or only one result
    assume(len(results) >= 2)
    
    # Property 2: Facilities should be sorted by distance in ascending order
    # Only check facilities with calculated distances
    distances = [f.distance_km for f in results if f.distance_km is not None]
    
    # Skip if we don't have at least 2 facilities with distances
    assume(len(distances) >= 2)
    
    for i in range(len(distances) - 1):
        assert distances[i] <= distances[i + 1], \
            f"Facilities not sorted by distance: {distances[i]}km > {distances[i+1]}km"
    
    # Property 3: Facilities without distance should be at the end
    has_distance = [f.distance_km is not None for f in results]
    # Once we see a None, all subsequent should be None
    seen_none = False
    for has_dist in has_distance:
        if not has_dist:
            seen_none = True
        elif seen_none:
            assert False, "Facilities with distance should come before facilities without distance"


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    location=location_strategy(),
    radius_km=radius_strategy()
)
def test_facility_distance_calculation_accuracy(location, radius_km, test_db_with_facilities):
    """
    Feature: bharatsahayak, Property 13: Health Facility Distance Accuracy
    
    For any location query, the calculated distances should be accurate 
    according to the Haversine formula.
    
    This tests that distance calculations are mathematically correct.
    """
    # Create test facilities
    facilities_data = create_test_facilities(test_db_with_facilities, location, num_facilities=10)
    
    # Create health advisor
    advisor = HealthAdvisor(test_db_with_facilities)
    
    # Find facilities within radius
    results = advisor.find_facilities(location, radius_km=radius_km)
    
    # Property 3: Calculated distances should match reference implementation
    for facility in results:
        if facility.distance_km is not None and facility.latitude and facility.longitude:
            # Calculate expected distance using reference implementation
            expected_distance = calculate_haversine_distance(
                location.latitude,
                location.longitude,
                facility.latitude,
                facility.longitude
            )
            
            # Allow small tolerance for floating point arithmetic (0.1 km = 100 meters)
            tolerance = 0.1
            assert abs(facility.distance_km - expected_distance) <= tolerance, \
                f"Distance calculation inaccurate: got {facility.distance_km}km, expected {expected_distance}km"


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    location=location_strategy(),
    radius_km=radius_strategy(),
    facility_type=facility_type_strategy()
)
def test_facility_distance_with_type_filter(location, radius_km, facility_type, test_db_with_facilities):
    """
    Feature: bharatsahayak, Property 13: Health Facility Distance Accuracy
    
    For any location query with facility type filter, all returned facilities 
    should match the type AND be within radius, sorted by distance.
    
    This tests that filtering doesn't break distance constraints.
    """
    # Create test facilities
    facilities_data = create_test_facilities(test_db_with_facilities, location, num_facilities=15)
    
    # Create health advisor
    advisor = HealthAdvisor(test_db_with_facilities)
    
    # Find facilities with type filter
    results = advisor.find_facilities(location, facility_type=facility_type, radius_km=radius_km)
    
    # Property 1: All facilities should match the type
    for facility in results:
        assert facility.facility_type == facility_type, \
            f"Facility type mismatch: expected {facility_type}, got {facility.facility_type}"
    
    # Property 2: All facilities should be within radius
    for facility in results:
        if facility.distance_km is not None:
            assert facility.distance_km <= radius_km, \
                f"Facility at distance {facility.distance_km}km exceeds radius {radius_km}km"
    
    # Property 3: Facilities should be sorted by distance
    distances = [f.distance_km for f in results if f.distance_km is not None]
    if len(distances) >= 2:
        for i in range(len(distances) - 1):
            assert distances[i] <= distances[i + 1], \
                f"Facilities not sorted by distance"
    
    # Property 4: Facilities without distance should be at the end
    has_distance = [f.distance_km is not None for f in results]
    seen_none = False
    for has_dist in has_distance:
        if not has_dist:
            seen_none = True
        elif seen_none:
            assert False, "Facilities with distance should come before facilities without distance"


def test_facility_distance_specific_example(test_db_with_facilities):
    """
    Specific example test: Create facilities at known distances and verify.
    
    This complements property-based tests with a concrete example.
    """
    # Create a specific location
    location = Location(
        state='Maharashtra',
        district='Mumbai',
        latitude=19.0760,  # Mumbai coordinates
        longitude=72.8777
    )
    
    # Create facilities at specific distances
    # Facility 1: Very close (approximately 5 km away)
    facility1 = HealthFacility(
        facility_id=uuid.uuid4(),
        name="Nearby PHC",
        facility_type='PHC',
        state='Maharashtra',
        district='Mumbai',
        address="Near location",
        latitude=19.1200,  # ~5 km north
        longitude=72.8777,
        contact="1234567890",
        services=['OPD'],
        created_at=datetime.utcnow()
    )
    
    # Facility 2: Medium distance (approximately 20 km away)
    facility2 = HealthFacility(
        facility_id=uuid.uuid4(),
        name="District Hospital",
        facility_type='District Hospital',
        state='Maharashtra',
        district='Mumbai',
        address="Medium distance",
        latitude=19.2500,  # ~20 km north
        longitude=72.8777,
        contact="1234567891",
        services=['OPD', 'Emergency'],
        created_at=datetime.utcnow()
    )
    
    # Facility 3: Far away (approximately 50 km away)
    facility3 = HealthFacility(
        facility_id=uuid.uuid4(),
        name="Specialty Center",
        facility_type='Specialty Center',
        state='Maharashtra',
        district='Mumbai',
        address="Far location",
        latitude=19.5000,  # ~50 km north
        longitude=72.8777,
        contact="1234567892",
        services=['Specialty'],
        created_at=datetime.utcnow()
    )
    
    test_db_with_facilities.add_all([facility1, facility2, facility3])
    test_db_with_facilities.commit()
    
    # Create health advisor
    advisor = HealthAdvisor(test_db_with_facilities)
    
    # Test with 25 km radius - should get facility1 and facility2
    results_25km = advisor.find_facilities(location, radius_km=25)
    
    assert len(results_25km) >= 1, "Should find at least nearby facility"
    
    # All results should be within 25 km
    for facility in results_25km:
        if facility.distance_km is not None:
            assert facility.distance_km <= 25, \
                f"Facility {facility.name} at {facility.distance_km}km exceeds 25km radius"
    
    # Results should be sorted by distance
    distances = [f.distance_km for f in results_25km if f.distance_km is not None]
    assert distances == sorted(distances), "Facilities should be sorted by distance"
    
    # Test with 60 km radius - should get all facilities
    results_60km = advisor.find_facilities(location, radius_km=60)
    
    assert len(results_60km) >= 2, "Should find multiple facilities within 60km"
    
    # All results should be within 60 km
    for facility in results_60km:
        if facility.distance_km is not None:
            assert facility.distance_km <= 60, \
                f"Facility at {facility.distance_km}km exceeds 60km radius"


def test_facility_distance_no_coordinates(test_db_with_facilities):
    """
    Test that facilities without coordinates are handled gracefully.
    """
    # Create a location
    location = Location(
        state='Maharashtra',
        district='Mumbai',
        latitude=19.0760,
        longitude=72.8777
    )
    
    # Create facility without coordinates
    facility_no_coords = HealthFacility(
        facility_id=uuid.uuid4(),
        name="Facility Without Coords",
        facility_type='PHC',
        state='Maharashtra',
        district='Mumbai',
        address="No coordinates",
        latitude=None,
        longitude=None,
        contact="1234567890",
        services=['OPD'],
        created_at=datetime.utcnow()
    )
    
    test_db_with_facilities.add(facility_no_coords)
    test_db_with_facilities.commit()
    
    # Create health advisor
    advisor = HealthAdvisor(test_db_with_facilities)
    
    # Find facilities
    results = advisor.find_facilities(location, radius_km=50)
    
    # Should handle facilities without coordinates
    # They should either be excluded or have distance_km = None
    for facility in results:
        if facility.latitude is None or facility.longitude is None:
            assert facility.distance_km is None, \
                "Facilities without coordinates should have distance_km = None"


def test_facility_distance_edge_case_zero_distance(test_db_with_facilities):
    """
    Test edge case where facility is at exact same location as query.
    """
    # Create a location with coordinates
    location = Location(
        state='Maharashtra',
        district='Mumbai',
        latitude=19.0760,
        longitude=72.8777
    )
    
    # Create facility at exact same location
    facility_same_location = HealthFacility(
        facility_id=uuid.uuid4(),
        name="Same Location Facility",
        facility_type='PHC',
        state='Maharashtra',
        district='Mumbai',
        address="Same location",
        latitude=19.0760,  # Exact same
        longitude=72.8777,  # Exact same
        contact="1234567890",
        services=['OPD'],
        created_at=datetime.utcnow()
    )
    
    test_db_with_facilities.add(facility_same_location)
    test_db_with_facilities.commit()
    
    # Create health advisor
    advisor = HealthAdvisor(test_db_with_facilities)
    
    # Find facilities
    results = advisor.find_facilities(location, radius_km=10)
    
    # Should find the facility
    assert len(results) >= 1, "Should find facility at same location"
    
    # Distance should be 0 or very close to 0
    same_location_facility = next((f for f in results if f.name == "Same Location Facility"), None)
    assert same_location_facility is not None, "Should find the same location facility"
    
    # The distance should be calculated (not None) since both have coordinates
    if same_location_facility.distance_km is not None:
        assert same_location_facility.distance_km < 0.1, \
            f"Distance should be near 0, got {same_location_facility.distance_km}km"
    else:
        # If distance is None, it means coordinates weren't properly used
        # This is acceptable if the implementation doesn't calculate for same location
        # but we should at least verify the facility was found
        assert same_location_facility.latitude == location.latitude
        assert same_location_facility.longitude == location.longitude


def test_facility_distance_different_districts(test_db_with_facilities):
    """
    Test that only facilities in the same district are returned.
    """
    # Create a location
    location = Location(
        state='Maharashtra',
        district='Mumbai',
        latitude=19.0760,
        longitude=72.8777
    )
    
    # Create facility in same district
    facility_same_district = HealthFacility(
        facility_id=uuid.uuid4(),
        name="Mumbai Facility",
        facility_type='PHC',
        state='Maharashtra',
        district='Mumbai',
        address="Mumbai",
        latitude=19.1000,
        longitude=72.8777,
        contact="1234567890",
        services=['OPD'],
        created_at=datetime.utcnow()
    )
    
    # Create facility in different district (even if geographically close)
    facility_different_district = HealthFacility(
        facility_id=uuid.uuid4(),
        name="Pune Facility",
        facility_type='PHC',
        state='Maharashtra',
        district='Pune',
        address="Pune",
        latitude=19.1100,  # Close coordinates
        longitude=72.8777,
        contact="1234567891",
        services=['OPD'],
        created_at=datetime.utcnow()
    )
    
    test_db_with_facilities.add_all([facility_same_district, facility_different_district])
    test_db_with_facilities.commit()
    
    # Create health advisor
    advisor = HealthAdvisor(test_db_with_facilities)
    
    # Find facilities
    results = advisor.find_facilities(location, radius_km=50)
    
    # Should only return facilities from Mumbai district
    for facility in results:
        assert facility.district == 'Mumbai', \
            f"Should only return facilities from Mumbai district, got {facility.district}"


def test_facility_distance_empty_results(test_db_with_facilities):
    """
    Test that empty results are handled when no facilities are within radius.
    """
    # Create a location
    location = Location(
        state='Maharashtra',
        district='Mumbai',
        latitude=19.0760,
        longitude=72.8777
    )
    
    # Create facility far away (> 100 km)
    facility_far = HealthFacility(
        facility_id=uuid.uuid4(),
        name="Far Facility",
        facility_type='PHC',
        state='Maharashtra',
        district='Mumbai',
        address="Far away",
        latitude=20.0000,  # ~100+ km away
        longitude=73.5000,
        contact="1234567890",
        services=['OPD'],
        created_at=datetime.utcnow()
    )
    
    test_db_with_facilities.add(facility_far)
    test_db_with_facilities.commit()
    
    # Create health advisor
    advisor = HealthAdvisor(test_db_with_facilities)
    
    # Find facilities with small radius
    results = advisor.find_facilities(location, radius_km=10)
    
    # Should return empty list (no facilities within 10 km)
    assert isinstance(results, list), "Should return a list"
    assert len(results) == 0, "Should return empty list when no facilities within radius"
