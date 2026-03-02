"""Lambda handler for health facility search."""

import json
import os
import logging
from typing import Dict, Any

from src.models.location import Location
from src.core.health_facility_repository import HealthFacilityRepository, DynamoDBRepositoryError

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize repository
HEALTH_FACILITIES_TABLE = os.environ.get('HEALTH_FACILITIES_TABLE', 'bharatsahayak-health-facilities-dev')
repository = HealthFacilityRepository(table_name=HEALTH_FACILITIES_TABLE)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle GET /health/facilities requests.
    
    Query Parameters:
        state: User's state (required)
        district: User's district (required)
        latitude: User's latitude (required for distance calculation)
        longitude: User's longitude (required for distance calculation)
        pincode: User's pincode (required)
        radius_km: Search radius in km (optional, default 25)
        facility_type: Filter by facility type (optional)
    
    Response:
    {
        "facilities": [
            {
                "facility_id": "...",
                "name": "...",
                "facility_type": "...",
                "location": {...},
                "address": "...",
                "contact": "...",
                "services": [...],
                "distance_km": 5.2
            }
        ],
        "count": 3
    }
    
    Error Responses:
    - 400: Invalid query parameters
    - 404: No facilities found
    - 500: Internal server error
    """
    try:
        # Extract query parameters
        query_params = event.get('queryStringParameters') or {}
        
        # Validate required parameters
        state = query_params.get('state')
        district = query_params.get('district')
        pincode = query_params.get('pincode')
        latitude_str = query_params.get('latitude')
        longitude_str = query_params.get('longitude')
        
        if not all([state, district, pincode, latitude_str, longitude_str]):
            return error_response(
                400,
                "Missing required parameters: state, district, pincode, latitude, longitude"
            )
        
        # Parse coordinates
        try:
            latitude = float(latitude_str)
            longitude = float(longitude_str)
        except ValueError:
            return error_response(400, "Invalid latitude or longitude format")
        
        # Parse optional parameters
        radius_km = float(query_params.get('radius_km', 25.0))
        facility_type = query_params.get('facility_type')
        
        # Create location object
        try:
            location = Location(
                state=state,
                district=district,
                pincode=pincode,
                latitude=latitude,
                longitude=longitude
            )
        except Exception as e:
            logger.error(f"Invalid location parameters: {str(e)}")
            return error_response(400, f"Invalid location parameters: {str(e)}")
        
        logger.info(
            f"Searching health facilities: state={state}, district={district}, "
            f"radius={radius_km}km, type={facility_type}"
        )
        
        # Search for nearby facilities
        facilities = repository.find_nearby(
            location=location,
            radius_km=radius_km,
            facility_type=facility_type
        )
        
        if not facilities:
            return error_response(
                404,
                f"No health facilities found within {radius_km}km of {district}, {state}"
            )
        
        # Convert to response format
        facilities_data = [facility.model_dump() for facility in facilities]
        
        logger.info(f"Found {len(facilities)} health facilities")
        return success_response({
            'facilities': facilities_data,
            'count': len(facilities)
        })
        
    except DynamoDBRepositoryError as e:
        logger.error(f"Repository error: {str(e)}")
        return error_response(500, "Error accessing health facility database")
    
    except ValueError as e:
        logger.error(f"Invalid parameter value: {str(e)}")
        return error_response(400, f"Invalid parameter value: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return error_response(500, "Internal server error")


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
