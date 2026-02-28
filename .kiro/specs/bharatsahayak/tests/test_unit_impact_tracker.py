"""
Unit tests for Impact Tracker Service

Tests event recording with various event types, aggregation with different filters,
and anonymization completeness.

Feature: bharatsahayak
Requirements: 9.1, 9.2, 9.3, 9.4
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import uuid

from app.services.impact_tracker import ImpactTracker
from app.models.impact import InteractionEvent, OutcomeEvent
from app.schemas.impact import (
    InteractionEventCreate,
    OutcomeEventCreate,
    InteractionEventType,
    OutcomeEventType,
    MetricFilters,
    ReportType,
    DateRange
)


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    return Mock()


@pytest.fixture
def sample_interaction_events():
    """Create sample interaction events for testing"""
    user_id1 = uuid.uuid4()
    user_id2 = uuid.uuid4()
    
    now = datetime.utcnow()
    
    events = [
        InteractionEvent(
            interaction_id=uuid.uuid4(),
            user_id=user_id1,
            event_type="query_submitted",
            event_data={"query": "PM-KISAN scheme", "region": "Maharashtra"},
            language="hi",
            timestamp=now - timedelta(days=5)
        ),
        InteractionEvent(
            interaction_id=uuid.uuid4(),
            user_id=user_id1,
            event_type="scheme_accessed",
            event_data={"scheme_id": "pm-kisan-123", "state": "Maharashtra"},
            language="hi",
            timestamp=now - timedelta(days=4)
        ),
        InteractionEvent(
            interaction_id=uuid.uuid4(),
            user_id=user_id2,
            event_type="crop_advice_requested",
            event_data={"crop": "wheat", "district": "Pune"},
            language="mr",
            timestamp=now - timedelta(days=3)
        ),
        InteractionEvent(
            interaction_id=uuid.uuid4(),
            user_id=user_id2,
            event_type="job_discovered",
            event_data={"job_id": "job-456", "region": "Karnataka"},
            language="kn",
            timestamp=now - timedelta(days=2)
        ),
        InteractionEvent(
            interaction_id=uuid.uuid4(),
            user_id=user_id1,
            event_type="health_check_performed",
            event_data={"symptoms": ["fever", "cough"]},
            language="hi",
            timestamp=now - timedelta(days=1)
        ),
    ]
    
    return events


@pytest.fixture
def sample_outcome_events():
    """Create sample outcome events for testing"""
    user_id1 = uuid.uuid4()
    user_id2 = uuid.uuid4()
    
    now = datetime.utcnow()
    
    outcomes = [
        OutcomeEvent(
            outcome_id=uuid.uuid4(),
            user_id=user_id1,
            outcome_type="scheme_applied",
            outcome_data={"scheme_id": "pm-kisan-123", "state": "Maharashtra"},
            timestamp=now - timedelta(days=3)
        ),
        OutcomeEvent(
            outcome_id=uuid.uuid4(),
            user_id=user_id2,
            outcome_type="crop_planted",
            outcome_data={"crop": "wheat", "district": "Pune"},
            timestamp=now - timedelta(days=2)
        ),
    ]
    
    return outcomes


class TestEventRecording:
    """Test event recording with various event types"""
    
    def test_record_interaction_query_submitted(self, mock_db):
        """Test recording a query_submitted interaction event"""
        tracker = ImpactTracker(mock_db)
        
        event = InteractionEventCreate(
            user_id=str(uuid.uuid4()),
            event_type=InteractionEventType.QUERY_SUBMITTED,
            event_data={"query": "government schemes for farmers"},
            language="hi"
        )
        
        # Mock database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        result = tracker.record_interaction(event)
        
        # Verify database operations were called
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_record_interaction_scheme_accessed(self, mock_db):
        """Test recording a scheme_accessed interaction event"""
        tracker = ImpactTracker(mock_db)
        
        event = InteractionEventCreate(
            user_id=str(uuid.uuid4()),
            event_type=InteractionEventType.SCHEME_ACCESSED,
            event_data={"scheme_id": "pm-kisan-123", "scheme_name": "PM-KISAN"},
            language="hi"
        )
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        result = tracker.record_interaction(event)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_record_interaction_farmer_events(self, mock_db):
        """Test recording farmer-related interaction events"""
        tracker = ImpactTracker(mock_db)
        
        # Test crop advice
        crop_event = InteractionEventCreate(
            user_id=str(uuid.uuid4()),
            event_type=InteractionEventType.CROP_ADVICE_REQUESTED,
            event_data={"crop": "wheat", "soil_type": "loamy"},
            language="hi"
        )
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        tracker.record_interaction(crop_event)
        assert mock_db.add.call_count == 1
        
        # Test fertilizer advice
        fertilizer_event = InteractionEventCreate(
            user_id=str(uuid.uuid4()),
            event_type=InteractionEventType.FERTILIZER_ADVICE_REQUESTED,
            event_data={"crop": "rice", "stage": "vegetative"},
            language="mr"
        )
        
        tracker.record_interaction(fertilizer_event)
        assert mock_db.add.call_count == 2
        
        # Test market price check
        price_event = InteractionEventCreate(
            user_id=str(uuid.uuid4()),
            event_type=InteractionEventType.MARKET_PRICE_CHECKED,
            event_data={"crop": "wheat", "mandi": "Pune"},
            language="mr"
        )
        
        tracker.record_interaction(price_event)
        assert mock_db.add.call_count == 3
    
    def test_record_interaction_skills_events(self, mock_db):
        """Test recording skills and employment interaction events"""
        tracker = ImpactTracker(mock_db)
        
        # Test skill program viewed
        skill_event = InteractionEventCreate(
            user_id=str(uuid.uuid4()),
            event_type=InteractionEventType.SKILL_PROGRAM_VIEWED,
            event_data={"program_id": "skill-123", "category": "technical"},
            language="hi"
        )
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        tracker.record_interaction(skill_event)
        assert mock_db.add.call_count == 1
        
        # Test job discovered
        job_event = InteractionEventCreate(
            user_id=str(uuid.uuid4()),
            event_type=InteractionEventType.JOB_DISCOVERED,
            event_data={"job_id": "job-456", "department": "Railways"},
            language="hi"
        )
        
        tracker.record_interaction(job_event)
        assert mock_db.add.call_count == 2
    
    def test_record_interaction_health_events(self, mock_db):
        """Test recording health-related interaction events"""
        tracker = ImpactTracker(mock_db)
        
        # Test health check
        health_event = InteractionEventCreate(
            user_id=str(uuid.uuid4()),
            event_type=InteractionEventType.HEALTH_CHECK_PERFORMED,
            event_data={"symptoms": ["fever", "cough"], "urgency": "routine"},
            language="hi"
        )
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        tracker.record_interaction(health_event)
        assert mock_db.add.call_count == 1
        
        # Test facility located
        facility_event = InteractionEventCreate(
            user_id=str(uuid.uuid4()),
            event_type=InteractionEventType.FACILITY_LOCATED,
            event_data={"facility_id": "phc-123", "distance_km": 5},
            language="hi"
        )
        
        tracker.record_interaction(facility_event)
        assert mock_db.add.call_count == 2
    
    def test_record_interaction_voice_and_language(self, mock_db):
        """Test recording voice interaction and language usage events"""
        tracker = ImpactTracker(mock_db)
        
        # Test voice interaction
        voice_event = InteractionEventCreate(
            user_id=str(uuid.uuid4()),
            event_type=InteractionEventType.VOICE_INTERACTION,
            event_data={"duration_seconds": 45, "transcription_confidence": 0.92},
            language="hi"
        )
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        tracker.record_interaction(voice_event)
        assert mock_db.add.call_count == 1
        
        # Test language used
        lang_event = InteractionEventCreate(
            user_id=str(uuid.uuid4()),
            event_type=InteractionEventType.LANGUAGE_USED,
            event_data={"language": "mr", "context": "scheme_search"},
            language="mr"
        )
        
        tracker.record_interaction(lang_event)
        assert mock_db.add.call_count == 2
    
    def test_record_interaction_without_user_id(self, mock_db):
        """Test recording interaction event without user_id (anonymous)"""
        tracker = ImpactTracker(mock_db)
        
        event = InteractionEventCreate(
            user_id=None,  # Anonymous
            event_type=InteractionEventType.QUERY_SUBMITTED,
            event_data={"query": "health schemes"},
            language="hi"
        )
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        result = tracker.record_interaction(event)
        
        # Should still record the event
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_record_interaction_with_invalid_user_id(self, mock_db):
        """Test recording interaction with invalid user_id format"""
        tracker = ImpactTracker(mock_db)
        
        event = InteractionEventCreate(
            user_id="invalid-uuid-format",
            event_type=InteractionEventType.QUERY_SUBMITTED,
            event_data={"query": "schemes"},
            language="hi"
        )
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Should handle gracefully and still record
        result = tracker.record_interaction(event)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_record_interaction_database_error(self, mock_db):
        """Test recording interaction handles database errors"""
        tracker = ImpactTracker(mock_db)
        
        event = InteractionEventCreate(
            user_id=str(uuid.uuid4()),
            event_type=InteractionEventType.QUERY_SUBMITTED,
            event_data={"query": "schemes"},
            language="hi"
        )
        
        # Simulate database error
        mock_db.add = Mock()
        mock_db.commit = Mock(side_effect=Exception("Database error"))
        mock_db.rollback = Mock()
        
        with pytest.raises(Exception):
            tracker.record_interaction(event)
        
        # Verify rollback was called
        mock_db.rollback.assert_called_once()
    
    def test_record_outcome_scheme_applied(self, mock_db):
        """Test recording a scheme_applied outcome event"""
        tracker = ImpactTracker(mock_db)
        
        outcome = OutcomeEventCreate(
            user_id=str(uuid.uuid4()),
            outcome_type=OutcomeEventType.SCHEME_APPLIED,
            outcome_data={"scheme_id": "pm-kisan-123", "application_id": "app-789"}
        )
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        result = tracker.record_outcome(outcome)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_record_outcome_job_applied(self, mock_db):
        """Test recording a job_applied outcome event"""
        tracker = ImpactTracker(mock_db)
        
        outcome = OutcomeEventCreate(
            user_id=str(uuid.uuid4()),
            outcome_type=OutcomeEventType.JOB_APPLIED,
            outcome_data={"job_id": "job-456", "application_date": "2026-02-27"}
        )
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        result = tracker.record_outcome(outcome)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_record_outcome_farmer_outcomes(self, mock_db):
        """Test recording farmer-related outcome events"""
        tracker = ImpactTracker(mock_db)
        
        # Test crop planted
        crop_outcome = OutcomeEventCreate(
            user_id=str(uuid.uuid4()),
            outcome_type=OutcomeEventType.CROP_PLANTED,
            outcome_data={"crop": "wheat", "area_acres": 5}
        )
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        tracker.record_outcome(crop_outcome)
        assert mock_db.add.call_count == 1
        
        # Test fertilizer purchased
        fertilizer_outcome = OutcomeEventCreate(
            user_id=str(uuid.uuid4()),
            outcome_type=OutcomeEventType.FERTILIZER_PURCHASED,
            outcome_data={"fertilizer_type": "NPK", "quantity_kg": 50}
        )
        
        tracker.record_outcome(fertilizer_outcome)
        assert mock_db.add.call_count == 2
    
    def test_record_outcome_other_types(self, mock_db):
        """Test recording other outcome event types"""
        tracker = ImpactTracker(mock_db)
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Test facility visited
        facility_outcome = OutcomeEventCreate(
            user_id=str(uuid.uuid4()),
            outcome_type=OutcomeEventType.FACILITY_VISITED,
            outcome_data={"facility_id": "phc-123", "visit_date": "2026-02-27"}
        )
        tracker.record_outcome(facility_outcome)
        
        # Test skill enrolled
        skill_outcome = OutcomeEventCreate(
            user_id=str(uuid.uuid4()),
            outcome_type=OutcomeEventType.SKILL_ENROLLED,
            outcome_data={"program_id": "skill-123", "enrollment_date": "2026-02-27"}
        )
        tracker.record_outcome(skill_outcome)
        
        # Test recommendation followed
        rec_outcome = OutcomeEventCreate(
            user_id=str(uuid.uuid4()),
            outcome_type=OutcomeEventType.RECOMMENDATION_FOLLOWED,
            outcome_data={"recommendation_type": "crop_advice", "followed": True}
        )
        tracker.record_outcome(rec_outcome)
        
        assert mock_db.add.call_count == 3
    
    def test_record_outcome_without_user_id(self, mock_db):
        """Test recording outcome event without user_id"""
        tracker = ImpactTracker(mock_db)
        
        outcome = OutcomeEventCreate(
            user_id=None,
            outcome_type=OutcomeEventType.SCHEME_APPLIED,
            outcome_data={"scheme_id": "pm-kisan-123"}
        )
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        result = tracker.record_outcome(outcome)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_record_outcome_database_error(self, mock_db):
        """Test recording outcome handles database errors"""
        tracker = ImpactTracker(mock_db)
        
        outcome = OutcomeEventCreate(
            user_id=str(uuid.uuid4()),
            outcome_type=OutcomeEventType.SCHEME_APPLIED,
            outcome_data={"scheme_id": "pm-kisan-123"}
        )
        
        mock_db.add = Mock()
        mock_db.commit = Mock(side_effect=Exception("Database error"))
        mock_db.rollback = Mock()
        
        with pytest.raises(Exception):
            tracker.record_outcome(outcome)
        
        mock_db.rollback.assert_called_once()


class TestMetricsAggregation:
    """Test aggregation with different filters"""
    
    def test_get_metrics_without_filters(self, mock_db, sample_interaction_events, sample_outcome_events):
        """Test getting metrics without any filters (default 30 days)"""
        tracker = ImpactTracker(mock_db)
        
        # Mock query for users_served
        mock_query_users = Mock()
        mock_query_users.filter.return_value = mock_query_users
        mock_query_users.scalar.return_value = 2  # 2 unique users
        
        # Mock query for queries_resolved
        mock_query_queries = Mock()
        mock_query_queries.filter.return_value = mock_query_queries
        mock_query_queries.scalar.return_value = 5  # 5 total queries
        
        # Mock query for schemes_accessed
        mock_query_schemes = Mock()
        mock_query_schemes.filter.return_value = mock_query_schemes
        mock_query_schemes.scalar.return_value = 1
        
        # Mock query for farmers_assisted
        mock_query_farmers = Mock()
        mock_query_farmers.filter.return_value = mock_query_farmers
        mock_query_farmers.scalar.return_value = 1
        
        # Mock query for jobs_discovered
        mock_query_jobs = Mock()
        mock_query_jobs.filter.return_value = mock_query_jobs
        mock_query_jobs.scalar.return_value = 1
        
        # Mock query for health_checks
        mock_query_health = Mock()
        mock_query_health.filter.return_value = mock_query_health
        mock_query_health.scalar.return_value = 1
        
        # Mock query for languages_used
        mock_query_languages = Mock()
        mock_query_languages.filter.return_value = mock_query_languages
        mock_query_languages.group_by.return_value = mock_query_languages
        mock_query_languages.all.return_value = [("hi", 3), ("mr", 1), ("kn", 1)]
        
        # Mock query for events_by_type
        mock_query_events = Mock()
        mock_query_events.filter.return_value = mock_query_events
        mock_query_events.group_by.return_value = mock_query_events
        mock_query_events.all.return_value = [
            ("query_submitted", 1),
            ("scheme_accessed", 1),
            ("crop_advice_requested", 1),
            ("job_discovered", 1),
            ("health_check_performed", 1)
        ]
        
        # Mock query for outcomes_by_type
        mock_query_outcomes = Mock()
        mock_query_outcomes.filter.return_value = mock_query_outcomes
        mock_query_outcomes.group_by.return_value = mock_query_outcomes
        mock_query_outcomes.all.return_value = [
            ("scheme_applied", 1),
            ("crop_planted", 1)
        ]
        
        # Set up mock_db.query to return different mocks based on call order
        mock_db.query.side_effect = [
            mock_query_users,
            mock_query_queries,
            mock_query_schemes,
            mock_query_farmers,
            mock_query_jobs,
            mock_query_health,
            mock_query_languages,
            mock_query_events,
            mock_query_outcomes
        ]
        
        filters = MetricFilters()
        metrics = tracker.get_metrics(filters)
        
        assert metrics.users_served == 2
        assert metrics.queries_resolved == 5
        assert metrics.schemes_accessed == 1
        assert metrics.farmers_assisted == 1
        assert metrics.jobs_discovered == 1
        assert metrics.health_checks_performed == 1
        assert metrics.languages_used == {"hi": 3, "mr": 1, "kn": 1}
        assert metrics.success_rate == 2 / 5  # 2 outcomes / 5 queries
    
    def test_get_metrics_with_date_range_filter(self, mock_db):
        """Test getting metrics with specific date range"""
        tracker = ImpactTracker(mock_db)
        
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # Setup minimal mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 0
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        filters = MetricFilters(start_date=start_date, end_date=end_date)
        metrics = tracker.get_metrics(filters)
        
        assert metrics.period_start == start_date
        assert metrics.period_end == end_date
    
    def test_get_metrics_with_language_filter(self, mock_db):
        """Test getting metrics filtered by language"""
        tracker = ImpactTracker(mock_db)
        
        # Setup minimal mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 0
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        filters = MetricFilters(language="hi")
        metrics = tracker.get_metrics(filters)
        
        # Verify filter was applied (language filter should be in the query)
        assert mock_query.filter.called
    
    def test_get_metrics_with_region_filter(self, mock_db):
        """Test getting metrics filtered by region"""
        tracker = ImpactTracker(mock_db)
        
        # Setup minimal mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 0
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        filters = MetricFilters(region="Maharashtra")
        metrics = tracker.get_metrics(filters)
        
        # Verify filter was applied
        assert mock_query.filter.called
    
    def test_get_metrics_with_event_type_filter(self, mock_db):
        """Test getting metrics filtered by event type"""
        tracker = ImpactTracker(mock_db)
        
        # Setup minimal mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 0
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        filters = MetricFilters(event_type="scheme_accessed")
        metrics = tracker.get_metrics(filters)
        
        # Verify filter was applied
        assert mock_query.filter.called
    
    def test_get_metrics_with_outcome_type_filter(self, mock_db):
        """Test getting metrics filtered by outcome type"""
        tracker = ImpactTracker(mock_db)
        
        # Setup minimal mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 0
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        filters = MetricFilters(outcome_type="scheme_applied")
        metrics = tracker.get_metrics(filters)
        
        # Verify filter was applied
        assert mock_query.filter.called
    
    def test_get_metrics_with_service_category_filter(self, mock_db):
        """Test getting metrics filtered by service category"""
        tracker = ImpactTracker(mock_db)
        
        # Setup minimal mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 0
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        # Test schemes category
        filters = MetricFilters(service_category="schemes")
        metrics = tracker.get_metrics(filters)
        assert mock_query.filter.called
        
        # Test farmer category
        filters = MetricFilters(service_category="farmer")
        metrics = tracker.get_metrics(filters)
        
        # Test skills category
        filters = MetricFilters(service_category="skills")
        metrics = tracker.get_metrics(filters)
        
        # Test health category
        filters = MetricFilters(service_category="health")
        metrics = tracker.get_metrics(filters)
    
    def test_get_metrics_with_multiple_filters(self, mock_db):
        """Test getting metrics with multiple filters combined"""
        tracker = ImpactTracker(mock_db)
        
        # Setup minimal mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 0
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        filters = MetricFilters(
            language="hi",
            region="Maharashtra",
            service_category="schemes"
        )
        metrics = tracker.get_metrics(filters)
        
        # Verify multiple filters were applied
        assert mock_query.filter.call_count >= 3
    
    def test_get_metrics_success_rate_calculation(self, mock_db):
        """Test success rate calculation in metrics"""
        tracker = ImpactTracker(mock_db)
        
        # Mock 10 queries and 3 outcomes
        mock_query_queries = Mock()
        mock_query_queries.filter.return_value = mock_query_queries
        mock_query_queries.scalar.return_value = 10
        
        mock_query_outcomes = Mock()
        mock_query_outcomes.filter.return_value = mock_query_outcomes
        mock_query_outcomes.group_by.return_value = mock_query_outcomes
        mock_query_outcomes.all.return_value = [
            ("scheme_applied", 2),
            ("job_applied", 1)
        ]
        
        # Setup other mocks
        mock_query_default = Mock()
        mock_query_default.filter.return_value = mock_query_default
        mock_query_default.scalar.return_value = 0
        mock_query_default.group_by.return_value = mock_query_default
        mock_query_default.all.return_value = []
        
        mock_db.query.side_effect = [
            mock_query_default,  # users_served
            mock_query_queries,  # queries_resolved
            mock_query_default,  # schemes_accessed
            mock_query_default,  # farmers_assisted
            mock_query_default,  # jobs_discovered
            mock_query_default,  # health_checks
            mock_query_default,  # languages_used
            mock_query_default,  # events_by_type
            mock_query_outcomes   # outcomes_by_type
        ]
        
        filters = MetricFilters()
        metrics = tracker.get_metrics(filters)
        
        # Success rate should be 3/10 = 0.3
        assert metrics.success_rate == 0.3
    
    def test_get_metrics_success_rate_zero_queries(self, mock_db):
        """Test success rate when there are zero queries"""
        tracker = ImpactTracker(mock_db)
        
        # Setup minimal mocks with zero queries
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 0
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        filters = MetricFilters()
        metrics = tracker.get_metrics(filters)
        
        # Success rate should be 0.0 when no queries
        assert metrics.success_rate == 0.0
    
    def test_get_metrics_handles_database_error(self, mock_db):
        """Test that get_metrics handles database errors"""
        tracker = ImpactTracker(mock_db)
        
        # Simulate database error
        mock_db.query.side_effect = Exception("Database connection error")
        
        filters = MetricFilters()
        
        with pytest.raises(Exception):
            tracker.get_metrics(filters)


class TestReportGeneration:
    """Test report generation with different types"""
    
    def test_generate_daily_report(self, mock_db):
        """Test generating a daily report"""
        tracker = ImpactTracker(mock_db)
        
        # Setup minimal mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 0
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        report = tracker.generate_report(ReportType.DAILY)
        
        assert report.report_type == "daily"
        assert report.date_range.end_date - report.date_range.start_date == timedelta(days=1)
        assert report.metrics is not None
        assert report.regional_breakdown is not None
        assert report.language_breakdown is not None
        assert report.service_breakdown is not None
    
    def test_generate_weekly_report(self, mock_db):
        """Test generating a weekly report"""
        tracker = ImpactTracker(mock_db)
        
        # Setup minimal mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 0
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        report = tracker.generate_report(ReportType.WEEKLY)
        
        assert report.report_type == "weekly"
        assert report.date_range.end_date - report.date_range.start_date == timedelta(days=7)
    
    def test_generate_monthly_report(self, mock_db):
        """Test generating a monthly report"""
        tracker = ImpactTracker(mock_db)
        
        # Setup minimal mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 0
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        report = tracker.generate_report(ReportType.MONTHLY)
        
        assert report.report_type == "monthly"
        assert report.date_range.end_date - report.date_range.start_date == timedelta(days=30)
    
    def test_generate_quarterly_report(self, mock_db):
        """Test generating a quarterly report"""
        tracker = ImpactTracker(mock_db)
        
        # Setup minimal mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 0
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        report = tracker.generate_report(ReportType.QUARTERLY)
        
        assert report.report_type == "quarterly"
        assert report.date_range.end_date - report.date_range.start_date == timedelta(days=90)
    
    def test_generate_custom_report(self, mock_db):
        """Test generating a custom report with specific date range"""
        tracker = ImpactTracker(mock_db)
        
        # Setup minimal mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 0
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        start_date = datetime(2026, 1, 1)
        end_date = datetime(2026, 1, 31)
        date_range = DateRange(start_date=start_date, end_date=end_date)
        
        report = tracker.generate_report(ReportType.CUSTOM, date_range=date_range)
        
        assert report.report_type == "custom"
        assert report.date_range.start_date == start_date
        assert report.date_range.end_date == end_date
    
    def test_generate_custom_report_without_date_range(self, mock_db):
        """Test that custom report requires date_range parameter"""
        tracker = ImpactTracker(mock_db)
        
        with pytest.raises(ValueError, match="date_range required"):
            tracker.generate_report(ReportType.CUSTOM)
    
    def test_generate_report_includes_breakdowns(self, mock_db):
        """Test that report includes regional, language, and service breakdowns"""
        tracker = ImpactTracker(mock_db)
        
        # Mock regional breakdown
        mock_query_regional = Mock()
        mock_query_regional.filter.return_value = mock_query_regional
        mock_query_regional.group_by.return_value = mock_query_regional
        mock_query_regional.all.return_value = [
            ("Maharashtra", "scheme_accessed", 5),
            ("Karnataka", "job_discovered", 3)
        ]
        
        # Mock language breakdown
        mock_query_language = Mock()
        mock_query_language.filter.return_value = mock_query_language
        mock_query_language.group_by.return_value = mock_query_language
        mock_query_language.all.return_value = [
            ("hi", "query_submitted", 10),
            ("mr", "scheme_accessed", 5)
        ]
        
        # Mock service breakdown
        mock_query_service = Mock()
        mock_query_service.filter.return_value = mock_query_service
        mock_query_service.group_by.return_value = mock_query_service
        mock_query_service.all.return_value = [
            ("scheme_accessed", 5),
            ("crop_advice_requested", 3)
        ]
        
        # Setup default mocks for metrics
        mock_query_default = Mock()
        mock_query_default.filter.return_value = mock_query_default
        mock_query_default.scalar.return_value = 0
        mock_query_default.group_by.return_value = mock_query_default
        mock_query_default.all.return_value = []
        
        # Setup query side effects
        mock_db.query.side_effect = [
            # For get_metrics calls
            mock_query_default, mock_query_default, mock_query_default,
            mock_query_default, mock_query_default, mock_query_default,
            mock_query_default, mock_query_default, mock_query_default,
            # For breakdown calls
            mock_query_regional,
            mock_query_language,
            mock_query_service
        ]
        
        report = tracker.generate_report(ReportType.DAILY)
        
        assert isinstance(report.regional_breakdown, dict)
        assert isinstance(report.language_breakdown, dict)
        assert isinstance(report.service_breakdown, dict)


class TestDataAnonymization:
    """Test anonymization completeness in analytics"""
    
    def test_metrics_do_not_expose_user_ids(self, mock_db):
        """Test that metrics aggregation does not expose individual user IDs"""
        tracker = ImpactTracker(mock_db)
        
        # Setup minimal mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 5
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        filters = MetricFilters()
        metrics = tracker.get_metrics(filters)
        
        # Verify metrics only contain aggregated counts, not user IDs
        assert hasattr(metrics, 'users_served')
        assert isinstance(metrics.users_served, int)
        
        # Verify no user_id fields in the response
        metrics_dict = metrics.model_dump()
        assert 'user_id' not in str(metrics_dict)
        assert 'user_ids' not in str(metrics_dict)
    
    def test_report_does_not_expose_user_ids(self, mock_db):
        """Test that reports do not expose individual user IDs"""
        tracker = ImpactTracker(mock_db)
        
        # Setup minimal mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 0
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        report = tracker.generate_report(ReportType.DAILY)
        
        # Verify report only contains aggregated data
        report_dict = report.model_dump()
        assert 'user_id' not in str(report_dict)
        assert 'user_ids' not in str(report_dict)
    
    def test_regional_breakdown_anonymized(self, mock_db):
        """Test that regional breakdown is anonymized"""
        tracker = ImpactTracker(mock_db)
        
        # Mock regional breakdown query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [
            ("Maharashtra", "scheme_accessed", 10),
            ("Karnataka", "job_discovered", 5)
        ]
        
        mock_db.query.return_value = mock_query
        
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        breakdown = tracker._get_regional_breakdown(start_date, end_date)
        
        # Verify breakdown contains only aggregated counts by region
        assert isinstance(breakdown, dict)
        for region, data in breakdown.items():
            assert isinstance(data, dict)
            for event_type, count in data.items():
                assert isinstance(count, int)
        
        # Verify no user IDs in breakdown
        assert 'user_id' not in str(breakdown)
    
    def test_language_breakdown_anonymized(self, mock_db):
        """Test that language breakdown is anonymized"""
        tracker = ImpactTracker(mock_db)
        
        # Mock language breakdown query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [
            ("hi", "query_submitted", 20),
            ("mr", "scheme_accessed", 10)
        ]
        
        mock_db.query.return_value = mock_query
        
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        breakdown = tracker._get_language_breakdown(start_date, end_date)
        
        # Verify breakdown contains only aggregated counts by language
        assert isinstance(breakdown, dict)
        for language, data in breakdown.items():
            assert isinstance(data, dict)
            for event_type, count in data.items():
                assert isinstance(count, int)
        
        # Verify no user IDs in breakdown
        assert 'user_id' not in str(breakdown)
    
    def test_service_breakdown_anonymized(self, mock_db):
        """Test that service breakdown is anonymized"""
        tracker = ImpactTracker(mock_db)
        
        # Mock service breakdown query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [
            ("scheme_accessed", 15),
            ("crop_advice_requested", 8),
            ("job_discovered", 5)
        ]
        
        mock_db.query.return_value = mock_query
        
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        breakdown = tracker._get_service_breakdown(start_date, end_date)
        
        # Verify breakdown contains only aggregated counts by service
        assert isinstance(breakdown, dict)
        for service, data in breakdown.items():
            assert isinstance(data, dict)
            for event_type, count in data.items():
                assert isinstance(count, int)
        
        # Verify no user IDs in breakdown
        assert 'user_id' not in str(breakdown)
    
    def test_events_by_type_anonymized(self, mock_db):
        """Test that events_by_type aggregation is anonymized"""
        tracker = ImpactTracker(mock_db)
        
        # Mock events by type query
        mock_query_events = Mock()
        mock_query_events.filter.return_value = mock_query_events
        mock_query_events.group_by.return_value = mock_query_events
        mock_query_events.all.return_value = [
            ("query_submitted", 50),
            ("scheme_accessed", 30),
            ("job_discovered", 20)
        ]
        
        # Setup other mocks
        mock_query_default = Mock()
        mock_query_default.filter.return_value = mock_query_default
        mock_query_default.scalar.return_value = 0
        mock_query_default.group_by.return_value = mock_query_default
        mock_query_default.all.return_value = []
        
        mock_db.query.side_effect = [
            mock_query_default,  # users_served
            mock_query_default,  # queries_resolved
            mock_query_default,  # schemes_accessed
            mock_query_default,  # farmers_assisted
            mock_query_default,  # jobs_discovered
            mock_query_default,  # health_checks
            mock_query_default,  # languages_used
            mock_query_events,   # events_by_type
            mock_query_default   # outcomes_by_type
        ]
        
        filters = MetricFilters()
        metrics = tracker.get_metrics(filters)
        
        # Verify events_by_type contains only counts
        assert isinstance(metrics.events_by_type, dict)
        for event_type, count in metrics.events_by_type.items():
            assert isinstance(count, int)
        
        # Verify no user IDs
        assert 'user_id' not in str(metrics.events_by_type)
    
    def test_outcomes_by_type_anonymized(self, mock_db):
        """Test that outcomes_by_type aggregation is anonymized"""
        tracker = ImpactTracker(mock_db)
        
        # Mock outcomes by type query
        mock_query_outcomes = Mock()
        mock_query_outcomes.filter.return_value = mock_query_outcomes
        mock_query_outcomes.group_by.return_value = mock_query_outcomes
        mock_query_outcomes.all.return_value = [
            ("scheme_applied", 15),
            ("job_applied", 10),
            ("crop_planted", 8)
        ]
        
        # Setup other mocks
        mock_query_default = Mock()
        mock_query_default.filter.return_value = mock_query_default
        mock_query_default.scalar.return_value = 0
        mock_query_default.group_by.return_value = mock_query_default
        mock_query_default.all.return_value = []
        
        mock_db.query.side_effect = [
            mock_query_default,  # users_served
            mock_query_default,  # queries_resolved
            mock_query_default,  # schemes_accessed
            mock_query_default,  # farmers_assisted
            mock_query_default,  # jobs_discovered
            mock_query_default,  # health_checks
            mock_query_default,  # languages_used
            mock_query_default,  # events_by_type
            mock_query_outcomes  # outcomes_by_type
        ]
        
        filters = MetricFilters()
        metrics = tracker.get_metrics(filters)
        
        # Verify outcomes_by_type contains only counts
        assert isinstance(metrics.outcomes_by_type, dict)
        for outcome_type, count in metrics.outcomes_by_type.items():
            assert isinstance(count, int)
        
        # Verify no user IDs
        assert 'user_id' not in str(metrics.outcomes_by_type)
    
    def test_aggregation_uses_count_not_list(self, mock_db):
        """Test that aggregation returns counts, not lists of events"""
        tracker = ImpactTracker(mock_db)
        
        # Setup minimal mocks
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 100
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = [("hi", 50), ("mr", 30), ("kn", 20)]
        
        mock_db.query.return_value = mock_query
        
        filters = MetricFilters()
        metrics = tracker.get_metrics(filters)
        
        # Verify all metrics are integers (counts), not lists
        assert isinstance(metrics.users_served, int)
        assert isinstance(metrics.queries_resolved, int)
        assert isinstance(metrics.schemes_accessed, int)
        assert isinstance(metrics.farmers_assisted, int)
        assert isinstance(metrics.jobs_discovered, int)
        assert isinstance(metrics.health_checks_performed, int)
        
        # Verify dictionaries contain counts, not event objects
        for count in metrics.languages_used.values():
            assert isinstance(count, int)
        
        for count in metrics.events_by_type.values():
            assert isinstance(count, int)
        
        for count in metrics.outcomes_by_type.values():
            assert isinstance(count, int)
