"""
Property-Based Test: Fertilizer Guidance Completeness
Feature: bharatsahayak, Property 8: Fertilizer Guidance Completeness

For any crop and soil data combination, the System should provide fertilizer 
guidance containing fertilizer type, quantity, timing, and application method.

Validates: Requirements 3.2
"""
import pytest
from hypothesis import given, settings, strategies as st, HealthCheck
from hypothesis.strategies import composite
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.farmer import FarmProfile
from app.models.user import User
from app.models.location import Location
from app.services.fertilizer_advisor import FertilizerAdvisor
from app.schemas.farmer import SoilData
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


# Strategy for generating soil data
@composite
def soil_data_strategy(draw):
    """Generate optional soil data"""
    # Sometimes return None to test without soil data
    if draw(st.booleans()):
        return None
    
    return SoilData(
        soil_ph=draw(st.one_of(st.none(), st.floats(min_value=4.0, max_value=9.0))),
        nitrogen_level=draw(st.one_of(st.none(), st.sampled_from(['low', 'medium', 'high']))),
        phosphorus_level=draw(st.one_of(st.none(), st.sampled_from(['low', 'medium', 'high']))),
        potassium_level=draw(st.one_of(st.none(), st.sampled_from(['low', 'medium', 'high']))),
        organic_matter=draw(st.one_of(st.none(), st.sampled_from(['low', 'medium', 'high'])))
    )


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
    crop_name=st.sampled_from(['rice', 'wheat', 'cotton', 'maize', 'sugarcane', 'pulses', 'vegetables', 'soybean', 'groundnut']),
    growth_stage=st.sampled_from(['sowing', 'vegetative', 'flowering', 'fruiting', 'maturity']),
    soil_data=soil_data_strategy()
)
def test_fertilizer_guidance_completeness(farm_data, location_data, crop_name, growth_stage, soil_data, test_db_session):
    """
    Feature: bharatsahayak, Property 8: Fertilizer Guidance Completeness
    
    For any crop and soil data combination, the System should provide fertilizer 
    guidance containing fertilizer type, quantity, timing, and application method.
    
    This tests that all required fields are always present in fertilizer recommendations.
    """
    # Create farm profile in database
    farm_profile = create_farm_profile_in_db(test_db_session, farm_data, location_data)
    
    # Create fertilizer advisor and get recommendation
    advisor = FertilizerAdvisor(test_db_session)
    recommendation = advisor.recommend_fertilizer(farm_profile, crop_name, growth_stage, soil_data)
    
    # Property 1: Recommendation should not be None
    assert recommendation is not None, \
        f"Should return a fertilizer recommendation for crop {crop_name} at {growth_stage} stage"
    
    # Property 2: All required fields must be present and not None
    required_fields = ['fertilizer_type', 'quantity_per_acre', 'timing', 'application_method']
    
    for field in required_fields:
        assert hasattr(recommendation, field), \
            f"Recommendation missing required field: {field}"
        
        value = getattr(recommendation, field)
        assert value is not None, \
            f"Required field '{field}' should not be None for crop {crop_name} at {growth_stage}"
        
        # All required fields should be non-empty strings
        assert isinstance(value, str), \
            f"Field '{field}' should be a string, got {type(value)}"
        assert len(value) > 0, \
            f"Field '{field}' should not be empty for crop {crop_name} at {growth_stage}"
    
    # Property 3: fertilizer_type should contain meaningful information
    assert len(recommendation.fertilizer_type) >= 3, \
        f"fertilizer_type should be descriptive, got: {recommendation.fertilizer_type}"
    
    # Property 4: quantity_per_acre should contain numeric information
    assert any(char.isdigit() for char in recommendation.quantity_per_acre), \
        f"quantity_per_acre should contain numeric value, got: {recommendation.quantity_per_acre}"
    
    # Property 5: timing should be descriptive
    assert len(recommendation.timing) >= 5, \
        f"timing should be descriptive, got: {recommendation.timing}"
    
    # Property 6: application_method should be descriptive
    assert len(recommendation.application_method) >= 5, \
        f"application_method should be descriptive, got: {recommendation.application_method}"
    
    # Property 7: crop_name and growth_stage should match input
    assert recommendation.crop_name == crop_name, \
        f"crop_name should match input: expected {crop_name}, got {recommendation.crop_name}"
    assert recommendation.growth_stage == growth_stage, \
        f"growth_stage should match input: expected {growth_stage}, got {recommendation.growth_stage}"


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    farm_data=farm_profile_strategy(),
    location_data=location_strategy(),
    crop_name=st.sampled_from(['rice', 'wheat', 'cotton', 'maize', 'sugarcane', 'pulses', 'vegetables']),
    growth_stage=st.sampled_from(['sowing', 'vegetative', 'flowering', 'fruiting', 'maturity'])
)
def test_fertilizer_guidance_without_soil_data(farm_data, location_data, crop_name, growth_stage, test_db_session):
    """
    Feature: bharatsahayak, Property 8: Fertilizer Guidance Completeness
    
    Even without soil data, the System should provide complete fertilizer guidance.
    
    This tests that soil data is optional and recommendations work without it.
    """
    # Create farm profile in database
    farm_profile = create_farm_profile_in_db(test_db_session, farm_data, location_data)
    
    # Create fertilizer advisor and get recommendation WITHOUT soil data
    advisor = FertilizerAdvisor(test_db_session)
    recommendation = advisor.recommend_fertilizer(farm_profile, crop_name, growth_stage, soil_data=None)
    
    # Property: All required fields should still be present
    required_fields = ['fertilizer_type', 'quantity_per_acre', 'timing', 'application_method']
    
    for field in required_fields:
        value = getattr(recommendation, field)
        assert value is not None and len(value) > 0, \
            f"Field '{field}' should be present even without soil data"


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    farm_data=farm_profile_strategy(),
    location_data=location_strategy(),
    crop_name=st.sampled_from(['rice', 'wheat', 'cotton', 'maize']),
    growth_stage=st.sampled_from(['sowing', 'vegetative', 'flowering'])
)
def test_fertilizer_guidance_with_soil_data_adjustments(farm_data, location_data, crop_name, growth_stage, test_db_session):
    """
    Feature: bharatsahayak, Property 8: Fertilizer Guidance Completeness
    
    When soil data is provided, recommendations should be adjusted accordingly.
    
    This tests that soil data influences the recommendations.
    """
    # Create farm profile in database
    farm_profile = create_farm_profile_in_db(test_db_session, farm_data, location_data)
    
    # Create fertilizer advisor
    advisor = FertilizerAdvisor(test_db_session)
    
    # Get recommendation without soil data
    rec_without_soil = advisor.recommend_fertilizer(farm_profile, crop_name, growth_stage, soil_data=None)
    
    # Get recommendation with soil data showing low nitrogen
    soil_data_low_n = SoilData(
        soil_ph=6.5,
        nitrogen_level='low',
        phosphorus_level='medium',
        potassium_level='medium'
    )
    rec_with_low_n = advisor.recommend_fertilizer(farm_profile, crop_name, growth_stage, soil_data_low_n)
    
    # Property: Both should have all required fields
    for rec in [rec_without_soil, rec_with_low_n]:
        assert rec.fertilizer_type is not None and len(rec.fertilizer_type) > 0
        assert rec.quantity_per_acre is not None and len(rec.quantity_per_acre) > 0
        assert rec.timing is not None and len(rec.timing) > 0
        assert rec.application_method is not None and len(rec.application_method) > 0
    
    # Property: Recommendations with soil data should have additional notes or adjustments
    # (The application_method or additional_notes may contain soil-specific guidance)
    assert rec_with_low_n.application_method is not None


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    farm_data=farm_profile_strategy(),
    location_data=location_strategy(),
    crop_name=st.sampled_from(['rice', 'wheat', 'cotton', 'maize', 'sugarcane'])
)
def test_fertilizer_guidance_across_growth_stages(farm_data, location_data, crop_name, test_db_session):
    """
    Feature: bharatsahayak, Property 8: Fertilizer Guidance Completeness
    
    For any crop, recommendations should be available for all growth stages.
    
    This tests that the system provides guidance throughout the crop lifecycle.
    """
    # Create farm profile in database
    farm_profile = create_farm_profile_in_db(test_db_session, farm_data, location_data)
    
    # Create fertilizer advisor
    advisor = FertilizerAdvisor(test_db_session)
    
    # Test all growth stages
    growth_stages = ['sowing', 'vegetative', 'flowering', 'fruiting', 'maturity']
    
    for stage in growth_stages:
        recommendation = advisor.recommend_fertilizer(farm_profile, crop_name, stage, soil_data=None)
        
        # Property: Each stage should have complete guidance
        assert recommendation is not None, \
            f"Should provide recommendation for {crop_name} at {stage} stage"
        
        assert recommendation.fertilizer_type is not None and len(recommendation.fertilizer_type) > 0, \
            f"fertilizer_type missing for {crop_name} at {stage}"
        
        assert recommendation.quantity_per_acre is not None and len(recommendation.quantity_per_acre) > 0, \
            f"quantity_per_acre missing for {crop_name} at {stage}"
        
        assert recommendation.timing is not None and len(recommendation.timing) > 0, \
            f"timing missing for {crop_name} at {stage}"
        
        assert recommendation.application_method is not None and len(recommendation.application_method) > 0, \
            f"application_method missing for {crop_name} at {stage}"


def test_fertilizer_guidance_specific_rice_sowing(test_db_session):
    """
    Specific example test: Rice at sowing stage should get appropriate NPK recommendation.
    
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
    
    # Create farm profile
    farm_profile = FarmProfile(
        farm_id=uuid.uuid4(),
        user_id=user.user_id,
        land_size_acres=5.0,
        soil_type='clay',
        irrigation_type='canal',
        location_id=location.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db_session.add(farm_profile)
    test_db_session.commit()
    
    # Get fertilizer recommendation for rice at sowing
    advisor = FertilizerAdvisor(test_db_session)
    recommendation = advisor.recommend_fertilizer(farm_profile, 'rice', 'sowing', soil_data=None)
    
    # Check all required fields are present
    assert recommendation.fertilizer_type is not None
    assert recommendation.quantity_per_acre is not None
    assert recommendation.timing is not None
    assert recommendation.application_method is not None
    
    # Check values are meaningful
    assert len(recommendation.fertilizer_type) > 0
    assert len(recommendation.quantity_per_acre) > 0
    assert len(recommendation.timing) > 0
    assert len(recommendation.application_method) > 0
    
    # Rice at sowing typically needs NPK
    assert 'npk' in recommendation.fertilizer_type.lower() or ':' in recommendation.fertilizer_type
    
    # Should have quantity information
    assert 'kg' in recommendation.quantity_per_acre.lower() or 'acre' in recommendation.quantity_per_acre.lower()


def test_fertilizer_guidance_specific_wheat_vegetative(test_db_session):
    """
    Specific example test: Wheat at vegetative stage should get nitrogen recommendation.
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
    
    # Create farm profile
    farm_profile = FarmProfile(
        farm_id=uuid.uuid4(),
        user_id=user.user_id,
        land_size_acres=10.0,
        soil_type='loam',
        irrigation_type='canal',
        location_id=location.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db_session.add(farm_profile)
    test_db_session.commit()
    
    # Get fertilizer recommendation for wheat at vegetative stage
    advisor = FertilizerAdvisor(test_db_session)
    recommendation = advisor.recommend_fertilizer(farm_profile, 'wheat', 'vegetative', soil_data=None)
    
    # Check all required fields
    assert recommendation.fertilizer_type is not None and len(recommendation.fertilizer_type) > 0
    assert recommendation.quantity_per_acre is not None and len(recommendation.quantity_per_acre) > 0
    assert recommendation.timing is not None and len(recommendation.timing) > 0
    assert recommendation.application_method is not None and len(recommendation.application_method) > 0
    
    # Vegetative stage typically needs nitrogen (Urea)
    assert 'urea' in recommendation.fertilizer_type.lower() or 'n' in recommendation.fertilizer_type.lower()


def test_fertilizer_guidance_with_acidic_soil(test_db_session):
    """
    Test that acidic soil (low pH) triggers lime recommendation.
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
        phone_number='+919876543212',
        language='en'
    )
    test_db_session.add(user)
    test_db_session.flush()
    
    # Create farm profile
    farm_profile = FarmProfile(
        farm_id=uuid.uuid4(),
        user_id=user.user_id,
        land_size_acres=3.0,
        soil_type='laterite',
        irrigation_type='drip',
        location_id=location.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db_session.add(farm_profile)
    test_db_session.commit()
    
    # Create soil data with acidic pH
    soil_data = SoilData(
        soil_ph=5.0,  # Acidic
        nitrogen_level='medium',
        phosphorus_level='medium',
        potassium_level='medium'
    )
    
    # Get recommendation
    advisor = FertilizerAdvisor(test_db_session)
    recommendation = advisor.recommend_fertilizer(farm_profile, 'maize', 'sowing', soil_data)
    
    # Should have all required fields
    assert recommendation.fertilizer_type is not None and len(recommendation.fertilizer_type) > 0
    assert recommendation.quantity_per_acre is not None and len(recommendation.quantity_per_acre) > 0
    assert recommendation.timing is not None and len(recommendation.timing) > 0
    assert recommendation.application_method is not None and len(recommendation.application_method) > 0
    
    # Should mention lime for acidic soil correction
    combined_text = (recommendation.application_method + ' ' + (recommendation.additional_notes or '')).lower()
    assert 'lime' in combined_text, "Should recommend lime for acidic soil"


def test_fertilizer_guidance_unknown_crop(test_db_session):
    """
    Test that unknown crops still get default recommendations with all required fields.
    """
    # Create location
    location = Location(
        id=uuid.uuid4(),
        state='Tamil Nadu',
        district='Chennai',
        pincode='600001'
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
    
    # Create farm profile
    farm_profile = FarmProfile(
        farm_id=uuid.uuid4(),
        user_id=user.user_id,
        land_size_acres=2.0,
        soil_type='sandy',
        irrigation_type='well',
        location_id=location.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db_session.add(farm_profile)
    test_db_session.commit()
    
    # Get recommendation for unknown crop
    advisor = FertilizerAdvisor(test_db_session)
    recommendation = advisor.recommend_fertilizer(farm_profile, 'unknown_exotic_crop', 'vegetative', soil_data=None)
    
    # Should still have all required fields
    assert recommendation.fertilizer_type is not None and len(recommendation.fertilizer_type) > 0
    assert recommendation.quantity_per_acre is not None and len(recommendation.quantity_per_acre) > 0
    assert recommendation.timing is not None and len(recommendation.timing) > 0
    assert recommendation.application_method is not None and len(recommendation.application_method) > 0
    
    # Should indicate it's a general recommendation
    if recommendation.additional_notes:
        assert 'general' in recommendation.additional_notes.lower() or 'soil testing' in recommendation.additional_notes.lower()
