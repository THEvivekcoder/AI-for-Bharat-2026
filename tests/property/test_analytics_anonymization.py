"""Property-based tests for analytics data anonymization.

Feature: bharatsahayak, Property 25: Analytics Data Anonymization
**Validates: Requirements 9.4**

This test verifies that analytics query results do not contain personally
identifiable information (PII) such as phone numbers, exact locations, or names,
ensuring user privacy protection.
"""

import pytest
from hypothesis import given, settings, strategies as st
from datetime import datetime
from unittest.mock import Mock, patch
import re

from src.core.impact_repository import ImpactRepository


# Custom strategies for generating test data with PII
@st.composite
def event_with_pii_strategy(draw):
    """Generate event dictionaries that may contain PII in event_data."""
    # Generate user_id (this is acceptable as it's anonymized)
    user_id = f"user_{draw(st.integers(min_value=100000, max_value=999999))}"
    
    # Generate event with potential PII in event_data
    event_type = draw(st.sampled_from([
        "query_submitted",
        "scheme_accessed",
        "job_discovered"
    ]))
    
    # Create event_data that might contain PII
    event_data = {
        "category": draw(st.sampled_from(["agriculture", "health", "education"])),
    }
    
    # Potentially add PII fields (these should NOT appear in analytics)
    if draw(st.booleans()):
        event_data["user_phone"] = f"+91{draw(st.integers(min_value=6000000000, max_value=9999999999))}"
    
    if draw(st.booleans()):
        event_data["user_name"] = draw(st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
    
    if draw(st.booleans()):
        event_data["exact_location"] = {
            "latitude": draw(st.floats(min_value=8.0, max_value=35.0, allow_nan=False, allow_infinity=False)),
            "longitude": draw(st.floats(min_value=68.0, max_value=97.0, allow_nan=False, allow_infinity=False)),
            "address": draw(st.text(min_size=10, max_size=100))
        }
    
    return {
        'event_id': f"evt_{draw(st.integers(min_value=100000, max_value=999999))}",
        'user_id': user_id,
        'event_type': event_type,
        'event_data': event_data,
        'language': draw(st.sampled_from(["hi", "en", "mr", "ta"])),
        'timestamp': datetime.utcnow().isoformat(),
        'record_type': 'interaction'
    }


def contains_phone_number(data: any) -> bool:
    """
    Check if data contains phone numbers.
    Looks for patterns like +91XXXXXXXXXX or 10-digit numbers.
    """
    if isinstance(data, str):
        # Check for phone number patterns
        phone_patterns = [
            r'\+91\d{10}',  # +91 followed by 10 digits
            r'\b\d{10}\b',  # 10 consecutive digits
            r'\(\d{3}\)\s*\d{3}-\d{4}',  # (XXX) XXX-XXXX format
        ]
        for pattern in phone_patterns:
            if re.search(pattern, data):
                return True
    elif isinstance(data, dict):
        for value in data.values():
            if contains_phone_number(value):
                return True
    elif isinstance(data, list):
        for item in data:
            if contains_phone_number(item):
                return True
    return False


def contains_exact_location(data: any) -> bool:
    """
    Check if data contains exact location coordinates.
    Looks for latitude/longitude fields or coordinate patterns.
    """
    if isinstance(data, dict):
        # Check for coordinate fields
        if 'latitude' in data or 'longitude' in data:
            return True
        if 'lat' in data or 'lon' in data or 'lng' in data:
            return True
        # Check for address field
        if 'address' in data and isinstance(data['address'], str) and len(data['address']) > 10:
            return True
        # Recursively check nested dicts
        for value in data.values():
            if contains_exact_location(value):
                return True
    elif isinstance(data, list):
        for item in data:
            if contains_exact_location(item):
                return True
    return False


def contains_personal_name(data: any) -> bool:
    """
    Check if data contains personal name fields.
    Looks for common name-related keys.
    """
    if isinstance(data, dict):
        # Check for name-related keys
        name_keys = ['name', 'user_name', 'full_name', 'first_name', 'last_name', 'person_name']
        for key in name_keys:
            if key in data and isinstance(data[key], str) and len(data[key]) > 0:
                return True
        # Recursively check nested dicts
        for value in data.values():
            if contains_personal_name(value):
                return True
    elif isinstance(data, list):
        for item in data:
            if contains_personal_name(item):
                return True
    return False


@settings(max_examples=100, deadline=None)
@given(events=st.lists(event_with_pii_strategy(), min_size=5, max_size=20))
def test_analytics_data_anonymization(events):
    """
    Feature: bharatsahayak, Property 25: Analytics Data Anonymization
    
    For any analytics query result, the returned data should not contain
    personally identifiable information (PII) such as:
    - Phone numbers
    - Exact location coordinates (latitude/longitude)
    - Personal names
    - Addresses
    
    This test verifies:
    1. Analytics results contain only aggregated metrics
    2. No phone numbers appear in the response
    3. No exact location coordinates appear in the response
    4. No personal names appear in the response
    5. User IDs are aggregated (only count, not individual IDs)
    """
    # Create mock table
    mock_table = Mock()
    
    with patch('boto3.resource') as mock_resource:
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb
        
        with patch('boto3.client'):
            repo = ImpactRepository(table_name="TestInteractions")
            repo.table = mock_table
            
            # Mock the scan operation to return our test events
            mock_table.scan.return_value = {'Items': events}
            
            # Get analytics data
            metrics = repo.get_analytics_data(limit=len(events))
            
            # Verify metrics structure
            assert isinstance(metrics, dict)
            assert 'total_users' in metrics
            assert 'total_queries' in metrics
            assert 'schemes_accessed' in metrics
            assert 'by_category' in metrics
            assert 'by_language' in metrics
            
            # Convert metrics to JSON string for comprehensive PII checking
            import json
            metrics_json = json.dumps(metrics)
            
            # Verify no phone numbers in response
            assert not contains_phone_number(metrics_json), \
                "Analytics response contains phone numbers - PII not anonymized!"
            
            # Verify no exact locations in response
            assert not contains_exact_location(metrics), \
                "Analytics response contains exact location data - PII not anonymized!"
            
            # Verify no personal names in response
            assert not contains_personal_name(metrics), \
                "Analytics response contains personal names - PII not anonymized!"
            
            # Verify user_ids are not exposed individually
            # Only the count should be present
            assert 'user_id' not in metrics_json, \
                "Analytics response contains individual user_ids - should only show count!"
            
            # Verify only aggregated data is present
            assert isinstance(metrics['total_users'], int), \
                "total_users should be an integer count, not individual user data"
            
            assert metrics['total_users'] >= 0, \
                "total_users should be a non-negative count"
            
            # Verify category aggregation doesn't contain PII
            for category, count in metrics['by_category'].items():
                assert isinstance(count, int), \
                    f"Category count for {category} should be integer, not detailed user data"
                assert not contains_phone_number(category), \
                    f"Category name {category} should not contain phone numbers"
            
            # Verify language aggregation doesn't contain PII
            for language, count in metrics['by_language'].items():
                assert isinstance(count, int), \
                    f"Language count for {language} should be integer, not detailed user data"
                assert language in ['hi', 'en', 'bn', 'te', 'mr', 'ta', 'gu', 'kn', 'pa', 'or'], \
                    f"Language code {language} should be a valid language code, not PII"


@settings(max_examples=50, deadline=None)
@given(events=st.lists(event_with_pii_strategy(), min_size=10, max_size=30))
def test_analytics_aggregation_only(events):
    """
    Test that analytics returns only aggregated counts, not individual records.
    
    This verifies that the analytics function properly aggregates data and
    doesn't leak individual event details.
    """
    # Create mock table
    mock_table = Mock()
    
    with patch('boto3.resource') as mock_resource:
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb
        
        with patch('boto3.client'):
            repo = ImpactRepository(table_name="TestInteractions")
            repo.table = mock_table
            
            # Mock the scan operation
            mock_table.scan.return_value = {'Items': events}
            
            # Get analytics data
            metrics = repo.get_analytics_data(limit=len(events))
            
            # Verify response contains only aggregated metrics
            # Should NOT contain:
            # - Individual event records
            # - Lists of user_ids
            # - Lists of events
            # - Detailed event_data
            
            # Check that we don't have lists of events
            for key, value in metrics.items():
                if key not in ['by_category', 'by_language']:
                    # These should be scalar values (int or float)
                    assert isinstance(value, (int, float)), \
                        f"Metric {key} should be a scalar value, not a list or dict of individual records"
            
            # Verify by_category and by_language are aggregations
            assert isinstance(metrics['by_category'], dict), \
                "by_category should be a dictionary of counts"
            
            for category, count in metrics['by_category'].items():
                assert isinstance(count, int), \
                    f"Category {category} should have an integer count"
                assert count > 0, \
                    f"Category {category} count should be positive"
            
            assert isinstance(metrics['by_language'], dict), \
                "by_language should be a dictionary of counts"
            
            for language, count in metrics['by_language'].items():
                assert isinstance(count, int), \
                    f"Language {language} should have an integer count"
                assert count > 0, \
                    f"Language {language} count should be positive"


@settings(max_examples=50, deadline=None)
@given(events=st.lists(event_with_pii_strategy(), min_size=1, max_size=10))
def test_user_count_anonymization(events):
    """
    Test that user counts are anonymized - only the total count is provided,
    not individual user identifiers.
    """
    # Create mock table
    mock_table = Mock()
    
    with patch('boto3.resource') as mock_resource:
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_resource.return_value = mock_dynamodb
        
        with patch('boto3.client'):
            repo = ImpactRepository(table_name="TestInteractions")
            repo.table = mock_table
            
            # Mock the scan operation
            mock_table.scan.return_value = {'Items': events}
            
            # Get analytics data
            metrics = repo.get_analytics_data(limit=len(events))
            
            # Extract unique user_ids from events
            unique_users = set(event['user_id'] for event in events)
            
            # Verify total_users is correct count
            assert metrics['total_users'] == len(unique_users), \
                "total_users should match the count of unique users"
            
            # Verify individual user_ids are NOT in the response
            import json
            metrics_json = json.dumps(metrics)
            
            for user_id in unique_users:
                assert user_id not in metrics_json, \
                    f"Individual user_id {user_id} should not appear in analytics response"
            
            # Verify only the count is present
            assert isinstance(metrics['total_users'], int), \
                "total_users should be an integer count"
