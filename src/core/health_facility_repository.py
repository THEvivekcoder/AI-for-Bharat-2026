"""Health facility repository for DynamoDB operations."""

from typing import List, Optional
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr
import logging
import math

from src.models.health import HealthFacility
from src.models.location import Location
from .base_repository import BaseRepository, ItemNotFoundError, DynamoDBRepositoryError

logger = logging.getLogger(__name__)


class HealthFacilityRepository(BaseRepository):
    """Repository for health facility operations."""
    
    def __init__(self, table_name: str = "HealthFacilities", region_name: str = "us-east-1"):
        """
        Initialize HealthFacilityRepository.
        
        Args:
            table_name: Name of the HealthFacilities DynamoDB table
            region_name: AWS region name
        """
        super().__init__(table_name, region_name)
    
    def create(self, facility: HealthFacility) -> HealthFacility:
        """
        Create a new health facility in DynamoDB.
        
        Args:
            facility: HealthFacility object to create
            
        Returns:
            Created HealthFacility object
            
        Raises:
            DynamoDBRepositoryError: If creation fails
        """
        try:
            item = self._serialize_item(facility.model_dump())
            
            self.table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(facility_id)'
            )
            
            logger.info(f"Created health facility: {facility.facility_id}")
            return facility
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise DynamoDBRepositoryError(
                    f"Health facility with ID {facility.facility_id} already exists"
                )
            self._handle_client_error(e, "create health facility")
    
    def get(self, facility_id: str) -> HealthFacility:
        """
        Retrieve a health facility by facility_id.
        
        Args:
            facility_id: Unique facility identifier
            
        Returns:
            HealthFacility object
            
        Raises:
            ItemNotFoundError: If facility not found
            DynamoDBRepositoryError: If retrieval fails
        """
        try:
            response = self.table.get_item(Key={'facility_id': facility_id})
            
            if 'Item' not in response:
                raise ItemNotFoundError(f"Health facility with ID {facility_id} not found")
            
            item = self._deserialize_item(response['Item'])
            return HealthFacility(**item)
            
        except ClientError as e:
            self._handle_client_error(e, f"get health facility {facility_id}")
    
    def find_nearby(
        self,
        location: Location,
        radius_km: float = 25.0,
        facility_type: Optional[str] = None
    ) -> List[HealthFacility]:
        """
        Find health facilities near a location within a radius.
        
        Args:
            location: User location with latitude and longitude
            radius_km: Search radius in kilometers
            facility_type: Optional filter by facility type
            
        Returns:
            List of HealthFacility objects sorted by distance
            
        Raises:
            DynamoDBRepositoryError: If search fails
        """
        if location.latitude is None or location.longitude is None:
            raise DynamoDBRepositoryError(
                "Location must have latitude and longitude for proximity search"
            )
        
        try:
            # Build filter expression
            filter_expr = None
            
            # Filter by state and district for efficiency
            filter_expr = Attr('location.state').eq(location.state)
            filter_expr = filter_expr & Attr('location.district').eq(location.district)
            
            # Add facility type filter if provided
            if facility_type:
                filter_expr = filter_expr & Attr('facility_type').eq(facility_type)
            
            # Scan with filters
            scan_params = {'FilterExpression': filter_expr}
            response = self.table.scan(**scan_params)
            
            # Calculate distances and filter by radius
            facilities_with_distance = []
            for item in response.get('Items', []):
                deserialized = self._deserialize_item(item)
                facility = HealthFacility(**deserialized)
                
                # Calculate distance
                if facility.location.latitude and facility.location.longitude:
                    distance = self._calculate_distance(
                        location.latitude,
                        location.longitude,
                        facility.location.latitude,
                        facility.location.longitude
                    )
                    
                    # Only include facilities within radius
                    if distance <= radius_km:
                        facility.distance_km = round(distance, 2)
                        facilities_with_distance.append(facility)
            
            # Sort by distance
            facilities_with_distance.sort(key=lambda f: f.distance_km or float('inf'))
            
            return facilities_with_distance
            
        except ClientError as e:
            self._handle_client_error(e, "find nearby health facilities")
    
    def _calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate distance between two coordinates using Haversine formula.
        
        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point
            
        Returns:
            Distance in kilometers
        """
        # Earth radius in kilometers
        R = 6371.0
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c
        return distance
    
    def get_all(self, limit: int = 100) -> List[HealthFacility]:
        """
        Get all health facilities.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of HealthFacility objects
            
        Raises:
            DynamoDBRepositoryError: If retrieval fails
        """
        try:
            response = self.table.scan(Limit=limit)
            
            facilities = []
            for item in response.get('Items', []):
                deserialized = self._deserialize_item(item)
                facilities.append(HealthFacility(**deserialized))
            
            return facilities
            
        except ClientError as e:
            self._handle_client_error(e, "get all health facilities")
