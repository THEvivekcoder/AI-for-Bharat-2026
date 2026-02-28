"""
Unit tests for Cache Manager

Tests cache storage, retrieval, sync with conflicts, cache eviction, and offline mode.

Requirements: 7.1, 7.3, 7.4
"""
import pytest
import tempfile
import os
import time
import json
from pathlib import Path
from app.services.offline_cache import CacheManager, SyncOperation, SyncResult


@pytest.fixture
def temp_cache_db():
    """Create a temporary cache database for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_cache.db")
        yield db_path


@pytest.fixture
def cache_manager(temp_cache_db):
    """Create a CacheManager instance with temporary database"""
    manager = CacheManager(db_path=temp_cache_db, max_cache_size_mb=1)
    yield manager
    # Cleanup
    manager.clear_all_cache()


class TestCacheStorageAndRetrieval:
    """Test cache storage and retrieval functionality"""
    
    def test_cache_content_basic(self, cache_manager):
        """Test basic content caching"""
        content = {
            "id": "scheme_001",
            "name": "PM-KISAN",
            "description": "Direct income support for farmers"
        }
        
        result = cache_manager.cache_content(
            content_type="schemes",
            content=content,
            priority=1,
            language="en"
        )
        
        assert result is True
        
        # Retrieve cached content
        cached = cache_manager.get_cached_content(content_type="schemes")
        assert len(cached) == 1
        assert cached[0]["id"] == "scheme_001"
        assert cached[0]["name"] == "PM-KISAN"
    
    def test_cache_multiple_items(self, cache_manager):
        """Test caching multiple items of same type"""
        schemes = [
            {"id": "scheme_001", "name": "PM-KISAN"},
            {"id": "scheme_002", "name": "Ayushman Bharat"},
            {"id": "scheme_003", "name": "MGNREGA"}
        ]
        
        for scheme in schemes:
            cache_manager.cache_content(
                content_type="schemes",
                content=scheme,
                priority=1
            )
        
        cached = cache_manager.get_cached_content(content_type="schemes")
        assert len(cached) == 3
    
    def test_cache_different_content_types(self, cache_manager):
        """Test caching different content types"""
        scheme = {"id": "scheme_001", "name": "PM-KISAN"}
        health_tip = {"id": "tip_001", "content": "Drink clean water"}
        crop_advice = {"id": "crop_001", "crop": "wheat", "season": "rabi"}
        
        cache_manager.cache_content("schemes", scheme, priority=1)
        cache_manager.cache_content("health_tips", health_tip, priority=2)
        cache_manager.cache_content("crop_advice", crop_advice, priority=1)
        
        schemes = cache_manager.get_cached_content("schemes")
        tips = cache_manager.get_cached_content("health_tips")
        advice = cache_manager.get_cached_content("crop_advice")
        
        assert len(schemes) == 1
        assert len(tips) == 1
        assert len(advice) == 1
    
    def test_cache_with_language_filter(self, cache_manager):
        """Test caching and retrieving content by language"""
        # Use different IDs for different languages to avoid replacement
        content_en = {"id": "scheme_001_en", "name": "PM-KISAN"}
        content_hi = {"id": "scheme_001_hi", "name": "पीएम-किसान"}
        
        cache_manager.cache_content("schemes", content_en, priority=1, language="en")
        cache_manager.cache_content("schemes", content_hi, priority=1, language="hi")
        
        cached_en = cache_manager.get_cached_content("schemes", language="en")
        cached_hi = cache_manager.get_cached_content("schemes", language="hi")
        
        assert len(cached_en) == 1
        assert len(cached_hi) == 1
        assert cached_en[0]["name"] == "PM-KISAN"
        assert cached_hi[0]["name"] == "पीएम-किसान"
    
    def test_cache_with_query_search(self, cache_manager):
        """Test retrieving cached content with text search"""
        schemes = [
            {"id": "scheme_001", "name": "PM-KISAN", "category": "agriculture"},
            {"id": "scheme_002", "name": "Ayushman Bharat", "category": "health"},
            {"id": "scheme_003", "name": "MGNREGA", "category": "employment"}
        ]
        
        for scheme in schemes:
            cache_manager.cache_content("schemes", scheme, priority=1)
        
        # Search for agriculture-related schemes
        results = cache_manager.get_cached_content("schemes", query="agriculture")
        assert len(results) == 1
        assert results[0]["name"] == "PM-KISAN"
        
        # Search for health-related schemes
        results = cache_manager.get_cached_content("schemes", query="health")
        assert len(results) == 1
        assert results[0]["name"] == "Ayushman Bharat"
    
    def test_cache_content_replacement(self, cache_manager):
        """Test that caching same content ID replaces old content"""
        content_v1 = {"id": "scheme_001", "name": "PM-KISAN", "version": 1}
        content_v2 = {"id": "scheme_001", "name": "PM-KISAN Updated", "version": 2}
        
        cache_manager.cache_content("schemes", content_v1, priority=1)
        cache_manager.cache_content("schemes", content_v2, priority=1)
        
        cached = cache_manager.get_cached_content("schemes")
        # Should only have one item (replaced)
        assert len(cached) == 1
        assert cached[0]["version"] == 2
        assert cached[0]["name"] == "PM-KISAN Updated"
    
    def test_cache_expiration(self, cache_manager):
        """Test that expired content is not retrieved"""
        content = {"id": "scheme_001", "name": "PM-KISAN"}
        
        # Cache with very short TTL (1 second)
        cache_manager.cache_content(
            "schemes", 
            content, 
            priority=1, 
            ttl_hours=1/3600  # 1 second
        )
        
        # Should be retrievable immediately
        cached = cache_manager.get_cached_content("schemes")
        assert len(cached) == 1
        
        # Wait for expiration
        time.sleep(2)
        
        # Should not be retrievable after expiration
        cached = cache_manager.get_cached_content("schemes")
        assert len(cached) == 0
    
    def test_get_cache_stats(self, cache_manager):
        """Test cache statistics retrieval"""
        # Cache some content
        cache_manager.cache_content("schemes", {"id": "1", "name": "Scheme 1"}, priority=1)
        cache_manager.cache_content("schemes", {"id": "2", "name": "Scheme 2"}, priority=2)
        cache_manager.cache_content("health_tips", {"id": "1", "tip": "Tip 1"}, priority=1)
        
        stats = cache_manager.get_cache_stats()
        
        assert stats["total_items"] == 3
        assert stats["by_type"]["schemes"] == 2
        assert stats["by_type"]["health_tips"] == 1
        assert stats["by_priority"][1] == 2
        assert stats["by_priority"][2] == 1
        assert "total_size_bytes" in stats
        assert "usage_percent" in stats


class TestCacheEviction:
    """Test cache eviction based on size and priority"""
    
    def test_cache_eviction_on_size_limit(self, cache_manager):
        """Test that low-priority items are evicted when cache is full"""
        # Create large content items to fill cache
        large_content = {"id": "large", "data": "x" * 100000}  # ~100KB
        
        # Cache multiple items with different priorities
        for i in range(15):
            content = {
                "id": f"item_{i}",
                "data": "x" * 100000
            }
            priority = 1 if i < 5 else 5  # First 5 are high priority
            cache_manager.cache_content("test_data", content, priority=priority)
        
        # Check that some items were evicted
        stats = cache_manager.get_cache_stats()
        assert stats["total_items"] < 15  # Some items should be evicted
        
        # High priority items should still be there
        cached = cache_manager.get_cached_content("test_data")
        high_priority_ids = [f"item_{i}" for i in range(5)]
        cached_ids = [item["id"] for item in cached]
        
        # At least some high priority items should remain
        high_priority_remaining = sum(1 for id in high_priority_ids if id in cached_ids)
        assert high_priority_remaining > 0
    
    def test_priority_based_eviction(self, cache_manager):
        """Test that lower priority items are evicted first"""
        # Cache high priority item
        cache_manager.cache_content(
            "important", 
            {"id": "critical", "data": "x" * 50000}, 
            priority=1
        )
        
        # Fill cache with low priority items
        for i in range(20):
            cache_manager.cache_content(
                "unimportant",
                {"id": f"low_{i}", "data": "x" * 50000},
                priority=5
            )
        
        # High priority item should still be cached
        cached = cache_manager.get_cached_content("important")
        assert len(cached) > 0
        assert cached[0]["id"] == "critical"


class TestCacheInvalidation:
    """Test cache invalidation functionality"""
    
    def test_invalidate_by_content_type(self, cache_manager):
        """Test invalidating cache by content type"""
        # Cache with short TTL so they expire
        cache_manager.cache_content("schemes", {"id": "1"}, priority=1, ttl_hours=1/3600)
        cache_manager.cache_content("health_tips", {"id": "2"}, priority=1)
        
        # Wait for schemes to expire
        time.sleep(2)
        
        # Invalidate only schemes
        deleted = cache_manager.invalidate_cache(content_type="schemes", max_age_days=0)
        
        assert deleted == 1
        assert len(cache_manager.get_cached_content("schemes")) == 0
        assert len(cache_manager.get_cached_content("health_tips")) == 1
    
    def test_invalidate_all_content(self, cache_manager):
        """Test invalidating all cached content"""
        # Cache with short TTL so they expire
        cache_manager.cache_content("schemes", {"id": "1"}, priority=1, ttl_hours=1/3600)
        cache_manager.cache_content("health_tips", {"id": "2"}, priority=1, ttl_hours=1/3600)
        cache_manager.cache_content("crop_advice", {"id": "3"}, priority=1, ttl_hours=1/3600)
        
        # Wait for content to expire
        time.sleep(2)
        
        # Invalidate all with max_age_days=0
        deleted = cache_manager.invalidate_cache(max_age_days=0)
        
        assert deleted == 3
        assert cache_manager.get_cache_stats()["total_items"] == 0
    
    def test_invalidate_by_age(self, cache_manager):
        """Test invalidating cache by age"""
        # Cache old content (simulate by setting old timestamp)
        cache_manager.cache_content(
            "schemes", 
            {"id": "old"}, 
            priority=1,
            ttl_hours=1/3600  # 1 second TTL
        )
        
        time.sleep(2)
        
        # Cache new content
        cache_manager.cache_content("schemes", {"id": "new"}, priority=1)
        
        # Invalidate old content
        deleted = cache_manager.invalidate_cache(max_age_days=0)
        
        # Old content should be removed
        cached = cache_manager.get_cached_content("schemes")
        assert len(cached) == 1
        assert cached[0]["id"] == "new"


class TestSyncOperations:
    """Test sync operations and conflict resolution"""
    
    def test_add_pending_sync(self, cache_manager):
        """Test adding operations to pending sync queue"""
        entity_data = {"id": "user_001", "name": "Test User"}
        
        sync_id = cache_manager.add_pending_sync(
            operation="create",
            entity_type="user_profile",
            entity_data=entity_data
        )
        
        assert sync_id != ""
        assert "user_profile" in sync_id
        assert "create" in sync_id
    
    def test_get_pending_syncs(self, cache_manager):
        """Test retrieving pending sync operations"""
        # Add multiple pending syncs
        cache_manager.add_pending_sync("create", "user", {"id": "1"})
        cache_manager.add_pending_sync("update", "scheme", {"id": "2"})
        cache_manager.add_pending_sync("delete", "job", {"id": "3"})
        
        pending = cache_manager.get_pending_syncs()
        
        assert len(pending) == 3
        assert all(isinstance(op, SyncOperation) for op in pending)
        assert pending[0].operation == "create"
        assert pending[1].operation == "update"
        assert pending[2].operation == "delete"
    
    def test_clear_pending_sync(self, cache_manager):
        """Test clearing individual sync operations"""
        sync_id = cache_manager.add_pending_sync("create", "user", {"id": "1"})
        
        # Verify it's in the queue
        pending = cache_manager.get_pending_syncs()
        assert len(pending) == 1
        
        # Clear it
        result = cache_manager.clear_pending_sync(sync_id)
        assert result is True
        
        # Verify it's removed
        pending = cache_manager.get_pending_syncs()
        assert len(pending) == 0
    
    def test_sync_with_server_success(self, cache_manager):
        """Test successful sync with server"""
        # Add pending operations
        cache_manager.add_pending_sync("create", "user", {"id": "1", "name": "User 1"})
        cache_manager.add_pending_sync("update", "scheme", {"id": "2", "name": "Scheme 2"})
        
        # Mock sync callback that always succeeds
        def mock_sync_callback(operation, entity_type, entity_data):
            return True
        
        result = cache_manager.sync_with_server(sync_callback=mock_sync_callback)
        
        assert result.success is True
        assert result.synced_count == 2
        assert result.failed_count == 0
        assert len(result.errors) == 0
        
        # Pending queue should be empty
        assert len(cache_manager.get_pending_syncs()) == 0
    
    def test_sync_with_server_partial_failure(self, cache_manager):
        """Test sync with some operations failing"""
        cache_manager.add_pending_sync("create", "user", {"id": "1"})
        cache_manager.add_pending_sync("update", "scheme", {"id": "2"})
        cache_manager.add_pending_sync("delete", "job", {"id": "3"})
        
        # Mock callback that fails for delete operations
        def mock_sync_callback(operation, entity_type, entity_data):
            return operation != "delete"
        
        result = cache_manager.sync_with_server(sync_callback=mock_sync_callback)
        
        assert result.success is False
        assert result.synced_count == 2
        assert result.failed_count == 1
        assert len(result.errors) == 1
        
        # Failed operation should still be in queue
        pending = cache_manager.get_pending_syncs()
        assert len(pending) == 1
        assert pending[0].operation == "delete"
    
    def test_sync_with_server_no_callback(self, cache_manager):
        """Test sync without callback (default behavior)"""
        cache_manager.add_pending_sync("create", "user", {"id": "1"})
        
        # Sync without callback should succeed (default behavior)
        result = cache_manager.sync_with_server()
        
        assert result.success is True
        assert result.synced_count == 1
        assert len(cache_manager.get_pending_syncs()) == 0
    
    def test_sync_conflict_resolution(self, cache_manager):
        """Test handling sync conflicts"""
        # Simulate conflict: same entity updated locally and on server
        local_update = {"id": "scheme_001", "name": "Local Version", "version": 1}
        
        cache_manager.add_pending_sync("update", "scheme", local_update)
        
        # Mock callback that simulates conflict detection
        conflicts_detected = []
        
        def mock_sync_with_conflict(operation, entity_type, entity_data):
            if entity_data.get("id") == "scheme_001":
                # Simulate conflict: server has newer version
                conflicts_detected.append({
                    "entity_id": entity_data["id"],
                    "local_version": entity_data.get("version"),
                    "server_version": 2
                })
                return False  # Sync fails due to conflict
            return True
        
        result = cache_manager.sync_with_server(sync_callback=mock_sync_with_conflict)
        
        assert result.failed_count == 1
        assert len(conflicts_detected) == 1
        assert conflicts_detected[0]["entity_id"] == "scheme_001"


class TestOfflineModeExamples:
    """Test offline mode scenarios"""
    
    def test_offline_scheme_access(self, cache_manager):
        """Test accessing schemes in offline mode"""
        # Simulate caching schemes while online
        schemes = [
            {"id": "scheme_001", "name": "PM-KISAN", "category": "agriculture"},
            {"id": "scheme_002", "name": "Ayushman Bharat", "category": "health"},
            {"id": "scheme_003", "name": "MGNREGA", "category": "employment"}
        ]
        
        for scheme in schemes:
            cache_manager.cache_content("schemes", scheme, priority=1)
        
        # Simulate offline mode: retrieve from cache
        cached_schemes = cache_manager.get_cached_content("schemes")
        
        assert len(cached_schemes) == 3
        assert all("name" in scheme for scheme in cached_schemes)
    
    def test_offline_user_interaction_tracking(self, cache_manager):
        """Test tracking user interactions while offline"""
        # User performs actions while offline
        interactions = [
            {"user_id": "user_001", "action": "view_scheme", "scheme_id": "scheme_001"},
            {"user_id": "user_001", "action": "check_eligibility", "scheme_id": "scheme_002"},
            {"user_id": "user_001", "action": "search_jobs", "query": "teacher"}
        ]
        
        # Queue interactions for sync with small delays to avoid ID collisions
        for i, interaction in enumerate(interactions):
            time.sleep(0.01)  # Small delay to ensure unique timestamps
            cache_manager.add_pending_sync("create", f"interaction_{i}", interaction)
        
        # Verify all interactions are queued
        pending = cache_manager.get_pending_syncs()
        assert len(pending) == 3
        
        # Simulate coming back online and syncing
        synced_interactions = []
        
        def mock_sync_callback(operation, entity_type, entity_data):
            synced_interactions.append(entity_data)
            return True
        
        result = cache_manager.sync_with_server(sync_callback=mock_sync_callback)
        
        assert result.success is True
        assert len(synced_interactions) == 3
    
    def test_offline_content_priority(self, cache_manager):
        """Test that high-priority content is available offline"""
        # Cache content with different priorities
        critical_content = [
            {"id": "emergency_001", "type": "emergency_contact"},
            {"id": "health_001", "type": "health_facility"}
        ]
        
        nice_to_have_content = [
            {"id": "tip_001", "type": "farming_tip"},
            {"id": "news_001", "type": "agriculture_news"}
        ]
        
        # Cache critical content with high priority
        for content in critical_content:
            cache_manager.cache_content("critical", content, priority=1)
        
        # Cache nice-to-have with low priority
        for content in nice_to_have_content:
            cache_manager.cache_content("optional", content, priority=5)
        
        # Verify critical content is cached
        critical_cached = cache_manager.get_cached_content("critical")
        assert len(critical_cached) == 2
        
        # Fill cache to trigger eviction
        for i in range(20):
            cache_manager.cache_content(
                "filler",
                {"id": f"filler_{i}", "data": "x" * 50000},
                priority=3
            )
        
        # Critical content should still be available
        critical_cached = cache_manager.get_cached_content("critical")
        assert len(critical_cached) > 0
    
    def test_offline_to_online_transition(self, cache_manager):
        """Test transition from offline to online mode"""
        # Offline: cache content and queue operations
        cache_manager.cache_content("schemes", {"id": "scheme_001"}, priority=1)
        cache_manager.add_pending_sync("create", "user_action", {"action": "view"})
        
        stats_before = cache_manager.get_cache_stats()
        pending_before = len(cache_manager.get_pending_syncs())
        
        assert stats_before["total_items"] > 0
        assert pending_before > 0
        
        # Online: sync with server
        def mock_sync_callback(operation, entity_type, entity_data):
            return True
        
        result = cache_manager.sync_with_server(sync_callback=mock_sync_callback)
        
        assert result.success is True
        assert result.synced_count == pending_before
        
        # Pending queue should be cleared
        assert len(cache_manager.get_pending_syncs()) == 0
        
        # Cached content should still be available
        cached = cache_manager.get_cached_content("schemes")
        assert len(cached) > 0
    
    def test_offline_search_functionality(self, cache_manager):
        """Test search functionality works offline with cached data"""
        # Cache agricultural advice
        advice_items = [
            {"id": "1", "crop": "wheat", "season": "rabi", "advice": "Sow in November"},
            {"id": "2", "crop": "rice", "season": "kharif", "advice": "Sow in June"},
            {"id": "3", "crop": "wheat", "season": "rabi", "advice": "Harvest in April"}
        ]
        
        for item in advice_items:
            cache_manager.cache_content("crop_advice", item, priority=1)
        
        # Search for wheat-related advice (offline)
        wheat_advice = cache_manager.get_cached_content("crop_advice", query="wheat")
        assert len(wheat_advice) == 2
        
        # Search for kharif season advice
        kharif_advice = cache_manager.get_cached_content("crop_advice", query="kharif")
        assert len(kharif_advice) == 1
        assert kharif_advice[0]["crop"] == "rice"


class TestCacheManagerEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_cache_retrieval(self, cache_manager):
        """Test retrieving from empty cache"""
        cached = cache_manager.get_cached_content("nonexistent_type")
        assert cached == []
    
    def test_cache_with_empty_content(self, cache_manager):
        """Test caching empty content"""
        result = cache_manager.cache_content("test", {}, priority=1)
        assert result is True
        
        cached = cache_manager.get_cached_content("test")
        assert len(cached) == 1
        assert cached[0] == {}
    
    def test_cache_with_large_content(self, cache_manager):
        """Test caching very large content"""
        large_content = {
            "id": "large_001",
            "data": "x" * 500000  # 500KB
        }
        
        result = cache_manager.cache_content("large", large_content, priority=1)
        assert result is True
        
        cached = cache_manager.get_cached_content("large")
        assert len(cached) == 1
    
    def test_clear_all_cache(self, cache_manager):
        """Test clearing all cache"""
        # Add various content
        cache_manager.cache_content("schemes", {"id": "1"}, priority=1)
        cache_manager.cache_content("health_tips", {"id": "2"}, priority=1)
        cache_manager.add_pending_sync("create", "user", {"id": "3"})
        
        # Clear all
        result = cache_manager.clear_all_cache()
        assert result is True
        
        # Verify everything is cleared
        stats = cache_manager.get_cache_stats()
        assert stats["total_items"] == 0
        assert stats["pending_syncs"] == 0
    
    def test_concurrent_cache_operations(self, cache_manager):
        """Test multiple cache operations in sequence"""
        # Simulate rapid cache operations
        for i in range(10):
            cache_manager.cache_content("test", {"id": f"item_{i}"}, priority=1)
        
        cached = cache_manager.get_cached_content("test")
        assert len(cached) == 10
    
    def test_cache_stats_with_empty_cache(self, cache_manager):
        """Test getting stats from empty cache"""
        stats = cache_manager.get_cache_stats()
        
        assert stats["total_items"] == 0
        assert stats["total_size_bytes"] == 0
        assert stats["pending_syncs"] == 0
        assert stats["by_type"] == {}
        assert stats["by_priority"] == {}
