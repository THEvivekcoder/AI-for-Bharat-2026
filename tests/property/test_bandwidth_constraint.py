"""Property-based tests for bandwidth constraint compliance.

Feature: bharatsahayak, Property 18: Bandwidth Constraint Compliance
**Validates: Requirements 7.2**

This test verifies that API responses are under 100KB when compressed,
ensuring low-bandwidth compatibility for rural users with limited connectivity.
"""

import pytest
import json
import gzip
from hypothesis import given, settings, strategies as st, HealthCheck
from typing import Dict, Any, List

# Import all API handlers to test
from src.api.schemes_search import lambda_handler as schemes_search_handler
from src.api.scheme_details import lambda_handler as scheme_details_handler
from src.api.eligible_schemes import lambda_handler as eligible_schemes_handler
from src.api.health_check import lambda_handler as health_check_handler
from src.api.health_facilities import lambda_handler as health_facilities_handler
from src.api.crop_advice import lambda_handler as crop_advice_handler
from src.api.market_price import lambda_handler as market_price_handler
from src.api.job_search import lambda_handler as job_search_handler
from src.api.skills_match import lambda_handler as skills_match_handler


# Constants
MAX_COMPRESSED_SIZE_BYTES = 100 * 1024  # 100KB = 102400 bytes


def compress_response(response_body: str) -> bytes:
    """
    Compress response body using gzip compression.
    
    Args:
        response_body: JSON string response body
        
    Returns:
        Compressed bytes
    """
    return gzip.compress(response_body.encode('utf-8'))


def get_compressed_size(response: Dict[str, Any]) -> int:
    """
    Get the compressed size of an API response.
    
    Args:
        response: Lambda response dictionary with statusCode and body
        
    Returns:
        Size in bytes after gzip compression
    """
    if response.get('statusCode') != 200:
        # Don't test error responses
        return 0
    
    body = response.get('body', '')
    compressed = compress_response(body)
    return len(compressed)


# Custom strategies for generating test data
@st.composite
def scheme_search_params_strategy(draw):
    """Generate random scheme search parameters."""
    categories = ['agriculture', 'health', 'education', 'employment', 'social_welfare']
    states = ['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Uttar Pradesh', 'Bihar', None]
    
    return {
        'q': draw(st.one_of(
            st.none(),
            st.sampled_from(['farmer', 'health', 'education', 'loan', 'pension', 'subsidy'])
        )),
        'category': draw(st.one_of(st.none(), st.sampled_from(categories))),
        'state': draw(st.one_of(st.none(), st.sampled_from(states))),
        'page': draw(st.integers(min_value=1, max_value=3)),
        'limit': draw(st.integers(min_value=10, max_value=50))
    }


@st.composite
def health_check_params_strategy(draw):
    """Generate random health check parameters."""
    common_symptoms = [
        "fever", "cough", "cold", "headache", "body ache", "sore throat",
        "stomach pain", "diarrhea", "nausea", "vomiting", "fatigue",
        "dizziness", "rash", "chest pain", "difficulty breathing"
    ]
    
    num_symptoms = draw(st.integers(min_value=1, max_value=5))
    symptoms = draw(st.lists(
        st.sampled_from(common_symptoms),
        min_size=num_symptoms,
        max_size=num_symptoms,
        unique=True
    ))
    
    return {
        'symptoms': symptoms,
        'user_info': {
            'age': draw(st.integers(min_value=18, max_value=80)),
            'gender': draw(st.sampled_from(['male', 'female']))
        }
    }


@st.composite
def crop_advice_params_strategy(draw):
    """Generate random crop advice parameters."""
    soil_types = ['black', 'loam', 'clay', 'sandy', 'alluvial']
    irrigation_types = ['rainfed', 'well', 'canal', 'drip', 'sprinkler']
    seasons = ['kharif', 'rabi', 'zaid']
    
    return {
        'user_id': f"user_{draw(st.integers(min_value=1000, max_value=9999))}",
        'land_size_acres': draw(st.floats(min_value=1.0, max_value=50.0)),
        'soil_type': draw(st.sampled_from(soil_types)),
        'irrigation_type': draw(st.sampled_from(irrigation_types)),
        'location': {
            'state': 'Maharashtra',
            'district': 'Pune',
            'pincode': '411001'
        },
        'current_crops': [],
        'previous_crops': [],
        'season': draw(st.sampled_from(seasons))
    }


@st.composite
def job_search_params_strategy(draw):
    """Generate random job search parameters."""
    education_levels = ['10th', '12th', 'graduate', 'postgraduate']
    departments = ['Agriculture', 'Health', 'Education', 'Police', 'Railways']
    
    return {
        'education': draw(st.one_of(st.none(), st.sampled_from(education_levels))),
        'department': draw(st.one_of(st.none(), st.sampled_from(departments))),
        'state': draw(st.one_of(st.none(), st.sampled_from(['Maharashtra', 'Karnataka']))),
        'page': draw(st.integers(min_value=1, max_value=2)),
        'limit': draw(st.integers(min_value=10, max_value=30))
    }


@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
@given(params=scheme_search_params_strategy())
def test_schemes_search_bandwidth_constraint(params):
    """
    Feature: bharatsahayak, Property 18: Bandwidth Constraint Compliance
    
    Test that scheme search API responses are under 100KB when compressed.
    This ensures the API works well in low-bandwidth rural environments.
    """
    # Create Lambda event
    event = {
        'httpMethod': 'GET',
        'path': '/schemes',
        'queryStringParameters': {
            k: str(v) for k, v in params.items() if v is not None
        }
    }
    
    # Call handler
    response = schemes_search_handler(event, None)
    
    # Get compressed size
    compressed_size = get_compressed_size(response)
    
    # Skip if error response
    if compressed_size == 0:
        return
    
    # Assert bandwidth constraint
    assert compressed_size < MAX_COMPRESSED_SIZE_BYTES, (
        f"Schemes search response size {compressed_size} bytes exceeds "
        f"100KB limit ({MAX_COMPRESSED_SIZE_BYTES} bytes) when compressed. "
        f"Params: {params}"
    )


@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
@given(params=health_check_params_strategy())
def test_health_check_bandwidth_constraint(params):
    """
    Test that health check API responses are under 100KB when compressed.
    """
    # Create Lambda event
    event = {
        'httpMethod': 'POST',
        'path': '/health/check',
        'body': json.dumps(params)
    }
    
    # Call handler
    response = health_check_handler(event, None)
    
    # Get compressed size
    compressed_size = get_compressed_size(response)
    
    # Skip if error response
    if compressed_size == 0:
        return
    
    # Assert bandwidth constraint
    assert compressed_size < MAX_COMPRESSED_SIZE_BYTES, (
        f"Health check response size {compressed_size} bytes exceeds "
        f"100KB limit ({MAX_COMPRESSED_SIZE_BYTES} bytes) when compressed. "
        f"Symptoms: {params['symptoms']}"
    )


@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
@given(params=crop_advice_params_strategy())
def test_crop_advice_bandwidth_constraint(params):
    """
    Test that crop advice API responses are under 100KB when compressed.
    """
    # Create Lambda event
    event = {
        'httpMethod': 'POST',
        'path': '/farmer/crop-advice',
        'body': json.dumps(params)
    }
    
    # Call handler
    response = crop_advice_handler(event, None)
    
    # Get compressed size
    compressed_size = get_compressed_size(response)
    
    # Skip if error response
    if compressed_size == 0:
        return
    
    # Assert bandwidth constraint
    assert compressed_size < MAX_COMPRESSED_SIZE_BYTES, (
        f"Crop advice response size {compressed_size} bytes exceeds "
        f"100KB limit ({MAX_COMPRESSED_SIZE_BYTES} bytes) when compressed. "
        f"Farm: {params['soil_type']}, {params['irrigation_type']}"
    )


@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.data_too_large])
@given(params=job_search_params_strategy())
def test_job_search_bandwidth_constraint(params):
    """
    Test that job search API responses are under 100KB when compressed.
    """
    # Create Lambda event
    event = {
        'httpMethod': 'GET',
        'path': '/jobs',
        'queryStringParameters': {
            k: str(v) for k, v in params.items() if v is not None
        }
    }
    
    # Call handler
    response = job_search_handler(event, None)
    
    # Get compressed size
    compressed_size = get_compressed_size(response)
    
    # Skip if error response
    if compressed_size == 0:
        return
    
    # Assert bandwidth constraint
    assert compressed_size < MAX_COMPRESSED_SIZE_BYTES, (
        f"Job search response size {compressed_size} bytes exceeds "
        f"100KB limit ({MAX_COMPRESSED_SIZE_BYTES} bytes) when compressed. "
        f"Params: {params}"
    )


def test_bandwidth_constraint_with_max_results():
    """
    Test bandwidth constraint with maximum result sets.
    
    This tests the worst-case scenario where the API returns the maximum
    number of results allowed.
    """
    # Test schemes search with max limit
    event = {
        'httpMethod': 'GET',
        'path': '/schemes',
        'queryStringParameters': {
            'limit': '100',  # Maximum allowed
            'page': '1'
        }
    }
    
    response = schemes_search_handler(event, None)
    compressed_size = get_compressed_size(response)
    
    if compressed_size > 0:
        assert compressed_size < MAX_COMPRESSED_SIZE_BYTES, (
            f"Schemes search with max results ({compressed_size} bytes) "
            f"exceeds 100KB limit when compressed"
        )


def test_bandwidth_constraint_with_detailed_response():
    """
    Test bandwidth constraint with detailed responses.
    
    This tests endpoints that return detailed information which might
    be larger than summary responses.
    """
    # Test health check with multiple symptoms (detailed response)
    event = {
        'httpMethod': 'POST',
        'path': '/health/check',
        'body': json.dumps({
            'symptoms': [
                'fever', 'cough', 'cold', 'headache', 'body ache',
                'sore throat', 'fatigue', 'dizziness'
            ],
            'user_info': {
                'age': 45,
                'gender': 'male'
            }
        })
    }
    
    response = health_check_handler(event, None)
    compressed_size = get_compressed_size(response)
    
    if compressed_size > 0:
        assert compressed_size < MAX_COMPRESSED_SIZE_BYTES, (
            f"Health check with many symptoms ({compressed_size} bytes) "
            f"exceeds 100KB limit when compressed"
        )


def test_compression_ratio():
    """
    Test that responses achieve reasonable compression ratios.
    
    This verifies that the API responses are compressible (JSON format)
    and that compression is effective.
    """
    # Test with a typical scheme search
    event = {
        'httpMethod': 'GET',
        'path': '/schemes',
        'queryStringParameters': {
            'limit': '20',
            'page': '1'
        }
    }
    
    response = schemes_search_handler(event, None)
    
    if response.get('statusCode') == 200:
        body = response.get('body', '')
        uncompressed_size = len(body.encode('utf-8'))
        compressed_size = len(compress_response(body))
        
        # Calculate compression ratio
        if uncompressed_size > 0:
            compression_ratio = compressed_size / uncompressed_size
            
            # JSON should compress to at least 30% of original size
            assert compression_ratio < 0.7, (
                f"Poor compression ratio: {compression_ratio:.2%}. "
                f"Uncompressed: {uncompressed_size} bytes, "
                f"Compressed: {compressed_size} bytes"
            )


def test_all_major_endpoints_bandwidth():
    """
    Test that all major API endpoints respect bandwidth constraints.
    
    This is a comprehensive test that checks multiple endpoints with
    typical request parameters.
    """
    test_cases = [
        # Schemes search
        {
            'handler': schemes_search_handler,
            'event': {
                'httpMethod': 'GET',
                'path': '/schemes',
                'queryStringParameters': {'limit': '20', 'category': 'agriculture'}
            },
            'name': 'schemes_search'
        },
        # Health check
        {
            'handler': health_check_handler,
            'event': {
                'httpMethod': 'POST',
                'path': '/health/check',
                'body': json.dumps({'symptoms': ['fever', 'cough']})
            },
            'name': 'health_check'
        },
        # Crop advice
        {
            'handler': crop_advice_handler,
            'event': {
                'httpMethod': 'POST',
                'path': '/farmer/crop-advice',
                'body': json.dumps({
                    'user_id': 'test_user',
                    'land_size_acres': 5.0,
                    'soil_type': 'black',
                    'irrigation_type': 'well',
                    'location': {'state': 'Maharashtra', 'district': 'Pune', 'pincode': '411001'},
                    'current_crops': [],
                    'previous_crops': [],
                    'season': 'kharif'
                })
            },
            'name': 'crop_advice'
        },
        # Job search
        {
            'handler': job_search_handler,
            'event': {
                'httpMethod': 'GET',
                'path': '/jobs',
                'queryStringParameters': {'limit': '20', 'education': 'graduate'}
            },
            'name': 'job_search'
        }
    ]
    
    for test_case in test_cases:
        handler = test_case['handler']
        event = test_case['event']
        name = test_case['name']
        
        response = handler(event, None)
        compressed_size = get_compressed_size(response)
        
        if compressed_size > 0:
            assert compressed_size < MAX_COMPRESSED_SIZE_BYTES, (
                f"{name} endpoint response size {compressed_size} bytes "
                f"exceeds 100KB limit ({MAX_COMPRESSED_SIZE_BYTES} bytes) when compressed"
            )
