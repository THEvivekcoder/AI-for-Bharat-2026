"""Test script for cache API endpoints"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_cache_endpoints():
    """Test cache API endpoints"""
    print("\n=== Testing Cache API Endpoints ===\n")
    
    # Test 1: Cache content
    print("Test 1: POST /api/cache/content - Cache content...")
    response = requests.post(
        f"{BASE_URL}/api/cache/content",
        json={
            "content_type": "schemes",
            "content": {
                "id": "scheme_001",
                "name": "PM-KISAN",
                "description": "Direct income support to farmers",
                "benefits": ["Rs 6000 per year"]
            },
            "priority": 1,
            "language": "en",
            "ttl_hours": 168
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["success"] == True
    print("✓ Test 1 passed\n")
    
    # Test 2: Query cache
    print("Test 2: POST /api/cache/query - Query cached content...")
    response = requests.post(
        f"{BASE_URL}/api/cache/query",
        json={
            "content_type": "schemes",
            "language": "en"
        }
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: Found {data['count']} items")
    assert response.status_code == 200
    assert data["success"] == True
    assert data["count"] > 0
    print("✓ Test 2 passed\n")
    
    # Test 3: Get cache stats
    print("Test 3: GET /api/cache/stats - Get cache statistics...")
    response = requests.get(f"{BASE_URL}/api/cache/stats")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data['stats'], indent=2)}")
    assert response.status_code == 200
    assert data["success"] == True
    print("✓ Test 3 passed\n")
    
    # Test 4: Check connectivity
    print("Test 4: GET /api/cache/connectivity - Check network connectivity...")
    response = requests.get(f"{BASE_URL}/api/cache/connectivity")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: Online={data['is_online']}")
    assert response.status_code == 200
    print("✓ Test 4 passed\n")
    
    # Test 5: Sync cache
    print("Test 5: POST /api/cache/sync - Sync cache with server...")
    response = requests.post(
        f"{BASE_URL}/api/cache/sync",
        json={"force": True}
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: Synced={data['synced_count']}, Failed={data['failed_count']}")
    assert response.status_code == 200
    print("✓ Test 5 passed\n")
    
    # Test 6: Invalidate cache
    print("Test 6: DELETE /api/cache/invalidate - Invalidate stale cache...")
    response = requests.delete(
        f"{BASE_URL}/api/cache/invalidate",
        params={"max_age_days": 30}
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: Invalidated {data['invalidated_count']} items")
    assert response.status_code == 200
    assert data["success"] == True
    print("✓ Test 6 passed\n")
    
    # Test 7: Clear cache
    print("Test 7: DELETE /api/cache/clear - Clear all cache...")
    response = requests.delete(f"{BASE_URL}/api/cache/clear")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {data['message']}")
    assert response.status_code == 200
    assert data["success"] == True
    print("✓ Test 7 passed\n")
    
    print("✓ All cache endpoint tests passed!")


def main():
    """Run all tests"""
    print("=" * 60)
    print("CACHE API ENDPOINT TESTS")
    print("=" * 60)
    print("\nMake sure the server is running: uvicorn app.main:app --reload")
    print("Press Enter to continue or Ctrl+C to cancel...")
    input()
    
    try:
        test_cache_endpoints()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to server")
        print("Make sure the server is running: uvicorn app.main:app --reload")
    except AssertionError as e:
        print(f"\n✗ Test assertion failed: {e}")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
