"""Lambda handler for mandi price information."""

import json
import os
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import boto3
from decimal import Decimal

from src.models.mandi import MandiPrice, MandiPriceQuery
from src.services.agmarknet_service import AgmarknetService
from src.utils.distance_calculator import DistanceCalculator

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
MANDI_PRICES_TABLE = os.environ.get('MANDI_PRICES_TABLE', 'bharatsahayak-mandi-prices-dev')
mandi_prices_table = dynamodb.Table(MANDI_PRICES_TABLE)

# Initialize AGMARKNET service
AGMARKNET_API_KEY = os.environ.get('AGMARKNET_API_KEY')
agmarknet_service = AgmarknetService(api_key=AGMARKNET_API_KEY)


# Mock mandi price data (in production, this would come from government API)
# Government APIs: https://data.gov.in/catalog/daily-prices-various-commodities
MOCK_MANDI_DATA = {
    "Maharashtra": {
        "Pune": [
            {"mandi": "Pune APMC", "wheat": 2500, "rice": 3000, "soybean": 4500, "cotton": 6000},
            {"mandi": "Hadapsar Market", "wheat": 2450, "rice": 2950, "soybean": 4400, "cotton": 5900},
        ],
        "Mumbai": [
            {"mandi": "Vashi APMC", "wheat": 2600, "rice": 3100, "soybean": 4600, "cotton": 6100},
        ],
        "Nagpur": [
            {"mandi": "Nagpur APMC", "wheat": 2400, "rice": 2900, "soybean": 4300, "cotton": 5800},
        ]
    },
    "Karnataka": {
        "Bangalore": [
            {"mandi": "Bangalore APMC", "wheat": 2550, "rice": 3050, "soybean": 4550, "cotton": 6050},
        ],
        "Mysore": [
            {"mandi": "Mysore Market", "wheat": 2500, "rice": 3000, "soybean": 4500, "cotton": 6000},
        ]
    },
    "Gujarat": {
        "Ahmedabad": [
            {"mandi": "Ahmedabad APMC", "wheat": 2600, "rice": 3100, "soybean": 4600, "cotton": 6200},
        ]
    }
}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle GET /farmer/market-price requests.
    
    Query Parameters:
        crop_name: Crop name (required)
        state: User's state (required)
        district: User's district (required)
        radius_km: Search radius in km (optional, default 50)
    
    Response:
    {
        "prices": [
            {
                "mandi_name": "...",
                "crop_name": "...",
                "state": "...",
                "district": "...",
                "price_per_quintal": 2500.0,
                "price_date": "...",
                "distance_km": 15.5
            }
        ],
        "last_updated": "...",
        "source": "government_api"
    }
    
    Error Responses:
    - 400: Invalid query parameters
    - 404: No prices found
    - 500: Internal server error
    """
    try:
        # Extract query parameters
        query_params = event.get('queryStringParameters') or {}
        
        # Validate required parameters
        crop_name = query_params.get('crop_name')
        state = query_params.get('state')
        district = query_params.get('district')
        
        if not all([crop_name, state, district]):
            return error_response(400, "Missing required parameters: crop_name, state, district")
        
        # Parse radius (optional)
        radius_km = int(query_params.get('radius_km', 50))
        
        # Validate query
        try:
            query = MandiPriceQuery(
                crop_name=crop_name,
                state=state,
                district=district,
                radius_km=radius_km
            )
        except Exception as e:
            logger.error(f"Invalid query parameters: {str(e)}")
            return error_response(400, f"Invalid query parameters: {str(e)}")
        
        logger.info(f"Fetching mandi prices: crop={crop_name}, state={state}, district={district}, radius={radius_km}km")
        
        # Try to get cached prices from DynamoDB
        cached_prices = _get_cached_prices(query)
        
        if cached_prices:
            logger.info(f"Returning {len(cached_prices)} cached prices")
            return success_response({
                'prices': cached_prices,
                'last_updated': datetime.now().isoformat(),
                'source': 'cache'
            })
        
        # Fetch fresh prices (mock implementation)
        fresh_prices = _fetch_fresh_prices(query)
        
        if not fresh_prices:
            return error_response(404, f"No prices found for {crop_name} in {district}, {state}")
        
        # Cache prices in DynamoDB
        _cache_prices(fresh_prices)
        
        logger.info(f"Returning {len(fresh_prices)} fresh prices")
        return success_response({
            'prices': fresh_prices,
            'last_updated': datetime.now().isoformat(),
            'source': 'government_api'
        })
        
    except ValueError as e:
        logger.error(f"Invalid parameter value: {str(e)}")
        return error_response(400, f"Invalid parameter value: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return error_response(500, "Internal server error")


def _get_cached_prices(query: MandiPriceQuery) -> List[Dict[str, Any]]:
    """
    Get cached prices from DynamoDB.
    
    Returns cached prices if they are less than 24 hours old.
    """
    try:
        # Query DynamoDB for cached prices
        response = mandi_prices_table.query(
            KeyConditionExpression='crop_name = :crop AND begins_with(state_district, :location)',
            ExpressionAttributeValues={
                ':crop': query.crop_name.lower(),
                ':location': f"{query.state}#{query.district}"
            }
        )
        
        items = response.get('Items', [])
        
        if not items:
            return []
        
        # Filter by date (only return prices less than 24 hours old)
        cutoff_date = datetime.now() - timedelta(hours=24)
        fresh_items = []
        
        for item in items:
            price_date = datetime.fromisoformat(item['price_date'])
            if price_date >= cutoff_date:
                fresh_items.append({
                    'mandi_name': item['mandi_name'],
                    'crop_name': item['crop_name'],
                    'state': item['state'],
                    'district': item['district'],
                    'price_per_quintal': float(item['price_per_quintal']),
                    'price_date': item['price_date'],
                    'distance_km': float(item.get('distance_km', 0))
                })
        
        return fresh_items
        
    except Exception as e:
        logger.warning(f"Error fetching cached prices: {str(e)}")
        return []


def _fetch_fresh_prices(query: MandiPriceQuery) -> List[Dict[str, Any]]:
    """
    Fetch fresh prices from AGMARKNET API.
    
    This function:
    1. Calls the AGMARKNET API via data.gov.in
    2. Filters results by radius
    3. Calculates distances from user location
    4. Sorts by distance
    
    Falls back to mock data if API is unavailable.
    """
    prices = []
    
    try:
        # Map crop name to AGMARKNET commodity name
        commodity = agmarknet_service.get_commodity_mapping(query.crop_name)
        
        # Fetch prices from AGMARKNET API
        logger.info(f"Fetching prices from AGMARKNET API for {commodity}")
        agmarknet_prices = agmarknet_service.fetch_prices(
            commodity=commodity,
            state=query.state,
            limit=100
        )
        
        if not agmarknet_prices:
            logger.warning(f"No prices found from AGMARKNET API, falling back to mock data")
            return _fetch_mock_prices(query)
        
        # Process and filter prices
        for agm_price in agmarknet_prices:
            # Calculate distance
            distance = DistanceCalculator.calculate_distance(
                query.state, query.district,
                agm_price.state, agm_price.district
            )
            
            # If distance calculation fails, use approximate distance
            if distance is None:
                # Same state but unknown coordinates - assume nearby
                if agm_price.state == query.state:
                    distance = 45.0 if agm_price.district != query.district else 0.0
                else:
                    # Different state - skip
                    continue
            
            # Filter by radius
            if distance > query.radius_km:
                continue
            
            # Add to results
            prices.append({
                'mandi_name': agm_price.market,
                'crop_name': query.crop_name,
                'state': agm_price.state,
                'district': agm_price.district,
                'price_per_quintal': agm_price.modal_price,  # Use modal price
                'price_date': agm_price.arrival_date or datetime.now().isoformat(),
                'distance_km': round(distance, 2)
            })
        
        # Sort by distance
        prices.sort(key=lambda x: x['distance_km'])
        
        logger.info(f"Fetched {len(prices)} prices from AGMARKNET API")
        return prices
        
    except Exception as e:
        logger.error(f"Error fetching from AGMARKNET API: {e}", exc_info=True)
        logger.info("Falling back to mock data")
        return _fetch_mock_prices(query)


def _fetch_mock_prices(query: MandiPriceQuery) -> List[Dict[str, Any]]:
    """
    Fetch prices from mock data (fallback when API is unavailable).
    
    This is used for:
    - Development and testing
    - Fallback when AGMARKNET API is down
    - Offline mode
    """
    prices = []
    crop_key = query.crop_name.lower()
    
    # Get prices from user's district
    if query.state in MOCK_MANDI_DATA:
        state_data = MOCK_MANDI_DATA[query.state]
        
        if query.district in state_data:
            district_mandis = state_data[query.district]
            
            for mandi_data in district_mandis:
                if crop_key in mandi_data:
                    prices.append({
                        'mandi_name': mandi_data['mandi'],
                        'crop_name': query.crop_name,
                        'state': query.state,
                        'district': query.district,
                        'price_per_quintal': float(mandi_data[crop_key]),
                        'price_date': datetime.now().isoformat(),
                        'distance_km': 0.0  # Same district
                    })
        
        # Get prices from nearby districts (within radius)
        for district, mandis in state_data.items():
            if district != query.district:
                for mandi_data in mandis:
                    if crop_key in mandi_data:
                        # Calculate distance
                        distance = DistanceCalculator.calculate_distance(
                            query.state, query.district,
                            query.state, district
                        )
                        
                        # Use approximate distance if calculation fails
                        if distance is None:
                            distance = 45.0
                        
                        if distance <= query.radius_km:
                            prices.append({
                                'mandi_name': mandi_data['mandi'],
                                'crop_name': query.crop_name,
                                'state': query.state,
                                'district': district,
                                'price_per_quintal': float(mandi_data[crop_key]),
                                'price_date': datetime.now().isoformat(),
                                'distance_km': round(distance, 2)
                            })
    
    # Sort by distance
    prices.sort(key=lambda x: x['distance_km'])
    
    return prices


def _cache_prices(prices: List[Dict[str, Any]]) -> None:
    """Cache prices in DynamoDB for offline access."""
    try:
        with mandi_prices_table.batch_writer() as batch:
            for price in prices:
                # Convert float to Decimal for DynamoDB
                item = {
                    'crop_name': price['crop_name'].lower(),
                    'state_district': f"{price['state']}#{price['district']}",
                    'mandi_name': price['mandi_name'],
                    'state': price['state'],
                    'district': price['district'],
                    'price_per_quintal': Decimal(str(price['price_per_quintal'])),
                    'price_date': price['price_date'],
                    'distance_km': Decimal(str(price['distance_km'])),
                    'cached_at': datetime.now().isoformat()
                }
                batch.put_item(Item=item)
        
        logger.info(f"Cached {len(prices)} prices in DynamoDB")
        
    except Exception as e:
        logger.warning(f"Error caching prices: {str(e)}")
        # Don't fail the request if caching fails


def success_response(data: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
    """Create a successful API response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(data)
    }


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Create an error API response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': message
        })
    }
