# External API Integrations

This directory contains integrations with external APIs for fetching real-time data.

## Available Integrations

### 1. Government Schemes API (`government_schemes_api.py`)
Integrates with data.gov.in and other government portals for scheme information.

**Features:**
- Fetch government schemes by category and state
- Get detailed scheme information
- Verify scheme existence

**Configuration:**
```bash
DATA_GOV_IN_API_KEY=your-api-key
```

**Usage:**
```python
from app.integrations.government_schemes_api import government_schemes_api

# Fetch schemes
schemes = await government_schemes_api.fetch_schemes(
    category="agriculture",
    state="Punjab",
    limit=100
)

# Get scheme details
details = await government_schemes_api.fetch_scheme_details(scheme_id="PM-KISAN")
```

### 2. Mandi Price API (`mandi_price_api.py`)
Integrates with Agmarknet and agricultural market price APIs.

**Features:**
- Fetch current mandi prices for crops
- Get price trends over time
- List available commodities

**Configuration:**
```bash
AGMARKNET_API_KEY=your-api-key
```

**Usage:**
```python
from app.integrations.mandi_price_api import mandi_price_api

# Fetch current prices
prices = await mandi_price_api.fetch_current_prices(
    crop="Rice",
    state="Punjab",
    district="Ludhiana"
)

# Get price trend
trend = await mandi_price_api.fetch_price_trend(
    crop="Wheat",
    state="Punjab",
    days=30
)
```

### 3. Weather API (`weather_api.py`)
Integrates with OpenWeatherMap and India Meteorological Department.

**Features:**
- Get current weather conditions
- Fetch weather forecasts
- Agricultural weather analysis

**Configuration:**
```bash
OPENWEATHER_API_KEY=your-api-key
IMD_API_KEY=your-imd-api-key
```

**Usage:**
```python
from app.integrations.weather_api import weather_api

# Get current weather
weather = await weather_api.get_current_weather(
    latitude=30.9010,
    longitude=75.8573
)

# Get forecast
forecast = await weather_api.get_forecast(
    latitude=30.9010,
    longitude=75.8573,
    days=7
)

# Get agricultural weather
ag_weather = await weather_api.get_agricultural_weather(
    latitude=30.9010,
    longitude=75.8573
)
```

## API Key Management

API keys are managed centrally in `api_keys.py` and loaded from environment variables.

### Setting Up API Keys

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Add your API keys to `.env`:
```bash
# Government Data APIs
DATA_GOV_IN_API_KEY=your-key-here
AGMARKNET_API_KEY=your-key-here

# Weather APIs
OPENWEATHER_API_KEY=your-key-here
IMD_API_KEY=your-key-here
```

3. API keys are automatically loaded when the application starts.

## Obtaining API Keys

### data.gov.in
1. Visit https://data.gov.in/
2. Register for an account
3. Request API access
4. Generate API key from dashboard

### Agmarknet
1. Visit https://agmarknet.gov.in/
2. Contact for API access
3. Follow their API documentation

### OpenWeatherMap
1. Visit https://openweathermap.org/api
2. Sign up for free account
3. Generate API key from dashboard
4. Free tier includes:
   - Current weather data
   - 5-day forecast
   - 1000 calls/day

### India Meteorological Department (IMD)
1. Visit https://mausam.imd.gov.in/
2. Contact for API access
3. Follow their guidelines

## Error Handling

All API integrations include:
- Timeout handling (30 seconds default)
- HTTP error handling
- Logging of errors
- Graceful fallbacks

## Rate Limiting

Be aware of rate limits for each API:
- **data.gov.in**: Varies by dataset
- **Agmarknet**: Check documentation
- **OpenWeatherMap Free**: 1000 calls/day, 60 calls/minute

## Testing

Test API integrations without actual API calls:

```python
# Mock API responses for testing
from unittest.mock import AsyncMock, patch

@patch('app.integrations.weather_api.weather_api.get_current_weather')
async def test_weather(mock_weather):
    mock_weather.return_value = {"temperature": 25, "humidity": 60}
    # Your test code here
```

## Future Integrations

Planned integrations:
- SMS/OTP service (Twilio)
- Translation APIs (Bhashini, Google Translate)
- Additional government portals
- State-specific APIs

## Notes

- All API calls are asynchronous using `httpx`
- Responses are cached where appropriate
- Failed API calls return empty results or None
- Always check for None/empty responses before using data
