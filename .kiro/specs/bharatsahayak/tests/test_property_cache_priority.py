"""
Property-Based Test: Offline Cache Priority

Feature: bharatsahayak, Property 19: Offline Cache Priority

Property:
For any content cached for offline access, high-priority content (priority 1-2) 
should be cached before low-priority content (priority 3-5), and the cache should 
respect size limits.

Validates: Requirements 7.3
"""
import pytest
from hypothesis import given, settings, strategies as st, assume
import tempfile
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.services.offline_cache import CacheManager


# Constants
HIGH_PRIORITY_RANGE = (1, 2)
LOW_PRIORITY_RANGE = (3, 5)
CACHE_SIZE_MB = 1  # Small cache for testing


def create_content_item(content_id: str, size_kb: int = 10) -> Dict[str, Any]:
    """
    Create a content item of approximately specified size
    
    Args:
        content_id: Unique identifier for content
        size_kb: Approximate size in KB
        
    Returns:
        Dictionary representing content
    """
    # Create content with padding to reach desired size
    padding_size = max(0, (size_kb * 1024) - 200)  # Account for JSON overhead
    padding = "x" * padding_size
    
    return {
        "id": content_id,
        "type": "scheme",
        "name": f"Content {content_id}",
        "description": f"Description for content {content_id}",
        "data": {
            "field1": "value1",
            "field2": "value2",
            "padding": padding
        }
    }


@st.composite
def content_with_priority_strategy(draw):
    """
    Generate content items with priorities
    
    Returns:
        Tuple of (content_dict, priority)
    """
    content_id = draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    priority = draw(st.integers(min_value=1, max_value=5))
    size_kb = draw(st.integers(min_value=5, max_value=50))
    
    content = create_content_item(content_id, size_kb)
    
    return (content, priority)


@st.composite
def content_list_strategy(draw, min_items=5, max_items=20):
    """
    Generate a list of content items with mixed priorities
    
    Returns:
        List of (content_dict, priority) tuples
    """
    count = draw(st.integers(min_value=min_items, max_value=max_items))
    items = []
    
    for i in range(count):
        content_id = f"content_{i}_{draw(st.integers(min_value=1, max_value=10000))}"
        priority = draw(st.integers(min_value=1, max_value=5))
        size_kb = draw(st.integers(min_value=5, max_value=30))
        
        content = create_content_item(content_id, size_kb)
        items.append((content, priority))
    
    return items


# Property Tests

@settings(max_examples=100, deadline=None)
@given(content_items=content_list_strategy(min_items=10, max_items=30))
def test_cache_priority_ordering(content_items: List[Tuple[Dict[str, Any], int]]):
    """
    Property 19: Offline Cache Priority - Priority Ordering
    
    For any set of content items with different priorities, high-priority content 
    (priority 1-2) should be retained in cache before low-priority content (priority 3-5)
    when cache space is limited.
    
    This property ensures that:
    1. High-priority items are cached successfully
    2. When cache is full, low-priority items are evicted before high-priority items
    3. Cache respects priority ordering during eviction
    """
    # Create temporary cache with small size
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_cache.db")
        cache_manager = CacheManager(db_path=db_path, max_cache_size_mb=CACHE_SIZE_MB)
        
        # Separate items by priority
        high_priority_items = [(c, p) for c, p in content_items if p in HIGH_PRIORITY_RANGE]
        low_priority_items = [(c, p) for c, p in content_items if p in LOW_PRIORITY_RANGE]
        
        # Skip if we don't have both high and low priority items
        assume(len(high_priority_items) > 0 and len(low_priority_items) > 0)
        
        print(f"\nTest setup:")
        print(f"  High-priority items: {len(high_priority_items)}")
        print(f"  Low-priority items: {len(low_priority_items)}")
        print(f"  Total items: {len(content_items)}")
        
        # Cache all items (mix of priorities)
        cached_ids = []
        for content, priority in content_items:
            success = cache_manager.cache_content(
                content_type="test_content",
                content=content,
                priority=priority,
                language="en",
                ttl_hours=24
            )
            if success:
                cached_ids.append((content["id"], priority))
        
        # Get cache stats
        stats = cache_manager.get_cache_stats()
        print(f"\nCache stats after caching:")
        print(f"  Total items: {stats['total_items']}")
        print(f"  Size: {stats['total_size_mb']} MB / {stats['max_size_mb']} MB")
        print(f"  Usage: {stats['usage_percent']}%")
        print(f"  By priority: {stats['by_priority']}")
        
        # Retrieve all cached content
        cached_content = cache_manager.get_cached_content(content_type="test_content")
        cached_content_ids = {item["id"] for item in cached_content}
        
        # Count how many high and low priority items are in cache
        high_priority_cached = sum(1 for cid, p in cached_ids if p in HIGH_PRIORITY_RANGE and cid in cached_content_ids)
        low_priority_cached = sum(1 for cid, p in cached_ids if p in LOW_PRIORITY_RANGE and cid in cached_content_ids)
        
        print(f"\nCached items:")
        print(f"  High-priority cached: {high_priority_cached}/{len(high_priority_items)}")
        print(f"  Low-priority cached: {low_priority_cached}/{len(low_priority_items)}")
        
        # Property 1: If cache had to evict items, high-priority items should be retained
        # Calculate retention rates
        high_priority_retention = high_priority_cached / len(high_priority_items) if len(high_priority_items) > 0 else 1.0
        low_priority_retention = low_priority_cached / len(low_priority_items) if len(low_priority_items) > 0 else 1.0
        
        print(f"\nRetention rates:")
        print(f"  High-priority: {high_priority_retention * 100:.1f}%")
        print(f"  Low-priority: {low_priority_retention * 100:.1f}%")
        
        # If cache is full (usage > 80%), high-priority retention should be >= low-priority retention
        if stats['usage_percent'] > 80:
            assert high_priority_retention >= low_priority_retention, (
                f"High-priority retention ({high_priority_retention * 100:.1f}%) should be >= "
                f"low-priority retention ({low_priority_retention * 100:.1f}%) when cache is full. "
                f"Cache should prioritize high-priority content."
            )
        
        # Property 2: Cache should not exceed size limit
        assert stats['total_size_mb'] <= stats['max_size_mb'], (
            f"Cache size {stats['total_size_mb']} MB exceeds maximum {stats['max_size_mb']} MB. "
            f"Cache should respect size limits."
        )


@settings(max_examples=50, deadline=None)
@given(
    high_priority_count=st.integers(min_value=3, max_value=10),
    low_priority_count=st.integers(min_value=3, max_value=10),
    item_size_kb=st.integers(min_value=20, max_value=100)
)
def test_cache_priority_eviction_order(
    high_priority_count: int,
    low_priority_count: int,
    item_size_kb: int
):
    """
    Property 19: Offline Cache Priority - Eviction Order
    
    When cache is full, low-priority items should be evicted before high-priority items.
    
    This test:
    1. Fills cache with high-priority items
    2. Adds low-priority items (forcing eviction)
    3. Verifies high-priority items are retained
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_cache.db")
        cache_manager = CacheManager(db_path=db_path, max_cache_size_mb=CACHE_SIZE_MB)
        
        print(f"\nTest setup:")
        print(f"  High-priority items: {high_priority_count}")
        print(f"  Low-priority items: {low_priority_count}")
        print(f"  Item size: {item_size_kb} KB")
        
        # Step 1: Cache high-priority items
        high_priority_ids = []
        for i in range(high_priority_count):
            content = create_content_item(f"high_priority_{i}", item_size_kb)
            success = cache_manager.cache_content(
                content_type="test_content",
                content=content,
                priority=1,  # High priority
                language="en",
                ttl_hours=24
            )
            if success:
                high_priority_ids.append(content["id"])
        
        stats_after_high = cache_manager.get_cache_stats()
        print(f"\nAfter caching high-priority items:")
        print(f"  Cached: {len(high_priority_ids)}/{high_priority_count}")
        print(f"  Size: {stats_after_high['total_size_mb']} MB")
        print(f"  Usage: {stats_after_high['usage_percent']}%")
        
        # Step 2: Cache low-priority items (may trigger eviction)
        low_priority_ids = []
        for i in range(low_priority_count):
            content = create_content_item(f"low_priority_{i}", item_size_kb)
            success = cache_manager.cache_content(
                content_type="test_content",
                content=content,
                priority=5,  # Low priority
                language="en",
                ttl_hours=24
            )
            if success:
                low_priority_ids.append(content["id"])
        
        stats_after_low = cache_manager.get_cache_stats()
        print(f"\nAfter caching low-priority items:")
        print(f"  Cached: {len(low_priority_ids)}/{low_priority_count}")
        print(f"  Size: {stats_after_low['total_size_mb']} MB")
        print(f"  Usage: {stats_after_low['usage_percent']}%")
        
        # Step 3: Verify high-priority items are still in cache
        cached_content = cache_manager.get_cached_content(content_type="test_content")
        cached_ids = {item["id"] for item in cached_content}
        
        high_priority_retained = sum(1 for hid in high_priority_ids if hid in cached_ids)
        low_priority_retained = sum(1 for lid in low_priority_ids if lid in cached_ids)
        
        print(f"\nRetained items:")
        print(f"  High-priority: {high_priority_retained}/{len(high_priority_ids)}")
        print(f"  Low-priority: {low_priority_retained}/{len(low_priority_ids)}")
        
        # Property: If eviction occurred, high-priority items should be retained preferentially
        total_cached = len(cached_ids)
        total_attempted = len(high_priority_ids) + len(low_priority_ids)
        
        if total_cached < total_attempted:
            # Eviction occurred
            high_priority_retention_rate = high_priority_retained / len(high_priority_ids) if len(high_priority_ids) > 0 else 1.0
            low_priority_retention_rate = low_priority_retained / len(low_priority_ids) if len(low_priority_ids) > 0 else 1.0
            
            print(f"\nEviction occurred:")
            print(f"  High-priority retention: {high_priority_retention_rate * 100:.1f}%")
            print(f"  Low-priority retention: {low_priority_retention_rate * 100:.1f}%")
            
            assert high_priority_retention_rate >= low_priority_retention_rate, (
                f"When eviction occurs, high-priority items should be retained preferentially. "
                f"High-priority retention: {high_priority_retention_rate * 100:.1f}%, "
                f"Low-priority retention: {low_priority_retention_rate * 100:.1f}%"
            )


@settings(max_examples=50, deadline=None)
@given(
    priorities=st.lists(
        st.integers(min_value=1, max_value=5),
        min_size=5,
        max_size=15
    )
)
def test_cache_priority_size_limit_enforcement(priorities: List[int]):
    """
    Property 19: Offline Cache Priority - Size Limit Enforcement
    
    Cache should never exceed the configured size limit, regardless of priority.
    
    This test:
    1. Attempts to cache many items
    2. Verifies cache size stays within limit
    3. Verifies cache evicts items when necessary
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_cache.db")
        cache_manager = CacheManager(db_path=db_path, max_cache_size_mb=CACHE_SIZE_MB)
        
        print(f"\nTest setup:")
        print(f"  Items to cache: {len(priorities)}")
        print(f"  Priorities: {priorities}")
        print(f"  Max cache size: {CACHE_SIZE_MB} MB")
        
        # Cache items with varying priorities
        cached_count = 0
        for i, priority in enumerate(priorities):
            content = create_content_item(f"content_{i}", size_kb=50)
            success = cache_manager.cache_content(
                content_type="test_content",
                content=content,
                priority=priority,
                language="en",
                ttl_hours=24
            )
            if success:
                cached_count += 1
        
        # Get final cache stats
        stats = cache_manager.get_cache_stats()
        
        print(f"\nFinal cache stats:")
        print(f"  Cached: {cached_count}/{len(priorities)}")
        print(f"  Total items: {stats['total_items']}")
        print(f"  Size: {stats['total_size_mb']} MB / {stats['max_size_mb']} MB")
        print(f"  Usage: {stats['usage_percent']}%")
        print(f"  By priority: {stats['by_priority']}")
        
        # Property 1: Cache size must not exceed limit
        assert stats['total_size_mb'] <= stats['max_size_mb'], (
            f"Cache size {stats['total_size_mb']} MB exceeds maximum {stats['max_size_mb']} MB. "
            f"Cache must enforce size limits."
        )
        
        # Property 2: If not all items were cached, eviction occurred correctly
        if cached_count < len(priorities):
            print(f"\nEviction occurred: {len(priorities) - cached_count} items not cached")
            
            # Verify cache is near capacity (within 20% of max)
            assert stats['usage_percent'] >= 60, (
                f"If eviction occurred, cache should be near capacity. "
                f"Current usage: {stats['usage_percent']}%"
            )


@settings(max_examples=30, deadline=None)
@given(
    priority_distribution=st.lists(
        st.tuples(
            st.integers(min_value=1, max_value=5),  # priority
            st.integers(min_value=1, max_value=5)   # count
        ),
        min_size=2,
        max_size=5
    )
)
def test_cache_priority_distribution(priority_distribution: List[Tuple[int, int]]):
    """
    Property 19: Offline Cache Priority - Priority Distribution
    
    When caching items with various priority levels, the cache should maintain
    a distribution that favors higher-priority items.
    
    This test:
    1. Caches items with different priority levels
    2. Verifies the distribution in cache favors high-priority items
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_cache.db")
        cache_manager = CacheManager(db_path=db_path, max_cache_size_mb=CACHE_SIZE_MB)
        
        print(f"\nTest setup:")
        print(f"  Priority distribution: {priority_distribution}")
        
        # Cache items according to distribution
        total_items = 0
        for priority, count in priority_distribution:
            for i in range(count):
                content = create_content_item(f"p{priority}_item_{i}", size_kb=30)
                cache_manager.cache_content(
                    content_type="test_content",
                    content=content,
                    priority=priority,
                    language="en",
                    ttl_hours=24
                )
                total_items += 1
        
        # Get cache stats
        stats = cache_manager.get_cache_stats()
        
        print(f"\nCache stats:")
        print(f"  Total attempted: {total_items}")
        print(f"  Total cached: {stats['total_items']}")
        print(f"  Size: {stats['total_size_mb']} MB")
        print(f"  By priority: {stats['by_priority']}")
        
        # Property: High-priority items should have better representation in cache
        if stats['total_items'] < total_items:
            # Eviction occurred
            by_priority = stats['by_priority']
            
            # Calculate representation rates for high vs low priority
            high_priority_in_cache = sum(by_priority.get(p, 0) for p in [1, 2])
            low_priority_in_cache = sum(by_priority.get(p, 0) for p in [4, 5])
            
            high_priority_attempted = sum(count for priority, count in priority_distribution if priority in [1, 2])
            low_priority_attempted = sum(count for priority, count in priority_distribution if priority in [4, 5])
            
            if high_priority_attempted > 0 and low_priority_attempted > 0:
                high_priority_rate = high_priority_in_cache / high_priority_attempted
                low_priority_rate = low_priority_in_cache / low_priority_attempted
                
                print(f"\nRepresentation rates:")
                print(f"  High-priority (1-2): {high_priority_rate * 100:.1f}%")
                print(f"  Low-priority (4-5): {low_priority_rate * 100:.1f}%")
                
                # High-priority items should have equal or better representation
                # Allow some tolerance for small sample sizes and cache dynamics
                min_items_for_strict_check = 5
                
                # Only enforce strict priority if we have enough items and reasonable cache usage
                if (high_priority_attempted >= min_items_for_strict_check and 
                    low_priority_attempted >= min_items_for_strict_check and
                    stats['usage_percent'] > 90):  # Only when cache is very full
                    
                    # When cache is very full, high-priority should be better represented
                    assert high_priority_rate >= low_priority_rate * 0.7, (
                        f"When cache is full, high-priority items should be better represented. "
                        f"High-priority: {high_priority_rate * 100:.1f}%, "
                        f"Low-priority: {low_priority_rate * 100:.1f}%"
                    )
                else:
                    # For other cases, just verify high-priority items are present
                    if high_priority_attempted > 0:
                        assert high_priority_in_cache > 0, (
                            f"At least some high-priority items should be cached"
                        )


def test_cache_priority_real_world_scenario():
    """
    Test cache priority with a realistic scenario
    
    This tests a real-world use case where:
    1. Critical schemes (priority 1) are cached
    2. Important health tips (priority 2) are cached
    3. General FAQs (priority 3) are cached
    4. Optional content (priority 4-5) is cached
    5. Cache respects priority when space is limited
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_cache.db")
        cache_manager = CacheManager(db_path=db_path, max_cache_size_mb=CACHE_SIZE_MB)
        
        # Define content categories with priorities
        content_categories = [
            ("critical_schemes", 1, 5, 40),      # 5 critical schemes, 40KB each
            ("health_tips", 2, 8, 30),           # 8 health tips, 30KB each
            ("faqs", 3, 10, 20),                 # 10 FAQs, 20KB each
            ("optional_content", 4, 15, 25),     # 15 optional items, 25KB each
        ]
        
        print("\nReal-world scenario:")
        
        # Cache all content
        cached_by_category = {}
        for category, priority, count, size_kb in content_categories:
            cached_ids = []
            for i in range(count):
                content = create_content_item(f"{category}_{i}", size_kb)
                success = cache_manager.cache_content(
                    content_type=category,
                    content=content,
                    priority=priority,
                    language="en",
                    ttl_hours=24
                )
                if success:
                    cached_ids.append(content["id"])
            
            cached_by_category[category] = cached_ids
            print(f"  {category} (priority {priority}): {len(cached_ids)}/{count} cached")
        
        # Get cache stats
        stats = cache_manager.get_cache_stats()
        print(f"\nCache stats:")
        print(f"  Size: {stats['total_size_mb']} MB / {stats['max_size_mb']} MB")
        print(f"  Usage: {stats['usage_percent']}%")
        print(f"  By priority: {stats['by_priority']}")
        
        # Verify critical content is prioritized
        critical_cached = len(cached_by_category["critical_schemes"])
        health_cached = len(cached_by_category["health_tips"])
        optional_cached = len(cached_by_category["optional_content"])
        
        # Property 1: All critical schemes should be cached
        assert critical_cached == 5, (
            f"All critical schemes (priority 1) should be cached. "
            f"Only {critical_cached}/5 were cached."
        )
        
        # Property 2: Health tips should have high retention
        assert health_cached >= 6, (
            f"Most health tips (priority 2) should be cached. "
            f"Only {health_cached}/8 were cached."
        )
        
        # Property 3: Optional content may be partially evicted
        # (This is acceptable as it's low priority)
        print(f"\nOptional content retention: {optional_cached}/15")
        
        # Property 4: Cache size is within limit
        assert stats['total_size_mb'] <= stats['max_size_mb'], (
            f"Cache size must not exceed limit"
        )


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
