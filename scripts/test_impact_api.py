"""Test script for Impact Tracker API endpoints"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"


def test_record_interaction_event():
    """Test POST /api/impact/event/interaction"""
    print("\n=== Testing POST /api/impact/event/interaction ===")
    
    # Test with anonymous user
    payload = {
        "event_type": "query_submitted",
        "event_data": {
            "query": "PM-KISAN scheme details",
            "state": "Karnataka"
        },
        "language": "kn"
    }
    
    response = requests.post(f"{BASE_URL}/api/impact/event/interaction", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        print("✓ Interaction event recorded successfully")
        return True
    else:
        print("✗ Failed to record interaction event")
        return False


def test_record_outcome_event():
    """Test POST /api/impact/event/outcome"""
    print("\n=== Testing POST /api/impact/event/outcome ===")
    
    payload = {
        "outcome_type": "scheme_applied",
        "outcome_data": {
            "scheme_id": "PM-KISAN",
            "application_id": "APP456"
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/impact/event/outcome", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        print("✓ Outcome event recorded successfully")
        return True
    else:
        print("✗ Failed to record outcome event")
        return False


def test_get_metrics():
    """Test POST /api/impact/metrics"""
    print("\n=== Testing POST /api/impact/metrics ===")
    
    # Test with default filters
    payload = {}
    
    response = requests.post(f"{BASE_URL}/api/impact/metrics", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Users served: {data['users_served']}")
        print(f"Queries resolved: {data['queries_resolved']}")
        print(f"Success rate: {data['success_rate']:.2%}")
        print(f"Languages used: {data['languages_used']}")
        print("✓ Metrics retrieved successfully")
        return True
    else:
        print(f"✗ Failed to get metrics: {response.text}")
        return False


def test_get_metrics_with_filters():
    """Test POST /api/impact/metrics with filters"""
    print("\n=== Testing POST /api/impact/metrics with filters ===")
    
    # Test with language filter
    payload = {
        "language": "hi"
    }
    
    response = requests.post(f"{BASE_URL}/api/impact/metrics", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Hindi queries: {data['queries_resolved']}")
        print("✓ Filtered metrics retrieved successfully")
        return True
    else:
        print(f"✗ Failed to get filtered metrics: {response.text}")
        return False


def test_generate_daily_report():
    """Test GET /api/impact/report/daily"""
    print("\n=== Testing GET /api/impact/report/daily ===")
    
    response = requests.get(f"{BASE_URL}/api/impact/report/daily")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Report type: {data['report_type']}")
        print(f"Users served: {data['metrics']['users_served']}")
        print(f"Regional breakdown: {len(data['regional_breakdown'])} regions")
        print(f"Language breakdown: {len(data['language_breakdown'])} languages")
        print("✓ Daily report generated successfully")
        return True
    else:
        print(f"✗ Failed to generate daily report: {response.text}")
        return False


def test_generate_weekly_report():
    """Test GET /api/impact/report/weekly"""
    print("\n=== Testing GET /api/impact/report/weekly ===")
    
    response = requests.get(f"{BASE_URL}/api/impact/report/weekly")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Report type: {data['report_type']}")
        print(f"Users served: {data['metrics']['users_served']}")
        print("✓ Weekly report generated successfully")
        return True
    else:
        print(f"✗ Failed to generate weekly report: {response.text}")
        return False


def main():
    """Run all API tests"""
    print("=" * 60)
    print("Impact Tracker API Test Suite")
    print("=" * 60)
    print("\nMake sure the server is running on http://localhost:8000")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("\n✗ Server is not responding correctly")
            return 1
    except requests.exceptions.ConnectionError:
        print("\n✗ Cannot connect to server. Please start the server first.")
        print("Run: uvicorn app.main:app --reload")
        return 1
    
    results = []
    
    # Run tests
    results.append(("Record Interaction Event", test_record_interaction_event()))
    results.append(("Record Outcome Event", test_record_outcome_event()))
    results.append(("Get Metrics", test_get_metrics()))
    results.append(("Get Metrics with Filters", test_get_metrics_with_filters()))
    results.append(("Generate Daily Report", test_generate_daily_report()))
    results.append(("Generate Weekly Report", test_generate_weekly_report()))
    
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
        print("\n🎉 All API tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
