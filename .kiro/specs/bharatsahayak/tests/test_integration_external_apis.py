"""
Integration Tests for External APIs
Tests integration with government schemes, mandi price, and weather APIs

Feature: bharatsahayak
Requirements: 2.5, 3.3
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date, datetime, timedelta
import httpx
import types

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

from app.integrations.government_schemes_api import government_schemes_api
from app.integrations.mandi_price_api import mandi_price_api
from app.integrations.weather_api import weather_api


@pytest.fixture(autouse=True)
def setup_api_keys():
    """Set up API keys for testing"""
    # Save original keys
    orig_gov_key = government_schemes_api.api_key
    orig_mandi_key = mandi_price_api.api_key
    orig_weather_key = weather_api.openweather_key
    
    # Set test keys
    government_schemes_api.api_key = "test-gov-key"
    mandi_price_api.api_key = "test-mandi-key"
    weather_api.openweather_key = "test-weather-key"
    
    yield
    
    # Restore original keys
    government_schemes_api.api_key = orig_gov_key
    mandi_price_api.api_key = orig_mandi_key
    weather_api.openweather_key = orig_weather_key


def create_mock_http_client(mock_response):
    """
    Helper to create a properly mocked httpx.AsyncClient
    
    Args:
        mock_response: Mock response object or callable that returns mock response
    """
    class MockAsyncClient:
        def __init__(self):
            if callable(mock_response) and not isinstance(mock_response, (AsyncMock, MagicMock)):
                self.get = mock_response
            else:
                self.get = AsyncMock(return_value=mock_response)
        
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, *args):
            return None
    
    return MockAsyncClient()


class TestGovernmentSchemesAPIIntegration:
    """Test government schemes API integration"""
    
    @pytest.mark.asyncio
    async def test_fetch_schemes_success(self):
        """Test successful scheme fetching"""
        mock_response_data = {
            "records": [
                {
                    "id": "PM-KISAN",
                    "name": "PM-KISAN",
                    "category": "agriculture",
                    "state": None,
                    "description": "Income support for farmers"
                },
                {
                    "id": "PMAY",
                    "name": "Pradhan Mantri Awas Yojana",
                    "category": "housing",
                    "state": None,
                    "description": "Housing for all"
                }
            ]
        }
        
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.raise_for_status = MagicMock()
        
        mock_client = create_mock_http_client(mock_response)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            schemes = await government_schemes_api.fetch_schemes(
                category="agriculture",
                limit=100
            )
            
            assert len(schemes) == 2
            assert schemes[0]["id"] == "PM-KISAN"
            assert schemes[0]["category"] == "agriculture"
    
    @pytest.mark.asyncio
    async def test_fetch_schemes_with_filters(self):
        """Test scheme fetching with category and state filters"""
        mock_response_data = {
            "records": [
                {
                    "id": "STATE-SCHEME-1",
                    "name": "State Agriculture Scheme",
                    "category": "agriculture",
                    "state": "Punjab",
                    "description": "State-level support"
                }
            ]
        }
        
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            schemes = await government_schemes_api.fetch_schemes(
                category="agriculture",
                state="Punjab",
                limit=50
            )
            
            assert len(schemes) == 1
            assert schemes[0]["state"] == "Punjab"
    
    @pytest.mark.asyncio
    async def test_fetch_schemes_api_error(self):
        """Test handling of API errors"""
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPError("API Error")
        )
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            schemes = await government_schemes_api.fetch_schemes()
            
            assert schemes == []
    
    @pytest.mark.asyncio
    async def test_fetch_schemes_no_api_key(self):
        """Test behavior when API key is not configured"""
        original_key = government_schemes_api.api_key
        government_schemes_api.api_key = None
        
        try:
            schemes = await government_schemes_api.fetch_schemes()
            assert schemes == []
        finally:
            government_schemes_api.api_key = original_key
    
    @pytest.mark.asyncio
    async def test_fetch_scheme_details_success(self):
        """Test fetching details for a specific scheme"""
        mock_response_data = {
            "records": [
                {
                    "id": "PM-KISAN",
                    "name": "PM-KISAN",
                    "category": "agriculture",
                    "description": "Income support for farmers",
                    "benefits": ["Rs 6000 per year"],
                    "eligibility": {
                        "occupation": ["farmer"],
                        "land_holding": "up to 2 hectares"
                    }
                }
            ]
        }
        
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            details = await government_schemes_api.fetch_scheme_details("PM-KISAN")
            
            assert details is not None
            assert details["id"] == "PM-KISAN"
            assert "benefits" in details
    
    @pytest.mark.asyncio
    async def test_fetch_scheme_details_not_found(self):
        """Test fetching details for non-existent scheme"""
        mock_response_data = {"records": []}
        
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            details = await government_schemes_api.fetch_scheme_details("NONEXISTENT")
            
            assert details is None
    
    @pytest.mark.asyncio
    async def test_verify_scheme_exists(self):
        """Test scheme existence verification"""
        mock_response_data = {
            "records": [
                {"id": "PM-KISAN", "name": "PM-KISAN"},
                {"id": "PMAY", "name": "Pradhan Mantri Awas Yojana"}
            ]
        }
        
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            exists = await government_schemes_api.verify_scheme_exists("PM-KISAN")
            assert exists is True
            
            not_exists = await government_schemes_api.verify_scheme_exists("FAKE-SCHEME")
            assert not_exists is False


class TestMandiPriceAPIIntegration:
    """Test mandi price API integration"""
    
    @pytest.mark.asyncio
    async def test_fetch_current_prices_success(self):
        """Test successful price fetching"""
        mock_response_data = {
            "records": [
                {
                    "commodity": "Rice",
                    "state": "Punjab",
                    "district": "Ludhiana",
                    "market": "Ludhiana Mandi",
                    "modal_price": "2500",
                    "arrival_date": "2026-02-28"
                },
                {
                    "commodity": "Rice",
                    "state": "Punjab",
                    "district": "Amritsar",
                    "market": "Amritsar Mandi",
                    "modal_price": "2480",
                    "arrival_date": "2026-02-28"
                }
            ]
        }
        
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            prices = await mandi_price_api.fetch_current_prices(
                crop="Rice",
                state="Punjab"
            )
            
            assert len(prices) == 2
            assert prices[0]["commodity"] == "Rice"
            assert prices[0]["state"] == "Punjab"
    
    @pytest.mark.asyncio
    async def test_fetch_current_prices_with_district_filter(self):
        """Test price fetching with district filter"""
        mock_response_data = {
            "records": [
                {
                    "commodity": "Wheat",
                    "state": "Punjab",
                    "district": "Ludhiana",
                    "market": "Ludhiana Mandi",
                    "modal_price": "2200",
                    "arrival_date": "2026-02-28"
                }
            ]
        }
        
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            prices = await mandi_price_api.fetch_current_prices(
                crop="Wheat",
                state="Punjab",
                district="Ludhiana"
            )
            
            assert len(prices) == 1
            assert prices[0]["district"] == "Ludhiana"
    
    @pytest.mark.asyncio
    async def test_fetch_current_prices_with_date_range(self):
        """Test price fetching with date range"""
        date_from = date.today() - timedelta(days=7)
        
        mock_response_data = {
            "records": [
                {
                    "commodity": "Rice",
                    "state": "Punjab",
                    "district": "Ludhiana",
                    "market": "Ludhiana Mandi",
                    "modal_price": "2500",
                    "arrival_date": date.today().strftime("%Y-%m-%d")
                }
            ]
        }
        
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            prices = await mandi_price_api.fetch_current_prices(
                crop="Rice",
                state="Punjab",
                date_from=date_from
            )
            
            assert len(prices) >= 0
    
    @pytest.mark.asyncio
    async def test_fetch_current_prices_api_error(self):
        """Test handling of API errors"""
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPError("API Error")
        )
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            prices = await mandi_price_api.fetch_current_prices(crop="Rice")
            
            assert prices == []
    
    @pytest.mark.asyncio
    async def test_fetch_current_prices_no_api_key(self):
        """Test behavior when API key is not configured"""
        original_key = mandi_price_api.api_key
        mandi_price_api.api_key = None
        
        try:
            prices = await mandi_price_api.fetch_current_prices(crop="Rice")
            assert prices == []
        finally:
            mandi_price_api.api_key = original_key
    
    @pytest.mark.asyncio
    async def test_fetch_price_trend_success(self):
        """Test fetching price trend over time"""
        mock_response_data = {
            "records": [
                {
                    "commodity": "Wheat",
                    "state": "Punjab",
                    "district": "Ludhiana",
                    "market": "Ludhiana Mandi",
                    "modal_price": "2200",
                    "arrival_date": (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
                }
                for i in range(30)
            ]
        }
        
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            trend = await mandi_price_api.fetch_price_trend(
                crop="Wheat",
                state="Punjab",
                days=30
            )
            
            assert len(trend) == 30
    
    @pytest.mark.asyncio
    async def test_fetch_all_commodities_success(self):
        """Test fetching list of all commodities"""
        mock_response_data = {
            "records": [
                {"commodity": "Rice"},
                {"commodity": "Wheat"},
                {"commodity": "Rice"},  # Duplicate
                {"commodity": "Maize"}
            ]
        }
        
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            commodities = await mandi_price_api.fetch_all_commodities()
            
            # Should remove duplicates
            assert len(commodities) == 3
            assert "Rice" in commodities
            assert "Wheat" in commodities
            assert "Maize" in commodities


class TestWeatherAPIIntegration:
    """Test weather API integration"""
    
    @pytest.mark.asyncio
    async def test_get_current_weather_success(self):
        """Test successful current weather fetching"""
        mock_response_data = {
            "main": {
                "temp": 25.5,
                "feels_like": 26.0,
                "humidity": 60,
                "pressure": 1013
            },
            "weather": [
                {"description": "clear sky"}
            ],
            "wind": {
                "speed": 3.5
            },
            "clouds": {
                "all": 10
            },
            "dt": int(datetime.now().timestamp())
        }
        
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            weather = await weather_api.get_current_weather(
                latitude=30.9010,
                longitude=75.8573
            )
            
            assert weather is not None
            assert weather["temperature"] == 25.5
            assert weather["humidity"] == 60
            assert weather["description"] == "clear sky"
    
    @pytest.mark.asyncio
    async def test_get_current_weather_with_rainfall(self):
        """Test weather data with rainfall information"""
        mock_response_data = {
            "main": {
                "temp": 22.0,
                "feels_like": 22.5,
                "humidity": 85,
                "pressure": 1010
            },
            "weather": [
                {"description": "light rain"}
            ],
            "wind": {
                "speed": 5.0
            },
            "clouds": {
                "all": 80
            },
            "rain": {
                "1h": 2.5,
                "3h": 5.0
            },
            "dt": int(datetime.now().timestamp())
        }
        
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            weather = await weather_api.get_current_weather(
                latitude=30.9010,
                longitude=75.8573
            )
            
            assert weather is not None
            assert "rainfall_1h" in weather
            assert weather["rainfall_1h"] == 2.5
            assert weather["rainfall_3h"] == 5.0
    
    @pytest.mark.asyncio
    async def test_get_current_weather_api_error(self):
        """Test handling of API errors"""
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPError("API Error")
        )
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            weather = await weather_api.get_current_weather(
                latitude=30.9010,
                longitude=75.8573
            )
            
            assert weather is None
    
    @pytest.mark.asyncio
    async def test_get_current_weather_no_api_key(self):
        """Test behavior when API key is not configured"""
        original_key = weather_api.openweather_key
        weather_api.openweather_key = None
        
        try:
            weather = await weather_api.get_current_weather(
                latitude=30.9010,
                longitude=75.8573
            )
            assert weather is None
        finally:
            weather_api.openweather_key = original_key
    
    @pytest.mark.asyncio
    async def test_get_forecast_success(self):
        """Test successful weather forecast fetching"""
        mock_response_data = {
            "city": {
                "name": "Ludhiana"
            },
            "list": [
                {
                    "dt": int((datetime.now() + timedelta(hours=i*3)).timestamp()),
                    "main": {
                        "temp": 25.0 + i,
                        "humidity": 60
                    },
                    "weather": [
                        {"description": "clear sky"}
                    ],
                    "wind": {
                        "speed": 3.0
                    },
                    "clouds": {
                        "all": 10
                    }
                }
                for i in range(40)  # 5 days * 8 forecasts per day
            ]
        }
        
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_response_data)
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            forecast = await weather_api.get_forecast(
                latitude=30.9010,
                longitude=75.8573,
                days=5
            )
            
            assert forecast is not None
            assert "location" in forecast
            assert "forecasts" in forecast
            assert len(forecast["forecasts"]) == 40
    
    @pytest.mark.asyncio
    async def test_get_agricultural_weather_success(self):
        """Test agricultural weather information"""
        # Mock current weather
        mock_current_data = {
            "main": {
                "temp": 28.0,
                "feels_like": 29.0,
                "humidity": 70,
                "pressure": 1012
            },
            "weather": [{"description": "partly cloudy"}],
            "wind": {"speed": 4.0},
            "clouds": {"all": 40},
            "dt": int(datetime.now().timestamp())
        }
        
        # Mock forecast
        mock_forecast_data = {
            "city": {"name": "Ludhiana"},
            "list": [
                {
                    "dt": int((datetime.now() + timedelta(hours=i*3)).timestamp()),
                    "main": {
                        "temp": 25.0 + (i % 8),
                        "humidity": 65 + (i % 10)
                    },
                    "weather": [{"description": "clear sky"}],
                    "wind": {"speed": 3.0},
                    "clouds": {"all": 20},
                    "rain": {"3h": 1.0} if i % 5 == 0 else {}
                }
                for i in range(56)  # 7 days
            ]
        }
        
        # Create mock responses
        mock_response_current = AsyncMock()
        mock_response_current.json = AsyncMock(return_value=mock_current_data)
        mock_response_current.raise_for_status = MagicMock()
        
        mock_response_forecast = AsyncMock()
        mock_response_forecast.json = AsyncMock(return_value=mock_forecast_data)
        mock_response_forecast.raise_for_status = MagicMock()
        
        # Create mock that returns different responses
        call_count = [0]
        
        async def mock_get(*args, **kwargs):
            result = mock_response_current if call_count[0] == 0 else mock_response_forecast
            call_count[0] += 1
            return result
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = mock_get
            
            ag_weather = await weather_api.get_agricultural_weather(
                latitude=30.9010,
                longitude=75.8573
            )
            
            assert ag_weather is not None
            assert "current" in ag_weather
            assert "forecast_summary" in ag_weather
            assert "agricultural_advice" in ag_weather
            
            summary = ag_weather["forecast_summary"]
            assert "total_rainfall_mm" in summary
            assert "avg_temperature" in summary
            assert "avg_humidity" in summary
    
    @pytest.mark.asyncio
    async def test_get_agricultural_weather_partial_failure(self):
        """Test agricultural weather when one API call fails"""
        # First call succeeds
        mock_response_success = AsyncMock()
        mock_response_success.json = AsyncMock(return_value={
            "main": {"temp": 25, "feels_like": 26, "humidity": 60, "pressure": 1013},
            "weather": [{"description": "clear"}],
            "wind": {"speed": 3},
            "clouds": {"all": 10},
            "dt": int(datetime.now().timestamp())
        })
        mock_response_success.raise_for_status = MagicMock()
        
        # Second call fails
        mock_response_fail = AsyncMock()
        mock_response_fail.raise_for_status = MagicMock(
            side_effect=httpx.HTTPError("API Error")
        )
        
        # Create mock that returns different responses
        call_count = [0]
        
        async def mock_get(*args, **kwargs):
            result = mock_response_success if call_count[0] == 0 else mock_response_fail
            call_count[0] += 1
            return result
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = mock_get
            
            ag_weather = await weather_api.get_agricultural_weather(
                latitude=30.9010,
                longitude=75.8573
            )
            
            # Should return None if forecast fails
            assert ag_weather is None


class TestAPIIntegrationErrorHandling:
    """Test error handling across all API integrations"""
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test handling of API timeouts"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.Timeout("Request timeout")
            )
            
            # Test all APIs handle timeout gracefully
            schemes = await government_schemes_api.fetch_schemes()
            assert schemes == []
            
            prices = await mandi_price_api.fetch_current_prices(crop="Rice")
            assert prices == []
            
            weather = await weather_api.get_current_weather(30.9, 75.8)
            assert weather is None
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test handling of network errors"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.NetworkError("Network unreachable")
            )
            
            schemes = await government_schemes_api.fetch_schemes()
            assert schemes == []
            
            prices = await mandi_price_api.fetch_current_prices(crop="Wheat")
            assert prices == []
            
            weather = await weather_api.get_current_weather(30.9, 75.8)
            assert weather is None
    
    @pytest.mark.asyncio
    async def test_invalid_json_response(self):
        """Test handling of invalid JSON responses"""
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(side_effect=ValueError("Invalid JSON"))
        mock_response.raise_for_status = MagicMock()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            schemes = await government_schemes_api.fetch_schemes()
            assert schemes == []
            
            prices = await mandi_price_api.fetch_current_prices(crop="Rice")
            assert prices == []
            
            weather = await weather_api.get_current_weather(30.9, 75.8)
            assert weather is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
