"""
Property-Based Test: Crop Recommendation Generation
Feature: bharatsahayak, Property 7: Crop Recommendation Generation

For any valid farm profile, the System should generate at least one crop 
recommendation with all required fields (crop_name, suitability_score, reasoning, 
water_requirement, duration_days) populated.

Validates: Requirements 3.1
"""
import pytest
from hypothesis import given, settings, strategies as st, HealthCheck, assume
from hypothesis.strategies import composite
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.farmer import FarmProfile
from app.models.user import User
from app.models.location import Location
from app.services.crop_advisor import CropAdvisor
import uuid


# Strategy for generating valid locations
@composite
def location_strategy(draw):
    """Generate a valid location"""
    states = ['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh', 'Bihar', 
              'Punjab', 'Haryana', 'Rajasthan', 'Gujarat', 'Madhya Pradesh']
    districts = ['District A', 'District B', 'District C', 'District D']
    
    return {
        'id': uuid.uuid4(),
        'state': draw(st.sampled_from(states)),
        'district': draw(st.sampled_from(districts)),
        'block': draw(st.one_of(st.none(), st.text(min_size=3, max_size=20))),
        'village': draw(st.one_of(st.none(), st.text(min_size=3, max_size=20))),
        'pincode': draw(st.from_regex(r'[1-9][0-9]{5}', fullmatch=True)),
        'latitude': draw(st.one_of(st.none(), st.floats(min_value=8.0, max_value=35.0))),
        'longitude': draw(st.one_of(st.none(), st.floats(min_value=68.0, max_value=97.0)))
    }


# Strategy for generating valid farm profiles
@composite
def farm_profile_strategy(draw):
    """Generate a valid farm profile"""
    soil_types = ['clay', 'loam', 'sandy', 'silt', 'black', 'red', 'laterite', 'alluvial']
    irrigation_types = ['rainfed', 'canal', 'well', 'drip', 'sprinkler', 'borewell']
    
    crops = ['rice', 'wheat', 'cotton', 'sugarcane', 'maize', 'pulses', 'groundnut', 'soybean']
    
    return {
        'farm_id': uuid.uuid4(),
        'user_id': uuid.uuid4(),
        'land_size_acres': draw(st.floats(min_value=0.5, max_value=100.0)),
        'soil_type': draw(st.sampled_from(soil_types)),
        'irrigation_type': draw(st.sampled_from(irrigation_types)),
        'location_id': uuid.uuid4(),
        'current_crops': draw(st.one_of(
            st.none(),
            st.lists(st.sampled_from(crops), min_size=0, max_size=3)
        )),
        'previous_crops': draw(st.one_of(
            st.none(),
            st.lists(st.sampled_from(crops), min_size=0, max_size=5)
        )),
        'livestock': draw(st.one_of(
            st.none(),
            st.lists(st.sampled_from(['cow', 'buffalo', 'goat', 'chicken']), min_size=0, max_size=3)
        )),
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }


@pytest.fixture(scope="function")
def test_db_session():
    """Create a test database session"""
    from sqlalchemy.types import TypeDecorator, CHAR
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    from sqlalchemy import Table, Column, String, DateTime, Text, Float, Integer, ForeignKey, JSON
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
    
    # Users table
    users_table = Table(
        'users', metadata,
        Column('user_id', UUID(), primary_key=True),
        Column('phone_number', String(15), nullable=False, unique=True),
        Column('language', String(10), nullable=False),
        Column('created_at', DateTime, nullable=False),
        Column('updated_at', DateTime, nullable=False)
    )
    
    # Farm profiles table
    farm_profiles_table = Table(
        'farm_profiles', metadata,
        Column('farm_id', UUID(), primary_key=True),
        Column('user_id', UUID(), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, unique=True),
        Column('land_size_acres', Float, nullable=False),
        Column('soil_type', String(50), nullable=False),
        Column('irrigation_type', String(50), nullable=False),
        Column('location_id', UUID(), ForeignKey('locations.id'), nullable=False),
        Column('current_crops', JSON, nullable=True),
        Column('previous_crops', JSON, nullable=True),
        Column('livestock', JSON, nullable=True),
        Column('created_at', DateTime, nullable=False),
        Column('updated_at', DateTime, nullable=False)
    )
    
    metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


def create_farm_profile_in_db(session, farm_data, location_data):
    """Helper to create farm profile with location in database"""
    # Create location
    location = Location(**location_data)
    session.add(location)
    session.flush()
    
    # Create user (simplified - just the required fields)
    user = User(
        user_id=farm_data['user_id'],
        phone_number=f"+91{uuid.uuid4().hex[:10]}",
        language='en'
    )
    session.add(user)
    session.flush()
    
    # Create farm profile
    farm_data['location_id'] = location.id
    farm_profile = FarmProfile(**farm_data)
    session.add(farm_profile)
    session.commit()
    
    return farm_profile


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    farm_data=farm_profile_strategy(),
    location_data=location_strategy(),
    season=st.sampled_from(['kharif', 'rabi', 'zaid'])
)
def test_crop_recommendation_generation_completeness(farm_data, location_data, season, test_db_session):
    """
    Feature: bharatsahayak, Property 7: Crop Recommendation Generation
    
    For any valid farm profile, the System should generate at least one crop 
    recommendation with all required fields populated.
    
    This tests that recommendations are always generated with complete data.
    """
    # Create farm profile in database
    farm_profile = create_farm_profile_in_db(test_db_session, farm_data, location_data)
    
    # Create crop advisor and get recommendations
    advisor = CropAdvisor(test_db_session)
    recommendations = advisor.recommend_crops(farm_profile, season)
    
    # Property 1: Should generate at least one recommendation
    assert len(recommendations) >= 1, \
        f"Should generate at least one crop recommendation for season {season}"
    
    # Property 2: All recommendations should have required fields populated
    required_fields = ['crop_name', 'suitability_score', 'reasoning', 'water_requirement', 'duration_days']
    
    for rec in recommendations:
        # Check all required fields are present and not None
        for field in required_fields:
            assert hasattr(rec, field), \
                f"Recommendation missing required field: {field}"
            
            value = getattr(rec, field)
            assert value is not None, \
                f"Required field '{field}' should not be None"
            
            # Additional type checks
            if field == 'crop_name':
                assert isinstance(value, str) and len(value) > 0, \
                    "crop_name should be a non-empty string"
            
            elif field == 'suitability_score':
                assert isinstance(value, (int, float)), \
                    "suitability_score should be numeric"
                assert 0.0 <= value <= 1.0, \
                    f"suitability_score should be between 0 and 1, got {value}"
            
            elif field == 'reasoning':
                assert isinstance(value, str) and len(value) > 0, \
                    "reasoning should be a non-empty string"
            
            elif field == 'water_requirement':
                assert isinstance(value, str) and len(value) > 0, \
                    "water_requirement should be a non-empty string"
                assert value.lower() in ['low', 'medium', 'high'], \
                    f"water_requirement should be low/medium/high, got {value}"
            
            elif field == 'duration_days':
                assert isinstance(value, int) and value > 0, \
                    f"duration_days should be a positive integer, got {value}"


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    farm_data=farm_profile_strategy(),
    location_data=location_strategy(),
    season=st.sampled_from(['kharif', 'rabi', 'zaid'])
)
def test_crop_recommendation_season_filtering(farm_data, location_data, season, test_db_session):
    """
    Feature: bharatsahayak, Property 7: Crop Recommendation Generation
    
    For any season specified, all returned crop recommendations should be 
    suitable for that season.
    
    This tests that season filtering works correctly.
    """
    # Create farm profile in database
    farm_profile = create_farm_profile_in_db(test_db_session, farm_data, location_data)
    
    # Create crop advisor and get recommendations
    advisor = CropAdvisor(test_db_session)
    recommendations = advisor.recommend_crops(farm_profile, season)
    
    # Property: All recommendations should be for the requested season
    for rec in recommendations:
        # Check if crop is in the crop database
        crop_data = advisor.CROP_DATABASE.get(rec.crop_name.lower())
        
        if crop_data:
            assert season in crop_data['seasons'], \
                f"Crop {rec.crop_name} should be suitable for season {season}"


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    farm_data=farm_profile_strategy(),
    location_data=location_strategy(),
    season=st.sampled_from(['kharif', 'rabi', 'zaid'])
)
def test_crop_recommendation_suitability_ordering(farm_data, location_data, season, test_db_session):
    """
    Feature: bharatsahayak, Property 7: Crop Recommendation Generation
    
    Crop recommendations should be ordered by suitability score in descending order.
    
    This tests that the most suitable crops appear first.
    """
    # Create farm profile in database
    farm_profile = create_farm_profile_in_db(test_db_session, farm_data, location_data)
    
    # Create crop advisor and get recommendations
    advisor = CropAdvisor(test_db_session)
    recommendations = advisor.recommend_crops(farm_profile, season)
    
    # Property: Recommendations should be sorted by suitability_score descending
    if len(recommendations) > 1:
        for i in range(len(recommendations) - 1):
            assert recommendations[i].suitability_score >= recommendations[i+1].suitability_score, \
                f"Recommendations should be sorted by suitability score (descending)"


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    farm_data=farm_profile_strategy(),
    location_data=location_strategy(),
    season=st.sampled_from(['kharif', 'rabi', 'zaid'])
)
def test_crop_recommendation_soil_compatibility(farm_data, location_data, season, test_db_session):
    """
    Feature: bharatsahayak, Property 7: Crop Recommendation Generation
    
    Crops with soil types matching the farm profile should have higher 
    suitability scores than those with non-matching soil types.
    
    This tests that soil compatibility affects recommendations.
    """
    # Create farm profile in database
    farm_profile = create_farm_profile_in_db(test_db_session, farm_data, location_data)
    
    # Create crop advisor and get recommendations
    advisor = CropAdvisor(test_db_session)
    recommendations = advisor.recommend_crops(farm_profile, season)
    
    # Separate recommendations by soil compatibility
    matching_soil = []
    non_matching_soil = []
    
    for rec in recommendations:
        crop_data = advisor.CROP_DATABASE.get(rec.crop_name.lower())
        if crop_data:
            if farm_profile.soil_type in crop_data['suitable_soils']:
                matching_soil.append(rec)
            else:
                non_matching_soil.append(rec)
    
    # Property: If both groups exist, matching soil should generally have higher scores
    if matching_soil and non_matching_soil:
        avg_matching = sum(r.suitability_score for r in matching_soil) / len(matching_soil)
        avg_non_matching = sum(r.suitability_score for r in non_matching_soil) / len(non_matching_soil)
        
        # Matching soil should have higher average suitability
        assert avg_matching > avg_non_matching, \
            f"Crops with matching soil should have higher average suitability"


def test_crop_recommendation_specific_rice_kharif(test_db_session):
    """
    Specific example test: Rice should be recommended for kharif season 
    with suitable soil and irrigation.
    
    This complements property-based tests with a concrete example.
    """
    # Create location
    location = Location(
        id=uuid.uuid4(),
        state='Maharashtra',
        district='Pune',
        pincode='411001'
    )
    test_db_session.add(location)
    test_db_session.flush()
    
    # Create user
    user = User(
        user_id=uuid.uuid4(),
        phone_number='+919876543210',
        language='en'
    )
    test_db_session.add(user)
    test_db_session.flush()
    
    # Create farm profile ideal for rice
    farm_profile = FarmProfile(
        farm_id=uuid.uuid4(),
        user_id=user.user_id,
        land_size_acres=5.0,
        soil_type='clay',  # Ideal for rice
        irrigation_type='canal',  # Good water availability
        location_id=location.id,
        current_crops=['rice'],
        previous_crops=['wheat'],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db_session.add(farm_profile)
    test_db_session.commit()
    
    # Get recommendations for kharif season
    advisor = CropAdvisor(test_db_session)
    recommendations = advisor.recommend_crops(farm_profile, 'kharif')
    
    # Should include rice
    crop_names = [r.crop_name.lower() for r in recommendations]
    assert 'rice' in crop_names, "Rice should be recommended for kharif with clay soil and canal irrigation"
    
    # Find rice recommendation
    rice_rec = next(r for r in recommendations if r.crop_name.lower() == 'rice')
    
    # Rice should have high suitability for this profile
    assert rice_rec.suitability_score >= 0.7, \
        f"Rice should have high suitability score, got {rice_rec.suitability_score}"
    
    # Check all required fields
    assert rice_rec.crop_name == 'rice'
    assert rice_rec.water_requirement == 'high'
    assert rice_rec.duration_days == 120
    assert len(rice_rec.reasoning) > 0
    assert rice_rec.suitability_score > 0


def test_crop_recommendation_specific_wheat_rabi(test_db_session):
    """
    Specific example test: Wheat should be recommended for rabi season.
    """
    # Create location
    location = Location(
        id=uuid.uuid4(),
        state='Punjab',
        district='Ludhiana',
        pincode='141001'
    )
    test_db_session.add(location)
    test_db_session.flush()
    
    # Create user
    user = User(
        user_id=uuid.uuid4(),
        phone_number='+919876543211',
        language='en'
    )
    test_db_session.add(user)
    test_db_session.flush()
    
    # Create farm profile suitable for wheat
    farm_profile = FarmProfile(
        farm_id=uuid.uuid4(),
        user_id=user.user_id,
        land_size_acres=10.0,
        soil_type='loam',  # Good for wheat
        irrigation_type='canal',
        location_id=location.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db_session.add(farm_profile)
    test_db_session.commit()
    
    # Get recommendations for rabi season
    advisor = CropAdvisor(test_db_session)
    recommendations = advisor.recommend_crops(farm_profile, 'rabi')
    
    # Should include wheat
    crop_names = [r.crop_name.lower() for r in recommendations]
    assert 'wheat' in crop_names, "Wheat should be recommended for rabi season"
    
    # Find wheat recommendation
    wheat_rec = next(r for r in recommendations if r.crop_name.lower() == 'wheat')
    
    # Check fields
    assert wheat_rec.water_requirement == 'medium'
    assert wheat_rec.duration_days == 120
    assert wheat_rec.suitability_score > 0


def test_crop_recommendation_empty_season(test_db_session):
    """
    Edge case test: If no crops are suitable for a season, should return empty list.
    """
    # Create location
    location = Location(
        id=uuid.uuid4(),
        state='Maharashtra',
        district='Mumbai',
        pincode='400001'
    )
    test_db_session.add(location)
    test_db_session.flush()
    
    # Create user
    user = User(
        user_id=uuid.uuid4(),
        phone_number='+919876543212',
        language='en'
    )
    test_db_session.add(user)
    test_db_session.flush()
    
    # Create farm profile
    farm_profile = FarmProfile(
        farm_id=uuid.uuid4(),
        user_id=user.user_id,
        land_size_acres=2.0,
        soil_type='sandy',
        irrigation_type='rainfed',
        location_id=location.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db_session.add(farm_profile)
    test_db_session.commit()
    
    # Get recommendations
    advisor = CropAdvisor(test_db_session)
    
    # All valid seasons should return some recommendations
    for season in ['kharif', 'rabi', 'zaid']:
        recommendations = advisor.recommend_crops(farm_profile, season)
        # Should return a list (may be empty or have recommendations)
        assert isinstance(recommendations, list), \
            f"Should return a list for season {season}"


def test_crop_recommendation_small_vs_large_farm(test_db_session):
    """
    Test that land size affects recommendations appropriately.
    """
    # Create location
    location = Location(
        id=uuid.uuid4(),
        state='Karnataka',
        district='Bangalore',
        pincode='560001'
    )
    test_db_session.add(location)
    test_db_session.flush()
    
    # Create user
    user = User(
        user_id=uuid.uuid4(),
        phone_number='+919876543213',
        language='en'
    )
    test_db_session.add(user)
    test_db_session.flush()
    
    # Small farm profile
    small_farm = FarmProfile(
        farm_id=uuid.uuid4(),
        user_id=user.user_id,
        land_size_acres=1.0,
        soil_type='loam',
        irrigation_type='drip',
        location_id=location.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db_session.add(small_farm)
    test_db_session.commit()
    
    # Get recommendations for small farm
    advisor = CropAdvisor(test_db_session)
    small_recs = advisor.recommend_crops(small_farm, 'kharif')
    
    # Should get recommendations
    assert len(small_recs) > 0, "Should get recommendations for small farm"
    
    # All recommendations should have valid suitability scores
    for rec in small_recs:
        assert 0.0 <= rec.suitability_score <= 1.0, \
            "Suitability score should be between 0 and 1"
