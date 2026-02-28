# Farmer Advisory Service Implementation

## Overview

The Farmer Advisory Service provides comprehensive agricultural guidance to farmers, including crop recommendations, fertilizer advice, market prices, and crop calendars. This implementation follows the design specifications from the BharatSahayak project.

## Components Implemented

### 1. Data Models (`app/models/farmer.py`)

Created five database models:

- **FarmProfile**: Stores farmer's land details (size, soil type, irrigation, location, crops)
- **CropRecommendation**: Records crop recommendations with suitability scores
- **FertilizerRecommendation**: Stores fertilizer guidance for specific crops and stages
- **MandiPrice**: Market price data for crops at different mandis
- **CropCalendar**: Planting and harvest schedules for crops by region

### 2. Pydantic Schemas (`app/schemas/farmer.py`)

Created request/response schemas for all farmer advisory operations:

- Farm profile management (create, update, response)
- Crop recommendations (request, response)
- Fertilizer recommendations (request with soil data, response)
- Mandi prices (query, response, trend)
- Crop calendar (request, response)

### 3. Services

#### Crop Advisor (`app/services/crop_advisor.py`)

**Features:**
- Recommends suitable crops based on farm profile and season
- Calculates suitability scores (0-1) considering:
  - Soil type compatibility
  - Irrigation type match
  - Water requirement vs irrigation capability
  - Land size considerations
- Provides crop calendars with planting/harvest schedules
- Includes reasoning for each recommendation
- Supports 9 major crops: rice, wheat, cotton, sugarcane, maize, pulses, groundnut, soybean, vegetables

**Key Methods:**
- `recommend_crops()`: Generate ranked crop recommendations
- `get_crop_calendar()`: Retrieve planting/harvest schedules
- `_calculate_suitability_score()`: Score crops based on farm characteristics

#### Fertilizer Advisor (`app/services/fertilizer_advisor.py`)

**Features:**
- Provides fertilizer recommendations based on:
  - Crop type
  - Growth stage (sowing, vegetative, flowering, fruiting, maturity)
  - Soil test data (pH, NPK levels)
  - Farm characteristics
- Adjusts recommendations based on soil nutrient levels
- Includes application timing and methods
- Provides additional notes for organic matter and micronutrients

**Key Methods:**
- `recommend_fertilizer()`: Generate fertilizer recommendation
- `_adjust_for_soil_data()`: Modify recommendations based on soil tests
- `_generate_additional_notes()`: Provide context-specific guidance

#### Mandi Price Service (`app/services/mandi_price_service.py`)

**Features:**
- Retrieves current market prices within specified radius
- Calculates distances using Haversine formula
- Provides price trends over time
- Caches results for performance
- Supports bulk price updates from external APIs

**Key Methods:**
- `get_current_price()`: Get prices within radius, sorted by distance
- `get_price_trend()`: Historical price analysis with trend detection
- `update_prices()`: Bulk update from external data sources
- `seed_sample_prices()`: Populate with test data

### 4. API Endpoints (`app/api/farmer.py`)

Implemented 8 RESTful endpoints:

#### Farm Profile Management
- `POST /api/farmer/profile` - Create farm profile
- `GET /api/farmer/profile` - Get current user's farm profile
- `PUT /api/farmer/profile` - Update farm profile

#### Advisory Services
- `POST /api/farmer/crop-advice` - Get crop recommendations for a season
- `POST /api/farmer/fertilizer-advice` - Get fertilizer guidance
- `GET /api/farmer/market-price` - Get mandi prices within radius
- `GET /api/farmer/market-price/trend` - Get price trend over time
- `GET /api/farmer/crop-calendar` - Get crop planting/harvest schedule

All endpoints require authentication and use the current user's farm profile.

### 5. Database Migration

Created migration `2026_02_27_1401-406ef543f8b6_add_farmer_tables.py` with:
- farm_profiles table
- crop_recommendations table
- fertilizer_recommendations table
- mandi_prices table (with spatial indexing support)
- crop_calendars table

## Testing

Created comprehensive test script (`scripts/test_farmer_service.py`) that validates:

1. **Crop Advisor**:
   - Kharif and Rabi season recommendations
   - Suitability scoring
   - Crop calendar retrieval

2. **Fertilizer Advisor**:
   - Stage-specific recommendations
   - Soil data adjustments
   - Unknown crop handling

3. **Mandi Price Service**:
   - Sample data seeding
   - Distance-based price retrieval
   - Price trend analysis

All tests passed successfully.

## Key Features

### Intelligent Crop Recommendations
- Multi-factor suitability scoring
- Season-aware filtering
- Soil and irrigation compatibility
- Market demand consideration
- Risk assessment

### Comprehensive Fertilizer Guidance
- Growth stage-specific recommendations
- Soil test data integration
- NPK ratio recommendations
- Application timing and methods
- Organic matter suggestions

### Market Price Intelligence
- Radius-based mandi search
- Distance calculation and sorting
- Price trend analysis
- Caching for performance
- Support for external API integration

### Crop Calendar
- Region-specific schedules
- Planting and harvest windows
- Care activity timelines
- Default calendars for common crops

## Data Coverage

### Crops Supported
- Rice, Wheat, Cotton, Sugarcane
- Maize, Pulses, Groundnut, Soybean
- Vegetables (general category)

### Soil Types
- Clay, Loam, Sandy, Silt
- Black, Red, Laterite, Alluvial

### Irrigation Types
- Rainfed, Canal, Well, Borewell
- Drip, Sprinkler

### Growth Stages
- Sowing, Vegetative, Flowering
- Fruiting, Maturity

## Integration Points

1. **Authentication**: All endpoints require valid JWT token
2. **Location Services**: Uses Location model for spatial queries
3. **Caching**: Redis integration for mandi price caching
4. **External APIs**: Ready for integration with government mandi price APIs

## Future Enhancements

1. **Weather Integration**: Incorporate real-time weather data in recommendations
2. **ML Models**: Use machine learning for yield prediction
3. **Pest/Disease Advisory**: Add pest and disease management guidance
4. **Government Scheme Integration**: Link to relevant agricultural schemes
5. **Market Linkage**: Connect farmers with buyers
6. **Soil Testing**: Integration with soil testing labs

## API Usage Examples

### Create Farm Profile
```bash
POST /api/farmer/profile
Authorization: Bearer <token>
{
  "land_size_acres": 5.0,
  "soil_type": "loam",
  "irrigation_type": "canal",
  "location": {
    "state": "Punjab",
    "district": "Ludhiana",
    "pincode": "141001"
  },
  "current_crops": ["wheat"]
}
```

### Get Crop Recommendations
```bash
POST /api/farmer/crop-advice
Authorization: Bearer <token>
{
  "season": "kharif",
  "include_weather": true
}
```

### Get Fertilizer Advice
```bash
POST /api/farmer/fertilizer-advice
Authorization: Bearer <token>
{
  "crop_name": "rice",
  "growth_stage": "vegetative",
  "soil_data": {
    "soil_ph": 6.5,
    "nitrogen_level": "low"
  }
}
```

### Get Market Prices
```bash
GET /api/farmer/market-price?crop_name=rice&radius_km=50
Authorization: Bearer <token>
```

## Conclusion

The Farmer Advisory Service is now fully implemented with all core features operational. The service provides intelligent, data-driven agricultural guidance to help farmers make informed decisions about crop selection, fertilizer application, and market timing.
