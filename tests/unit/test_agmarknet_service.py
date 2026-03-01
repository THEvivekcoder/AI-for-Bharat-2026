"""Unit tests for AGMARKNET service."""

import pytest
from unittest.mock import Mock, patch
import requests

from src.services.agmarknet_service import AgmarknetService, AgmarknetPrice


@pytest.fixture
def agmarknet_service():
    """Create AGMARKNET service instance."""
    return AgmarknetService(api_key='test-key')


@pytest.fixture
def mock_api_response():
    """Mock API response from data.gov.in."""
    return {
        'records': [
            {
                'state': 'Maharashtra',
                'district': 'Pune',
                'market': 'Pune APMC',
                'commodity': 'Wheat',
                'variety': 'Local',
                'arrival_date': '2024-01-20',
                'min_price': '2400',
                'max_price': '2600',
                'modal_price': '2500'
            },
            {
                'state': 'Maharashtra',
                'district': 'Mumbai',
                'market': 'Vashi APMC',
                'commodity': 'Wheat',
                'variety': 'Local',
                'arrival_date': '2024-01-20',
                'min_price': '2500',
                'max_price': '2700',
                'modal_price': '2600'
            }
        ]
    }


def test_fetch_prices_success(agmarknet_service, mock_api_response):
    """Test successful price fetching from API."""
    with patch.object(agmarknet_service.session, 'get') as mock_get:
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = mock_api_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Fetch prices
        prices = agmarknet_service.fetch_prices(
            commodity='Wheat',
            state='Maharashtra',
            district='Pune'
        )
        
        # Verify results
        assert len(prices) == 2
        assert prices[0].state == 'Maharashtra'
        assert prices[0].district == 'Pune'
        assert prices[0].commodity == 'Wheat'
        assert prices[0].modal_price == 2500.0


def test_fetch_prices_no_records(agmarknet_service):
    """Test handling of empty API response."""
    with patch.object(agmarknet_service.session, 'get') as mock_get:
        # Mock empty response
        mock_response = Mock()
        mock_response.json.return_value = {'records': []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Fetch prices
        prices = agmarknet_service.fetch_prices(commodity='Wheat')
        
        # Should return empty list
        assert len(prices) == 0


def test_fetch_prices_api_error(agmarknet_service):
    """Test handling of API request errors."""
    with patch.object(agmarknet_service.session, 'get') as mock_get:
        # Mock API error
        mock_get.side_effect = requests.RequestException("API Error")
        
        # Should raise exception
        with pytest.raises(requests.RequestException):
            agmarknet_service.fetch_prices(commodity='Wheat')


def test_parse_record_valid(agmarknet_service):
    """Test parsing valid record."""
    record = {
        'state': 'Maharashtra',
        'district': 'Pune',
        'market': 'Pune APMC',
        'commodity': 'Wheat',
        'variety': 'Local',
        'arrival_date': '2024-01-20',
        'min_price': '2400',
        'max_price': '2600',
        'modal_price': '2500'
    }
    
    price = agmarknet_service._parse_record(record)
    
    assert price is not None
    assert price.state == 'Maharashtra'
    assert price.district == 'Pune'
    assert price.market == 'Pune APMC'
    assert price.commodity == 'Wheat'
    assert price.min_price == 2400.0
    assert price.max_price == 2600.0
    assert price.modal_price == 2500.0


def test_parse_record_missing_fields(agmarknet_service):
    """Test parsing record with missing required fields."""
    record = {
        'state': 'Maharashtra',
        # Missing district, market, commodity
        'min_price': '2500'
    }
    
    price = agmarknet_service._parse_record(record)
    
    # Should return None for invalid record
    assert price is None


def test_parse_price_various_formats(agmarknet_service):
    """Test price parsing from various formats."""
    # Integer
    assert agmarknet_service._parse_price(2500) == 2500.0
    
    # Float
    assert agmarknet_service._parse_price(2500.50) == 2500.50
    
    # String
    assert agmarknet_service._parse_price('2500') == 2500.0
    
    # String with comma
    assert agmarknet_service._parse_price('2,500') == 2500.0
    
    # Empty string
    assert agmarknet_service._parse_price('') == 0.0
    
    # Invalid value
    assert agmarknet_service._parse_price('invalid') == 0.0
    
    # None
    assert agmarknet_service._parse_price(None) == 0.0


def test_commodity_mapping(agmarknet_service):
    """Test commodity name mapping."""
    # Test known mappings
    assert agmarknet_service.get_commodity_mapping('wheat') == 'Wheat'
    assert agmarknet_service.get_commodity_mapping('rice') == 'Rice'
    assert agmarknet_service.get_commodity_mapping('soybean') == 'Soyabean'
    assert agmarknet_service.get_commodity_mapping('cotton') == 'Cotton'
    
    # Test unknown commodity (should return title case)
    assert agmarknet_service.get_commodity_mapping('unknown') == 'Unknown'
    
    # Test case insensitivity
    assert agmarknet_service.get_commodity_mapping('WHEAT') == 'Wheat'
    assert agmarknet_service.get_commodity_mapping('WhEaT') == 'Wheat'


def test_fetch_prices_with_filters(agmarknet_service):
    """Test that API is called with correct filters."""
    with patch.object(agmarknet_service.session, 'get') as mock_get:
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {'records': []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Fetch with filters
        agmarknet_service.fetch_prices(
            commodity='Wheat',
            state='Maharashtra',
            district='Pune',
            limit=50
        )
        
        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        
        # Check parameters
        params = call_args[1]['params']
        assert params['limit'] == 50
        assert 'filters' in params


def test_fetch_prices_timeout(agmarknet_service):
    """Test that API requests have timeout."""
    with patch.object(agmarknet_service.session, 'get') as mock_get:
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {'records': []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Fetch prices
        agmarknet_service.fetch_prices(commodity='Wheat')
        
        # Verify timeout is set
        call_args = mock_get.call_args
        assert call_args[1]['timeout'] == 10
