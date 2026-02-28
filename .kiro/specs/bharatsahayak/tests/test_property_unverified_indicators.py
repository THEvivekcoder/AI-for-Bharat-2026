"""
Property-Based Test: Unverified Information Indicators
Feature: bharatsahayak, Property 27: Unverified Information Indicators

For any information that cannot be verified against official sources, the response 
should include an uncertainty indicator or source attribution.

Validates: Requirements 12.3
"""
import pytest
from hypothesis import given, settings, strategies as st, assume
from hypothesis.strategies import composite
from datetime import datetime, timedelta
from app.services.verification_tracker import (
    VerificationTracker,
    VerificationStatus,
    DataFreshnessLevel
)


# Strategy for generating data with various verification states
@composite
def data_with_verification_strategy(draw):
    """Generate data with different verification states"""
    verification_statuses = [
        VerificationStatus.VERIFIED,
        VerificationStatus.UNVERIFIED,
        VerificationStatus.PENDING,
        None  # No verification status
    ]
    
    # Generate timestamp (or None)
    has_timestamp = draw(st.booleans())
    if has_timestamp:
        days_ago = draw(st.integers(min_value=0, max_value=365))
        last_updated = datetime.utcnow() - timedelta(days=days_ago)
    else:
        last_updated = None
    
    # Generate verification status
    verification_status = draw(st.sampled_from(verification_statuses))
    
    # Generate source attribution
    sources = [
        'Official Government Portal',
        'Third-party aggregator',
        'User submission',
        'Community contribution',
        None
    ]
    verification_source = draw(st.sampled_from(sources))
    
    # Generate base data
    data = {
        'name': draw(st.text(min_size=5, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' -'
        ))),
        'description': draw(st.text(min_size=10, max_size=100, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' .,'
        ))),
        'value': draw(st.integers(min_value=0, max_value=10000))
    }
    
    return {
        'data': data,
        'last_updated': last_updated,
        'verification_status': verification_status,
        'verification_source': verification_source
    }


@settings(max_examples=100, deadline=None)
@given(test_data=data_with_verification_strategy())
def test_unverified_data_has_uncertainty_indicators(test_data):
    """
    Feature: bharatsahayak, Property 27: Unverified Information Indicators
    
    For any information that cannot be verified against official sources, 
    the response should include an uncertainty indicator or source attribution.
    
    Property: Unverified data must have is_verified=False and appropriate warnings.
    """
    data = test_data['data'].copy()
    last_updated = test_data['last_updated']
    verification_status = test_data['verification_status']
    verification_source = test_data['verification_source']
    
    # Add uncertainty indicators
    result = VerificationTracker.add_uncertainty_indicators(
        data=data,
        last_updated=last_updated,
        verification_status=verification_status,
        verification_source=verification_source
    )
    
    # Property 1: Result must have is_verified field
    assert 'is_verified' in result, \
        "Response must include is_verified indicator"
    
    # Property 2: If verification_status is not VERIFIED, is_verified should be False
    if verification_status != VerificationStatus.VERIFIED:
        assert result['is_verified'] is False, \
            "Unverified data must have is_verified=False"
        
        # Property 3: Unverified data should have warnings
        assert 'data_warnings' in result, \
            "Unverified data must include data_warnings"
        
        assert len(result['data_warnings']) > 0, \
            "Unverified data must have at least one warning"
        
        # Property 4: Warning should mention verification status
        warning_text = ' '.join(result['data_warnings']).lower()
        assert 'verified' in warning_text or 'verify' in warning_text, \
            "Warning should mention verification status"


@settings(max_examples=100, deadline=None)
@given(test_data=data_with_verification_strategy())
def test_unverified_data_includes_source_attribution(test_data):
    """
    Feature: bharatsahayak, Property 27: Unverified Information Indicators
    
    Property: Unverified data with a source should include source attribution.
    """
    data = test_data['data'].copy()
    last_updated = test_data['last_updated']
    verification_status = test_data['verification_status']
    verification_source = test_data['verification_source']
    
    # Only test when data is unverified and has a source
    assume(verification_status != VerificationStatus.VERIFIED)
    assume(verification_source is not None)
    
    # Add uncertainty indicators
    result = VerificationTracker.add_uncertainty_indicators(
        data=data,
        last_updated=last_updated,
        verification_status=verification_status,
        verification_source=verification_source
    )
    
    # Property: Unverified data with source should include verification_source field
    assert 'verification_source' in result, \
        "Unverified data with source must include verification_source field"
    
    assert result['verification_source'] == verification_source, \
        "verification_source should match the provided source"


@settings(max_examples=100, deadline=None)
@given(test_data=data_with_verification_strategy())
def test_verified_data_has_no_uncertainty_warnings(test_data):
    """
    Feature: bharatsahayak, Property 27: Unverified Information Indicators
    
    Property: Verified data should not have uncertainty warnings about verification.
    """
    data = test_data['data'].copy()
    last_updated = test_data['last_updated']
    verification_status = VerificationStatus.VERIFIED
    verification_source = test_data['verification_source']
    
    # Ensure we have a recent timestamp for verified data
    if last_updated is None or (datetime.utcnow() - last_updated).days > 30:
        last_updated = datetime.utcnow() - timedelta(days=5)
    
    # Add uncertainty indicators
    result = VerificationTracker.add_uncertainty_indicators(
        data=data,
        last_updated=last_updated,
        verification_status=verification_status,
        verification_source=verification_source
    )
    
    # Property 1: Verified data should have is_verified=True
    assert result['is_verified'] is True, \
        "Verified data must have is_verified=True"
    
    # Property 2: Verified data should not have verification warnings
    if 'data_warnings' in result:
        warning_text = ' '.join(result['data_warnings']).lower()
        # Should not have verification-related warnings
        assert 'not been verified' not in warning_text, \
            "Verified data should not have 'not been verified' warning"


@settings(max_examples=100, deadline=None)
@given(test_data=data_with_verification_strategy())
def test_all_data_has_freshness_indicators(test_data):
    """
    Feature: bharatsahayak, Property 27: Unverified Information Indicators
    
    Property: All data should have freshness level indicators regardless of 
    verification status.
    """
    data = test_data['data'].copy()
    last_updated = test_data['last_updated']
    verification_status = test_data['verification_status']
    verification_source = test_data['verification_source']
    
    # Add uncertainty indicators
    result = VerificationTracker.add_uncertainty_indicators(
        data=data,
        last_updated=last_updated,
        verification_status=verification_status,
        verification_source=verification_source
    )
    
    # Property 1: Must have freshness_level field
    assert 'freshness_level' in result, \
        "Response must include freshness_level indicator"
    
    # Property 2: freshness_level must be a valid value
    valid_freshness_levels = [level.value for level in DataFreshnessLevel]
    assert result['freshness_level'] in valid_freshness_levels, \
        f"freshness_level must be one of {valid_freshness_levels}"
    
    # Property 3: Must have data_age_days field
    assert 'data_age_days' in result, \
        "Response must include data_age_days indicator"


@settings(max_examples=100, deadline=None)
@given(test_data=data_with_verification_strategy())
def test_stale_data_has_staleness_warning(test_data):
    """
    Feature: bharatsahayak, Property 27: Unverified Information Indicators
    
    Property: Stale data (>30 days old) should have warnings about being outdated.
    """
    data = test_data['data'].copy()
    verification_status = test_data['verification_status']
    verification_source = test_data['verification_source']
    
    # Force stale data
    days_old = 45  # More than 30 days
    last_updated = datetime.utcnow() - timedelta(days=days_old)
    
    # Add uncertainty indicators
    result = VerificationTracker.add_uncertainty_indicators(
        data=data,
        last_updated=last_updated,
        verification_status=verification_status,
        verification_source=verification_source
    )
    
    # Property 1: Stale data should have warnings
    assert 'data_warnings' in result, \
        "Stale data must include data_warnings"
    
    assert len(result['data_warnings']) > 0, \
        "Stale data must have at least one warning"
    
    # Property 2: Warning should mention staleness
    warning_text = ' '.join(result['data_warnings']).lower()
    assert 'outdated' in warning_text or 'old' in warning_text or 'updated' in warning_text, \
        "Warning should mention data staleness"


@settings(max_examples=100, deadline=None)
@given(test_data=data_with_verification_strategy())
def test_unknown_timestamp_has_warning(test_data):
    """
    Feature: bharatsahayak, Property 27: Unverified Information Indicators
    
    Property: Data with unknown timestamp should have warnings about unknown freshness.
    """
    data = test_data['data'].copy()
    verification_status = test_data['verification_status']
    verification_source = test_data['verification_source']
    
    # Force unknown timestamp
    last_updated = None
    
    # Add uncertainty indicators
    result = VerificationTracker.add_uncertainty_indicators(
        data=data,
        last_updated=last_updated,
        verification_status=verification_status,
        verification_source=verification_source
    )
    
    # Property 1: Unknown timestamp should result in UNKNOWN freshness level
    assert result['freshness_level'] == DataFreshnessLevel.UNKNOWN.value, \
        "Data without timestamp should have UNKNOWN freshness level"
    
    # Property 2: Should have warning about unknown update date
    assert 'data_warnings' in result, \
        "Data with unknown timestamp must include data_warnings"
    
    warning_text = ' '.join(result['data_warnings']).lower()
    assert 'unknown' in warning_text or 'update date' in warning_text, \
        "Warning should mention unknown update date"


@settings(max_examples=100, deadline=None)
@given(
    verification_status=st.sampled_from([
        VerificationStatus.VERIFIED,
        VerificationStatus.UNVERIFIED,
        VerificationStatus.PENDING,
        None
    ])
)
def test_is_verified_field_consistency(verification_status):
    """
    Feature: bharatsahayak, Property 27: Unverified Information Indicators
    
    Property: The is_verified field should be consistent with verification_status.
    """
    data = {'test': 'data'}
    last_updated = datetime.utcnow()
    
    result = VerificationTracker.add_uncertainty_indicators(
        data=data,
        last_updated=last_updated,
        verification_status=verification_status,
        verification_source='Test Source'
    )
    
    # Property: is_verified should be True only when status is VERIFIED
    expected_is_verified = (verification_status == VerificationStatus.VERIFIED)
    assert result['is_verified'] == expected_is_verified, \
        f"is_verified should be {expected_is_verified} for status {verification_status}"


def test_specific_unverified_scheme_has_indicators():
    """
    Specific example test: An unverified scheme should have uncertainty indicators.
    """
    scheme_data = {
        'name': 'Community Reported Scheme',
        'description': 'A scheme reported by community members',
        'benefits': ['Financial assistance']
    }
    
    result = VerificationTracker.add_uncertainty_indicators(
        data=scheme_data,
        last_updated=datetime.utcnow() - timedelta(days=10),
        verification_status=VerificationStatus.UNVERIFIED,
        verification_source='Community submission'
    )
    
    assert result['is_verified'] is False, \
        "Unverified scheme must have is_verified=False"
    
    assert 'data_warnings' in result, \
        "Unverified scheme must have warnings"
    
    assert 'verification_source' in result, \
        "Unverified scheme must include source attribution"
    
    assert result['verification_source'] == 'Community submission', \
        "Source attribution should match"


def test_verified_scheme_no_uncertainty_warnings():
    """
    Specific example test: A verified scheme should not have uncertainty warnings.
    """
    scheme_data = {
        'name': 'PM-KISAN',
        'description': 'Official government scheme',
        'benefits': ['Rs 6000 per year']
    }
    
    result = VerificationTracker.add_uncertainty_indicators(
        data=scheme_data,
        last_updated=datetime.utcnow() - timedelta(days=5),
        verification_status=VerificationStatus.VERIFIED,
        verification_source='https://pmkisan.gov.in'
    )
    
    assert result['is_verified'] is True, \
        "Verified scheme must have is_verified=True"
    
    # Should not have verification warnings
    if 'data_warnings' in result:
        warning_text = ' '.join(result['data_warnings']).lower()
        assert 'not been verified' not in warning_text, \
            "Verified scheme should not have verification warnings"


def test_pending_verification_has_indicators():
    """
    Edge case test: Data pending verification should have uncertainty indicators.
    """
    data = {
        'name': 'New Scheme Under Review',
        'description': 'Recently submitted scheme awaiting verification'
    }
    
    result = VerificationTracker.add_uncertainty_indicators(
        data=data,
        last_updated=datetime.utcnow(),
        verification_status=VerificationStatus.PENDING,
        verification_source='Government portal submission'
    )
    
    assert result['is_verified'] is False, \
        "Pending verification should have is_verified=False"
    
    assert 'data_warnings' in result, \
        "Pending verification should have warnings"


def test_multiple_warnings_for_stale_unverified_data():
    """
    Edge case test: Stale AND unverified data should have multiple warnings.
    """
    data = {
        'name': 'Old Unverified Scheme',
        'description': 'Very old data that is also unverified'
    }
    
    result = VerificationTracker.add_uncertainty_indicators(
        data=data,
        last_updated=datetime.utcnow() - timedelta(days=60),
        verification_status=VerificationStatus.UNVERIFIED,
        verification_source='Unknown source'
    )
    
    assert 'data_warnings' in result, \
        "Stale unverified data must have warnings"
    
    # Should have multiple warnings (staleness + unverified)
    assert len(result['data_warnings']) >= 2, \
        "Stale unverified data should have multiple warnings"
    
    warning_text = ' '.join(result['data_warnings']).lower()
    
    # Should mention both staleness and verification
    assert ('outdated' in warning_text or 'old' in warning_text), \
        "Should have staleness warning"
    
    assert 'verified' in warning_text, \
        "Should have verification warning"


def test_fresh_verified_data_minimal_warnings():
    """
    Test that fresh, verified data has minimal or no warnings.
    """
    data = {
        'name': 'Current Verified Scheme',
        'description': 'Recently verified official scheme'
    }
    
    result = VerificationTracker.add_uncertainty_indicators(
        data=data,
        last_updated=datetime.utcnow() - timedelta(days=2),
        verification_status=VerificationStatus.VERIFIED,
        verification_source='https://official.gov.in'
    )
    
    assert result['is_verified'] is True, \
        "Fresh verified data should be marked as verified"
    
    assert result['freshness_level'] == DataFreshnessLevel.FRESH.value, \
        "Should have FRESH freshness level"
    
    # Should have no warnings or minimal warnings
    if 'data_warnings' in result:
        assert len(result['data_warnings']) == 0, \
            "Fresh verified data should have no warnings"


def test_uncertainty_indicators_preserve_original_data():
    """
    Test that adding uncertainty indicators preserves original data fields.
    """
    original_data = {
        'name': 'Test Scheme',
        'description': 'Test description',
        'benefits': ['Benefit 1', 'Benefit 2'],
        'custom_field': 'custom_value'
    }
    
    result = VerificationTracker.add_uncertainty_indicators(
        data=original_data.copy(),
        last_updated=datetime.utcnow(),
        verification_status=VerificationStatus.VERIFIED,
        verification_source='Test source'
    )
    
    # Original fields should be preserved
    for key, value in original_data.items():
        assert key in result, \
            f"Original field '{key}' should be preserved"
        assert result[key] == value, \
            f"Original field '{key}' value should be unchanged"


def test_source_attribution_not_added_for_verified_data():
    """
    Test that verification_source is not added to response for verified data.
    """
    data = {'name': 'Verified Scheme'}
    
    result = VerificationTracker.add_uncertainty_indicators(
        data=data,
        last_updated=datetime.utcnow(),
        verification_status=VerificationStatus.VERIFIED,
        verification_source='https://official.gov.in'
    )
    
    # Verified data should not expose verification_source in response
    # (it's internal metadata, not an uncertainty indicator)
    assert 'verification_source' not in result, \
        "Verified data should not include verification_source in response"
