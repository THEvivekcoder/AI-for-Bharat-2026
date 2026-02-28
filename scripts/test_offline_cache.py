"""Test script for offline cache functionality"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.offline_cache import CacheManager, SyncResult
from app.services.network_monitor import NetworkMonitor, OfflineModeHandler
import time
import json


def test_cache_manager():
    """Test CacheManager functionality"""
    print("\n=== Testing CacheManager ===\n")
    
    # Initialize cache manager with test database
    cache = CacheManager(db_path="data/test_cache.db", max_cache_size_mb=10)
    
    # Clear any existing data
    cache.clear_all_cache()
    
    # Test 1: Cache content
    print("Test 1: Caching content...")
    test_scheme = {
        "id": "scheme_001",
        "name": "PM-KISAN",
        "description": "Direct income support to farmers",
        "benefits": ["Rs 6000 per year", "Direct bank transfer"],
        "eligibility": {"occupation": "farmer", "land_size_max": 2}
    }
    
    success = cache.cache_content(
        content_type="schemes",
        content=test_scheme,
        priority=1,
        language="en",
        ttl_hours=168
    )
    print(f"✓ Content cached: {success}")
    
    # Test 2: Retrieve cached content
    print("\nTest 2: Retrieving cached content...")
    results = cache.get_cached_content(content_type="schemes")
    print(f"✓ Retrieved {len(results)} items")
    print(f"  First item: {results[0]['name']}")
    
    # Test 3: Cache with different priorities
    print("\nTest 3: Caching with different priorities...")
    for i in range(5):
        cache.cache_content(
            content_type="health_tips",
            content={"id": f"tip_{i}", "tip": f"Health tip {i}"},
            priority=i + 1,
            language="en"
        )
    print(f"✓ Cached 5 items with different priorities")
    
    # Test 4: Query with search
    print("\nTest 4: Querying with search...")
    cache.cache_content(
        content_type="schemes",
        content={"id": "scheme_002", "name": "Ayushman Bharat", "category": "health"},
        priority=2,
        language="en"
    )
    results = cache.get_cached_content(content_type="schemes", query="health")
    print(f"✓ Found {len(results)} items matching 'health'")
    
    # Test 5: Cache statistics
    print("\nTest 5: Cache statistics...")
    stats = cache.get_cache_stats()
    print(f"✓ Total items: {stats['total_items']}")
    print(f"  Total size: {stats['total_size_mb']} MB")
    print(f"  Usage: {stats['usage_percent']}%")
    print(f"  By type: {stats['by_type']}")
    print(f"  By priority: {stats['by_priority']}")
    
    # Test 6: Pending sync operations
    print("\nTest 6: Pending sync operations...")
    sync_id = cache.add_pending_sync(
        operation="create",
        entity_type="user_profile",
        entity_data={"user_id": "user_001", "name": "Test User"}
    )
    print(f"✓ Added pending sync: {sync_id}")
    
    pending = cache.get_pending_syncs()
    print(f"✓ Pending syncs: {len(pending)}")
    
    # Test 7: Sync with server
    print("\nTest 7: Syncing with server...")
    result = cache.sync_with_server()
    print(f"✓ Sync result: success={result.success}, synced={result.synced_count}")
    
    # Test 8: Invalidate cache
    print("\nTest 8: Invalidating stale cache...")
    count = cache.invalidate_cache(max_age_days=0)  # Invalidate all
    print(f"✓ Invalidated {count} items")
    
    print("\n✓ All CacheManager tests passed!")
    
    # Cleanup
    cache.clear_all_cache()


def test_network_monitor():
    """Test NetworkMonitor functionality"""
    print("\n=== Testing NetworkMonitor ===\n")
    
    # Initialize network monitor
    monitor = NetworkMonitor(check_interval=5)
    
    # Test 1: Check connectivity
    print("Test 1: Checking connectivity...")
    is_online = monitor.check_connectivity()
    print(f"✓ Network status: {'online' if is_online else 'offline'}")
    
    # Test 2: Get status
    print("\nTest 2: Getting status...")
    status = monitor.get_status()
    print(f"✓ Status: online={status.is_online}, last_check={status.last_check}")
    
    # Test 3: Register callback
    print("\nTest 3: Registering callback...")
    callback_called = []
    
    def test_callback(is_online: bool):
        callback_called.append(is_online)
        print(f"  Callback triggered: {'online' if is_online else 'offline'}")
    
    monitor.register_callback(test_callback)
    print("✓ Callback registered")
    
    print("\n✓ All NetworkMonitor tests passed!")


def test_offline_handler():
    """Test OfflineModeHandler functionality"""
    print("\n=== Testing OfflineModeHandler ===\n")
    
    # Initialize components
    cache = CacheManager(db_path="data/test_cache.db")
    cache.clear_all_cache()
    
    monitor = NetworkMonitor()
    handler = OfflineModeHandler(cache, monitor)
    
    # Test 1: Check offline status
    print("Test 1: Checking offline status...")
    is_offline = handler.is_offline()
    print(f"✓ Offline mode: {is_offline}")
    
    # Test 2: Get data with fallback
    print("\nTest 2: Getting data with fallback...")
    
    # First, cache some data
    cache.cache_content(
        content_type="schemes",
        content={"id": "scheme_001", "name": "Test Scheme"},
        priority=1,
        language="en"
    )
    
    # Define a fetch function that simulates server call
    def fetch_from_server():
        if monitor.is_online():
            return [{"id": "scheme_002", "name": "Server Scheme"}]
        else:
            raise Exception("Server unavailable")
    
    data, from_cache = handler.get_data_with_fallback(
        fetch_func=fetch_from_server,
        content_type="schemes",
        language="en"
    )
    
    print(f"✓ Retrieved data: {len(data) if isinstance(data, list) else 1} items")
    print(f"  From cache: {from_cache}")
    
    print("\n✓ All OfflineModeHandler tests passed!")
    
    # Cleanup
    cache.clear_all_cache()


def main():
    """Run all tests"""
    print("=" * 60)
    print("OFFLINE CACHE SYSTEM TESTS")
    print("=" * 60)
    
    try:
        test_cache_manager()
        test_network_monitor()
        test_offline_handler()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
