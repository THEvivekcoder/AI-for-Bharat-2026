#!/usr/bin/env python3
"""Test script for Impact Tracker models"""
import sys
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.impact import InteractionEvent, OutcomeEvent
from app.schemas.impact import (
    InteractionEventCreate,
    OutcomeEventCreate,
    InteractionEventType,
    OutcomeEventType
)


def test_interaction_event_creation():
    """Test creating an interaction event"""
    db = SessionLocal()
    try:
        # Create a test interaction event with NULL user_id (anonymous)
        event = InteractionEvent(
            user_id=None,  # Anonymous tracking
            event_type="query_submitted",
            event_data={"query": "test query", "service": "schemes"},
            language="hi",
            timestamp=datetime.utcnow()
        )
        
        db.add(event)
        db.commit()
        db.refresh(event)
        
        print(f"✓ Created InteractionEvent: {event.interaction_id}")
        print(f"  - Event Type: {event.event_type}")
        print(f"  - Language: {event.language}")
        print(f"  - Timestamp: {event.timestamp}")
        
        # Query it back
        retrieved = db.query(InteractionEvent).filter(
            InteractionEvent.interaction_id == event.interaction_id
        ).first()
        
        assert retrieved is not None
        assert retrieved.event_type == "query_submitted"
        assert retrieved.language == "hi"
        print("✓ InteractionEvent retrieved successfully")
        
        # Clean up
        db.delete(event)
        db.commit()
        print("✓ InteractionEvent deleted successfully")
        
        return True
    except Exception as e:
        print(f"✗ Error testing InteractionEvent: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_outcome_event_creation():
    """Test creating an outcome event"""
    db = SessionLocal()
    try:
        # Create a test outcome event with NULL user_id (anonymous)
        outcome = OutcomeEvent(
            user_id=None,  # Anonymous tracking
            outcome_type="scheme_applied",
            outcome_data={"scheme_id": str(uuid.uuid4()), "scheme_name": "Test Scheme"},
            timestamp=datetime.utcnow()
        )
        
        db.add(outcome)
        db.commit()
        db.refresh(outcome)
        
        print(f"✓ Created OutcomeEvent: {outcome.outcome_id}")
        print(f"  - Outcome Type: {outcome.outcome_type}")
        print(f"  - Timestamp: {outcome.timestamp}")
        
        # Query it back
        retrieved = db.query(OutcomeEvent).filter(
            OutcomeEvent.outcome_id == outcome.outcome_id
        ).first()
        
        assert retrieved is not None
        assert retrieved.outcome_type == "scheme_applied"
        print("✓ OutcomeEvent retrieved successfully")
        
        # Clean up
        db.delete(outcome)
        db.commit()
        print("✓ OutcomeEvent deleted successfully")
        
        return True
    except Exception as e:
        print(f"✗ Error testing OutcomeEvent: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_schemas():
    """Test Pydantic schemas"""
    try:
        # Test InteractionEventCreate schema
        interaction_data = InteractionEventCreate(
            user_id=str(uuid.uuid4()),
            event_type=InteractionEventType.QUERY_SUBMITTED,
            event_data={"query": "test"},
            language="hi"
        )
        print(f"✓ InteractionEventCreate schema validated")
        print(f"  - Event Type: {interaction_data.event_type}")
        
        # Test OutcomeEventCreate schema
        outcome_data = OutcomeEventCreate(
            user_id=str(uuid.uuid4()),
            outcome_type=OutcomeEventType.SCHEME_APPLIED,
            outcome_data={"scheme_id": str(uuid.uuid4())}
        )
        print(f"✓ OutcomeEventCreate schema validated")
        print(f"  - Outcome Type: {outcome_data.outcome_type}")
        
        return True
    except Exception as e:
        print(f"✗ Error testing schemas: {e}")
        return False


def test_anonymous_events():
    """Test creating events without user_id (anonymous tracking)"""
    db = SessionLocal()
    try:
        # Create anonymous interaction event
        event = InteractionEvent(
            user_id=None,  # Anonymous
            event_type="voice_interaction",
            event_data={"language_detected": "hi"},
            language="hi",
            timestamp=datetime.utcnow()
        )
        
        db.add(event)
        db.commit()
        db.refresh(event)
        
        print(f"✓ Created anonymous InteractionEvent: {event.interaction_id}")
        assert event.user_id is None
        print("✓ Anonymous tracking works correctly")
        
        # Clean up
        db.delete(event)
        db.commit()
        
        return True
    except Exception as e:
        print(f"✗ Error testing anonymous events: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Impact Tracker Models")
    print("=" * 60)
    
    tests = [
        ("InteractionEvent Creation", test_interaction_event_creation),
        ("OutcomeEvent Creation", test_outcome_event_creation),
        ("Pydantic Schemas", test_schemas),
        ("Anonymous Events", test_anonymous_events),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 60)
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
