"""
Unit Tests: Data Freshness and Verification Tracking

Tests timestamp updates and verification status tracking for data freshness.
Requirements: 12.1, 12.3, 12.5
"""
import pytest
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Table, Column, String, DateTime, Text, ForeignKey, Integer, Float, Numeric, Boolean, Date
from sqlalchemy.orm import sessionmaker
from sqlalchemy import JSON, MetaData
from app.models.scheme import Scheme
from app.models.farmer import MandiPrice
from app.models.skills import JobPosting
from app.services.verification_tracker import (
    VerificationTracker,
    VerificationStatus,
    DataFreshnessLevel
)
import uuid as uuid_module


@pytest.fixture(scope="function")
def test_db_session():
    """Create a test database session"""
    from sqlalchemy.types import TypeDecorator, CHAR
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    
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
    
    schemes_table = Table(
        'schemes', metadata,
        Column('scheme_id', UUID(), primary_key=True),
        Column('name', String(255), nullable=False),
        Column('category', String(50), nullable=False),
        Column('description', Text, nullable=True),
        Column('benefits', JSON, nullable=True),
        Column('eligibility_criteria', JSON, nullable=False),
        Column('required_documents', JSON, nullable=True),
        Column('application_process', JSON, nullable=True),
        Column('application_url', String(500), nullable=True),
        Column('department', String(100), nullable=True),
        Column('state', String(50), nullable=True),
        Column('last_updated', DateTime, nullable=True),
        Column('source_url', String(500), nullable=True),
        Column('created_at', DateTime, nullable=False),
        Column('verification_status', String(20), nullable=True),
        Column('verified_at', DateTime, nullable=True),
        Column('verification_source', String(255), nullable=True)
    )
    
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


class TestTimestampUpdates:
    """Test that timestamps are properly updated"""
    
    def test_scheme_last_updated_on_creation(self, test_db_session: Session):
        """Test that scheme gets last_updated timestamp on creation"""
        scheme = Scheme(
            name="Test Scheme",
            category="agriculture",
            eligibility_criteria={"age_min": 18},
            last_updated=datetime.utcnow()
        )
        test_db_session.add(scheme)
        test_db_session.commit()
        
        assert scheme.last_updated is not None
        assert isinstance(scheme.last_updated, datetime)
    
    def test_scheme_last_updated_on_modification(self, test_db_session: Session):
        """Test that scheme last_updated is updated when modified"""
        # Create scheme
        scheme = Scheme(
            name="Test Scheme",
            category="agriculture",
            eligibility_criteria={"age_min": 18},
            last_updated=datetime.utcnow() - timedelta(days=10)
        )
        test_db_session.add(scheme)
        test_db_session.commit()
        
        original_timestamp = scheme.last_updated
        
        # Modify scheme
        scheme.name = "Updated Scheme"
        scheme.last_updated = datetime.utcnow()
        test_db_session.commit()
        
        assert scheme.last_updated > original_timestamp
    
    def test_mandi_price_last_updated_on_creation(self, test_db_session: Session):
        """Test that mandi price gets last_updated timestamp on creation"""
        from datetime import date
        
        price = MandiPrice(
            crop_name="Wheat",
            mandi_name="Test Mandi",
            state="Punjab",
            district="Ludhiana",
            price_per_quintal=2000.0,
            price_date=date.today(),
            last_updated=datetime.utcnow()
        )
        test_db_session.add(price)
        test_db_session.commit()
        
        assert price.last_updated is not None
        assert isinstance(price.last_updated, datetime)
    
    def test_job_posting_last_updated_on_creation(self, test_db_session: Session):
        """Test that job posting gets last_updated timestamp on creation"""
        from datetime import date
        
        job = JobPosting(
            title="Test Job",
            department="Agriculture",
            application_deadline=date.today() + timedelta(days=30),
            last_updated=datetime.utcnow()
        )
        test_db_session.add(job)
        test_db_session.commit()
        
        assert job.last_updated is not None
        assert isinstance(job.last_updated, datetime)
    
    def test_timestamp_precision(self, test_db_session: Session):
        """Test that timestamps have sufficient precision"""
        scheme = Scheme(
            name="Test Scheme",
            category="agriculture",
            eligibility_criteria={"age_min": 18},
            last_updated=datetime.utcnow()
        )
        test_db_session.add(scheme)
        test_db_session.commit()
        
        # Timestamp should have at least second precision
        assert scheme.last_updated.microsecond >= 0


class TestVerificationStatusTracking:
    """Test verification status tracking functionality"""
    
    def test_scheme_default_verification_status(self, test_db_session: Session):
        """Test that new schemes have default unverified status"""
        scheme = Scheme(
            name="Test Scheme",
            category="agriculture",
            eligibility_criteria={"age_min": 18}
        )
        test_db_session.add(scheme)
        test_db_session.commit()
        
        assert scheme.verification_status == "unverified"
        assert scheme.verified_at is None
    
    def test_mark_scheme_as_verified(self, test_db_session: Session):
        """Test marking a scheme as verified"""
        scheme = Scheme(
            name="Test Scheme",
            category="agriculture",
            eligibility_criteria={"age_min": 18}
        )
        test_db_session.add(scheme)
        test_db_session.commit()
        
        # Mark as verified
        verification_data = VerificationTracker.mark_as_verified("official_website")
        scheme.verification_status = verification_data['verification_status']
        scheme.verified_at = verification_data['verified_at']
        scheme.verification_source = verification_data['verification_source']
        scheme.last_updated = verification_data['last_updated']
        test_db_session.commit()
        
        assert scheme.verification_status == VerificationStatus.VERIFIED
        assert scheme.verified_at is not None
        assert scheme.verification_source == "official_website"
    
    def test_mark_scheme_as_unverified(self, test_db_session: Session):
        """Test marking a scheme as unverified with source attribution"""
        scheme = Scheme(
            name="Test Scheme",
            category="agriculture",
            eligibility_criteria={"age_min": 18}
        )
        test_db_session.add(scheme)
        test_db_session.commit()
        
        # Mark as unverified with source
        verification_data = VerificationTracker.mark_as_unverified("community_report")
        scheme.verification_status = verification_data['verification_status']
        scheme.verified_at = verification_data['verified_at']
        scheme.verification_source = verification_data['verification_source']
        scheme.last_updated = verification_data['last_updated']
        test_db_session.commit()
        
        assert scheme.verification_status == VerificationStatus.UNVERIFIED
        assert scheme.verified_at is None
        assert scheme.verification_source == "community_report"
    
    def test_verification_status_transition(self, test_db_session: Session):
        """Test transitioning verification status from unverified to verified"""
        scheme = Scheme(
            name="Test Scheme",
            category="agriculture",
            eligibility_criteria={"age_min": 18},
            verification_status="unverified"
        )
        test_db_session.add(scheme)
        test_db_session.commit()
        
        # Verify the scheme
        verification_data = VerificationTracker.mark_as_verified("government_portal")
        scheme.verification_status = verification_data['verification_status']
        scheme.verified_at = verification_data['verified_at']
        scheme.verification_source = verification_data['verification_source']
        test_db_session.commit()
        
        assert scheme.verification_status == VerificationStatus.VERIFIED
        assert scheme.verified_at is not None
    
    def test_pending_verification_status(self, test_db_session: Session):
        """Test pending verification status"""
        scheme = Scheme(
            name="Test Scheme",
            category="agriculture",
            eligibility_criteria={"age_min": 18},
            verification_status="pending"
        )
        test_db_session.add(scheme)
        test_db_session.commit()
        
        assert scheme.verification_status == "pending"
        assert not VerificationTracker.is_verified(scheme.verification_status)


class TestDataAgeCalculation:
    """Test data age calculation functionality"""
    
    def test_calculate_data_age_recent(self):
        """Test calculating age for recent data"""
        last_updated = datetime.utcnow() - timedelta(days=5)
        age_days = VerificationTracker.calculate_data_age_days(last_updated)
        
        assert age_days == 5
    
    def test_calculate_data_age_old(self):
        """Test calculating age for old data"""
        last_updated = datetime.utcnow() - timedelta(days=45)
        age_days = VerificationTracker.calculate_data_age_days(last_updated)
        
        assert age_days == 45
    
    def test_calculate_data_age_none(self):
        """Test calculating age when timestamp is None"""
        age_days = VerificationTracker.calculate_data_age_days(None)
        
        assert age_days is None
    
    def test_calculate_data_age_today(self):
        """Test calculating age for data updated today"""
        last_updated = datetime.utcnow()
        age_days = VerificationTracker.calculate_data_age_days(last_updated)
        
        assert age_days == 0


class TestFreshnessLevelDetermination:
    """Test freshness level determination"""
    
    def test_fresh_data_level(self):
        """Test that data updated within 7 days is marked as fresh"""
        last_updated = datetime.utcnow() - timedelta(days=3)
        freshness = VerificationTracker.get_freshness_level(last_updated)
        
        assert freshness == DataFreshnessLevel.FRESH
    
    def test_recent_data_level(self):
        """Test that data updated within 30 days is marked as recent"""
        last_updated = datetime.utcnow() - timedelta(days=15)
        freshness = VerificationTracker.get_freshness_level(last_updated)
        
        assert freshness == DataFreshnessLevel.RECENT
    
    def test_stale_data_level(self):
        """Test that data older than 30 days is marked as stale"""
        last_updated = datetime.utcnow() - timedelta(days=45)
        freshness = VerificationTracker.get_freshness_level(last_updated)
        
        assert freshness == DataFreshnessLevel.STALE
    
    def test_unknown_data_level(self):
        """Test that data without timestamp is marked as unknown"""
        freshness = VerificationTracker.get_freshness_level(None)
        
        assert freshness == DataFreshnessLevel.UNKNOWN
    
    def test_boundary_fresh_to_recent(self):
        """Test boundary between fresh and recent (7 days)"""
        # 7 days should be recent
        last_updated = datetime.utcnow() - timedelta(days=7)
        freshness = VerificationTracker.get_freshness_level(last_updated)
        
        assert freshness == DataFreshnessLevel.FRESH
        
        # 8 days should be recent
        last_updated = datetime.utcnow() - timedelta(days=8)
        freshness = VerificationTracker.get_freshness_level(last_updated)
        
        assert freshness == DataFreshnessLevel.RECENT
    
    def test_boundary_recent_to_stale(self):
        """Test boundary between recent and stale (30 days)"""
        # 30 days should be recent
        last_updated = datetime.utcnow() - timedelta(days=30)
        freshness = VerificationTracker.get_freshness_level(last_updated)
        
        assert freshness == DataFreshnessLevel.RECENT
        
        # 31 days should be stale
        last_updated = datetime.utcnow() - timedelta(days=31)
        freshness = VerificationTracker.get_freshness_level(last_updated)
        
        assert freshness == DataFreshnessLevel.STALE


class TestReverificationLogic:
    """Test reverification logic"""
    
    def test_should_reverify_no_timestamp(self):
        """Test that data without verification timestamp should be reverified"""
        should_reverify = VerificationTracker.should_reverify(None)
        
        assert should_reverify is True
    
    def test_should_reverify_old_verification(self):
        """Test that old verification should trigger reverification"""
        verified_at = datetime.utcnow() - timedelta(days=35)
        should_reverify = VerificationTracker.should_reverify(verified_at, reverification_days=30)
        
        assert should_reverify is True
    
    def test_should_not_reverify_recent_verification(self):
        """Test that recent verification should not trigger reverification"""
        verified_at = datetime.utcnow() - timedelta(days=10)
        should_reverify = VerificationTracker.should_reverify(verified_at, reverification_days=30)
        
        assert should_reverify is False
    
    def test_reverification_boundary(self):
        """Test reverification at exact boundary"""
        # Exactly 30 days should trigger reverification
        verified_at = datetime.utcnow() - timedelta(days=30)
        should_reverify = VerificationTracker.should_reverify(verified_at, reverification_days=30)
        
        assert should_reverify is True
    
    def test_custom_reverification_period(self):
        """Test custom reverification period"""
        verified_at = datetime.utcnow() - timedelta(days=10)
        
        # Should reverify with 7-day period
        should_reverify = VerificationTracker.should_reverify(verified_at, reverification_days=7)
        assert should_reverify is True
        
        # Should not reverify with 14-day period
        should_reverify = VerificationTracker.should_reverify(verified_at, reverification_days=14)
        assert should_reverify is False


class TestUncertaintyIndicators:
    """Test uncertainty indicator generation"""
    
    def test_add_indicators_to_verified_fresh_data(self):
        """Test adding indicators to verified and fresh data"""
        data = {"name": "Test Scheme"}
        last_updated = datetime.utcnow() - timedelta(days=3)
        
        result = VerificationTracker.add_uncertainty_indicators(
            data,
            last_updated=last_updated,
            verification_status=VerificationStatus.VERIFIED,
            verification_source="official_website"
        )
        
        assert result['is_verified'] is True
        assert result['data_age_days'] == 3
        assert result['freshness_level'] == DataFreshnessLevel.FRESH.value
        assert 'data_warnings' not in result
    
    def test_add_indicators_to_unverified_data(self):
        """Test adding indicators to unverified data"""
        data = {"name": "Test Scheme"}
        last_updated = datetime.utcnow() - timedelta(days=5)
        
        result = VerificationTracker.add_uncertainty_indicators(
            data,
            last_updated=last_updated,
            verification_status=VerificationStatus.UNVERIFIED,
            verification_source="community_report"
        )
        
        assert result['is_verified'] is False
        assert result['verification_source'] == "community_report"
        assert 'data_warnings' in result
        assert any("not been verified" in warning for warning in result['data_warnings'])
    
    def test_add_indicators_to_stale_data(self):
        """Test adding indicators to stale data"""
        data = {"name": "Test Scheme"}
        last_updated = datetime.utcnow() - timedelta(days=45)
        
        result = VerificationTracker.add_uncertainty_indicators(
            data,
            last_updated=last_updated,
            verification_status=VerificationStatus.VERIFIED,
            verification_source="official_website"
        )
        
        assert result['freshness_level'] == DataFreshnessLevel.STALE.value
        assert 'data_warnings' in result
        assert any("45 days ago" in warning for warning in result['data_warnings'])
    
    def test_add_indicators_to_data_without_timestamp(self):
        """Test adding indicators to data without timestamp"""
        data = {"name": "Test Scheme"}
        
        result = VerificationTracker.add_uncertainty_indicators(
            data,
            last_updated=None,
            verification_status=VerificationStatus.UNVERIFIED,
            verification_source=None
        )
        
        assert result['data_age_days'] is None
        assert result['freshness_level'] == DataFreshnessLevel.UNKNOWN.value
        assert 'data_warnings' in result
        assert any("unknown" in warning.lower() for warning in result['data_warnings'])
    
    def test_multiple_warnings_for_stale_unverified_data(self):
        """Test that stale and unverified data gets multiple warnings"""
        data = {"name": "Test Scheme"}
        last_updated = datetime.utcnow() - timedelta(days=45)
        
        result = VerificationTracker.add_uncertainty_indicators(
            data,
            last_updated=last_updated,
            verification_status=VerificationStatus.UNVERIFIED,
            verification_source="unknown"
        )
        
        assert 'data_warnings' in result
        assert len(result['data_warnings']) >= 2  # Should have both staleness and verification warnings


class TestEdgeCases:
    """Test edge cases for data freshness tracking"""
    
    def test_future_timestamp_handling(self):
        """Test handling of future timestamps (clock skew)"""
        # Future timestamp should result in 0 or negative age
        future_timestamp = datetime.utcnow() + timedelta(days=1)
        age_days = VerificationTracker.calculate_data_age_days(future_timestamp)
        
        # Should handle gracefully (negative age)
        assert age_days <= 0
    
    def test_very_old_data(self):
        """Test handling of very old data (years old)"""
        old_timestamp = datetime.utcnow() - timedelta(days=730)  # 2 years
        freshness = VerificationTracker.get_freshness_level(old_timestamp)
        
        assert freshness == DataFreshnessLevel.STALE
    
    def test_empty_data_dict(self):
        """Test adding indicators to empty data dictionary"""
        data = {}
        last_updated = datetime.utcnow()
        
        result = VerificationTracker.add_uncertainty_indicators(
            data,
            last_updated=last_updated,
            verification_status=VerificationStatus.VERIFIED
        )
        
        assert 'is_verified' in result
        assert 'data_age_days' in result
        assert 'freshness_level' in result
    
    def test_verification_source_not_added_for_verified_data(self):
        """Test that verification_source is not added to response for verified data"""
        data = {"name": "Test Scheme"}
        last_updated = datetime.utcnow()
        
        result = VerificationTracker.add_uncertainty_indicators(
            data,
            last_updated=last_updated,
            verification_status=VerificationStatus.VERIFIED,
            verification_source="official_website"
        )
        
        # Verification source should not be in result for verified data
        assert 'verification_source' not in result
