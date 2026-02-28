#!/usr/bin/env python3
"""Test script for Impact Tracking API endpoints"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_record_interaction_event():
    """Test POST /api/impact/event with interaction event"""
    print("\n=== Testing POST /api/impact/event (interaction) ===")
    
    # Test with anonymous user (no user_id)
    payload = {
        "event": {
            "event_type": "query_submitted",
            "event_data": {
                "query": "What schemes are available for farmers?",
                "state": "Maharashtra",
                "district": "Pune"
            },
            "language": "hi"
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/impact/event", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    data = response.json()
    assert data["success"] == True
    assert "event_id" in data
    print("✓ Interaction event recorded successfully (anonymous)")
    return data["event_id"]


def test_record_outcome_event():
    """Test POST /api/impact/event with outcome event"""
    print("\n=== Testing POST /api/impact/event (outcome) ===")
    
    # Test with anonymous user (no user_id)
    payload = {
        "outcome": {
            "outcome_type": "scheme_applied",
            "outcome_data": {
                "scheme_id": "PM-KISAN-2024",
                "scheme_name": "PM-KISAN",
                "state": "Maharashtra"
            }
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/impact/event", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    data = response.json()
    assert data["success"] == True
    assert "event_id" in data
    print("✓ Outcome event recorded successfully (anonymous)")
    return data["event_id"]


def test_record_multiple_events():
    """Record multiple events for testing metrics"""
    print("\n=== Recording multiple events for metrics testing ===")
    
    # Use anonymous users (no user_id) to avoid foreign key issues
    events = [
        {
            "event": {
                "event_type": "scheme_accessed",
                "event_data": {"scheme_id": "PM-KISAN-2024", "state": "Karnataka"},
                "language": "kn"
            }
        },
        {
            "event": {
                "event_type": "crop_advice_requested",
                "event_data": {"crop": "rice", "state": "Punjab"},
                "language": "pa"
            }
        },
        {
            "event": {
                "event_type": "job_discovered",
                "event_data": {"job_id": "SSC-2024-001", "state": "Delhi"},
                "language": "hi"
            }
        },
        {
            "outcome": {
                "outcome_type": "job_applied",
                "outcome_data": {"job_id": "SSC-2024-001"}
            }
        }
    ]
    
    for i, payload in enumerate(events, 1):
        response = requests.post(f"{BASE_URL}/api/impact/event", json=payload)
        assert response.status_code == 201, f"Event {i} failed: {response.status_code}"
        print(f"✓ Event {i} recorded")
    
    print("✓ All events recorded successfully")


def test_get_metrics():
    """Test GET /api/impact with various filters"""
    print("\n=== Testing GET /api/impact (metrics) ===")
    
    # Test without filters (default last 30 days)
    print("\n--- Metrics without filters ---")
    response = requests.get(f"{BASE_URL}/api/impact")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "users_served" in data
    assert "queries_resolved" in data
    assert "success_rate" in data
    print("✓ Metrics retrieved successfully")
    
    # Test with language filter
    print("\n--- Metrics with language filter ---")
    response = requests.get(f"{BASE_URL}/api/impact?language=hi")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Users served (Hindi): {data['users_served']}")
    print("✓ Language filter works")
    
    # Test with date range
    print("\n--- Metrics with date range ---")
    end_date = datetime.utcnow().isoformat()
    start_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
    response = requests.get(
        f"{BASE_URL}/api/impact?start_date={start_date}&end_date={end_date}"
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Queries resolved (last 7 days): {data['queries_resolved']}")
    print("✓ Date range filter works")
    
    # Test with service category filter
    print("\n--- Metrics with service category filter ---")
    response = requests.get(f"{BASE_URL}/api/impact?service_category=farmer")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Farmers assisted: {data['farmers_assisted']}")
    print("✓ Service category filter works")


def test_generate_report():
    """Test GET /api/impact/report"""
    print("\n=== Testing GET /api/impact/report ===")
    
    # Test daily report
    print("\n--- Daily report ---")
    response = requests.get(f"{BASE_URL}/api/impact/report?report_type=daily")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "report_type" in data
    assert data["report_type"] == "daily"
    assert "metrics" in data
    assert "regional_breakdown" in data
    assert "language_breakdown" in data
    assert "service_breakdown" in data
    print("✓ Daily report generated successfully")
    
    # Test weekly report
    print("\n--- Weekly report ---")
    response = requests.get(f"{BASE_URL}/api/impact/report?report_type=weekly")
    print(f"Status: {response.status_code}")
    data = response.json()
    assert data["report_type"] == "weekly"
    print("✓ Weekly report generated successfully")
    
    # Test monthly report (default)
    print("\n--- Monthly report (default) ---")
    response = requests.get(f"{BASE_URL}/api/impact/report")
    print(f"Status: {response.status_code}")
    data = response.json()
    assert data["report_type"] == "monthly"
    print("✓ Monthly report generated successfully")
    
    # Test custom report
    print("\n--- Custom report ---")
    end_date = datetime.utcnow().isoformat()
    start_date = (datetime.utcnow() - timedelta(days=14)).isoformat()
    response = requests.get(
        f"{BASE_URL}/api/impact/report?report_type=custom&start_date={start_date}&end_date={end_date}"
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    assert data["report_type"] == "custom"
    print("✓ Custom report generated successfully")


def test_error_cases():
    """Test error handling"""
    print("\n=== Testing error cases ===")
    
    # Test missing both event and outcome
    print("\n--- Missing both event and outcome ---")
    response = requests.post(f"{BASE_URL}/api/impact/event", json={})
    print(f"Status: {response.status_code}")
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    print("✓ Correctly rejects empty request")
    
    # Test invalid report type
    print("\n--- Invalid report type ---")
    response = requests.get(f"{BASE_URL}/api/impact/report?report_type=invalid")
    print(f"Status: {response.status_code}")
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    print("✓ Correctly rejects invalid report type")
    
    # Test custom report without dates
    print("\n--- Custom report without dates ---")
    response = requests.get(f"{BASE_URL}/api/impact/report?report_type=custom")
    print(f"Status: {response.status_code}")
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    print("✓ Correctly requires dates for custom report")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Impact Tracking API Endpoint Tests")
    print("=" * 60)
    
    try:
        # Test event recording
        test_record_interaction_event()
        test_record_outcome_event()
        test_record_multiple_events()
        
        # Test metrics
        test_get_metrics()
        
        # Test reports
        test_generate_report()
        
        # Test error cases
        test_error_cases()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Could not connect to server. Is it running on http://localhost:8000?")
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
