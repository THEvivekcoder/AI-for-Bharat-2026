"""Test script for Impact Tracker service"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.impact import InteractionEvent, OutcomeEvent
from app.models.user import User
from app.services.impact_tracker import ImpactTracker
from app.schemas.impact import (
    InteractionEventCreate,
    InteractionEventType,
    OutcomeEventCreate,
    OutcomeEventType,
    MetricFilters,
    ReportType
)
import uuid


def create_test_user(db: Session) -> str:
    """Create a test user and return user_id"""
    user = User(
        user_id=uuid.uuid4(),
        phone_number=f"+91{uuid.uuid4().hex[:10]}",
        language="hi"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return str(user.user_id)


def test_record_interaction():
    """Test recording interaction events"""
    print("\n=== Testing record_interaction ===")
    db = SessionLocal()
    
    try:
        tracker = ImpactTracker(db)
        
        # Create test user
        user_id = create_test_user(db)
        print(f"Created test user: {user_id}")
        
        # Test various interaction types
        test_events = [
            InteractionEventCreate(
                user_id=user_id,
                event_type=InteractionEventType.QUERY_SUBMITTED,
                event_data={"query": "government schemes for farmers", "state": "Maharashtra"},
                language="hi"
            ),
            InteractionEventCreate(
                user_id=user_id,
                event_type=InteractionEventType.SCHEME_ACCESSED,
                event_data={"scheme_id": "PM-KISAN", "state": "Maharashtra"},
                language="hi"
            ),
            InteractionEventCreate(
                user_id=user_id,
                event_type=InteractionEventType.CROP_ADVICE_REQUESTED,
                event_data={"soil_type": "clay", "state": "Maharashtra", "district": "Pune"},
                language="mr"
            ),
            InteractionEventCreate(
                user_id=None,  # Anonymous user
                event_type=InteractionEventType.VOICE_INTERACTION,
                event_data={"duration_seconds": 45},
                language="hi"
            )
        ]
        
        for event in test_events:
            interaction = tracker.record_interaction(event)
            print(f"✓ Recorded {event.event_type.value}: {interaction.interaction_id}")
        
        print("✓ All interaction events recorded successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error recording interactions: {str(e)}")
        return False
    finally:
        db.close()


def test_record_outcome():
    """Test recording outcome events"""
    print("\n=== Testing record_outcome ===")
    db = SessionLocal()
    
    try:
        tracker = ImpactTracker(db)
        
        # Create test user
        user_id = create_test_user(db)
        print(f"Created test user: {user_id}")
        
        # Test various outcome types
        test_outcomes = [
            OutcomeEventCreate(
                user_id=user_id,
                outcome_type=OutcomeEventType.SCHEME_APPLIED,
                outcome_data={"scheme_id": "PM-KISAN", "application_id": "APP123"}
            ),
            OutcomeEventCreate(
                user_id=user_id,
                outcome_type=OutcomeEventType.CROP_PLANTED,
                outcome_data={"crop": "wheat", "area_acres": 5}
            ),
            OutcomeEventCreate(
                user_id=user_id,
                outcome_type=OutcomeEventType.RECOMMENDATION_FOLLOWED,
                outcome_data={"recommendation_type": "fertilizer", "action": "purchased"}
            )
        ]
        
        for outcome in test_outcomes:
            outcome_event = tracker.record_outcome(outcome)
            print(f"✓ Recorded {outcome.outcome_type.value}: {outcome_event.outcome_id}")
        
        print("✓ All outcome events recorded successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error recording outcomes: {str(e)}")
        return False
    finally:
        db.close()


def test_get_metrics():
    """Test getting aggregated metrics"""
    print("\n=== Testing get_metrics ===")
    db = SessionLocal()
    
    try:
        tracker = ImpactTracker(db)
        
        # Test with default filters (last 30 days)
        print("\n--- Default metrics (last 30 days) ---")
        filters = MetricFilters()
        metrics = tracker.get_metrics(filters)
        
        print(f"Users served: {metrics.users_served}")
        print(f"Queries resolved: {metrics.queries_resolved}")
        print(f"Schemes accessed: {metrics.schemes_accessed}")
        print(f"Farmers assisted: {metrics.farmers_assisted}")
        print(f"Jobs discovered: {metrics.jobs_discovered}")
        print(f"Health checks: {metrics.health_checks_performed}")
        print(f"Success rate: {metrics.success_rate:.2%}")
        print(f"Languages used: {metrics.languages_used}")
        print(f"Events by type: {metrics.events_by_type}")
        print(f"Outcomes by type: {metrics.outcomes_by_type}")
        
        # Test with language filter
        print("\n--- Metrics filtered by language (Hindi) ---")
        filters_hindi = MetricFilters(language="hi")
        metrics_hindi = tracker.get_metrics(filters_hindi)
        print(f"Hindi queries: {metrics_hindi.queries_resolved}")
        
        # Test with date range filter
        print("\n--- Metrics for last 7 days ---")
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        filters_week = MetricFilters(start_date=start_date, end_date=end_date)
        metrics_week = tracker.get_metrics(filters_week)
        print(f"Queries (last 7 days): {metrics_week.queries_resolved}")
        
        # Test with service category filter
        print("\n--- Metrics for farmer service ---")
        filters_farmer = MetricFilters(service_category="farmer")
        metrics_farmer = tracker.get_metrics(filters_farmer)
        print(f"Farmer service queries: {metrics_farmer.queries_resolved}")
        print(f"Farmers assisted: {metrics_farmer.farmers_assisted}")
        
        print("\n✓ Metrics retrieval successful")
        return True
        
    except Exception as e:
        print(f"✗ Error getting metrics: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_generate_report():
    """Test generating impact reports"""
    print("\n=== Testing generate_report ===")
    db = SessionLocal()
    
    try:
        tracker = ImpactTracker(db)
        
        # Test daily report
        print("\n--- Daily Report ---")
        daily_report = tracker.generate_report(ReportType.DAILY)
        print(f"Report type: {daily_report.report_type}")
        print(f"Period: {daily_report.date_range.start_date} to {daily_report.date_range.end_date}")
        print(f"Users served: {daily_report.metrics.users_served}")
        print(f"Queries resolved: {daily_report.metrics.queries_resolved}")
        print(f"Regional breakdown: {len(daily_report.regional_breakdown)} regions")
        print(f"Language breakdown: {len(daily_report.language_breakdown)} languages")
        print(f"Service breakdown: {len(daily_report.service_breakdown)} services")
        
        # Test weekly report
        print("\n--- Weekly Report ---")
        weekly_report = tracker.generate_report(ReportType.WEEKLY)
        print(f"Period: {weekly_report.date_range.start_date} to {weekly_report.date_range.end_date}")
        print(f"Users served: {weekly_report.metrics.users_served}")
        
        # Test monthly report
        print("\n--- Monthly Report ---")
        monthly_report = tracker.generate_report(ReportType.MONTHLY)
        print(f"Period: {monthly_report.date_range.start_date} to {monthly_report.date_range.end_date}")
        print(f"Users served: {monthly_report.metrics.users_served}")
        
        print("\n✓ Report generation successful")
        return True
        
    except Exception as e:
        print(f"✗ Error generating report: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """Run all tests"""
    print("=" * 60)
    print("Impact Tracker Service Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Record Interaction", test_record_interaction()))
    results.append(("Record Outcome", test_record_outcome()))
    results.append(("Get Metrics", test_get_metrics()))
    results.append(("Generate Report", test_generate_report()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
