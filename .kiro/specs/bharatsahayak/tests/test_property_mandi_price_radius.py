"""
Property-Based Test: Mandi Price Radius Constraint
Feature: bharatsahayak, Property 9: Mandi Price Radius Constraint

For any location and crop query, all returned mandi prices should be from mandis 
within the specified radius (default 50km), and results should be sorted by distance.

Validates: Requirements 3.3
"""
import pytest
from hypothesis import given, settings, strategies as st, HealthCheck, assume
from hypothesis.strategies import composite
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.farmer import MandiPrice
from app.models.location import Location
from app.services.mandi_price_service import MandiPriceService
import uuid
import math


# Strategy for generating valid locations with coordinates
@composite
def location_with_coords_strategy(draw):
    """Generate a valid location with coordinates"""
    states = ['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh', 'Bihar', 
              'Punjab', 'Haryana', 'Rajasthan', 'Gujarat', 'Madhya Pradesh']
    districts = ['District A', 'District B', 'District C', 'District D']
    
    # Generate coordinates within India's bounds
    latitude = draw(st.floats(min_value=8.0, max_value=35.0))
    longitude = draw(st.floats(min_value=68.0, max_value=97.0))
    
    return {
        'id': uuid.uuid4(),
        'state': draw(st.sampled_from(states)),
        'district': draw(st.sampled_from(districts)),
        'block': draw(st.one_of(st.none(), st.text(min_size=3, max_size=20))),
        'village': draw(st.one_of(st.none(), st.text(min_size=3, max_size=20))),
        'pincode': draw(st.from_regex(r'[1-9][0-9]{5}', fullmatch=True)),
        'latitude': latitude,
        'longitude': longitude
    }


@pytest.fixture(scope="function")
def test_db_session():
    """Create a test database session"""
    from sqlalchemy.types import TypeDecorator, CHAR
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    from sqlalchemy import Table, Column, String, DateTime, Float, Date, ForeignKey
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
    
    # Locations table
    locations_table = Table(
        'locations', metadata,
        Column('id', UUID(), primary_key=True),
        Column('state', String(50), nullable=False),
        Column('district', String(50), nullable=False),
        Column('block', String(50), nullable=True),
        Column('village', String(100), nullable=True),
        Column('pincode', String(10), nullable=False),
        Column('latitude', Float, nullable=True),
        Column('longitude', Float, nullable=True)
    )
    
    # Mandi prices table
    mandi_prices_table = Table(
        'mandi_prices', metadata,
        Column('price_id', UUID(), primary_key=True),
        Column('crop_name', String(100), nullable=False),
        Column('mandi_name', String(100), nullable=False),
        Column('state', String(50), nullable=False),
        Column('district', String(50), nullable=False),
        Column('latitude', Float, nullable=True),
        Column('longitude', Float, nullable=True),
        Column('price_per_quintal', Float, nullable=False),
        Column('price_date', Date, nullable=False),
        Column('source', String(100), nullable=True),
        Column('created_at', DateTime, nullable=False)
    )
    
    metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula
    (Same implementation as in MandiPriceService for verification)
    """
    R = 6371.0  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    location_data=location_with_coords_strategy(),
    radius_km=st.integers(min_value=10, max_value=100),
    crop_name=st.sampled_from(['rice', 'wheat', 'cotton', 'maize'])
)
def test_mandi_price_radius_constraint(location_data, radius_km, crop_name, test_db_session):
    """
    Feature: bharatsahayak, Property 9: Mandi Price Radius Constraint
    
    For any location and crop query, all returned mandi prices should be from 
    mandis within the specified radius.
    
    This tests that the radius filtering works correctly.
    """
    # Create user location
    user_location = Location(**location_data)
    test_db_session.add(user_location)
    test_db_session.flush()
    
    # Generate multiple mandi prices at various distances
    # Create some within radius and some outside
    num_mandis = 10
    for i in range(num_mandis):
        # Vary distance from 0 to 150km
        distance_offset_km = (i * 15)  # 0, 15, 30, 45, 60, 75, 90, 105, 120, 135
        
        # Convert to lat/lon offset (roughly 1 degree = 111km)
        lat_offset = distance_offset_km / 111.0
        lon_offset = distance_offset_km / 111.0
        
        # Alternate between positive and negative offsets
        if i % 2 == 0:
            lat_offset = -lat_offset
        if i % 3 == 0:
            lon_offset = -lon_offset
        
        mandi_lat = location_data['latitude'] + lat_offset
        mandi_lon = location_data['longitude'] + lon_offset
        
        # Ensure coordinates stay within India's bounds
        mandi_lat = max(8.0, min(35.0, mandi_lat))
        mandi_lon = max(68.0, min(97.0, mandi_lon))
        
        mandi_price = MandiPrice(
            price_id=uuid.uuid4(),
            crop_name=crop_name,
            mandi_name=f"Mandi_{i}_{uuid.uuid4().hex[:6]}",
            state=location_data['state'],
            district=location_data['district'],
            latitude=mandi_lat,
            longitude=mandi_lon,
            price_per_quintal=2000.0 + (i * 100),
            price_date=date.today(),
            source='Test Data',
            created_at=datetime.utcnow()
        )
        test_db_session.add(mandi_price)
    
    test_db_session.commit()
    
    # Query mandi prices with radius constraint
    service = MandiPriceService(test_db_session)
    results = service.get_current_price(crop_name, user_location, radius_km)
    
    # Property 1: All returned mandis should be within the specified radius
    for result in results:
        # Get the mandi from database to verify coordinates
        mandi = test_db_session.query(MandiPrice).filter(
            MandiPrice.mandi_name == result.mandi_name,
            MandiPrice.crop_name == crop_name
        ).first()
        
        if mandi and mandi.latitude and mandi.longitude:
            # Calculate actual distance
            actual_distance = calculate_distance(
                user_location.latitude,
                user_location.longitude,
                mandi.latitude,
                mandi.longitude
            )
            
            # Verify distance is within radius (with small tolerance for floating point)
            assert actual_distance <= radius_km + 0.1, \
                f"Mandi {result.mandi_name} at {actual_distance:.2f}km exceeds radius {radius_km}km"
            
            # Verify the distance_km field matches our calculation (within tolerance)
            if result.distance_km is not None:
                assert abs(result.distance_km - actual_distance) < 0.5, \
                    f"Reported distance {result.distance_km}km differs from calculated {actual_distance:.2f}km"


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    location_data=location_with_coords_strategy(),
    radius_km=st.integers(min_value=10, max_value=100),
    crop_name=st.sampled_from(['rice', 'wheat', 'cotton', 'maize'])
)
def test_mandi_price_sorted_by_distance(location_data, radius_km, crop_name, test_db_session):
    """
    Feature: bharatsahayak, Property 9: Mandi Price Radius Constraint
    
    Results should be sorted by distance in ascending order (nearest first).
    
    This tests that the distance sorting works correctly.
    """
    # Create user location
    user_location = Location(**location_data)
    test_db_session.add(user_location)
    test_db_session.flush()
    
    # Generate multiple mandi prices at various distances
    num_mandis = 10
    for i in range(num_mandis):
        distance_offset_km = (i * 15)
        lat_offset = distance_offset_km / 111.0
        lon_offset = distance_offset_km / 111.0
        
        if i % 2 == 0:
            lat_offset = -lat_offset
        if i % 3 == 0:
            lon_offset = -lon_offset
        
        mandi_lat = location_data['latitude'] + lat_offset
        mandi_lon = location_data['longitude'] + lon_offset
        
        mandi_lat = max(8.0, min(35.0, mandi_lat))
        mandi_lon = max(68.0, min(97.0, mandi_lon))
        
        mandi_price = MandiPrice(
            price_id=uuid.uuid4(),
            crop_name=crop_name,
            mandi_name=f"Mandi_{i}_{uuid.uuid4().hex[:6]}",
            state=location_data['state'],
            district=location_data['district'],
            latitude=mandi_lat,
            longitude=mandi_lon,
            price_per_quintal=2000.0 + (i * 100),
            price_date=date.today(),
            source='Test Data',
            created_at=datetime.utcnow()
        )
        test_db_session.add(mandi_price)
    
    test_db_session.commit()
    
    # Query mandi prices
    service = MandiPriceService(test_db_session)
    results = service.get_current_price(crop_name, user_location, radius_km)
    
    # Property 2: Results should be sorted by distance (ascending)
    if len(results) > 1:
        for i in range(len(results) - 1):
            # Get distances (handle None for same-district mandis)
            dist1 = results[i].distance_km if results[i].distance_km is not None else 0
            dist2 = results[i+1].distance_km if results[i+1].distance_km is not None else 0
            
            assert dist1 <= dist2, \
                f"Results not sorted by distance: {dist1}km before {dist2}km"


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    location_data=location_with_coords_strategy(),
    crop_name=st.sampled_from(['rice', 'wheat', 'cotton', 'maize'])
)
def test_mandi_price_default_radius(location_data, crop_name, test_db_session):
    """
    Feature: bharatsahayak, Property 9: Mandi Price Radius Constraint
    
    When no radius is specified, the default radius of 50km should be used.
    
    This tests the default radius behavior.
    """
    # Create user location
    user_location = Location(**location_data)
    test_db_session.add(user_location)
    test_db_session.flush()
    
    # Generate mandi prices at various distances
    num_mandis = 10
    for i in range(num_mandis):
        distance_offset_km = (i * 15)
        lat_offset = distance_offset_km / 111.0
        lon_offset = distance_offset_km / 111.0
        
        if i % 2 == 0:
            lat_offset = -lat_offset
        if i % 3 == 0:
            lon_offset = -lon_offset
        
        mandi_lat = location_data['latitude'] + lat_offset
        mandi_lon = location_data['longitude'] + lon_offset
        
        mandi_lat = max(8.0, min(35.0, mandi_lat))
        mandi_lon = max(68.0, min(97.0, mandi_lon))
        
        mandi_price = MandiPrice(
            price_id=uuid.uuid4(),
            crop_name=crop_name,
            mandi_name=f"Mandi_{i}_{uuid.uuid4().hex[:6]}",
            state=location_data['state'],
            district=location_data['district'],
            latitude=mandi_lat,
            longitude=mandi_lon,
            price_per_quintal=2000.0 + (i * 100),
            price_date=date.today(),
            source='Test Data',
            created_at=datetime.utcnow()
        )
        test_db_session.add(mandi_price)
    
    test_db_session.commit()
    
    # Query without specifying radius (should use default 50km)
    service = MandiPriceService(test_db_session)
    results = service.get_current_price(crop_name, user_location)
    
    # Property: All results should be within 50km (default radius)
    for result in results:
        mandi = test_db_session.query(MandiPrice).filter(
            MandiPrice.mandi_name == result.mandi_name,
            MandiPrice.crop_name == crop_name
        ).first()
        
        if mandi and mandi.latitude and mandi.longitude:
            actual_distance = calculate_distance(
                user_location.latitude,
                user_location.longitude,
                mandi.latitude,
                mandi.longitude
            )
            
            assert actual_distance <= 50.1, \
                f"Mandi {result.mandi_name} at {actual_distance:.2f}km exceeds default radius 50km"


def test_mandi_price_specific_within_radius(test_db_session):
    """
    Specific example test: Mandis within radius should be returned.
    """
    # Create user location (Delhi)
    user_location = Location(
        id=uuid.uuid4(),
        state='Delhi',
        district='New Delhi',
        pincode='110001',
        latitude=28.6139,
        longitude=77.2090
    )
    test_db_session.add(user_location)
    test_db_session.flush()
    
    # Create nearby mandi (Gurgaon - approximately 30km from Delhi)
    nearby_mandi = MandiPrice(
        price_id=uuid.uuid4(),
        crop_name='rice',
        mandi_name='Gurgaon Mandi',
        state='Haryana',
        district='Gurgaon',
        latitude=28.4595,
        longitude=77.0266,
        price_per_quintal=2500.0,
        price_date=date.today(),
        source='Test',
        created_at=datetime.utcnow()
    )
    test_db_session.add(nearby_mandi)
    
    # Create far mandi (Jaipur - approximately 280km from Delhi)
    far_mandi = MandiPrice(
        price_id=uuid.uuid4(),
        crop_name='rice',
        mandi_name='Jaipur Mandi',
        state='Rajasthan',
        district='Jaipur',
        latitude=26.9124,
        longitude=75.7873,
        price_per_quintal=2400.0,
        price_date=date.today(),
        source='Test',
        created_at=datetime.utcnow()
    )
    test_db_session.add(far_mandi)
    
    test_db_session.commit()
    
    # Query with 50km radius
    service = MandiPriceService(test_db_session)
    results = service.get_current_price('rice', user_location, radius_km=50)
    
    # Should include nearby mandi
    mandi_names = [r.mandi_name for r in results]
    assert 'Gurgaon Mandi' in mandi_names, "Nearby mandi should be included"
    
    # Should NOT include far mandi
    assert 'Jaipur Mandi' not in mandi_names, "Far mandi should be excluded"


def test_mandi_price_specific_outside_radius(test_db_session):
    """
    Specific example test: Mandis outside radius should be excluded.
    """
    # Create user location (Mumbai)
    user_location = Location(
        id=uuid.uuid4(),
        state='Maharashtra',
        district='Mumbai',
        pincode='400001',
        latitude=19.0760,
        longitude=72.8777
    )
    test_db_session.add(user_location)
    test_db_session.flush()
    
    # Create very far mandi (Delhi - approximately 1400km from Mumbai)
    far_mandi = MandiPrice(
        price_id=uuid.uuid4(),
        crop_name='wheat',
        mandi_name='Delhi Mandi',
        state='Delhi',
        district='New Delhi',
        latitude=28.6139,
        longitude=77.2090,
        price_per_quintal=2200.0,
        price_date=date.today(),
        source='Test',
        created_at=datetime.utcnow()
    )
    test_db_session.add(far_mandi)
    
    test_db_session.commit()
    
    # Query with 50km radius
    service = MandiPriceService(test_db_session)
    results = service.get_current_price('wheat', user_location, radius_km=50)
    
    # Should NOT include far mandi
    mandi_names = [r.mandi_name for r in results]
    assert 'Delhi Mandi' not in mandi_names, "Far mandi should be excluded from results"


def test_mandi_price_distance_sorting(test_db_session):
    """
    Specific example test: Results should be sorted by distance.
    """
    # Create user location (Bangalore)
    user_location = Location(
        id=uuid.uuid4(),
        state='Karnataka',
        district='Bangalore',
        pincode='560001',
        latitude=12.9716,
        longitude=77.5946
    )
    test_db_session.add(user_location)
    test_db_session.flush()
    
    # Create mandis at different distances
    # Nearby mandi (~10km)
    mandi1 = MandiPrice(
        price_id=uuid.uuid4(),
        crop_name='rice',
        mandi_name='Nearby Mandi',
        state='Karnataka',
        district='Bangalore',
        latitude=12.9800,
        longitude=77.6000,
        price_per_quintal=2500.0,
        price_date=date.today(),
        source='Test',
        created_at=datetime.utcnow()
    )
    test_db_session.add(mandi1)
    
    # Medium distance mandi (~30km)
    mandi2 = MandiPrice(
        price_id=uuid.uuid4(),
        crop_name='rice',
        mandi_name='Medium Mandi',
        state='Karnataka',
        district='Bangalore',
        latitude=13.1500,
        longitude=77.7000,
        price_per_quintal=2450.0,
        price_date=date.today(),
        source='Test',
        created_at=datetime.utcnow()
    )
    test_db_session.add(mandi2)
    
    test_db_session.commit()
    
    # Query with 50km radius
    service = MandiPriceService(test_db_session)
    results = service.get_current_price('rice', user_location, radius_km=50)
    
    # Should have both mandis
    assert len(results) >= 2, "Should return multiple mandis"
    
    # First result should be closer than second
    if len(results) >= 2:
        assert results[0].distance_km < results[1].distance_km, \
            "Results should be sorted by distance (nearest first)"


def test_mandi_price_no_coordinates_same_district(test_db_session):
    """
    Edge case test: Mandis without coordinates in same district should be included.
    """
    # Create user location
    user_location = Location(
        id=uuid.uuid4(),
        state='Punjab',
        district='Ludhiana',
        pincode='141001',
        latitude=30.9010,
        longitude=75.8573
    )
    test_db_session.add(user_location)
    test_db_session.flush()
    
    # Create mandi without coordinates but same district
    mandi_no_coords = MandiPrice(
        price_id=uuid.uuid4(),
        crop_name='wheat',
        mandi_name='Local Mandi',
        state='Punjab',
        district='Ludhiana',
        latitude=None,
        longitude=None,
        price_per_quintal=2300.0,
        price_date=date.today(),
        source='Test',
        created_at=datetime.utcnow()
    )
    test_db_session.add(mandi_no_coords)
    
    test_db_session.commit()
    
    # Query
    service = MandiPriceService(test_db_session)
    results = service.get_current_price('wheat', user_location, radius_km=50)
    
    # Should include mandi from same district even without coordinates
    mandi_names = [r.mandi_name for r in results]
    assert 'Local Mandi' in mandi_names, \
        "Mandi from same district should be included even without coordinates"


def test_mandi_price_empty_results(test_db_session):
    """
    Edge case test: No mandis within radius should return empty list.
    """
    # Create user location
    user_location = Location(
        id=uuid.uuid4(),
        state='Kerala',
        district='Kochi',
        pincode='682001',
        latitude=9.9312,
        longitude=76.2673
    )
    test_db_session.add(user_location)
    test_db_session.flush()
    
    # Don't add any mandis
    test_db_session.commit()
    
    # Query
    service = MandiPriceService(test_db_session)
    results = service.get_current_price('rice', user_location, radius_km=50)
    
    # Should return empty list
    assert isinstance(results, list), "Should return a list"
    assert len(results) == 0, "Should return empty list when no mandis found"
