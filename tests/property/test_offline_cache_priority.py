"""Property-based tests for offline cache priority.

Feature: bharatsahayak, Property 19: Offline Cache Priority
**Validates: Requirements 7.3**

This test verifies that high-priority content (priority 1-2) is cached before
low-priority content (priority 3-5), and the cache respects size limits.
"""

import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from typing import List, Dict, Any

from src.api.cache_export import get_frequently_accessed_schemes


# Custom strategies for generating test data
@st.composite
def scheme_with_access_count_strategy(draw):
    """Generate scheme data with access counts."""
    scheme_id = f"scheme_{draw(st.integers(min_value=1000, max_value=9999))}"
    access_count = draw(st.integers(min_value=0, max_value=200))
    
    scheme = {
        'scheme_id': scheme_id,
        'name': f"Scheme {scheme_id}",
        'category': draw(st.sampled_from(['agriculture', 'health', 'education', 'employment'])),
        'description': f"Description for {scheme_id}",
        'benefits': [f"Benefit 1 for {scheme_id}", f"Benefit 2 for {scheme_id}"],
        'eligibility_criteria': {
            'age_min': draw(st.integers(min_value=18, max_value=30)),
            'age_max': draw(st.integers(min_value=40, max_value=65)),
            'income_max': draw(st.integers(min_value=100000, max_value=500000))
        },
        'required_documents': ['Aadhaar', 'Income Certificate'],
        'application_process': ['Step 1', 'Step 2'],
        'last_updated': datetime.now(timezone.utc).isoformat()
    }
    
    return scheme, access_count


@st.composite
def schemes_list_strategy(draw):
    """Generate a list of schemes with varying access counts."""
    num_schemes = draw(st.integers(min_value=10, max_value=50))
    schemes_with_counts = []
    
    for _ in range(num_schemes):
        scheme, access_count = draw(scheme_with_access_count_strategy())
        schemes_with_counts.append((scheme, access_count))
    
    return schemes_with_counts


@settings(max_examples=5, deadline=None)
@given(schemes_data=schemes_list_strategy())
def test_offline_cache_priority_ordering(schemes_data):
    """
    Feature: bharatsahayak, Property 19: Offline Cache Priority
    
    For any content cached for offline access, high-priority content (priority 1-2)
    should be cached before low-priority content (priority 3-5), and the cache
    should respect size limits.
    
    This test verifies:
    1. Schemes are prioritized based on access count
    2. High-priority schemes (more accessed) come first
    3. Priority levels are correctly assigned (1=critical, 5=nice-to-have)
    4. Schemes are sorted by priority then access count
    """
    # Separate schemes and access counts
    schemes = [s for s, _ in schemes_data]
    access_counts = {s['scheme_id']: count for s, count in schemes_data}
    
    # Mock DynamoDB tables
    mock_schemes_table = Mock()
    mock_interactions_table = Mock()
    
    # Mock schemes table scan
    mock_schemes_table.scan.return_value = {
        'Items': schemes
    }
    
    # Mock interactions table scan for access counts
    interaction_items = []
    for scheme_id, count in access_counts.items():
        for _ in range(count):
            interaction_items.append({
                'event_type': 'scheme_accessed',
                'event_data': {'scheme_id': scheme_id}
            })
    
    mock_interactions_table.scan.return_value = {
        'Items': interaction_items
    }
    
    # Patch boto3 at the module level where it's imported
    with patch('src.api.cache_export.dynamodb') as mock_dynamodb:
        mock_dynamodb.Table.side_effect = lambda name: (
            mock_schemes_table if 'schemes' in name.lower() 
            else mock_interactions_table
        )
        
        # Get cached schemes
        cached_schemes = get_frequently_accessed_schemes(limit=len(schemes))
        
        # Verify priority assignment based on access count
        for cached_scheme in cached_schemes:
            scheme_id = cached_scheme['scheme_id']
            access_count = access_counts.get(scheme_id, 0)
            priority = cached_scheme['priority']
            
            # Verify priority matches access count thresholds
            if access_count >= 100:
                assert priority == 1, f"Scheme with {access_count} accesses should have priority 1"
            elif access_count >= 50:
                assert priority == 2, f"Scheme with {access_count} accesses should have priority 2"
            elif access_count >= 20:
                assert priority == 3, f"Scheme with {access_count} accesses should have priority 3"
            elif access_count >= 5:
                assert priority == 4, f"Scheme with {access_count} accesses should have priority 4"
            else:
                assert priority == 5, f"Scheme with {access_count} accesses should have priority 5"
        
        # Verify schemes are sorted by priority (ascending) and access count (descending)
        for i in range(len(cached_schemes) - 1):
            current = cached_schemes[i]
            next_scheme = cached_schemes[i + 1]
            
            current_priority = current['priority']
            next_priority = next_scheme['priority']
            
            current_access = access_counts.get(current['scheme_id'], 0)
            next_access = access_counts.get(next_scheme['scheme_id'], 0)
            
            # Priority should be non-decreasing
            assert current_priority <= next_priority, \
                f"Priority should be non-decreasing: {current_priority} > {next_priority}"
            
            # Within same priority, access count should be non-increasing
            if current_priority == next_priority:
                assert current_access >= next_access, \
                    f"Within priority {current_priority}, access count should be non-increasing: {current_access} < {next_access}"


@settings(max_examples=5, deadline=None)
@given(
    schemes_data=schemes_list_strategy(),
    limit=st.integers(min_value=5, max_value=30)
)
def test_cache_respects_size_limit(schemes_data, limit):
    """
    Test that cache export respects the specified limit on number of schemes.
    
    This verifies that when a limit is specified, only the top priority schemes
    up to that limit are returned.
    """
    schemes = [s for s, _ in schemes_data]
    access_counts = {s['scheme_id']: count for s, count in schemes_data}
    
    # Mock DynamoDB tables
    mock_schemes_table = Mock()
    mock_interactions_table = Mock()
    
    mock_schemes_table.scan.return_value = {'Items': schemes}
    
    interaction_items = []
    for scheme_id, count in access_counts.items():
        for _ in range(count):
            interaction_items.append({
                'event_type': 'scheme_accessed',
                'event_data': {'scheme_id': scheme_id}
            })
    
    mock_interactions_table.scan.return_value = {'Items': interaction_items}
    
    with patch('src.api.cache_export.dynamodb') as mock_dynamodb:
        mock_dynamodb.Table.side_effect = lambda name: (
            mock_schemes_table if 'schemes' in name.lower() 
            else mock_interactions_table
        )
        
        # Get cached schemes with limit
        cached_schemes = get_frequently_accessed_schemes(limit=limit)
        
        # Verify the number of schemes doesn't exceed limit
        assert len(cached_schemes) <= limit, \
            f"Cached schemes count {len(cached_schemes)} exceeds limit {limit}"
        
        # Verify that if we got fewer schemes than limit, it's because there weren't enough
        if len(cached_schemes) < limit:
            assert len(cached_schemes) <= len(schemes), \
                "Should return all available schemes if less than limit"


@settings(max_examples=5, deadline=None)
@given(
    schemes_data=schemes_list_strategy(),
    priority_filter=st.integers(min_value=1, max_value=5)
)
def test_priority_filter_works_correctly(schemes_data, priority_filter):
    """
    Test that priority filtering returns only schemes of the specified priority.
    
    This verifies that when a priority filter is applied, only schemes matching
    that priority level are returned.
    """
    schemes = [s for s, _ in schemes_data]
    access_counts = {s['scheme_id']: count for s, count in schemes_data}
    
    # Mock DynamoDB tables
    mock_schemes_table = Mock()
    mock_interactions_table = Mock()
    
    mock_schemes_table.scan.return_value = {'Items': schemes}
    
    interaction_items = []
    for scheme_id, count in access_counts.items():
        for _ in range(count):
            interaction_items.append({
                'event_type': 'scheme_accessed',
                'event_data': {'scheme_id': scheme_id}
            })
    
    mock_interactions_table.scan.return_value = {'Items': interaction_items}
    
    with patch('src.api.cache_export.dynamodb') as mock_dynamodb:
        mock_dynamodb.Table.side_effect = lambda name: (
            mock_schemes_table if 'schemes' in name.lower() 
            else mock_interactions_table
        )
        
        # Get cached schemes with priority filter
        cached_schemes = get_frequently_accessed_schemes(
            priority_filter=str(priority_filter),
            limit=100
        )
        
        # Verify all returned schemes have the specified priority
        for scheme in cached_schemes:
            assert scheme['priority'] == priority_filter, \
                f"Scheme has priority {scheme['priority']}, expected {priority_filter}"


@settings(max_examples=3, deadline=None)
@given(schemes_data=schemes_list_strategy())
def test_high_priority_schemes_cached_first(schemes_data):
    """
    Test that high-priority schemes (priority 1-2) appear before low-priority (3-5).
    
    This is the core property: critical and high-priority content should be
    cached before less important content.
    """
    schemes = [s for s, _ in schemes_data]
    access_counts = {s['scheme_id']: count for s, count in schemes_data}
    
    # Ensure we have schemes with different priorities by manipulating access counts
    # Set some schemes to have high access (priority 1-2) and some low (priority 3-5)
    high_priority_ids = []
    low_priority_ids = []
    
    for i, (scheme, _) in enumerate(schemes_data):
        scheme_id = scheme['scheme_id']
        if i % 3 == 0:
            # High priority (100+ accesses = priority 1)
            access_counts[scheme_id] = 100 + i
            high_priority_ids.append(scheme_id)
        else:
            # Low priority (< 5 accesses = priority 5)
            access_counts[scheme_id] = i % 5
            low_priority_ids.append(scheme_id)
    
    # Mock DynamoDB tables
    mock_schemes_table = Mock()
    mock_interactions_table = Mock()
    
    mock_schemes_table.scan.return_value = {'Items': schemes}
    
    interaction_items = []
    for scheme_id, count in access_counts.items():
        for _ in range(count):
            interaction_items.append({
                'event_type': 'scheme_accessed',
                'event_data': {'scheme_id': scheme_id}
            })
    
    mock_interactions_table.scan.return_value = {'Items': interaction_items}
    
    with patch('src.api.cache_export.dynamodb') as mock_dynamodb:
        mock_dynamodb.Table.side_effect = lambda name: (
            mock_schemes_table if 'schemes' in name.lower() 
            else mock_interactions_table
        )
        
        # Get cached schemes
        cached_schemes = get_frequently_accessed_schemes(limit=len(schemes))
        
        # Find positions of high and low priority schemes
        high_priority_positions = []
        low_priority_positions = []
        
        for i, scheme in enumerate(cached_schemes):
            if scheme['priority'] <= 2:
                high_priority_positions.append(i)
            elif scheme['priority'] >= 3:
                low_priority_positions.append(i)
        
        # Verify that all high-priority schemes come before all low-priority schemes
        if high_priority_positions and low_priority_positions:
            max_high_priority_pos = max(high_priority_positions)
            min_low_priority_pos = min(low_priority_positions)
            
            assert max_high_priority_pos < min_low_priority_pos, \
                f"High-priority schemes should come before low-priority schemes. " \
                f"Max high-priority position: {max_high_priority_pos}, " \
                f"Min low-priority position: {min_low_priority_pos}"
