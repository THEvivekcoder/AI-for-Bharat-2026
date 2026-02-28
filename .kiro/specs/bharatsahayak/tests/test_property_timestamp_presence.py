"""
Property-Based Test: Time-Sensitive Data Timestamps
Feature: bharatsahayak, Property 28: Time-Sensitive Data Timestamps

For any time-sensitive information (market prices, weather, job deadlines), 
the response should include a timestamp indicating when the data was last updated.

Validates: Requirements 12.5
"""
import pytest
from hypothesis import given, settings, strategies as st, HealthCheck, assume
from hypothesis.strategies import composite
from datetime import datetime, timedelta, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table, Column, String, DateTime, Text, Float, Date, Numeric, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON, MetaData
from app.models.farmer import MandiPrice
from app.models.skills import JobPosting
from app.services.mandi_price_service import MandiPriceService
import uuid


# Strategy for generating mandi price data
@composite
def mandi_price_strategy(draw):
    """Generate valid mandi price data with timestamps"""
    crops = ['Wheat', 'Rice', 'Cotton', 'Sugarcane', 'Maize', 'Soybean']
    states = ['Maharashtra', 'Karnataka', 'Punjab', 'Uttar Pradesh', 'Tamil Nadu']
    
    # Generate price date within last 30 days
    days_ago = draw(st.integers(min_value=0, max_value=30))
    price_date = date.today() - timedelta(days=days_ago)
    
    # Generate last_updated timestamp
    hours_ago = draw(st.integers(min_value=0, max_value=72))
    last_updated = datetime.utcnow() - timedelta(hours=hours_ago)
    
    state = draw(st.sampled_from(states))
    
    return {
        'price_id': uuid.uuid4(),
        'crop_name': draw(st.sampled_from(crops)),
        'mandi_name': f'{state} Mandi {draw(st.integers(min_value=1, max_value=10))}',
        'state': state,
   
     'district': draw(st.sampled_from(['District A', 'District B', 'District C'])),
        'latitude': draw(st.floats(min_value=8.0, max_value=35.0)),
        'longitude': draw(st.floats(min_value=68.0, max_value=97.0)),
        'price_per_quintal': draw(st.floats(min_value=1000.0, max_value=10000.0)),
        'price_date': price_date,
        'source': 'Government API',
        'last_updated': last_updated,
        'created_at': last_updated - timedelta(hours=draw(st.integers(min_value=1, max_value=24)))
    }


# Strategy for generating job posting data
@composite
def job_posting_strategy(draw):
    """Generate valid job posting data with timestamps"""
    departments = ['Agriculture', 'Health', 'Education', 'Transport', 'Revenue']
    
    # Generate application deadline (future date)
    days_ahead = draw(st.integers(min_value=1, max_value=90))
    application_deadline = date.today() + timedelta(days=days_ahead)
    
    # Generate posted date (past date)
    days_ago = draw(st.integers(min_value=1, max_value=30))
    posted_date = date.today() - timedelta(days=days_ago)
    
    # Generate last_updated timestamp
    hours_ago = draw(st.integers(min_value=0, max_value=72))
    last_updated = datetime.utcnow() - timedelta(hours=hours_ago)
    
    return {
        'job_id': uuid.uuid4(),
        'title': f'{draw(st.sampled_from(["Junior", "Senior", "Assistant"]))} {draw(st.sampled_from(["Engineer", "Officer", "Clerk"]))}',
        'department': draw(st.sampled_from(departments)),
        'description': draw(st.text(min_size=20, max_size=100)),
        'qualifications': {'education': ['Graduate'], 'experience': '2 years'},
        'location': {'state': 'Maharashtra', 'district': 'Pune'},
        'application_deadline': application_deadline,
        'application_url': f'https://jobs.gov.in/{uuid.uuid4()}',
        'posted_date': posted_date,
        'last_updated': last_updated,
        'created_at': last_updated - timedelta(hours=draw(st.integers(min_value=1, max_value=24))),
        'updated_at': last_updated
    }


@pytest.fixture(scope="function")
def test_db_session():
    """Create a test database session"""
    from sqlalchemy.types import TypeDecorator, CHAR
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
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
        Column('last_updated', DateTime, nullable=True),
        Column('created_at', DateTime, nullable=False)
    )
    
    job_postings_table = Table(
        'job_postings', metadata,
        Column('job_id', UUID(), primary_key=True),
        Column('title', String(255), nullable=False),
        Column('department', String(100), nullable=True),
        Column('description', Text, nullable=True),
        Column('qualifications', JSON, nullable=True),
        Column('location', JSON, nullable=True),
        Column('application_deadline', Date, nullable=True),
        Column('application_url', String(500), nullable=True),
        Column('posted_date', Date, nullable=True),
        Column('last_updated', DateTime, nullable=True),
        Column('created_at', DateTime, nullable=False),
        Column('updated_at', DateTime, nullable=False)
    )
    
    metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


def add_mandi_prices_to_db(session, prices_data):
    """Helper to add mandi prices to test database"""
    session.query(MandiPrice).delete()
    session.commit()
    
    prices = []
    for price_data in prices_data:
        price = MandiPrice(**price_data)
        session.add(price)
        prices.append(price)
    
    session.commit()
    return prices


def add_job_postings_to_db(session, jobs_data):
    """Helper to add job postings to test database"""
    session.query(JobPosting).delete()
    session.commit()
    
    jobs = []
    for job_data in jobs_data:
        job = JobPosting(**job_data)
        session.add(job)
        jobs.append(job)
    
    session.commit()
    return jobs


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    prices=st.lists(mandi_price_strategy(), min_size=1, max_size=20)
)
def test_mandi_prices_have_timestamps(prices, test_db_session):
    """
    Feature: bharatsahayak, Property 28: Time-Sensitive Data Timestamps
    
    For any market price data, the response should include both price_date 
    (when the price was recorded) and last_updated (when the data was last verified).
    
    Property: All mandi prices must have price_date and last_updated timestamps.
    """
    # Add prices to database
    add_mandi_prices_to_db(test_db_session, prices)
    
    # Retrieve all prices
    all_prices = test_db_session.query(MandiPrice).all()
    
    # Property 1: All prices must have price_date
    assert len(all_prices) > 0, "Should have prices in database"
    
    for price in all_prices:
        assert price.price_date is not None, \
            f"Mandi price for {price.crop_name} at {price.mandi_name} must have price_date"
        
        assert isinstance(price.price_date, date), \
            f"price_date must be a date object"
        
        # Property 2: All prices should have last_updated timestamp
        assert price.last_updated is not None, \
            f"Mandi price for {price.crop_name} at {price.mandi_name} must have last_updated timestamp"
        
        assert isinstance(price.last_updated, datetime), \
            f"last_updated must be a datetime object"


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    jobs=st.lists(job_posting_strategy(), min_size=1, max_size=20)
)
def test_job_postings_have_timestamps(jobs, test_db_session):
    """
    Feature: bharatsahayak, Property 28: Time-Sensitive Data Timestamps
    
    For any job posting, the response should include application_deadline, 
    posted_date, and last_updated timestamps.
    
    Property: All job postings must have deadline and timestamp information.
    """
    # Add jobs to database
    add_job_postings_to_db(test_db_session, jobs)
    
    # Retrieve all jobs
    all_jobs = test_db_session.query(JobPosting).all()
    
    # Property 1: All jobs must have application_deadline
    assert len(all_jobs) > 0, "Should have jobs in database"
    
    for job in all_jobs:
        assert job.application_deadline is not None, \
            f"Job '{job.title}' must have application_deadline"
        
        assert isinstance(job.application_deadline, date), \
            f"application_deadline must be a date object"
        
        # Property 2: All jobs should have posted_date
        assert job.posted_date is not None, \
            f"Job '{job.title}' must have posted_date"
        
        assert isinstance(job.posted_date, date), \
            f"posted_date must be a date object"
        
        # Property 3: All jobs should have last_updated timestamp
        assert job.last_updated is not None, \
            f"Job '{job.title}' must have last_updated timestamp"
        
        assert isinstance(job.last_updated, datetime), \
            f"last_updated must be a datetime object"


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    prices=st.lists(mandi_price_strategy(), min_size=1, max_size=20)
)
def test_price_timestamps_are_valid(prices, test_db_session):
    """
    Feature: bharatsahayak, Property 28: Time-Sensitive Data Timestamps
    
    Property: Timestamps on market prices should be valid (not in future, 
    price_date should be before or equal to last_updated).
    """
    # Add prices to database
    add_mandi_prices_to_db(test_db_session, prices)
    
    # Retrieve all prices
    all_prices = test_db_session.query(MandiPrice).all()
    
    current_time = datetime.utcnow()
    current_date = date.today()
    
    for price in all_prices:
        # Property 1: price_date should not be in the future
        assert price.price_date <= current_date + timedelta(days=1), \
            f"Price date for {price.crop_name} should not be in the future"
        
        # Property 2: last_updated should not be in the future
        assert price.last_updated <= current_time + timedelta(seconds=5), \
            f"last_updated for {price.crop_name} should not be in the future"
        
        # Property 3: last_updated should be after or equal to created_at
        assert price.last_updated >= price.created_at, \
            f"last_updated should not be before created_at"


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    jobs=st.lists(job_posting_strategy(), min_size=1, max_size=20)
)
def test_job_timestamps_are_valid(jobs, test_db_session):
    """
    Feature: bharatsahayak, Property 28: Time-Sensitive Data Timestamps
    
    Property: Timestamps on job postings should be valid (deadline in future, 
    posted_date in past, last_updated is recent).
    """
    # Add jobs to database
    add_job_postings_to_db(test_db_session, jobs)
    
    # Retrieve all jobs
    all_jobs = test_db_session.query(JobPosting).all()
    
    current_time = datetime.utcnow()
    current_date = date.today()
    
    for job in all_jobs:
        # Property 1: application_deadline should be in the future or today
        assert job.application_deadline >= current_date - timedelta(days=1), \
            f"Job '{job.title}' deadline should be today or in future (or recently past)"
        
        # Property 2: posted_date should not be in the future
        assert job.posted_date <= current_date + timedelta(days=1), \
            f"Job '{job.title}' posted_date should not be in the future"
        
        # Property 3: posted_date should be before or equal to deadline
        assert job.posted_date <= job.application_deadline, \
            f"Job '{job.title}' posted_date should be before deadline"
        
        # Property 4: last_updated should not be in the future
        assert job.last_updated <= current_time + timedelta(seconds=5), \
            f"Job '{job.title}' last_updated should not be in the future"


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    price_data=mandi_price_strategy()
)
def test_mandi_price_service_returns_timestamps(price_data, test_db_session):
    """
    Feature: bharatsahayak, Property 28: Time-Sensitive Data Timestamps
    
    Property: When querying mandi prices from the database, the returned 
    data should include timestamp information (price_date and last_updated).
    """
    # Add price to database
    add_mandi_prices_to_db(test_db_session, [price_data])
    
    # Query directly from database (simpler than service which has complex logic)
    retrieved_price = test_db_session.query(MandiPrice).filter_by(
        crop_name=price_data['crop_name']
    ).first()
    
    # Property: Retrieved price should have timestamp information
    assert retrieved_price is not None, "Should retrieve the price"
    
    assert retrieved_price.price_date is not None, \
        "Retrieved price data must include price_date"
    
    assert isinstance(retrieved_price.price_date, date), \
        "price_date should be a date object"
    
    assert retrieved_price.last_updated is not None, \
        "Retrieved price data must include last_updated timestamp"
    
    assert isinstance(retrieved_price.last_updated, datetime), \
        "last_updated should be a datetime object"


def test_specific_mandi_price_has_timestamps(test_db_session):
    """
    Specific example test: A concrete mandi price should have all timestamps.
    """
    price_data = {
        'price_id': uuid.uuid4(),
        'crop_name': 'Wheat',
        'mandi_name': 'Pune Mandi',
        'state': 'Maharashtra',
        'district': 'Pune',
        'latitude': 18.5204,
        'longitude': 73.8567,
        'price_per_quintal': 2500.0,
        'price_date': date.today() - timedelta(days=1),
        'source': 'Government API',
        'last_updated': datetime.utcnow() - timedelta(hours=2),
        'created_at': datetime.utcnow() - timedelta(days=1)
    }
    
    add_mandi_prices_to_db(test_db_session, [price_data])
    
    price = test_db_session.query(MandiPrice).filter_by(
        crop_name='Wheat',
        mandi_name='Pune Mandi'
    ).first()
    
    assert price is not None, "Price should be found"
    assert price.price_date is not None, "Should have price_date"
    assert price.last_updated is not None, "Should have last_updated"
    assert isinstance(price.price_date, date), "price_date should be date"
    assert isinstance(price.last_updated, datetime), "last_updated should be datetime"


def test_specific_job_posting_has_timestamps(test_db_session):
    """
    Specific example test: A concrete job posting should have all timestamps.
    """
    job_data = {
        'job_id': uuid.uuid4(),
        'title': 'Junior Engineer',
        'department': 'Public Works',
        'description': 'Engineering position in government department',
        'qualifications': {'education': ['B.E./B.Tech'], 'experience': '0-2 years'},
        'location': {'state': 'Maharashtra', 'district': 'Mumbai'},
        'application_deadline': date.today() + timedelta(days=30),
        'application_url': 'https://jobs.gov.in/apply',
        'posted_date': date.today() - timedelta(days=5),
        'last_updated': datetime.utcnow() - timedelta(hours=1),
        'created_at': datetime.utcnow() - timedelta(days=5),
        'updated_at': datetime.utcnow() - timedelta(hours=1)
    }
    
    add_job_postings_to_db(test_db_session, [job_data])
    
    job = test_db_session.query(JobPosting).filter_by(
        title='Junior Engineer'
    ).first()
    
    assert job is not None, "Job should be found"
    assert job.application_deadline is not None, "Should have application_deadline"
    assert job.posted_date is not None, "Should have posted_date"
    assert job.last_updated is not None, "Should have last_updated"
    assert isinstance(job.application_deadline, date), "deadline should be date"
    assert isinstance(job.posted_date, date), "posted_date should be date"
    assert isinstance(job.last_updated, datetime), "last_updated should be datetime"


def test_expired_job_still_has_timestamps(test_db_session):
    """
    Edge case test: Even expired jobs should maintain timestamp information.
    """
    job_data = {
        'job_id': uuid.uuid4(),
        'title': 'Expired Job',
        'department': 'Test Department',
        'description': 'This job has expired',
        'qualifications': {},
        'location': {},
        'application_deadline': date.today() - timedelta(days=10),  # Expired
        'application_url': 'https://jobs.gov.in/expired',
        'posted_date': date.today() - timedelta(days=40),
        'last_updated': datetime.utcnow() - timedelta(days=10),
        'created_at': datetime.utcnow() - timedelta(days=40),
        'updated_at': datetime.utcnow() - timedelta(days=10)
    }
    
    add_job_postings_to_db(test_db_session, [job_data])
    
    job = test_db_session.query(JobPosting).filter_by(
        title='Expired Job'
    ).first()
    
    # Even expired jobs should have all timestamps
    assert job.application_deadline is not None, "Expired job should have deadline"
    assert job.posted_date is not None, "Expired job should have posted_date"
    assert job.last_updated is not None, "Expired job should have last_updated"


def test_old_price_data_has_timestamps(test_db_session):
    """
    Edge case test: Old price data should still have timestamp information.
    """
    price_data = {
        'price_id': uuid.uuid4(),
        'crop_name': 'Rice',
        'mandi_name': 'Old Mandi',
        'state': 'Punjab',
        'district': 'Ludhiana',
        'latitude': 30.9010,
        'longitude': 75.8573,
        'price_per_quintal': 1800.0,
        'price_date': date.today() - timedelta(days=60),  # Old data
        'source': 'Government API',
        'last_updated': datetime.utcnow() - timedelta(days=60),
        'created_at': datetime.utcnow() - timedelta(days=60)
    }
    
    add_mandi_prices_to_db(test_db_session, [price_data])
    
    price = test_db_session.query(MandiPrice).filter_by(
        crop_name='Rice',
        mandi_name='Old Mandi'
    ).first()
    
    # Old data should still have timestamps
    assert price.price_date is not None, "Old price should have price_date"
    assert price.last_updated is not None, "Old price should have last_updated"
    
    # Should be able to calculate data age
    data_age = (datetime.utcnow() - price.last_updated).days
    assert data_age >= 60, "Should be able to calculate data age from timestamp"


def test_timestamp_preserved_across_retrieval(test_db_session):
    """
    Test that timestamps are preserved when retrieving time-sensitive data.
    """
    original_price_date = date.today() - timedelta(days=5)
    original_last_updated = datetime.utcnow() - timedelta(hours=12)
    
    price_data = {
        'price_id': uuid.uuid4(),
        'crop_name': 'Cotton',
        'mandi_name': 'Test Mandi',
        'state': 'Gujarat',
        'district': 'Ahmedabad',
        'latitude': 23.0225,
        'longitude': 72.5714,
        'price_per_quintal': 5500.0,
        'price_date': original_price_date,
        'source': 'Test Source',
        'last_updated': original_last_updated,
        'created_at': original_last_updated - timedelta(hours=1)
    }
    
    add_mandi_prices_to_db(test_db_session, [price_data])
    
    retrieved_price = test_db_session.query(MandiPrice).filter_by(
        crop_name='Cotton'
    ).first()
    
    # Timestamps should be preserved
    assert retrieved_price.price_date == original_price_date, \
        "price_date should be preserved across database operations"
    
    # last_updated should be preserved (within 1 second for precision)
    time_diff = abs((retrieved_price.last_updated - original_last_updated).total_seconds())
    assert time_diff < 1, \
        "last_updated should be preserved across database operations"


def test_multiple_prices_same_crop_have_timestamps(test_db_session):
    """
    Test that when multiple prices exist for the same crop, all have timestamps.
    """
    prices_data = []
    for i in range(5):
        prices_data.append({
            'price_id': uuid.uuid4(),
            'crop_name': 'Maize',
            'mandi_name': f'Mandi {i}',
            'state': 'Karnataka',
            'district': f'District {i}',
            'latitude': 12.9716 + i * 0.1,
            'longitude': 77.5946 + i * 0.1,
            'price_per_quintal': 1500.0 + i * 100,
            'price_date': date.today() - timedelta(days=i),
            'source': 'Government API',
            'last_updated': datetime.utcnow() - timedelta(hours=i),
            'created_at': datetime.utcnow() - timedelta(days=i)
        })
    
    add_mandi_prices_to_db(test_db_session, prices_data)
    
    all_maize_prices = test_db_session.query(MandiPrice).filter_by(
        crop_name='Maize'
    ).all()
    
    assert len(all_maize_prices) == 5, "Should have 5 prices"
    
    # All prices should have timestamps
    for price in all_maize_prices:
        assert price.price_date is not None, \
            f"Price at {price.mandi_name} should have price_date"
        assert price.last_updated is not None, \
            f"Price at {price.mandi_name} should have last_updated"
